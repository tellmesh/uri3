from __future__ import annotations

from typing import Any

from uri3.graph.adapters.registry import adapter_for_uri
from uri3.graph.conditions import evaluate_condition
from uri3.graph.dependency_graph import topological_sort
from uri3.graph.execution_models import (
    GraphExecutionPlan,
    StepExecutionResult,
)
from uri3.graph.graph_serializer import workflow_manifest
from uri3.graph.graph_validator import load_workflow_graph, validate_workflow_graph
from uri3.graph.models import GraphNode, WorkflowGraph
from uri3.graph.operation_registry import effective_kind, validate_node_operation


def build_execution_plan(graph: WorkflowGraph | dict[str, Any]) -> dict[str, Any]:
    workflow = graph if isinstance(graph, WorkflowGraph) else load_workflow_graph(graph)
    order = topological_sort(workflow)
    steps = []
    for node_id in order:
        node = workflow.nodes[node_id]
        steps.append(
            {
                "id": node.id,
                "uri": node.uri,
                "operation": node.operation,
                "kind": effective_kind(node),
                "depends_on": list(node.depends_on),
                "condition": node.condition,
                "requires_approval": effective_kind(node) == "command",
            }
        )
    plan = GraphExecutionPlan(graph_id=workflow.id, kind=workflow.kind, order=order, steps=steps)
    return {
        **plan.to_dict(),
        "manifest": workflow_manifest(workflow),
    }


def prepare_workflow(source: WorkflowGraph | dict[str, Any]) -> WorkflowGraph:
    errors = validate_workflow_graph(source)
    if errors:
        raise ValueError("Workflow graph validation failed: " + "; ".join(errors[:5]))
    workflow = source if isinstance(source, WorkflowGraph) else load_workflow_graph(source)
    for node in workflow.nodes.values():
        op_error = validate_node_operation(node)
        if op_error:
            raise ValueError(op_error)
    return workflow


def workflow_completion_message(
    *,
    pending_approval: list[str],
    dry_run: bool,
) -> str | None:
    if pending_approval:
        return "Workflow stopped: command node(s) require --approve"
    if dry_run:
        return "Dry-run completed without side effects"
    return None
