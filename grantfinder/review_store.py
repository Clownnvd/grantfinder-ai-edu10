from __future__ import annotations

import os
import uuid
from datetime import datetime
from threading import Lock

from psycopg import connect
from psycopg.rows import dict_row

from grantfinder.models import ReviewDecision, ReviewRequest


class ReviewStore:
    """Review persistence with a memory backend for tests and PostgreSQL for deploy."""

    def __init__(self) -> None:
        self.backend = os.getenv("REVIEW_STORE_BACKEND", "memory")
        self.database_url = os.getenv("DATABASE_URL")
        self._records: dict[str, dict] = {}
        self._lock = Lock()
        if self.backend == "postgres" and not self.database_url:
            raise RuntimeError("review_store_database_url_required")

    def create(self, request: ReviewRequest) -> dict:
        review_id = "review-" + uuid.uuid4().hex[:10]
        created_at = datetime.now()
        if self.backend == "postgres":
            assert self.database_url is not None
            with connect(self.database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO review_requests(
                            id, draft_id, opportunity_id, status,
                            researcher_note, created_at
                        ) VALUES (%s, %s, %s, 'pending', %s, %s)
                        RETURNING *
                        """,
                        (
                            review_id,
                            request.draft_id,
                            request.opportunity_id,
                            request.note,
                            created_at,
                        ),
                    )
                    row = cursor.fetchone()
                connection.commit()
            if row is None:
                raise RuntimeError("review_insert_failed")
            return self._serialize(row)

        record = {
            "review_id": review_id,
            "draft_id": request.draft_id,
            "opportunity_id": request.opportunity_id,
            "note": request.note,
            "status": "pending",
            "created_at": created_at.isoformat(timespec="seconds"),
            "decision": None,
        }
        with self._lock:
            self._records[review_id] = record
        return dict(record)

    def decide(self, review_id: str, decision: ReviewDecision) -> dict:
        status = "approved" if decision.approved else "changes_requested"
        decided_at = datetime.now()
        if self.backend == "postgres":
            assert self.database_url is not None
            with connect(self.database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE review_requests
                        SET status=%s, manager_note=%s, decided_at=%s
                        WHERE id=%s
                        RETURNING *
                        """,
                        (status, decision.note, decided_at, review_id),
                    )
                    row = cursor.fetchone()
                connection.commit()
            if row is None:
                raise KeyError("review_not_found")
            return self._serialize(row)

        with self._lock:
            if review_id not in self._records:
                raise KeyError("review_not_found")
            record = self._records[review_id]
            record["status"] = status
            record["decision"] = {
                "approved": decision.approved,
                "note": decision.note,
                "decided_at": decided_at.isoformat(timespec="seconds"),
            }
            return dict(record)

    def list(self) -> list[dict]:
        if self.backend == "postgres":
            assert self.database_url is not None
            with connect(self.database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM review_requests ORDER BY created_at DESC"
                    )
                    rows = cursor.fetchall()
            return [self._serialize(row) for row in rows]

        with self._lock:
            return [dict(item) for item in self._records.values()]

    @staticmethod
    def _serialize(row: dict) -> dict:
        decision = None
        if row.get("decided_at") is not None:
            decision = {
                "approved": row["status"] == "approved",
                "note": row.get("manager_note", ""),
                "decided_at": row["decided_at"].isoformat(timespec="seconds"),
            }
        return {
            "review_id": row["id"],
            "draft_id": row["draft_id"],
            "opportunity_id": row["opportunity_id"],
            "note": row.get("researcher_note", ""),
            "status": row["status"],
            "created_at": row["created_at"].isoformat(timespec="seconds"),
            "decision": decision,
        }
