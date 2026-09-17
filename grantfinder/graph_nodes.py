from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from typing import Literal

from psycopg import Error as PsycopgError

from grantfinder.catalog import GrantCatalog, rerank
from grantfinder.graph_state import (
    DRAFT_MISSING_INFORMATION,
    MATCH_LIMITATIONS,
    DraftGraphState,
    MatchGraphState,
)
from grantfinder.llm import improve_draft
from grantfinder.models import ToolEvent


def tool_event(
    *,
    step: int,
    tool: str,
    status: Literal["started", "succeeded", "failed", "waiting_for_human"],
    started_at: float,
    input_summary: dict,
    output_summary: dict | None = None,
    error: str | None = None,
) -> ToolEvent:
    return ToolEvent(
        step=step,
        tool=tool,
        status=status,
        input=input_summary,
        output_summary=output_summary or {},
        duration_ms=round((time.perf_counter() - started_at) * 1000),
        error=error,
    )


class GrantGraphNodes:
    """Nodes keep hard decisions deterministic and expose an auditable trace."""

    def __init__(self, catalog: GrantCatalog) -> None:
        self.catalog = catalog

    def search_opportunities(self, state: MatchGraphState) -> dict:
        request = state["request"]
        started_at = time.perf_counter()
        query = {
            "research_interests": request.profile.research_interests,
            "keywords": request.profile.keywords,
            "top_k": request.top_k,
        }
        engine = "in_memory_bm25+local_vector"
        warning: str | None = None

        if os.getenv("USE_PGVECTOR", "0") == "1":
            try:
                from grantfinder.pgvector_store import search as pg_search

                candidates = pg_search(
                    request.profile,
                    limit=max(30, request.top_k * 10),
                )
                engine = "postgresql_fts+pgvector"
            except (
                ConnectionError,
                OSError,
                PsycopgError,
                RuntimeError,
                TimeoutError,
            ) as exc:
                candidates = self.catalog.search(
                    request.profile,
                    limit=max(30, request.top_k * 10),
                )
                warning = (
                    f"{type(exc).__name__}: pgvector unavailable; "
                    "deterministic fallback used"
                )
        else:
            candidates = self.catalog.search(
                request.profile,
                limit=max(30, request.top_k * 10),
            )

        event = tool_event(
            step=1,
            tool="search_opportunities",
            status="succeeded",
            started_at=started_at,
            input_summary=query,
            output_summary={
                "candidates": len(candidates),
                "engine": engine,
                "warning": warning,
            },
        )
        return {
            "candidates": candidates,
            "retrieval_engine": engine,
            "retrieval_warning": warning,
            "tool_trace": [event],
        }

    @staticmethod
    def route_after_search(
        state: MatchGraphState,
    ) -> Literal["check_eligibility", "handle_no_results"]:
        return "check_eligibility" if state.get("candidates") else "handle_no_results"

    def handle_no_results(self, state: MatchGraphState) -> dict:
        event = ToolEvent(
            step=2,
            tool="handle_no_results",
            status="failed",
            input={"candidate_count": 0},
            output_summary={"next": "refine_research_profile"},
            duration_ms=0,
            error="no_grounded_opportunities_found",
        )
        return {
            "matches": [],
            "status": "needs_profile_refinement",
            "error": "no_grounded_opportunities_found",
            "limitations": MATCH_LIMITATIONS,
            "tool_trace": [event],
        }

    def check_eligibility(self, state: MatchGraphState) -> dict:
        request = state["request"]
        candidates = state.get("candidates", [])
        started_at = time.perf_counter()
        matches = rerank(request.profile, candidates, request.top_k)
        event = tool_event(
            step=2,
            tool="check_eligibility",
            status="succeeded",
            started_at=started_at,
            input_summary={
                "candidate_count": len(candidates),
                "profile_type": request.profile.institution_type,
            },
            output_summary={
                "shortlisted": len(matches),
                "hard_decision_owner": "deterministic_rules",
            },
        )
        return {"matches": matches, "tool_trace": [event]}

    @staticmethod
    def rerank_candidates(state: MatchGraphState) -> dict:
        started_at = time.perf_counter()
        matches = sorted(
            state.get("matches", []),
            key=lambda item: item.score.total,
            reverse=True,
        )
        event = tool_event(
            step=3,
            tool="rerank_candidates",
            status="succeeded",
            started_at=started_at,
            input_summary={
                "weights": {
                    "lexical": 0.42,
                    "semantic": 0.28,
                    "eligibility": 0.22,
                    "freshness": 0.08,
                }
            },
            output_summary={
                "top_ids": [item.opportunity.id for item in matches]
            },
        )
        return {"matches": matches, "tool_trace": [event]}

    @staticmethod
    def request_researcher_review(_: MatchGraphState) -> dict:
        return {
            "status": "awaiting_researcher_review",
            "limitations": MATCH_LIMITATIONS,
            "tool_trace": [
                ToolEvent(
                    step=4,
                    tool="request_human_review",
                    status="waiting_for_human",
                    input={"role": "researcher"},
                    output_summary={
                        "next": "select one opportunity before drafting"
                    },
                    duration_ms=0,
                )
            ],
        }

    def load_grounded_opportunity(self, state: DraftGraphState) -> dict:
        request = state["request"]
        started_at = time.perf_counter()
        opportunity = self.catalog.get(request.opportunity_id)
        if opportunity is None:
            event = tool_event(
                step=1,
                tool="load_grounded_opportunity",
                status="failed",
                started_at=started_at,
                input_summary={"opportunity_id": request.opportunity_id},
                error="opportunity_not_found",
            )
            return {
                "opportunity": None,
                "error": "opportunity_not_found",
                "status": "failed",
                "tool_trace": [event],
            }

        event = tool_event(
            step=1,
            tool="load_grounded_opportunity",
            status="succeeded",
            started_at=started_at,
            input_summary={"opportunity_id": request.opportunity_id},
            output_summary={
                "source": opportunity.source,
                "citations": len(opportunity.source_spans),
            },
        )
        return {
            "opportunity": opportunity,
            "citations": opportunity.source_spans,
            "tool_trace": [event],
        }

    @staticmethod
    def route_after_load(
        state: DraftGraphState,
    ) -> Literal["check_researcher_confirmation", "draft_failed"]:
        return (
            "draft_failed"
            if state.get("error") or state.get("opportunity") is None
            else "check_researcher_confirmation"
        )

    @staticmethod
    def check_researcher_confirmation(state: DraftGraphState) -> dict:
        confirmed = state["request"].human_confirmed
        return {
            "status": "confirmed" if confirmed else "awaiting_researcher_confirmation",
            "tool_trace": [
                ToolEvent(
                    step=2,
                    tool="check_researcher_confirmation",
                    status="succeeded" if confirmed else "waiting_for_human",
                    input={"required_role": "researcher"},
                    output_summary={"confirmed": confirmed},
                    duration_ms=0,
                )
            ],
        }

    @staticmethod
    def route_after_confirmation(
        state: DraftGraphState,
    ) -> Literal["build_proposal_draft", "researcher_confirmation_required"]:
        return (
            "build_proposal_draft"
            if state["request"].human_confirmed
            else "researcher_confirmation_required"
        )

    @staticmethod
    def researcher_confirmation_required(_: DraftGraphState) -> dict:
        return {
            "status": "awaiting_researcher_confirmation",
            "error": "researcher_confirmation_required",
            "tool_trace": [
                ToolEvent(
                    step=3,
                    tool="request_researcher_confirmation",
                    status="waiting_for_human",
                    input={"required_role": "researcher"},
                    output_summary={"draft_created": False},
                    duration_ms=0,
                )
            ],
        }

    @staticmethod
    def draft_failed(state: DraftGraphState) -> dict:
        return {
            "status": "failed",
            "error": state.get("error", "draft_failed"),
        }

    @staticmethod
    def build_proposal_draft(state: DraftGraphState) -> dict:
        request = state["request"]
        opportunity = state["opportunity"]
        assert opportunity is not None
        started_at = time.perf_counter()
        sections = {
            "Tóm tắt đề xuất": f"[DRAFT — CẦN DUYỆT] {request.research_question}",
            "Mức độ phù hợp với quỹ": (
                f"Đề xuất liên quan tới {opportunity.title}. Chỉ sử dụng điều kiện "
                "và phạm vi đã trích từ nguồn gốc."
            ),
            "Mục tiêu nghiên cứu": (
                "[NEEDS_INPUT] Viết 2 đến 3 mục tiêu đo được và kiểm tra lại với "
                "call-for-proposal."
            ),
            "Phương pháp": (
                "[NEEDS_INPUT] Mô tả thiết kế nghiên cứu, dữ liệu, phương pháp "
                "phân tích và kế hoạch quản trị rủi ro."
            ),
            "Kế hoạch công việc": (
                "[NEEDS_INPUT] Chia work package, mốc nghiệm thu, người phụ trách "
                "và thời gian."
            ),
            "Ngân sách": (
                "[NEEDS_INPUT] Ngân sách đề nghị: "
                f"{request.profile.requested_budget or 'chưa cung cấp'} "
                f"{opportunity.currency}; phải đối chiếu trần và chi phí hợp lệ."
            ),
            "Tác động dự kiến": (
                "[NEEDS_INPUT] Nêu kết quả khoa học, tác động xã hội và kế hoạch "
                "phổ biến."
            ),
            "Tuân thủ và đạo đức": (
                "[NEEDS_INPUT] Phòng KHCN xác nhận eligibility, đạo đức nghiên cứu, "
                "dữ liệu và xung đột lợi ích."
            ),
        }
        event = tool_event(
            step=3,
            tool="build_proposal_draft",
            status="succeeded",
            started_at=started_at,
            input_summary={
                "template": "grounded_generic_v1",
                "research_question": request.research_question,
            },
            output_summary={"sections": len(sections), "banner": "DRAFT_ONLY"},
        )
        return {
            "sections": sections,
            "missing_information": DRAFT_MISSING_INFORMATION,
            "banner": "DRAFT_ONLY — Chưa phải hồ sơ nộp; cần phòng KHCN duyệt.",
            "tool_trace": [event],
        }

    @staticmethod
    def optional_grounded_llm_rewrite(state: DraftGraphState) -> dict:
        request = state["request"]
        opportunity = state["opportunity"]
        assert opportunity is not None
        started_at = time.perf_counter()
        grounded_context = {
            "opportunity": opportunity.model_dump(mode="json"),
            "profile": request.profile.model_dump(mode="json"),
            "research_question": request.research_question,
        }
        sections, llm_info = improve_draft(
            state.get("sections", {}),
            grounded_context,
        )
        event = tool_event(
            step=4,
            tool="optional_grounded_llm_rewrite",
            status="succeeded",
            started_at=started_at,
            input_summary={"provider": "gemini_or_offline_fallback"},
            output_summary=llm_info,
        )
        return {"sections": sections, "llm_info": llm_info, "tool_trace": [event]}

    @staticmethod
    def validate_draft_output(state: DraftGraphState) -> dict:
        started_at = time.perf_counter()
        sections = state.get("sections", {})
        citations = state.get("citations", [])
        missing = [key for key, value in sections.items() if not value.strip()]
        if missing or not citations:
            error = "draft_output_guard_failed"
            event = tool_event(
                step=5,
                tool="validate_draft_output",
                status="failed",
                started_at=started_at,
                input_summary={"sections": len(sections), "citations": len(citations)},
                output_summary={"empty_sections": missing},
                error=error,
            )
            return {"status": "failed", "error": error, "tool_trace": [event]}

        event = tool_event(
            step=5,
            tool="validate_draft_output",
            status="succeeded",
            started_at=started_at,
            input_summary={"sections": len(sections), "citations": len(citations)},
            output_summary={
                "hard_facts_grounded": True,
                "automatic_submission": False,
            },
        )
        return {"tool_trace": [event]}

    @staticmethod
    def route_after_draft_guard(
        state: DraftGraphState,
    ) -> Literal["request_research_office_review", "draft_failed"]:
        return "draft_failed" if state.get("error") else "request_research_office_review"

    @staticmethod
    def request_research_office_review(_: DraftGraphState) -> dict:
        return {
            "status": "awaiting_research_office_review",
            "tool_trace": [
                ToolEvent(
                    step=6,
                    tool="request_research_office_review",
                    status="waiting_for_human",
                    input={"required_role": "research_manager"},
                    output_summary={"write_or_submit_performed": False},
                    duration_ms=0,
                )
            ],
        }


def initial_match_state(request, run_id: str) -> MatchGraphState:
    return {
        "request": request,
        "run_id": run_id,
        "generated_at": datetime.now(UTC),
        "candidates": [],
        "matches": [],
        "tool_trace": [],
        "limitations": MATCH_LIMITATIONS,
    }
