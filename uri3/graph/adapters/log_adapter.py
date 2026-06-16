from __future__ import annotations

from typing import Any

from uri3.graph.execution_models import ExecutionContext
from uri3.graph.models import GraphNode
from uri3.logs.reader import read_logs, summarize_logs


class LogAdapter:
    """Execute log:// steps inside uri3 workflow graphs."""

    schemes = frozenset({"log"})

    def execute(self, node: GraphNode, context: ExecutionContext) -> dict[str, Any]:
        uri = node.uri
        payload = dict(node.payload or {})
        limit = int(payload.get("limit") or 0) or None

        if context.dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "uri": uri,
                "operation": node.operation,
            }

        summary = summarize_logs(uri, root=context.root)
        entries = read_logs(uri, root=context.root) if summary.get("exists") else []
        if limit is not None:
            entries = entries[:limit]

        result: dict[str, Any] = {
            "ok": True,
            "uri": uri,
            "entries": entries,
            "count": len(entries),
            "summary": summary,
        }
        if payload.get("summary") and not entries:
            result["ok"] = bool(summary.get("exists"))
        return result
