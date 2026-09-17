from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from grantfinder.catalog import fold, get_catalog
from grantfinder.models import (
    DraftRequest,
    DraftResponse,
    MatchRequest,
    MatchResponse,
    ReviewDecision,
    ReviewRequest,
)
from grantfinder.workflow import GrantWorkflow

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(
    title="GrantFinder AI API",
    version="0.2.0",
    description=(
        "Grounded grant discovery, eligibility triage and proposal drafting "
        "orchestrated by LangGraph with HITL."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3002",
    ],
    allow_origin_regex=r"https://.*\.(up\.railway\.app|vercel\.app|pages\.dev)",
    allow_methods=["*"],
    allow_headers=["*"],
)
workflow = GrantWorkflow()
catalog = get_catalog()


@app.get("/health")
def health() -> dict:
    stats = catalog.stats()
    return {
        "ok": True,
        "service": "grantfinder-bff",
        "open_opportunities": stats["open_opportunities"],
        "snapshot_date": stats["snapshot_date"],
        "retrieval_mode": stats["retrieval_mode"],
        "orchestration": "langgraph",
        "checkpointing": workflow.checkpoint_backend,
        "review_persistence": workflow.review_store.backend,
        "human_review_required": True,
    }


@app.get("/api/v1/graph/runs/{run_id}")
def graph_run(run_id: str) -> dict:
    try:
        return workflow.inspect_run(run_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/v1/sources")
def sources() -> dict:
    stats = catalog.stats()
    return {
        **stats,
        "sources": [
            {
                "name": "Grants.gov",
                "role": "Cơ hội quốc tế",
                "mode": "Daily XML + public API",
                "provenance": "official",
                "count": stats["by_source"].get("Grants.gov", 0),
            },
            {
                "name": "NAFOSTED",
                "role": "Cơ hội Việt Nam",
                "mode": "Public WordPress REST + manual source audit",
                "provenance": "official",
                "count": stats["by_source"].get("NAFOSTED", 0),
            },
            {
                "name": "OpenAlex",
                "role": "Hồ sơ công bố nhà nghiên cứu",
                "mode": "REST on demand",
                "provenance": "official",
                "count": None,
            },
            {
                "name": "CORDIS",
                "role": "Dự án EU đã được tài trợ",
                "mode": "Bulk CSV/JSON",
                "provenance": "official",
                "count": None,
            },
        ],
    }


@app.get("/api/v1/monitoring")
def monitoring() -> dict:
    today = datetime.now(UTC).date()
    soon = today + timedelta(days=30)
    counts = {"active": 0, "closing_soon": 0, "expired": 0, "needs_review": 0}
    items = []
    for item in catalog.items:
        if item.close_date is None:
            status = "needs_review"
        elif item.close_date < today:
            status = "expired"
        elif item.close_date <= soon:
            status = "closing_soon"
        else:
            status = "active"
        counts[status] += 1
        items.append(
            {
                "id": item.id,
                "title": item.title,
                "source": item.source,
                "close_date": item.close_date,
                "status": status,
                "canonical_url": item.canonical_url,
            }
        )
    priority = {"closing_soon": 0, "needs_review": 1, "active": 2, "expired": 3}
    items.sort(
        key=lambda item: (
            priority[item["status"]],
            item["close_date"] or date.max,
        )
    )
    return {
        "checked_at": today,
        "snapshot_date": catalog.stats()["snapshot_date"],
        "counts": counts,
        "items": items[:30],
        "limitations": (
            "Corpus chính chỉ chứa call đang mở tại snapshot; call hết hạn được "
            "đánh dấu khi đồng bộ nguồn và không dùng cho matching."
        ),
    }


@app.get("/api/v1/opportunities")
def opportunities(
    q: str = "",
    source: str = "",
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    query = fold(q)
    selected = []
    for item in catalog.items:
        if source and fold(item.source) != fold(source):
            continue
        searchable = fold(
            " ".join(
                [
                    item.title,
                    item.issuer,
                    item.description,
                    " ".join(item.funding_categories),
                ]
            )
        )
        if query and not all(term in searchable for term in query.split()):
            continue
        selected.append(item)
        if len(selected) >= limit:
            break
    return {"count": len(selected), "items": selected}


@app.get("/api/v1/opportunities/{opportunity_id}")
def opportunity(opportunity_id: str):
    item = catalog.get(opportunity_id)
    if item is None:
        raise HTTPException(404, "Opportunity not found")
    return item


@app.post("/api/v1/match", response_model=MatchResponse)
def match(request: MatchRequest):
    return workflow.match(request)


@app.post("/api/v1/proposals/draft", response_model=DraftResponse)
def draft(request: DraftRequest):
    try:
        return workflow.draft(request)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(
            409,
            {
                "code": str(exc),
                "message": (
                    "Nhà nghiên cứu phải chọn và xác nhận cơ hội trước khi "
                    "tạo bản nháp."
                ),
            },
        ) from exc


@app.post("/api/v1/reviews")
def request_review(request: ReviewRequest):
    try:
        return workflow.request_review(request)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc


@app.get("/api/v1/reviews")
def reviews():
    return {"items": workflow.list_reviews()}


@app.post("/api/v1/reviews/{review_id}/decision")
def decide(review_id: str, decision: ReviewDecision):
    try:
        return workflow.decide(review_id, decision)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/v1/evaluation")
def evaluation():
    path = ROOT / "artifacts" / "eval" / "grantfinder_eval.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": "not_run",
        "message": (
            "Chạy python -m grantfinder.eval để tạo benchmark; "
            "không hiển thị số liệu giả."
        ),
    }
