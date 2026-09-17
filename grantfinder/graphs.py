from __future__ import annotations

import os

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph

from grantfinder.catalog import GrantCatalog
from grantfinder.graph_nodes import GrantGraphNodes
from grantfinder.graph_state import DraftGraphState, MatchGraphState


MATCH_GRAPH_NODES = [
    "search_opportunities",
    "check_eligibility",
    "rerank_candidates",
    "request_researcher_review",
]

DRAFT_GRAPH_NODES = [
    "load_grounded_opportunity",
    "check_researcher_confirmation",
    "build_proposal_draft",
    "optional_grounded_llm_rewrite",
    "validate_draft_output",
    "request_research_office_review",
]


def build_match_graph(nodes: GrantGraphNodes, checkpointer):
    builder = StateGraph(MatchGraphState)
    builder.add_node("search_opportunities", nodes.search_opportunities)
    builder.add_node("check_eligibility", nodes.check_eligibility)
    builder.add_node("handle_no_results", nodes.handle_no_results)
    builder.add_node("rerank_candidates", nodes.rerank_candidates)
    builder.add_node("request_researcher_review", nodes.request_researcher_review)

    builder.add_edge(START, "search_opportunities")
    builder.add_conditional_edges(
        "search_opportunities",
        nodes.route_after_search,
        {
            "check_eligibility": "check_eligibility",
            "handle_no_results": "handle_no_results",
        },
    )
    builder.add_edge("handle_no_results", END)
    builder.add_edge("check_eligibility", "rerank_candidates")
    builder.add_edge("rerank_candidates", "request_researcher_review")
    builder.add_edge("request_researcher_review", END)
    return builder.compile(checkpointer=checkpointer, name="grantfinder_match_graph")


def build_draft_graph(nodes: GrantGraphNodes, checkpointer):
    builder = StateGraph(DraftGraphState)
    builder.add_node("load_grounded_opportunity", nodes.load_grounded_opportunity)
    builder.add_node(
        "check_researcher_confirmation",
        nodes.check_researcher_confirmation,
    )
    builder.add_node(
        "researcher_confirmation_required",
        nodes.researcher_confirmation_required,
    )
    builder.add_node("build_proposal_draft", nodes.build_proposal_draft)
    builder.add_node(
        "optional_grounded_llm_rewrite",
        nodes.optional_grounded_llm_rewrite,
    )
    builder.add_node("validate_draft_output", nodes.validate_draft_output)
    builder.add_node(
        "request_research_office_review",
        nodes.request_research_office_review,
    )
    builder.add_node("draft_failed", nodes.draft_failed)

    builder.add_edge(START, "load_grounded_opportunity")
    builder.add_conditional_edges(
        "load_grounded_opportunity",
        nodes.route_after_load,
        {
            "check_researcher_confirmation": "check_researcher_confirmation",
            "draft_failed": "draft_failed",
        },
    )
    builder.add_conditional_edges(
        "check_researcher_confirmation",
        nodes.route_after_confirmation,
        {
            "build_proposal_draft": "build_proposal_draft",
            "researcher_confirmation_required": "researcher_confirmation_required",
        },
    )
    builder.add_edge("researcher_confirmation_required", END)
    builder.add_edge("build_proposal_draft", "optional_grounded_llm_rewrite")
    builder.add_edge("optional_grounded_llm_rewrite", "validate_draft_output")
    builder.add_conditional_edges(
        "validate_draft_output",
        nodes.route_after_draft_guard,
        {
            "request_research_office_review": "request_research_office_review",
            "draft_failed": "draft_failed",
        },
    )
    builder.add_edge("request_research_office_review", END)
    builder.add_edge("draft_failed", END)
    return builder.compile(checkpointer=checkpointer, name="grantfinder_draft_graph")


def build_checkpointer():
    serde = JsonPlusSerializer(
        allowed_msgpack_modules=[
            ("grantfinder.models", "DraftRequest"),
            ("grantfinder.models", "EligibilityCheck"),
            ("grantfinder.models", "MatchItem"),
            ("grantfinder.models", "MatchRequest"),
            ("grantfinder.models", "Opportunity"),
            ("grantfinder.models", "ResearcherProfile"),
            ("grantfinder.models", "ScoreBreakdown"),
            ("grantfinder.models", "SourceSpan"),
            ("grantfinder.models", "ToolEvent"),
        ]
    )
    if os.getenv("LANGGRAPH_CHECKPOINT_BACKEND", "memory") == "postgres":
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg import connect
        from psycopg.rows import dict_row

        database_url = os.getenv("LANGGRAPH_CHECKPOINT_DATABASE_URL") or os.getenv(
            "DATABASE_URL"
        )
        if not database_url:
            raise RuntimeError("langgraph_checkpoint_database_url_required")
        connection = connect(database_url, autocommit=True, row_factory=dict_row)
        checkpointer = PostgresSaver(connection, serde=serde)
        checkpointer.setup()
        return checkpointer, "postgres", connection

    return InMemorySaver(serde=serde), "memory", None


def build_graphs(catalog: GrantCatalog):
    checkpointer, backend, resource = build_checkpointer()
    nodes = GrantGraphNodes(catalog)
    return (
        build_match_graph(nodes, checkpointer),
        build_draft_graph(nodes, checkpointer),
        backend,
        resource,
    )
