"""Backward-compatible replay helpers.

Prefer ``uri2verify.replay`` for new code. Imports stay lazy so ``uri3`` can be
imported without the optional replay package installed.
"""

from __future__ import annotations

from typing import Any


def _replay_module():
    from uri2verify import replay

    return replay


def build_task_payload_from_events(*args: Any, **kwargs: Any) -> Any:
    return _replay_module().build_task_payload_from_events(*args, **kwargs)


def create_regression_test(*args: Any, **kwargs: Any) -> Any:
    return _replay_module().create_regression_test(*args, **kwargs)


def load_workflow_events(*args: Any, **kwargs: Any) -> Any:
    return _replay_module().load_workflow_events(*args, **kwargs)


def replay_workflow_events(*args: Any, **kwargs: Any) -> Any:
    return _replay_module().replay_workflow_events(*args, **kwargs)


def render_regression_test(*args: Any, **kwargs: Any) -> Any:
    return _replay_module().render_regression_test(*args, **kwargs)

__all__ = [
    "build_task_payload_from_events",
    "create_regression_test",
    "load_workflow_events",
    "replay_workflow_events",
    "render_regression_test",
]
