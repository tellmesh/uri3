from __future__ import annotations

from typing import Any


def summarize_fallbacks(fallbacks: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for entry in fallbacks or []:
        backend = entry.get("backend") or {}
        items.append(
            {
                "when": entry.get("when"),
                "backend_type": backend.get("type"),
                "backend_target": backend.get("target") or backend.get("command") or backend.get("url"),
            }
        )
    return items


def build_verification_hints(
    *,
    data_quality: dict[str, Any] | None,
    fallbacks: list[dict[str, Any]] | None = None,
    matched_registry: str,
) -> dict[str, Any]:
    dq = data_quality or {}
    enabled = bool(dq) or bool(fallbacks)
    hints: dict[str, Any] = {
        "source": "uri2verify",
        "matched_registry": matched_registry,
        "data_quality_enabled": bool(dq),
        "fallback_count": len(fallbacks or []),
        "expected_status_fields": [
            "workflow_status",
            "execution_status",
            "service_result_status",
            "data_quality_status",
            "verification_status",
        ],
    }
    if dq:
        hints["data_quality"] = {
            "failure_code": dq.get("failure_code") or "DATA_QUALITY_FAILED",
            "validators": list(dq.get("validators") or []),
            "min_confidence": dq.get("min_confidence"),
            "relevance_required": bool(dq.get("relevance_required")),
            "recoverable": bool(dq.get("recoverable", True)),
        }
        hints["on_failure"] = {
            "service_result_status": "failed",
            "data_quality_status": "failed",
            "verification_status": "failed",
            "note": "technical execution may still complete; business ok requires verification_status=passed",
        }
    if fallbacks:
        hints["fallbacks"] = summarize_fallbacks(fallbacks)
        hints["fallback_note"] = "fallback may recover service_result_status after data_quality failure"
    if not enabled:
        hints["note"] = "no data_quality or fallbacks configured for this resolution path"
    return hints
