"""Tests for log:// and llm:// decide workflow adapters."""

from __future__ import annotations

import json
from pathlib import Path

from uri3.graph import run_workflow
from uri3.graph.adapters.registry import adapter_for_uri
from uri3.llm.decide import decide


def _write_hypervisor_log(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = [
        {"timestamp": "2026-06-16T10:00:00Z", "level": "INFO", "logger": "lab", "message": "forward ok"},
        {
            "timestamp": "2026-06-16T10:01:00Z",
            "level": "ERROR",
            "logger": "urisys.forward",
            "message": "HTTP 502 Bad Gateway to urirdp",
        },
    ]
    path.write_text("\n".join(json.dumps(item) for item in entries) + "\n", encoding="utf-8")


def test_adapter_registry_includes_log_and_llm():
    assert adapter_for_uri("log://hypervisor?limit=10") is not None
    assert adapter_for_uri("llm://local/text/query/decide") is not None


def test_decide_mock_detects_502_in_context():
    context = {"entries": [{"level": "ERROR", "message": "HTTP 502 Bad Gateway"}]}
    result = decide(question="retry?", context_value=context, driver="mock")
    assert result["ok"] is True
    assert result["decision"] == "retry"


def test_run_nl_log_decision_workflow(tmp_path: Path, monkeypatch):
    log_file = tmp_path / "output" / "logs" / "hypervisor.log"
    _write_hypervisor_log(log_file)
    monkeypatch.setattr("uri3.logs.reader.find_repo_root", lambda start=None: tmp_path)

    payload = {
        "graph": {
            "id": "nl-log-decision",
            "nodes": [
                {
                    "id": "read_logs",
                    "uri": "log://hypervisor?level=ERROR&grep=502&limit=50",
                    "operation": "read",
                    "kind": "query",
                    "payload": {"summary": True},
                },
                {
                    "id": "nl_decide",
                    "uri": "llm://local/text/query/decide",
                    "operation": "decide",
                    "kind": "query",
                    "depends_on": ["read_logs"],
                    "payload": {
                        "question": "Czy logi wskazują na problem z forwardem do urirdp?",
                        "context_from": "read_logs",
                        "expect": "boolean",
                    },
                },
                {
                    "id": "retry_forward",
                    "uri": "assertion://equals",
                    "operation": "equals",
                    "kind": "assertion",
                    "depends_on": ["nl_decide"],
                    "condition": {"if": 'nl_decide.decision == "retry"'},
                    "payload": {"actual": "retry", "expected": "retry"},
                },
                {
                    "id": "escalate",
                    "uri": "message://local/alert/command/send",
                    "operation": "send",
                    "kind": "command",
                    "depends_on": ["nl_decide"],
                    "condition": {"if": 'nl_decide.decision == "abort"'},
                    "payload": {
                        "text": "W logach wykryto krytyczny błąd — wymaga interwencji",
                        "severity": "critical",
                    },
                },
            ],
        }
    }

    result = run_workflow(payload, approve=True, root=tmp_path, browser_mode="mock")
    statuses = {step.id: step.status for step in result.steps}
    outputs = {step.id: step.result for step in result.steps}

    assert result.ok is True
    assert statuses["read_logs"] == "completed"
    assert outputs["read_logs"]["count"] == 1
    assert statuses["nl_decide"] == "completed"
    assert outputs["nl_decide"]["ok"] is True
    assert outputs["nl_decide"]["decision"] == "retry"
    assert statuses["retry_forward"] == "completed"
    assert statuses["escalate"] == "skipped"
