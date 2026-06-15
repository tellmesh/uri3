from __future__ import annotations

from typing import Any

from uri3.graph.adapters.registry import adapter_for_uri
from uri3.graph.event_emitter import record_step, record_step_finished, record_step_started
from uri3.graph.execution_models import ExecutionContext, StepExecutionResult
from uri3.graph.models import GraphNode
from uri3.graph.operation_registry import effective_kind
from uri3.graph.policy import can_execute_step
from uri3.graph.conditions import evaluate_condition


def dependencies_ok(
    node: GraphNode,
    completed: dict[str, StepExecutionResult],
) -> tuple[bool, str | None]:
    for dependency in node.depends_on:
        prior = completed.get(dependency)
        if prior is None:
            return False, f"missing dependency {dependency!r}"
        if prior.status == "skipped":
            return False, f"dependency {dependency!r} was skipped"
        if not prior.ok and prior.status != "blocked":
            return False, f"dependency {dependency!r} failed"
    return True, None


def execute_step(node: GraphNode, context: ExecutionContext) -> dict[str, Any]:
    adapter = adapter_for_uri(node.uri)
    if adapter is None:
        return {
            "ok": True,
            "mock": True,
            "message": f"no adapter registered for {node.uri}; treated as no-op mock",
        }
    return adapter.execute(node, context)


def step_result(
    node: GraphNode,
    *,
    kind: str,
    status: str,
    ok: bool,
    result: dict[str, Any] | None = None,
    error: str | None = None,
    artifact_uri: str | None = None,
) -> StepExecutionResult:
    return StepExecutionResult(
        id=node.id,
        uri=node.uri,
        operation=node.operation,
        kind=kind,
        status=status,
        ok=ok,
        result=result,
        artifact_uri=artifact_uri,
        error=error,
    )


def handle_skipped_node(
    node: GraphNode,
    *,
    kind: str,
    context: ExecutionContext,
    completed: dict[str, StepExecutionResult],
) -> StepExecutionResult:
    skipped = step_result(
        node,
        kind=kind,
        status="skipped",
        ok=True,
        result={"reason": "condition_not_met"},
    )
    completed[node.id] = skipped
    context.step_outputs[node.id] = skipped.result
    return skipped


def handle_dependency_failure(
    node: GraphNode,
    *,
    kind: str,
    dep_error: str,
    workflow_id: str,
    context: ExecutionContext,
    completed: dict[str, StepExecutionResult],
) -> StepExecutionResult:
    failed = step_result(node, kind=kind, status="failed", ok=False, error=dep_error)
    completed[node.id] = failed
    record_step(
        workflow_id,
        context,
        {"type": "StepFailed", "workflow_id": workflow_id, "step_id": node.id, "error": dep_error},
    )
    return failed


def handle_blocked_node(
    node: GraphNode,
    *,
    kind: str,
    policy_error: str,
    workflow_id: str,
    context: ExecutionContext,
    completed: dict[str, StepExecutionResult],
    pending_approval: list[str],
) -> StepExecutionResult:
    blocked = step_result(node, kind=kind, status="blocked", ok=False, error=policy_error)
    completed[node.id] = blocked
    pending_approval.append(node.id)
    record_step(
        workflow_id,
        context,
        {
            "type": "StepBlocked",
            "workflow_id": workflow_id,
            "step_id": node.id,
            "reason": policy_error,
        },
    )
    return blocked


def handle_completed_node(
    node: GraphNode,
    *,
    kind: str,
    dry_run: bool,
    context: ExecutionContext,
    completed: dict[str, StepExecutionResult],
) -> tuple[StepExecutionResult, bool]:
    if dry_run:
        result_payload = {
            "ok": True,
            "dry_run": True,
            "uri": node.uri,
            "operation": node.operation,
        }
    else:
        result_payload = execute_step(node, context)

    ok = bool(result_payload.get("ok", True))
    step_artifact_uri = result_payload.get("artifact_uri")
    step = step_result(
        node,
        kind=kind,
        status="completed" if ok else "failed",
        ok=ok,
        result=result_payload,
        artifact_uri=step_artifact_uri,
        error=None if ok else str(result_payload.get("error") or "step failed"),
    )
    completed[node.id] = step
    context.step_outputs[node.id] = {**result_payload, "ok": ok}
    return step, ok


def run_workflow_node(
    node: GraphNode,
    *,
    workflow_id: str,
    approve: bool,
    dry_run: bool,
    context: ExecutionContext,
    completed: dict[str, StepExecutionResult],
    pending_approval: list[str],
) -> tuple[StepExecutionResult, bool]:
    kind = effective_kind(node)
    if not evaluate_condition(node.condition, context):
        return handle_skipped_node(node, kind=kind, context=context, completed=completed), True

    deps_ok, dep_error = dependencies_ok(node, completed)
    if not deps_ok:
        return (
            handle_dependency_failure(
                node,
                kind=kind,
                dep_error=str(dep_error),
                workflow_id=workflow_id,
                context=context,
                completed=completed,
            ),
            False,
        )

    record_step_started(node, kind=kind, workflow_id=workflow_id, context=context)
    allowed, policy_error = can_execute_step(node, approve_commands=approve, dry_run=dry_run)
    if not allowed:
        return (
            handle_blocked_node(
                node,
                kind=kind,
                policy_error=str(policy_error),
                workflow_id=workflow_id,
                context=context,
                completed=completed,
                pending_approval=pending_approval,
            ),
            False,
        )

    step, ok = handle_completed_node(
        node,
        kind=kind,
        dry_run=dry_run,
        context=context,
        completed=completed,
    )
    record_step_finished(
        step.id,
        ok=ok,
        workflow_id=workflow_id,
        context=context,
        artifact_uri=step.artifact_uri,
    )
    return step, ok
