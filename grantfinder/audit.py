from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from grantfinder.models import ToolEvent

AUDIT_PATH = (
    Path(__file__).resolve().parents[1] / "artifacts" / "audit" / "agent_runs.jsonl"
)


def record_graph_run(
    *,
    run_id: str,
    graph: str,
    status: str,
    trace: list[ToolEvent],
    checkpoint_backend: str,
) -> None:
    """Persist non-sensitive run metadata for reproducible AI-log evidence."""

    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "at": datetime.now(UTC).isoformat(timespec="seconds"),
        "run_id": run_id,
        "graph": graph,
        "status": status,
        "checkpoint_backend": checkpoint_backend,
        "tools": [
            {
                "step": event.step,
                "tool": event.tool,
                "status": event.status,
                "duration_ms": event.duration_ms,
                "error": event.error,
            }
            for event in trace
        ],
    }
    with AUDIT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
