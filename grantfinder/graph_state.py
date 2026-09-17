from __future__ import annotations

import operator
from datetime import datetime
from typing import Annotated, Any, TypedDict

from grantfinder.models import (
    DraftRequest,
    MatchItem,
    MatchRequest,
    Opportunity,
    SourceSpan,
    ToolEvent,
)

Candidate = tuple[Opportunity, float, float]


class MatchGraphState(TypedDict, total=False):
    """Shared state for the grant discovery graph."""

    request: MatchRequest
    run_id: str
    generated_at: datetime
    candidates: list[Candidate]
    matches: list[MatchItem]
    retrieval_engine: str
    retrieval_warning: str | None
    status: str
    error: str | None
    limitations: list[str]
    tool_trace: Annotated[list[ToolEvent], operator.add]


class DraftGraphState(TypedDict, total=False):
    """Shared state for the proposal drafting graph."""

    request: DraftRequest
    run_id: str
    opportunity: Opportunity | None
    sections: dict[str, str]
    llm_info: dict[str, Any]
    missing_information: list[str]
    citations: list[SourceSpan]
    banner: str
    status: str
    error: str | None
    tool_trace: Annotated[list[ToolEvent], operator.add]


MATCH_LIMITATIONS = [
    "Kết quả matching là shortlist; phòng KHCN phải xác minh eligibility trong tài liệu gốc.",
    "Local vector là fallback tất định; khi DATABASE_URL được cấu hình, ingestion và retrieval dùng pgvector.",
    "Không có hành động nộp hồ sơ tự động.",
]


DRAFT_MISSING_INFORMATION = [
    "Mục tiêu định lượng",
    "Phương pháp chi tiết",
    "Work packages",
    "Dự toán chi tiết",
    "Kế hoạch tác động",
    "Xác nhận eligibility",
]
