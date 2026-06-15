from __future__ import annotations

import re

from uri3.graph.execution_models import ExecutionContext


def evaluate_condition(condition: dict | None, context: ExecutionContext) -> bool:
    if not condition:
        return True
    expr = str(condition.get("if") or "").strip()
    if not expr:
        return True
    match = re.match(r"^([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\s*==\s*(true|false)$", expr, re.I)
    if not match:
        return True
    step_id, field_name, expected_raw = match.group(1), match.group(2), match.group(3)
    actual = context.step_outputs.get(step_id, {}).get(field_name)
    expected = expected_raw.lower() == "true"
    if isinstance(actual, bool):
        return actual == expected
    if actual is None:
        return expected is False
    return str(actual).lower() == str(expected).lower()
