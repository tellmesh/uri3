"""Tests for uri3 workflow executor MVP."""

from __future__ import annotations

import json
from pathlib import Path

from uri3.graph import (
    load_workflow_graph,
    run_workflow,
    workflow_event_path,
)

TASK_PAYLOAD = {
    "task": {"id": "check-agent-health", "description": "Check health"},
    "steps": [
        {
            "id": "open_health",
            "uri": "browser://chrome/page/open",
            "operation": "open",
            "kind": "command",
            "payload": {"url": "http://localhost:8101/health"},
        },
        {
            "id": "extract_body",
            "uri": "dom://chrome/active/body",
            "operation": "read",
            "kind": "query",
            "depends_on": ["open_health"],
        },
        {
            "id": "verify_ok",
            "uri": "assertion://contains",
            "operation": "check",
            "kind": "assertion",
            "depends_on": ["extract_body"],
            "payload": {"actual_from": "extract_body.text", "expected": "ok"},
        },
    ],
}


def test_run_workflow_dry_run_completes():
    result = run_workflow(TASK_PAYLOAD, dry_run=True, browser_mode="mock")
    assert result.ok is True
    assert result.mode == "dry_run"
    assert len(result.steps) == 3
    assert all(step.status == "completed" for step in result.steps)
    payload = result.to_dict()["workflow_result"]
    assert payload["workflow_status"] == "completed"
    assert payload["execution_status"] == "completed"
    assert payload["service_result_status"] == "succeeded"
    assert payload["run_id"]


def test_run_workflow_blocks_command_without_approve():
    result = run_workflow(TASK_PAYLOAD, dry_run=False, approve=False, browser_mode="mock")
    assert result.ok is False
    assert result.pending_approval == ["open_health"]
    assert result.steps[0].status == "blocked"
    payload = result.to_dict()["workflow_result"]
    assert payload["workflow_status"] == "failed"
    assert payload["execution_status"] == "failed"
    assert payload["service_result_status"] == "failed"
    assert payload["failed_nodes"] == ["open_health"]
    assert payload["errors"][0]["code"] == "STEP_BLOCKED"


def test_run_workflow_execute_mock_with_approve(tmp_path: Path):
    result = run_workflow(
        TASK_PAYLOAD,
        dry_run=False,
        approve=True,
        root=tmp_path,
        browser_mode="mock",
    )
    assert result.ok is True
    assert result.steps[-1].id == "verify_ok"
    assert result.steps[-1].ok is True
    event_path = workflow_event_path("check-agent-health", tmp_path)
    assert event_path.exists()
    events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
    assert events[0]["type"] == "WorkflowStarted"
    completed = next(event for event in events if event["type"] == "WorkflowCompleted")
    assert completed["workflow_status"] == "completed"
    assert completed["execution_status"] == "completed"
    assert completed["service_result_status"] == "succeeded"


def test_run_workflow_accepts_workflow_graph_object(tmp_path: Path):
    graph = load_workflow_graph(TASK_PAYLOAD)
    result = run_workflow(graph, dry_run=False, approve=True, root=tmp_path, browser_mode="mock")
    assert result.ok is True
    assert result.steps[-1].id == "verify_ok"


def test_run_workflow_skips_conditional_branch(tmp_path: Path):
    payload = {
        "graph": {
            "id": "conditional-logs",
            "nodes": [
                {
                    "id": "verify_ok",
                    "uri": "assertion://contains",
                    "operation": "check",
                    "kind": "assertion",
                    "payload": {"expected": "ok", "actual": "ok"},
                },
                {
                    "id": "read_logs_if_failed",
                    "uri": "log://weather-map-agent.local?limit=100",
                    "operation": "read",
                    "kind": "query",
                    "depends_on": ["verify_ok"],
                    "condition": {"if": "verify_ok.ok == false"},
                },
            ],
        }
    }
    result = run_workflow(payload, approve=True, root=tmp_path, browser_mode="mock")
    assert result.ok is True
    statuses = {step.id: step.status for step in result.steps}
    assert statuses["verify_ok"] == "completed"
    assert statuses["read_logs_if_failed"] == "skipped"


def test_run_workflow_service_failure_uses_completed_with_service_error(tmp_path: Path):
    payload = {
        "task": {"id": "assertion-service-error", "description": "Assert body"},
        "steps": [
            {
                "id": "verify_ok",
                "uri": "assertion://contains",
                "operation": "check",
                "kind": "assertion",
                "payload": {"actual": "not ready", "expected": "ok"},
            },
        ],
    }
    result = run_workflow(payload, approve=True, root=tmp_path, browser_mode="mock")
    workflow_result = result.to_dict()["workflow_result"]
    assert result.ok is False
    assert workflow_result["workflow_status"] == "completed_with_service_error"
    assert workflow_result["execution_status"] == "completed"
    assert workflow_result["service_result_status"] == "failed"
    assert workflow_result["failed_nodes"] == ["verify_ok"]
    assert workflow_result["errors"][0]["code"] == "STEP_SERVICE_FAILED"
