"""Tests for uri3 workflow event replay."""

from __future__ import annotations

import json
from pathlib import Path

from uri3.graph import run_workflow, workflow_event_path
from uri3.graph.replay import build_task_payload_from_events, create_regression_test, replay_workflow_events

TASK_PAYLOAD = {
    "task": {"id": "replay-demo", "description": "Replay demo"},
    "steps": [
        {
            "id": "open_health",
            "uri": "browser://chrome/page/open",
            "operation": "open",
            "kind": "command",
            "payload": {"url": "http://localhost:8101/health"},
        }
    ],
}


def test_replay_workflow_events_by_id(tmp_path: Path):
    run_workflow(TASK_PAYLOAD, approve=True, root=tmp_path, browser_mode="mock")
    summary = replay_workflow_events("replay-demo", root=tmp_path)
    assert summary["workflow_id"] == "replay-demo"
    assert summary["event_count"] >= 3
    assert summary["workflow_completed"]["ok"] is True
    assert summary["failed_steps"] == []


def test_replay_workflow_events_by_path(tmp_path: Path):
    run_workflow(TASK_PAYLOAD, approve=False, root=tmp_path, browser_mode="mock")
    path = workflow_event_path("replay-demo", tmp_path)
    summary = replay_workflow_events(path, root=tmp_path)
    assert summary["blocked_steps"]
    assert summary["workflow_completed"]["ok"] is False


def test_build_task_payload_from_step_started_events(tmp_path: Path):
    run_workflow(TASK_PAYLOAD, approve=True, root=tmp_path, browser_mode="mock")
    summary = replay_workflow_events("replay-demo", root=tmp_path)
    task_payload = build_task_payload_from_events(summary["timeline"])
    assert task_payload["task"]["id"] == "replay-demo"
    assert task_payload["steps"][0]["uri"] == "browser://chrome/page/open"
    assert task_payload["steps"][0]["payload"]["url"] == "http://localhost:8101/health"


def test_create_regression_test_writes_pytest(tmp_path: Path):
    run_workflow(TASK_PAYLOAD, approve=False, root=tmp_path, browser_mode="mock")
    out = tmp_path / "tests" / "test_replay_demo.py"
    result = create_regression_test("replay-demo", out=out, root=tmp_path)
    assert result["ok"] is True
    assert out.is_file()
    content = out.read_text(encoding="utf-8")
    assert "def test_replay_regression" in content
    assert "replay-demo" in content
