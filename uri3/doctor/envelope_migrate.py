from __future__ import annotations

import json
from pathlib import Path

from uri3.results.statuses import derive_statuses


def migrate_workflow_log(path: Path) -> dict[str, int]:
    events: list[dict] = []
    updated = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        event = json.loads(line)
        if event.get("type") == "WorkflowCompleted":
            missing = [
                field
                for field in ("workflow_status", "execution_status", "service_result_status")
                if field not in event
            ]
            if missing:
                workflow_status, execution_status, service_result_status = derive_statuses(
                    bool(event.get("ok"))
                )
                event.setdefault("workflow_status", workflow_status)
                event.setdefault("execution_status", execution_status)
                event.setdefault("service_result_status", service_result_status)
                updated += 1
        events.append(event)
    if updated:
        path.write_text(
            "\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n",
            encoding="utf-8",
        )
    return {"events": len(events), "updated": updated}


def migrate_workflow_logs(root: Path) -> dict[str, object]:
    logs_dir = root / "output" / "events" / "workflows"
    if not logs_dir.is_dir():
        return {"ok": True, "logs": 0, "updated_events": 0, "files": []}
    files: list[dict[str, object]] = []
    updated_events = 0
    for path in sorted(logs_dir.glob("*.jsonl")):
        summary = migrate_workflow_log(path)
        updated_events += int(summary["updated"])
        if summary["updated"]:
            files.append({"path": str(path), **summary})
    return {
        "ok": True,
        "logs": len(list(logs_dir.glob("*.jsonl"))),
        "updated_events": updated_events,
        "files": files,
    }
