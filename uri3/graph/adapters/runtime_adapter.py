from __future__ import annotations

from typing import Any

from uri3.graph.execution_models import ExecutionContext
from uri3.graph.models import GraphNode
from uri3.results import ServiceResult


def service_result_to_step_payload(result: ServiceResult) -> dict[str, Any]:
    body = result.to_dict()
    return {
        "ok": body.get("ok", False),
        "result_type": body.get("result_type"),
        "data": body.get("data"),
        "errors": body.get("errors"),
        "warnings": body.get("warnings"),
        "meta": body.get("meta"),
        "artifact_uri": body.get("artifact_uri"),
        "workflow_status": body.get("workflow_status"),
        "execution_status": body.get("execution_status"),
        "service_result_status": body.get("service_result_status"),
    }


class RuntimeAdapter:
    """Delegate executable runtime URI schemes to uri2run."""

    schemes = frozenset(
        {
            "python",
            "shell",
            "http",
            "https",
            "stdio",
            "ws",
            "sse",
            "docker",
            "ssh",
            "mcp",
            "a2a",
        }
    )

    def execute(self, node: GraphNode, context: ExecutionContext) -> dict[str, Any]:
        if context.dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "uri": node.uri,
                "operation": node.operation,
                "payload": dict(node.payload or {}),
                "runtime": "uri2run",
            }

        from uri2run import run_target

        payload = dict(node.payload or {})
        runtime_context = {
            "root": str(context.root),
            "run_id": context.run_id,
            "workflow_id": context.workflow_id,
            "operation": node.operation,
        }
        result = run_target(node.uri, payload, runtime_context)
        step_payload = service_result_to_step_payload(result)
        step_payload["runtime"] = "uri2run"
        if not step_payload.get("ok") and not step_payload.get("error"):
            errors = step_payload.get("errors") or []
            if errors:
                step_payload["error"] = (
                    errors[0].get("detail") if isinstance(errors[0], dict) else str(errors[0])
                )
        return step_payload
