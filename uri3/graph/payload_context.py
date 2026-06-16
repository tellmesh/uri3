from __future__ import annotations

from typing import Any

from uri3.graph.execution_models import ExecutionContext

_REF_KEYS = {
    "context_from": "context",
    "transcript_from": "transcript",
    "actual_from": "actual",
    "input_from": "input",
}


def extract_transcript(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if not isinstance(value, dict):
        return ""
    for key in ("transcript", "text"):
        direct = value.get(key)
        if isinstance(direct, str) and direct.strip():
            return direct.strip()
    for container_key in ("response", "result"):
        container = value.get(container_key)
        if not isinstance(container, dict):
            continue
        inner = container.get("result") if isinstance(container.get("result"), dict) else container
        if isinstance(inner, dict):
            for key in ("transcript", "text"):
                nested = inner.get(key)
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
    return ""


def merge_payload_from(payload: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Merge fields from a prior step (`payload_from`, `uri_from`)."""
    out = dict(payload or {})
    if "payload_from" in out:
        ref = str(out.pop("payload_from"))
        src = resolve_step_ref(ref, context)
        merged = _extract_payload(src)
        if merged:
            out = {**merged, **out}
    if "uri_from" in out:
        ref = str(out.pop("uri_from"))
        src = resolve_step_ref(ref, context)
        uri = _extract_uri(src)
        if uri:
            out["_resolved_uri"] = uri
    return out


def _extract_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        direct = value.get("payload")
        if isinstance(direct, dict):
            return dict(direct)
        response = value.get("response")
        if isinstance(response, dict):
            result = response.get("result")
            if isinstance(result, dict) and isinstance(result.get("payload"), dict):
                return dict(result["payload"])
    return {}


def _extract_uri(value: Any) -> str:
    if isinstance(value, dict):
        uri = value.get("uri") or value.get("_resolved_uri")
        if isinstance(uri, str) and uri:
            return uri
        response = value.get("response")
        if isinstance(response, dict):
            result = response.get("result")
            if isinstance(result, dict) and isinstance(result.get("uri"), str):
                return result["uri"]
    return ""


def resolve_step_payload(payload: dict[str, Any] | None, context: ExecutionContext) -> dict[str, Any]:
    """Resolve `*_from` step references in adapter payloads."""
    out = dict(payload or {})
    for ref_key, target_key in _REF_KEYS.items():
        if ref_key not in out:
            continue
        ref = str(out.pop(ref_key))
        resolved = resolve_step_ref(ref, context)
        if ref_key == "transcript_from":
            out[target_key] = extract_transcript(resolved)
        else:
            out[target_key] = resolved
    return merge_payload_from(out, context)


def resolve_step_ref(ref: str, context: ExecutionContext) -> Any:
    if "." in ref:
        return context.resolve_ref(ref)
    return context.step_outputs.get(ref, {})


def extract_log_entries(context_value: Any) -> list[dict[str, Any]]:
    if isinstance(context_value, list):
        return [item for item in context_value if isinstance(item, dict)]
    if isinstance(context_value, dict):
        entries = context_value.get("entries")
        if isinstance(entries, list):
            return [item for item in entries if isinstance(item, dict)]
    return []
