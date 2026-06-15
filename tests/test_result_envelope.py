"""Tests for ServiceResult envelope in uri3/uri2ops outputs."""

from __future__ import annotations

from pathlib import Path

from uri2ops.operator.runner import run_task
from uri2ops.operator.task import load_task
from uri3.graph import run_workflow

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
    ],
}


def test_uri3_workflow_result_includes_status_envelope(tmp_path: Path):
    result = run_workflow(TASK_PAYLOAD, approve=True, root=tmp_path, browser_mode="mock")
    payload = result.to_dict()
    workflow = payload["workflow_result"]
    assert workflow["workflow_status"] == "completed"
    assert workflow["execution_status"] == "completed"
    assert workflow["service_result_status"] == "succeeded"
    assert payload["steps"][0]["execution_status"] == "completed"
    assert payload["steps"][0]["service_result_status"] == "succeeded"


def test_uri3_workflow_blocked_has_failed_service_status():
    result = run_workflow(TASK_PAYLOAD, approve=False, browser_mode="mock")
    payload = result.to_dict()
    workflow = payload["workflow_result"]
    assert workflow["ok"] is False
    assert workflow["service_result_status"] == "failed"
    assert payload["steps"][0]["status"] == "blocked"


def test_uri2ops_task_result_includes_status_envelope(tmp_path: Path):
    task = load_task("examples/10_browser_operator/task.health.yaml")
    result = run_task(task, adapter="mock", approve=True, root=tmp_path)
    payload = result.to_dict()
    assert payload["workflow_result"]["service_result_status"] == "succeeded"
    assert payload["steps"][0]["service_result_status"] == "succeeded"
