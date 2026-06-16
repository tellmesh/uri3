from __future__ import annotations

import re

from uri3.graph.execution_models import ExecutionContext

_BOOL_PATTERN = re.compile(
    r"^([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\s*==\s*(true|false)$",
    re.I,
)
_STRING_PATTERN = re.compile(
    r"""^([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\s*==\s*(?:"([^"]*)"|'([^']*)')$""",
)


def _compare(actual: object, expected: object) -> bool:
    if isinstance(actual, bool) and isinstance(expected, bool):
        return actual == expected
    if actual is None:
        return expected in (False, "", None)
    return str(actual).lower() == str(expected).lower()


def evaluate_condition(condition: dict | None, context: ExecutionContext) -> bool:
    if not condition:
        return True
    expr = str(condition.get("if") or "").strip()
    if not expr:
        return True

    match = _BOOL_PATTERN.match(expr)
    if match:
        step_id, field_name, expected_raw = match.group(1), match.group(2), match.group(3)
        actual = context.step_outputs.get(step_id, {}).get(field_name)
        expected = expected_raw.lower() == "true"
        return _compare(actual, expected)

    match = _STRING_PATTERN.match(expr)
    if match:
        step_id, field_name = match.group(1), match.group(2)
        expected = match.group(3) if match.group(3) is not None else match.group(4)
        actual = context.step_outputs.get(step_id, {}).get(field_name)
        return _compare(actual, expected)

    return True
