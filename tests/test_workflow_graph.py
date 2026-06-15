"""Tests for uri3 workflow graph validation and planning."""

from __future__ import annotations

from uri3.graph import (
    build_execution_plan,
    detect_cycles,
    load_workflow_graph,
    normalize_graph_payload,
    validate_workflow_graph,
)


TASK_PAYLOAD = {
    "task": {"id": "check-agent-health", "description": "Check health"},
    "steps": [
        {"id": "open_health", "uri": "browser://chrome/page/open", "operation": "open", "payload": {"url": "http://localhost:8101/health"}},
        {"id": "extract_body", "uri": "dom://chrome/active/body", "operation": "read", "depends_on": ["open_health"]},
        {"id": "verify_ok", "uri": "assertion://contains", "operation": "check", "depends_on": ["extract_body"], "payload": {"expected": "ok"}},
    ],
}


def test_load_task_payload():
    graph = load_workflow_graph(TASK_PAYLOAD)
    assert graph.id == "check-agent-health"
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2


def test_validate_task_payload():
    assert validate_workflow_graph(TASK_PAYLOAD) == []


def test_execution_plan_order():
    plan = build_execution_plan(TASK_PAYLOAD)
    assert plan["order"] == ["open_health", "extract_body", "verify_ok"]


def test_detect_cycle():
    cyclic = normalize_graph_payload(
        {
            "id": "cycle",
            "nodes": [
                {"id": "a", "uri": "agent://a", "operation": "read", "depends_on": ["b"]},
                {"id": "b", "uri": "agent://b", "operation": "read", "depends_on": ["a"]},
            ],
        }
    )
    assert detect_cycles(cyclic)
    errors = validate_workflow_graph({"id": "cycle", "nodes": [node.to_dict() for node in cyclic.nodes.values()]})
    assert any("cycle" in error for error in errors)
