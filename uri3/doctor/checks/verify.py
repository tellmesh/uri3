from __future__ import annotations

from pathlib import Path
from typing import Any

from uri3.doctor.checks._helpers import check_result


def check_capability_plan(root: Path) -> dict[str, Any]:
    try:
        from hypervisor.contract_registry.loader import load_contract_registry
        from hypervisor.contract_registry.validate import validate_registry
        from uri2verify.capability_tests import capability_test_plan_from_registry
    except ImportError as exc:
        return check_result("uri2verify.capability_plan", ok=False, errors=[str(exc)])

    registry = load_contract_registry(root)
    errors = validate_registry(registry)
    if errors:
        return check_result("uri2verify.capability_plan", ok=False, errors=errors)
    plan = capability_test_plan_from_registry(registry)
    return check_result("uri2verify.capability_plan", ok=True, tests=len(plan))


def check_replay_failures(root: Path) -> dict[str, Any]:
    logs_dir = root / "output" / "events" / "workflows"
    if not logs_dir.is_dir():
        return check_result(
            "uri2verify.replay_failures", ok=True, failures=[], note="no workflow logs directory"
        )

    from uri2verify.replay import replay_workflow_events

    failures: list[dict[str, Any]] = []
    for path in sorted(logs_dir.glob("*.jsonl")):
        summary = replay_workflow_events(path, root=root)
        failed = summary.get("failed_steps") or []
        blocked = summary.get("blocked_steps") or []
        completed = summary.get("workflow_completed") or {}
        if failed or blocked or completed.get("ok") is False:
            failures.append(
                {
                    "workflow_id": summary.get("workflow_id"),
                    "event_log": summary.get("event_log"),
                    "failed_steps": len(failed),
                    "blocked_steps": len(blocked),
                    "workflow_ok": completed.get("ok"),
                }
            )
    return check_result("uri2verify.replay_failures", ok=not failures, failures=failures)
