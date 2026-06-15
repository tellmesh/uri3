from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from uri3.doctor.checks._helpers import check_result


def check_result_envelope() -> dict[str, Any]:
    try:
        from uri2verify.result_checks import enrich_result_dict, technical_vs_business_ok

        from uri3.results import service_result
    except ImportError as exc:
        return check_result("envelope.exports", ok=False, errors=[str(exc)])

    sample = service_result(ok=True, result_type="data", data={"x": 1})
    payload = enrich_result_dict(sample.to_dict())
    required = ("workflow_status", "execution_status", "service_result_status")
    missing = [field for field in required if field not in payload]
    split = technical_vs_business_ok(payload)
    return check_result(
        "envelope.exports",
        ok=not missing,
        missing_fields=missing,
        sample_statuses={field: payload.get(field) for field in required},
        technical_vs_business=split,
    )


def check_recent_workflow_logs(root: Path, *, strict: bool = False) -> dict[str, Any]:
    logs_dir = root / "output" / "events" / "workflows"
    if not logs_dir.is_dir():
        return check_result(
            "envelope.recent_logs",
            ok=True,
            logs=0,
            missing_fields=0,
            note="no workflow logs directory",
        )

    required = ("workflow_status", "execution_status", "service_result_status")
    missing_fields = 0
    logs_checked = 0
    for path in sorted(logs_dir.glob("*.jsonl")):
        logs_checked += 1
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            if event.get("type") != "WorkflowCompleted":
                continue
            missing_fields += sum(1 for field in required if field not in event)
    legacy = missing_fields > 0
    return check_result(
        "envelope.recent_logs",
        ok=(missing_fields == 0) if strict else True,
        logs=logs_checked,
        missing_fields=missing_fields,
        legacy_logs=legacy,
        strict=strict,
        directory=str(logs_dir),
        note="legacy workflow logs missing status envelope fields" if legacy and not strict else "",
    )
