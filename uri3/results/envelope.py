from __future__ import annotations

from typing import Any

from .errors import normalize_error
from .statuses import (
    EXECUTION_COMPLETED,
    EXECUTION_FAILED,
    SERVICE_FAILED,
    SERVICE_SUCCEEDED,
    WORKFLOW_COMPLETED,
    WORKFLOW_COMPLETED_WITH_SERVICE_ERROR,
    WORKFLOW_FAILED,
    derive_statuses,
)


def step_execution_status(*, status: str, has_result: bool = False, dry_run: bool = False) -> str:
    del dry_run
    if status == "skipped":
        return EXECUTION_COMPLETED
    if status == "blocked":
        return EXECUTION_FAILED
    if status == "failed" and not has_result:
        return EXECUTION_FAILED
    return EXECUTION_COMPLETED


def step_service_result_status(*, ok: bool, status: str) -> str:
    if status == "skipped" and ok:
        return SERVICE_SUCCEEDED
    if ok:
        return SERVICE_SUCCEEDED
    return SERVICE_FAILED


def _step_has_service_failure(step: dict[str, Any]) -> bool:
    if step.get("service_result_status") == SERVICE_FAILED:
        return True
    return not step.get("ok", True) and step.get("status") not in {"skipped"}


def _resolve_workflow_status(
    *,
    ok: bool,
    service_failed: bool,
    execution_failed: bool,
) -> str:
    if execution_failed:
        return WORKFLOW_FAILED
    if service_failed:
        return WORKFLOW_COMPLETED_WITH_SERVICE_ERROR
    return WORKFLOW_COMPLETED if ok else WORKFLOW_FAILED


def _workflow_service_failed(steps: list[dict[str, Any]]) -> bool:
    return any(_step_has_service_failure(step) for step in steps)


def _workflow_execution_failed(steps: list[dict[str, Any]]) -> bool:
    return any(step.get("execution_status") == EXECUTION_FAILED for step in steps)


def _workflow_execution_status(*, execution_failed: bool) -> str:
    return EXECUTION_FAILED if execution_failed else EXECUTION_COMPLETED


def _workflow_service_result_status(*, ok: bool, service_failed: bool) -> str:
    return SERVICE_FAILED if service_failed or not ok else SERVICE_SUCCEEDED


def workflow_aggregate_statuses(
    *,
    ok: bool,
    steps: list[dict[str, Any]],
    pending_approval: list[str] | None = None,
    dry_run: bool = False,
) -> tuple[str, str, str]:
    del dry_run
    if pending_approval:
        return WORKFLOW_FAILED, EXECUTION_FAILED, SERVICE_FAILED
    service_failed = _workflow_service_failed(steps)
    execution_failed = _workflow_execution_failed(steps)
    if ok and not service_failed:
        return WORKFLOW_COMPLETED, EXECUTION_COMPLETED, SERVICE_SUCCEEDED
    workflow_status = _resolve_workflow_status(
        ok=ok,
        service_failed=service_failed,
        execution_failed=execution_failed,
    )
    execution_status = _workflow_execution_status(execution_failed=execution_failed)
    service_result_status = _workflow_service_result_status(
        ok=ok,
        service_failed=service_failed,
    )
    return workflow_status, execution_status, service_result_status


