"""Tests for llm:// text/query/plan and payload refs."""

from __future__ import annotations

from uri3.graph.payload_context import extract_transcript, resolve_step_payload
from uri3.graph.execution_models import ExecutionContext
from uri3.llm.plan import plan
from pathlib import Path


def test_plan_maps_kliknij_ok():
    result = plan(transcript="kliknij OK", allowed_schemes=["kvm"])
    assert result["ok"] is True
    assert result["uri"] == "kvm://local/task/command/click-text"
    assert result["payload"]["text"] == "OK"


def test_extract_transcript_from_lab_step_output():
    blob = {
        "ok": True,
        "response": {"ok": True, "result": {"transcript": "kliknij OK"}},
    }
    assert extract_transcript(blob) == "kliknij OK"


def test_resolve_transcript_from():
    ctx = ExecutionContext(
        workflow_id="wf",
        run_id="run1",
        root=Path("."),
        step_outputs={
            "stt_transcript": {
                "ok": True,
                "response": {"result": {"transcript": "kliknij OK"}},
            }
        },
    )
    payload = resolve_step_payload({"transcript_from": "stt_transcript"}, ctx)
    assert payload["transcript"] == "kliknij OK"


def test_resolve_payload_from_plan_step():
    ctx = ExecutionContext(
        workflow_id="wf",
        run_id="run1",
        root=Path("."),
        step_outputs={
            "map_voice": {
                "ok": True,
                "uri": "kvm://local/task/command/click-text",
                "payload": {"text": "OK"},
            }
        },
    )
    payload = resolve_step_payload({"payload_from": "map_voice"}, ctx)
    assert payload["text"] == "OK"
