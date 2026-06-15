from __future__ import annotations

from typing import Any

from uri3.graph.event_log import append_workflow_event
from uri3.graph.execution_models import ExecutionContext
from uri3.graph.models import GraphNode


def redact_step_payload(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        from uri2ops.operator.redaction import redact_payload

        return redact_payload(payload)
    except ImportError:
        return payload


def record_step(
    workflow_id: str,
    context: ExecutionContext,
    event: dict[str, Any],
) -> None:
    append_workflow_event(workflow_id, event, root=context.root)


def record_step_started(
    node: GraphNode,
    *,
    kind: str,
    workflow_id: str,
    context: ExecutionContext,
) -> None:
    record_step(
        workflow_id,
        context,
        {
            "type": "StepStarted",
            "workflow_id": workflow_id,
            "step_id": node.id,
            "uri": node.uri,
            "operation": node.operation,
            "kind": kind,
            "payload": redact_step_payload(node.payload or {}),
        },
    )


def record_step_finished(
    step_id: str,
    *,
    ok: bool,
    workflow_id: str,
    context: ExecutionContext,
    artifact_uri: str | None = None,
) -> None:
    event: dict[str, Any] = {
        "type": "StepCompleted" if ok else "StepFailed",
        "workflow_id": workflow_id,
        "step_id": step_id,
        "ok": ok,
    }
    if artifact_uri:
        event["artifact_uri"] = artifact_uri
    record_step(workflow_id, context, event)


def record_workflow_started(
    workflow_id: str,
    *,
    run_id: str,
    mode: str,
    context: ExecutionContext,
) -> None:
    record_step(
        workflow_id,
        context,
        {
            "type": "WorkflowStarted",
            "workflow_id": workflow_id,
            "run_id": run_id,
            "mode": mode,
        },
    )


def record_workflow_completed(
    workflow_id: str,
    *,
    ok: bool,
    mode: str,
    context: ExecutionContext,
    workflow_status: str | None = None,
    execution_status: str | None = None,
    service_result_status: str | None = None,
) -> None:
    event: dict[str, Any] = {
        "type": "WorkflowCompleted",
        "workflow_id": workflow_id,
        "ok": ok,
        "mode": mode,
    }
    if workflow_status:
        event["workflow_status"] = workflow_status
    if execution_status:
        event["execution_status"] = execution_status
    if service_result_status:
        event["service_result_status"] = service_result_status
    record_step(workflow_id, context, event)
