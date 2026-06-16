from __future__ import annotations

from typing import Any

from uri3.graph.execution_models import ExecutionContext
from uri3.graph.models import GraphNode
from uri3.graph.payload_context import resolve_step_payload


class MessageAdapter:
    schemes = frozenset({"message"})

    def execute(self, node: GraphNode, context: ExecutionContext) -> dict[str, Any]:
        payload = resolve_step_payload(node.payload, context)
        text = str(payload.get("text") or "")
        if context.dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "uri": node.uri,
                "text": text,
                "channel": payload.get("channel", "alert"),
            }
        return {
            "ok": bool(text),
            "text": text,
            "channel": str(payload.get("channel") or "alert"),
            "severity": str(payload.get("severity") or "info"),
            "delivered": bool(text),
        }
