from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from uri3.graph.models import GraphNode

OPERATIONS_BY_SCHEME: dict[str, frozenset[str]] = {
    "browser": frozenset({"open", "read", "extract", "extract_dom", "screenshot", "capture", "capture_page"}),
    "dom": frozenset({"read", "extract", "extract_dom"}),
    "screen": frozenset({"capture", "screenshot"}),
    "assertion": frozenset({"check", "contains", "equals", "status-code", "json-path"}),
    "hypervisor": frozenset({"run", "status", "logs", "restart", "command", "query", "read"}),
    "http": frozenset({"read", "query", "get"}),
    "https": frozenset({"read", "query", "get"}),
    "log": frozenset({"read", "query"}),
    "agent": frozenset({"read", "status", "generate"}),
    "domain": frozenset({"generate", "read"}),
}

DEFAULT_KIND_BY_SCHEME: dict[str, str] = {
    "browser": "command",
    "dom": "query",
    "screen": "query",
    "assertion": "assertion",
    "hypervisor": "command",
    "http": "query",
    "https": "query",
    "log": "query",
    "agent": "command",
    "domain": "command",
}

APPROVAL_REQUIRED_KINDS = frozenset({"command"})


def scheme_from_uri(uri: str) -> str:
    return urlparse(uri).scheme or ""


def effective_kind(node: GraphNode) -> str:
    if node.kind:
        return node.kind
    return DEFAULT_KIND_BY_SCHEME.get(scheme_from_uri(node.uri), "query")


def requires_approval(node: GraphNode) -> bool:
    return effective_kind(node) in APPROVAL_REQUIRED_KINDS


def allowed_operations(scheme: str) -> frozenset[str]:
    return OPERATIONS_BY_SCHEME.get(scheme, frozenset({"read", "query", "check"}))


def validate_node_operation(node: GraphNode) -> str | None:
    scheme = scheme_from_uri(node.uri)
    if node.operation not in allowed_operations(scheme):
        allowed = ", ".join(sorted(allowed_operations(scheme)))
        return f"{node.id}: operation {node.operation!r} not allowed for scheme {scheme!r} (allowed: {allowed})"
    return None


def operation_registry_summary() -> dict[str, Any]:
    return {
        scheme: {
            "operations": sorted(operations),
            "default_kind": DEFAULT_KIND_BY_SCHEME.get(scheme, "query"),
            "requires_approval": DEFAULT_KIND_BY_SCHEME.get(scheme, "query") in APPROVAL_REQUIRED_KINDS,
        }
        for scheme, operations in sorted(OPERATIONS_BY_SCHEME.items())
    }
