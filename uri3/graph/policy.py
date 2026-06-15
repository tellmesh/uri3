from __future__ import annotations

from uri3.graph.models import GraphNode
from uri3.graph.operation_registry import effective_kind, requires_approval


def can_execute_step(
    node: GraphNode,
    *,
    approve_commands: bool,
    dry_run: bool,
) -> tuple[bool, str | None]:
    if dry_run:
        return True, None
    kind = effective_kind(node)
    if kind == "assertion" or kind == "query":
        return True, None
    if requires_approval(node) and not approve_commands:
        return False, f"command node {node.id!r} requires --approve"
    return True, None
