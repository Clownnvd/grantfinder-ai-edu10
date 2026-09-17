from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from grantfinder.audit import record_graph_run
from grantfinder.catalog import get_catalog
from grantfinder.graph_nodes import initial_match_state
from grantfinder.graph_state import DraftGraphState
from grantfinder.graphs import (
    DRAFT_GRAPH_NODES,
    MATCH_GRAPH_NODES,
    build_graphs,
)
from grantfinder.models import (
    DraftRequest,
    DraftResponse,
    MatchRequest,
    MatchResponse,
    ReviewDecision,
    ReviewRequest,
)
from grantfinder.review_store import ReviewStore


GraphKind = Literal["match", "draft"]


class GrantWorkflow:
    """LangGraph orchestration with deterministic facts and explicit HITL gates."""

    def __init__(self) -> None:
        self.catalog = get_catalog()
        (
            self.match_graph,
            self.draft_graph,
            self.checkpoint_backend,
            self._checkpoint_resource,
        ) = build_graphs(self.catalog)
        self.review_store = ReviewStore()

    @staticmethod
    def _config(run_id: str) -> dict[str, dict[str, str]]:
        return {"configurable": {"thread_id": run_id}}

    def match(self, request: MatchRequest) -> MatchResponse:
        run_id = "match-" + uuid.uuid4().hex[:12]
        final_state = self.match_graph.invoke(
            initial_match_state(request, run_id),
            config=self._config(run_id),
        )
        record_graph_run(
            run_id=run_id,
            graph="match",
            status=final_state.get("status", "unknown"),
            trace=final_state.get("tool_trace", []),
            checkpoint_backend=self.checkpoint_backend,
        )

        return MatchResponse(
            run_id=run_id,
            state=final_state.get("status", "awaiting_researcher_review"),
            generated_at=final_state.get("generated_at", datetime.now()),
            top_matches=final_state.get("matches", []),
            tool_trace=final_state.get("tool_trace", []),
            limitations=final_state.get("limitations", []),
            orchestration="langgraph",
            graph_nodes=MATCH_GRAPH_NODES,
        )

    def draft(self, request: DraftRequest) -> DraftResponse:
        run_id = "draft-" + uuid.uuid4().hex[:12]
        initial_state: DraftGraphState = {
            "request": request,
            "run_id": run_id,
            "sections": {},
            "tool_trace": [],
            "missing_information": [],
            "citations": [],
        }
        final_state = self.draft_graph.invoke(
            initial_state,
            config=self._config(run_id),
        )
        record_graph_run(
            run_id=run_id,
            graph="draft",
            status=final_state.get("status", "unknown"),
            trace=final_state.get("tool_trace", []),
            checkpoint_backend=self.checkpoint_backend,
        )

        error = final_state.get("error")
        if error == "opportunity_not_found":
            raise KeyError(error)
        if error == "researcher_confirmation_required":
            raise PermissionError(error)
        if error:
            raise RuntimeError(error)

        opportunity = final_state.get("opportunity")
        if opportunity is None:
            raise RuntimeError("draft_graph_missing_opportunity")

        return DraftResponse(
            run_id=run_id,
            draft_id="proposal-" + uuid.uuid4().hex[:12],
            state="awaiting_research_office_review",
            banner=final_state["banner"],
            opportunity=opportunity,
            sections=final_state.get("sections", {}),
            missing_information=final_state.get("missing_information", []),
            citations=final_state.get("citations", []),
            tool_trace=final_state.get("tool_trace", []),
            orchestration="langgraph",
            graph_nodes=DRAFT_GRAPH_NODES,
        )

    def inspect_run(self, run_id: str) -> dict[str, Any]:
        kind: GraphKind
        if run_id.startswith("match-"):
            kind = "match"
        elif run_id.startswith("draft-"):
            kind = "draft"
        else:
            raise KeyError("graph_run_not_found")

        graph = self.match_graph if kind == "match" else self.draft_graph
        snapshot = graph.get_state(self._config(run_id))
        values = snapshot.values
        if not values:
            raise KeyError("graph_run_not_found")
        trace = values.get("tool_trace", [])
        matches = values.get("matches", [])
        return {
            "run_id": run_id,
            "graph": kind,
            "orchestration": "langgraph",
            "status": values.get("status"),
            "checkpoint_id": snapshot.config.get("configurable", {}).get(
                "checkpoint_id"
            ),
            "next_nodes": list(snapshot.next),
            "candidate_count": len(values.get("candidates", [])),
            "top_ids": [item.opportunity.id for item in matches],
            "tool_trace": [item.model_dump(mode="json") for item in trace],
        }

    def request_review(self, request: ReviewRequest) -> dict:
        if request.role != "researcher":
            raise PermissionError("researcher_role_required")
        return self.review_store.create(request)

    def decide(self, review_id: str, decision: ReviewDecision) -> dict:
        if decision.role != "research_manager":
            raise PermissionError("research_manager_role_required")
        return self.review_store.decide(review_id, decision)

    def list_reviews(self) -> list[dict]:
        return self.review_store.list()
