from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

from uri3.llm.decide import _parse_json_response

# Shared phrase map (same semantics as urichat.handlers for migration).
_PHRASE_MAP: list[tuple[str, str, dict[str, Any]]] = [
    ("kliknij ok", "kvm://local/task/command/click-text", {"text": "OK"}),
    ("otwórz przeglądark", "browser://chrome/page/open", {"url": "http://localhost:8101/health"}),
    ("zrób screenshot", "kvm://local/monitor/primary/query/screenshot", {}),
    ("status rdp", "rdp://local/display/query/status", {}),
]


def _match_transcript(text: str) -> tuple[str, dict[str, Any]]:
    lowered = (text or "").lower().strip()
    for phrase, uri, payload in _PHRASE_MAP:
        if phrase in lowered:
            return uri, dict(payload)
    return "kvm://local/task/command/click-text", {"text": "OK"}


def _plan_messages(transcript: str, allowed_schemes: list[str] | None) -> list[dict[str, str]]:
    allowed = ", ".join(allowed_schemes) if allowed_schemes else "kvm, browser, rdp"
    prompt = (
        "Map a voice/desktop command to a URI automation step. "
        f"Allowed schemes: {allowed}. "
        'Return JSON only: {"uri": "scheme://...", "payload": {...}}. '
        f"Command: {transcript}"
    )
    return [{"role": "user", "content": prompt}]


def _normalize_plan(parsed: dict[str, Any], *, transcript: str, model: str) -> dict[str, Any]:
    uri = str(parsed.get("uri") or "")
    payload = parsed.get("payload") if isinstance(parsed.get("payload"), dict) else {}
    if not uri:
        return {"ok": False, "error": "llm plan missing uri", "transcript": transcript}
    return {
        "ok": True,
        "uri": uri,
        "payload": payload,
        "transcript": transcript,
        "model": model,
    }


def plan(
    *,
    transcript: str,
    allowed_schemes: list[str] | None = None,
    driver: str = "mock",
    dry_run: bool = False,
    model: str | None = None,
) -> dict[str, Any]:
    """Map voice/text command → target URI envelope."""
    transcript = str(transcript or "").strip()
    if not transcript:
        return {"ok": False, "error": "transcript is required"}

    if dry_run or driver in {"mock", "heuristic", "phrase-map"}:
        uri, inner_payload = _match_transcript(transcript)
        scheme = urlparse(uri).scheme
        if allowed_schemes and scheme not in {s.strip() for s in allowed_schemes if s.strip()}:
            return {
                "ok": False,
                "error": f"scheme {scheme!r} not in allowed_schemes",
                "uri": uri,
                "payload": inner_payload,
                "transcript": transcript,
            }
        return {
            "ok": True,
            "uri": uri,
            "payload": inner_payload,
            "transcript": transcript,
            "model": "phrase-map",
            "driver": driver,
        }

    chosen_model = model or "openrouter/google/gemini-2.0-flash-001"
    messages = _plan_messages(transcript, allowed_schemes)
    try:
        import litellm  # type: ignore

        response = litellm.completion(
            model=chosen_model,
            messages=messages,
            temperature=0.0,
            max_tokens=512,
        )
        parsed = _parse_json_response(response.choices[0].message.content)
        result = _normalize_plan(parsed, transcript=transcript, model=chosen_model)
        scheme = urlparse(result.get("uri", "")).scheme
        if result.get("ok") and allowed_schemes and scheme not in allowed_schemes:
            return {
                "ok": False,
                "error": f"scheme {scheme!r} not in allowed_schemes",
                "uri": result.get("uri"),
                "payload": result.get("payload"),
                "transcript": transcript,
                "model": chosen_model,
            }
        result["driver"] = driver
        return result
    except Exception as exc:
        fallback = plan(
            transcript=transcript,
            allowed_schemes=allowed_schemes,
            driver="phrase-map",
            dry_run=True,
        )
        fallback["reason"] = f"llm fallback ({exc})"
        return fallback
