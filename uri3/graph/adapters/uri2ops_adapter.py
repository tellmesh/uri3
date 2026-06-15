from __future__ import annotations

import json
import os
from importlib import import_module
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from uri2ops.operation_registry.dispatcher import call_handler
from uri2ops.operation_registry.uri_mapping import registry_operation, registry_scheme
from uri2ops.remote_registry.loader import resolve_operation_registry

from uri3.config.repo_root import ensure_repo_root_on_syspath
from uri3.graph.artifacts import mock_screenshot_png, write_artifact
from uri3.graph.execution_models import ExecutionContext
from uri3.graph.models import GraphNode

ensure_repo_root_on_syspath()

OPERATOR_SCHEMES = frozenset({"browser", "dom", "screen", "input"})


def _use_direct_uri2ops() -> bool:
    return os.getenv("URI3_DIRECT_URI2OPS", "").lower() in {"1", "true", "yes"}


def _use_legacy_browser_adapter() -> bool:
    return os.getenv("URI3_USE_LEGACY_BROWSER", "").lower() in {"1", "true", "yes"}


def _repo_for_routing(context: ExecutionContext) -> Path:
    try:
        from hypervisor.paths import find_repo_root

        return find_repo_root(context.root)
    except Exception:
        return context.root


def _service_result_to_payload(result: Any) -> dict[str, Any]:
    body = result.to_dict()
    if not body.get("ok", False):
        errors = body.get("errors") or []
        detail = errors[0].get("detail") if errors else "operator dispatch failed"
        return {"ok": False, "error": detail, **body}
    data = body.get("data")
    if isinstance(data, dict):
        return {"ok": True, **data}
    metadata = {key: value for key, value in body.items() if key != "data"}
    return {"ok": True, "data": data, **metadata}


def _sync_session_from_output(context: ExecutionContext, output: dict[str, Any]) -> None:
    state = context.adapter_state.setdefault("uri2ops", {})
    session = state.setdefault("session", {})
    if not isinstance(session, dict):
        return
    if output.get("text"):
        session["page_text"] = output["text"]
    if output.get("url"):
        session["last_url"] = output["url"]


def _cleanup_browser_session(state: dict[str, Any]) -> None:
    try:
        module = import_module("agents.operators.browser_operator.adapters.browser_router")
        cleanup_browser_session = module.cleanup_browser_session
    except Exception:
        return
    cleanup_browser_session(state)


def _execute_via_hypervisor(
    node: GraphNode,
    context: ExecutionContext,
    payload: dict[str, Any],
) -> dict[str, Any]:
    from hypervisor.routing import call_uri

    runtime_context = _runtime_context(context)
    runtime_payload = dict(payload)
    runtime_session = runtime_context.get("session")
    if isinstance(runtime_session, dict):
        runtime_payload.setdefault("session", runtime_session)
    if context.browser_mode and context.browser_mode != "auto":
        runtime_payload.setdefault("environment", context.browser_mode)
        runtime_payload.setdefault("adapter", context.browser_mode)
    result = call_uri(
        node.uri,
        runtime_payload,
        root=_repo_for_routing(context),
        approved=context.approve_commands,
    )
    output = _service_result_to_payload(result)
    if output.get("ok"):
        _sync_session_from_output(context, output)
    return output


def _runtime_context(context: ExecutionContext) -> dict[str, Any]:
    state = context.adapter_state.setdefault("uri2ops", {})
    session = state.setdefault("session", {})
    return {
        "adapter": context.browser_mode,
        "root": str(context.root),
        "task_id": context.workflow_id,
        "run_id": context.run_id,
        "session": session,
    }


def _artifact_suffix(scheme: str, operation: str) -> str | None:
    if scheme == "browser" and operation == "open":
        return "open.json"
    if scheme in {"browser", "dom"} and operation in {"read", "extract", "extract_dom"}:
        return "dom.json"
    if scheme in {"browser", "screen"} and operation in {"screenshot", "capture", "capture_page"}:
        return "screenshot.png"
    if scheme == "screen" and operation == "observe":
        return "screenshot.png"
    return None


def _attach_workflow_artifact(
    node: GraphNode,
    context: ExecutionContext,
    payload: dict[str, Any],
) -> dict[str, Any]:
    scheme = urlparse(node.uri).scheme
    operation = registry_operation(scheme, node.operation)
    suffix = _artifact_suffix(scheme, operation)
    if suffix is None:
        return payload

    if suffix.endswith(".json"):
        body = json.dumps(payload, indent=2, ensure_ascii=False)
    else:
        # For screenshots we must emit *valid* PNG bytes so the artifact is a real image file.
        # If the underlying handler provided a real capture path, re-use its bytes.
        real_path = payload.get("path")
        if real_path:
            rp = Path(real_path)
            body = rp.read_bytes() if rp.exists() else mock_screenshot_png()
        else:
            body = mock_screenshot_png()
    _, artifact_uri = write_artifact(context, node.id, suffix, body)
    return {**payload, "artifact_uri": artifact_uri}


class Uri2OpsAdapter:
    """Delegates operator schemes to uri2ops operation registry."""

    schemes = OPERATOR_SCHEMES

    def execute(self, node: GraphNode, context: ExecutionContext) -> dict[str, Any]:
        scheme = urlparse(node.uri).scheme
        registry_scheme_name = registry_scheme(scheme)
        registry_operation_name = registry_operation(scheme, node.operation)
        registry = resolve_operation_registry(root=context.root)
        spec = registry.require(registry_scheme_name, registry_operation_name)

        payload = dict(node.payload or {})
        payload.setdefault("target_uri", node.uri)
        payload.setdefault("step_id", node.id)

        if not _use_direct_uri2ops():
            try:
                output = _execute_via_hypervisor(node, context, payload)
            except Exception:
                output = None
            if output is not None:
                if not bool(output.get("ok", True)):
                    return output
                return _attach_workflow_artifact(node, context, output)

        runtime_context = _runtime_context(context)
        output = call_handler(spec, payload, runtime_context)
        if not bool(output.get("ok", True)):
            return output
        return _attach_workflow_artifact(node, context, output)


def cleanup_operator_adapters(context: ExecutionContext) -> None:
    uri2ops_state = context.adapter_state.get("uri2ops")
    if isinstance(uri2ops_state, dict):
        _cleanup_browser_session(uri2ops_state)


def resolve_operator_adapter(context: ExecutionContext) -> str:
    if _use_legacy_browser_adapter():
        return "legacy"
    return "uri2ops"