def enrich_step_dict(step: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    status = str(step.get("status") or "completed")
    ok = bool(step.get("ok", True))
    execution_status = step_execution_status(
        status=status,
        has_result=bool(step.get("result")),
        dry_run=dry_run,
    )
    service_result_status = step_service_result_status(ok=ok, status=status)
    payload = dict(step)
    payload["execution_status"] = execution_status
    payload["service_result_status"] = service_result_status
    result = dict(payload.get("result") or {})
    if result:
        workflow_status, _, _ = derive_statuses(ok and service_result_status == SERVICE_SUCCEEDED)
        result.setdefault("workflow_status", workflow_status)
        result.setdefault("execution_status", execution_status)
        result.setdefault("service_result_status", service_result_status)
        payload["result"] = result
    return payload


def _workflow_failed_nodes(steps: list[dict[str, Any]]) -> list[str]:
    return [
        str(step.get("id"))
        for step in steps
        if not bool(step.get("ok", True)) and step.get("status") != "skipped"
    ]


def _workflow_step_error(step: dict[str, Any]) -> dict[str, Any]:
    return normalize_error(
        {
            "code": _workflow_step_error_code(step),
            "source": str(step.get("uri") or ""),
            "recoverable": step.get("status") == "blocked",
            "detail": _workflow_step_error_detail(step),
        }
    ).to_dict()


def _workflow_step_errors(
    steps: list[dict[str, Any]],
    failed_nodes: list[str],
) -> list[dict[str, Any]]:
    failed_node_ids = set(failed_nodes)
    return [_workflow_step_error(step) for step in steps if str(step.get("id")) in failed_node_ids]


def _enriched_workflow_result(
    workflow_result: dict[str, Any],
    steps: list[dict[str, Any]],
    *,
    dry_run: bool,
) -> dict[str, Any]:
    wf_status, ex_status, svc_status = workflow_aggregate_statuses(
        ok=bool(workflow_result.get("ok", False)),
        steps=steps,
        pending_approval=list(workflow_result.get("pending_approval") or []),
        dry_run=dry_run,
    )
    workflow_result["workflow_status"] = wf_status
    workflow_result["execution_status"] = ex_status
    workflow_result["service_result_status"] = svc_status
    failed_nodes = _workflow_failed_nodes(steps)
    if failed_nodes:
        workflow_result["failed_nodes"] = failed_nodes
        workflow_result["errors"] = _workflow_step_errors(steps, failed_nodes)
    return workflow_result


def enrich_workflow_dict(payload: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    body = dict(payload)
    steps = [enrich_step_dict(step, dry_run=dry_run) for step in body.get("steps") or []]
    body["steps"] = steps
    workflow_result = dict(body.get("workflow_result") or {})
    body["workflow_result"] = _enriched_workflow_result(
        workflow_result,
        steps,
        dry_run=dry_run,
    )
    return body


def _workflow_step_error_code(step: dict[str, Any]) -> str:
    if step.get("status") == "blocked":
        return "STEP_BLOCKED"
    if step.get("execution_status") == EXECUTION_FAILED:
        return "STEP_EXECUTION_FAILED"
    return "STEP_SERVICE_FAILED"


def _workflow_step_error_detail(step: dict[str, Any]) -> str:
    result = step.get("result") or {}
    if isinstance(result, dict) and result.get("error"):
        return str(result["error"])
    if step.get("error"):
        return str(step["error"])
    return f"step {step.get('id')} failed"


_LIFECYCLE_OK_STATUSES = frozenset(
    {"running", "stopped", "deployed", "verified", "healthy", "generated"}
)


def _lifecycle_ok(body: dict[str, Any], status: str, runtime_status: str) -> bool:
    if (body.get("command_string") and not status) or status in _LIFECYCLE_OK_STATUSES:
        return True
    if runtime_status == "running":
        return True
    if "ok" in body:
        return bool(body["ok"])
    return status not in {"failed", "error"} and status != ""


def enrich_lifecycle_dict(payload: dict[str, Any]) -> dict[str, Any]:
    body = dict(payload)
    if all(key in body for key in ("workflow_status", "execution_status", "service_result_status")):
        return body

    status = str(body.get("status") or "")
    runtime_state = body.get("runtime_state")
    runtime_status = str(body.get("runtime_status") or "")
    if isinstance(runtime_state, dict) and runtime_state.get("status"):
        runtime_status = str(runtime_state["status"])

    service_status = str(body.get("service_status") or "")
    if service_status == "healthy":
        ok = True
    elif service_status in {"unhealthy", "degraded", "stopped", "blocked"}:
        ok = False
    else:
        ok = _lifecycle_ok(body, status, runtime_status)
    workflow_status, execution_status, service_result_status = derive_statuses(ok)
    body["ok"] = ok
    body["workflow_status"] = workflow_status
    body["execution_status"] = execution_status
    body["service_result_status"] = service_result_status
    body.setdefault("result_type", "lifecycle")
    return body


def unwrap_data(payload: dict[str, Any]) -> dict[str, Any]:
    """Return inner 'data' dict if present, else the original payload.

    Centralized unwrap helper to eliminate duplicated _payload_data / nested.get("data")
    logic across dashboard rendering, urish render/proof, and result processing.
    This addresses cross-area duplication flagged in architecture audits.
    """
    if not isinstance(payload, dict):
        return payload
    nested = payload.get("data")
    return nested if isinstance(nested, dict) else payload
