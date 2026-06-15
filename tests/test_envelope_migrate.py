"""Tests for workflow log envelope migration."""

from __future__ import annotations

import json
from pathlib import Path

from uri3.doctor.envelope_migrate import migrate_workflow_log


def test_migrate_workflow_log_adds_status_fields(tmp_path: Path):
    path = tmp_path / "demo.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"type":"WorkflowStarted","workflow_id":"demo","run_id":"r1","mode":"execute"}',
                '{"type":"WorkflowCompleted","workflow_id":"demo","ok":true,"mode":"execute"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    summary = migrate_workflow_log(path)
    assert summary["updated"] == 1
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    completed = events[-1]
    assert completed["workflow_status"] == "completed"
    assert completed["execution_status"] == "completed"
    assert completed["service_result_status"] == "succeeded"
