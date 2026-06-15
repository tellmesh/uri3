from __future__ import annotations

from uri3.graph.adapters.uri2ops_adapter import cleanup_operator_adapters
from uri3.graph.dependency_graph import topological_sort
from uri3.graph.event_emitter import record_workflow_completed, record_workflow_started
from uri3.graph.execution_models import (
    GraphExecutionResult,
    StepExecutionResult,
    new_execution_context,
    utc_now_iso,
)

# Re-export planning helpers for backward compatibility.
from uri3.graph.execution_plan import (
    build_execution_plan,  # noqa: F401
    prepare_workflow,
    workflow_completion_message,
)
from uri3.graph.models import WorkflowGraph
from uri3.graph.step_runner import run_workflow_node


def dry_run_workflow(source: WorkflowGraph | dict) -> dict:
    return run_workflow(source, dry_run=True).to_dict()


def run_workflow(
    source: WorkflowGraph | dict,
    *,
    approve: bool = False,
    dry_run: bool = False,
    root=None,
    browser_mode: str = "auto",
) -> GraphExecutionResult:
    workflow = prepare_workflow(source)
    context = new_execution_context(
        workflow.id,
        root=root,
        approve_commands=approve,
        dry_run=dry_run,
        browser_mode=browser_mode,
    )
    started_at = utc_now_iso()
    mode = "dry_run" if dry_run else "execute"
    record_workflow_started(workflow.id, run_id=context.run_id, mode=mode, context=context)

    order = topological_sort(workflow)
    completed: dict[str, StepExecutionResult] = {}
    step_results: list[StepExecutionResult] = []
    pending_approval: list[str] = []
    workflow_ok = True

    try:
        for node_id in order:
            node = workflow.nodes[node_id]
            step, should_continue = run_workflow_node(
                node,
                workflow_id=workflow.id,
                approve=approve,
                dry_run=dry_run,
                context=context,
                completed=completed,
                pending_approval=pending_approval,
            )
            step_results.append(step)
            if not should_continue:
                workflow_ok = False
                break
    finally:
        cleanup_operator_adapters(context)

    completed_at = utc_now_iso()
    workflow_ok_final = workflow_ok and not pending_approval
    graph_result = GraphExecutionResult(
        id=workflow.id,
        ok=workflow_ok_final,
        started_at=started_at,
        completed_at=completed_at,
        mode=mode,
        run_id=context.run_id,
        steps=step_results,
        pending_approval=pending_approval,
        message=workflow_completion_message(pending_approval=pending_approval, dry_run=dry_run),
    )
    workflow_payload = graph_result.to_dict()["workflow_result"]
    record_workflow_completed(
        workflow.id,
        ok=workflow_ok_final,
        mode=mode,
        context=context,
        workflow_status=workflow_payload["workflow_status"],
        execution_status=workflow_payload["execution_status"],
        service_result_status=workflow_payload["service_result_status"],
    )
    return graph_result
