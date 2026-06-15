from __future__ import annotations

import warnings
from typing import Any
from urllib.parse import urlparse

from uri3.graph.adapters.base import StepAdapter
from uri3.graph.adapters.browser_router import BrowserRouterAdapter
from uri3.graph.adapters.runtime_adapter import RuntimeAdapter
from uri3.graph.adapters.uri2ops_adapter import Uri2OpsAdapter, _use_legacy_browser_adapter
from uri3.graph.execution_models import ExecutionContext
from uri3.graph.models import GraphNode


class AssertionAdapter:
    schemes = frozenset({"assertion"})

    def execute(self, node: GraphNode, context: ExecutionContext) -> dict[str, Any]:
        payload = node.payload or {}
        expected = payload.get("expected")
        actual_ref = payload.get("actual_from")
        actual = payload.get("actual")
        if actual_ref:
            actual = context.resolve_ref(str(actual_ref))
        operation = node.operation
        if operation in {"check", "contains"} or node.uri.endswith("contains"):
            ok = expected is not None and str(expected) in str(actual or "")
            return {"ok": ok, "expected": expected, "actual": actual}
        if operation == "equals":
            ok = str(actual) == str(expected)
            return {"ok": ok, "expected": expected, "actual": actual}
        if operation == "status-code":
            code = payload.get("code", 200)
            actual_code = payload.get("actual_code", 200)
            return {"ok": int(actual_code) == int(code), "expected": code, "actual": actual_code}
        if operation == "json-path":
            ok = bool(payload.get("match", True))
            return {"ok": ok, "path": payload.get("path"), "actual": payload.get("actual")}
        return {"ok": False, "error": f"unsupported assertion operation: {operation}"}


class HypervisorAdapter:
    schemes = frozenset({"hypervisor"})

    def execute(self, node: GraphNode, context: ExecutionContext) -> dict[str, Any]:
        parsed = urlparse(node.uri)
        from hypervisor.deployment_registry.selector import parse_hypervisor_uri, resolve_deployment

        deployment_selector, action = parse_hypervisor_uri(node.uri)
        prefer_local = parsed.netloc == "local"
        if context.dry_run or not context.approve_commands:
            return {
                "ok": True,
                "dry_run": True,
                "deployment_id": deployment_selector,
                "action": action,
                "plan": {
                    "deployment_id": deployment_selector,
                    "action": action,
                    "uri": node.uri,
                    "hint": "Use uri3 run-workflow --approve to delegate to hypervisor lifecycle.",
                },
            }

        deployment = resolve_deployment(
            deployment_selector,
            root=context.root,
            prefer_local=prefer_local,
        )
        from hypervisor.deployment_registry.run_plans import build_run_plan

        deployment_id = deployment.id
        if action in {"run", "restart"}:
            plan = build_run_plan(deployment, root=context.root)
            return {"ok": True, "deployment_id": deployment_id, "action": action, "plan": plan}
        if action in {"status", "logs"}:
            from hypervisor.deployment_registry.lifecycle import agent_status

            status = agent_status(deployment_id, root=context.root, check_health=action != "logs")
            return {"ok": True, "deployment_id": deployment_id, "action": action, "status": status}
        return {
            "ok": True,
            "dry_run": True,
            "deployment_id": deployment_id,
            "action": action,
            "message": f"hypervisor adapter mock handled {node.uri}",
        }


class LegacyBrowserRouterAdapter(BrowserRouterAdapter):
    """Deprecated: use uri2ops via Uri2OpsAdapter (set URI3_USE_LEGACY_BROWSER=1 to force)."""

    def execute(self, node: GraphNode, context: ExecutionContext) -> dict[str, Any]:
        warnings.warn(
            "uri3 browser adapters are deprecated; operator schemes delegate to uri2ops",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().execute(node, context)


def _operator_adapter() -> StepAdapter:
    if _use_legacy_browser_adapter():
        return LegacyBrowserRouterAdapter()
    return Uri2OpsAdapter()


ADAPTERS: list[StepAdapter] = [
    RuntimeAdapter(),
    _operator_adapter(),
    AssertionAdapter(),
    HypervisorAdapter(),
]


def adapter_for_uri(uri: str) -> StepAdapter | None:
    scheme = urlparse(uri).scheme
    for adapter in ADAPTERS:
        if scheme in adapter.schemes:
            return adapter
    return None
