from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from uri3.logs.reader import DEFAULT_STREAM_FILES
from uri3.paths import find_repo_root

LOG_EVENT_SCHEMA = "schemas/log_event.schema.json"


def _event_code(level: str, message: str, fields: dict[str, Any]) -> str:
    if fields.get("event_code"):
        return str(fields["event_code"])
    if level.upper() == "ERROR":
        return "LOG_ERROR"
    if level.upper() == "WARNING":
        return "LOG_WARNING"
    return "LOG_INFO"


def append_log(
    stream: str,
    message: str,
    *,
    level: str = "INFO",
    logger: str | None = None,
    root: Path | None = None,
    validate: bool = False,
    **fields: Any,
) -> Path:
    repo = root or find_repo_root()
    relative = DEFAULT_STREAM_FILES.get(stream, f"output/logs/{stream}.log")
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    subject = fields.pop("subject_uri", None) or fields.pop("subject", None)
    correlation = fields.pop("correlation", None)
    if correlation is None:
        correlation = {
            key: fields.pop(key)
            for key in ("workflow_id", "step_id", "incident_id", "ticket_id")
            if key in fields
        } or None
    entry: dict[str, Any] = {
        "$schema": LOG_EVENT_SCHEMA,
        "apiVersion": "uri3.io/v1",
        "kind": "LogEvent",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "level": level.upper(),
        "logger": logger or stream,
        "message": message,
        "uri": {
            "self": f"log://{stream}",
        },
        "event": {
            "code": _event_code(level, message, fields),
            "message": message,
        },
    }
    if subject:
        entry["uri"]["subject"] = str(subject)
    if correlation:
        entry["correlation"] = correlation
    if fields:
        entry["fields"] = fields
    if validate:
        from uri3.artifacts.validator import validate_artifact

        errors = validate_artifact(entry, repo, LOG_EVENT_SCHEMA)
        if errors:
            raise ValueError(f"log event schema validation failed: {'; '.join(errors)}")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path
