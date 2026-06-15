from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from uri3.graph.execution_models import utc_now_iso


def workflow_event_path(workflow_id: str, root: Path) -> Path:
    return root / "output" / "events" / "workflows" / f"{workflow_id}.jsonl"


def append_workflow_event(workflow_id: str, event: dict[str, Any], *, root: Path) -> Path:
    path = workflow_event_path(workflow_id, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"at": utc_now_iso(), **event}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
