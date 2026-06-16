"""Tests for workflow if: condition evaluation."""

from __future__ import annotations

from pathlib import Path

from uri3.graph.conditions import evaluate_condition
from uri3.graph.execution_models import ExecutionContext


def test_condition_string_equality():
    ctx = ExecutionContext(
        workflow_id="wf",
        run_id="r1",
        root=Path("."),
        step_outputs={"nl_decide": {"ok": True, "decision": "retry"}},
    )
    assert evaluate_condition({"if": 'nl_decide.decision == "retry"'}, ctx) is True
    assert evaluate_condition({"if": 'nl_decide.decision == "abort"'}, ctx) is False


def test_condition_bool_still_works():
    ctx = ExecutionContext(
        workflow_id="wf",
        run_id="r1",
        root=Path("."),
        step_outputs={"step_a": {"ok": False}},
    )
    assert evaluate_condition({"if": "step_a.ok == false"}, ctx) is True


def test_condition_single_quotes():
    ctx = ExecutionContext(
        workflow_id="wf",
        run_id="r1",
        root=Path("."),
        step_outputs={"step_a": {"decision": "abort"}},
    )
    assert evaluate_condition({"if": "step_a.decision == 'abort'"}, ctx) is True
