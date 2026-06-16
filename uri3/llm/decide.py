from __future__ import annotations

import json
import re
from typing import Any

from uri3.graph.payload_context import extract_log_entries


def _mock_decide(question: str, context_value: Any, *, expect: str) -> dict[str, Any]:
    entries = extract_log_entries(context_value)
    blob = json.dumps(context_value or entries, ensure_ascii=False, default=str).lower()
    has_error = any(str(item.get("level", "")).upper() == "ERROR" for item in entries)
    has_502 = "502" in blob
    retry = has_error or has_502
    reason_parts = []
    if has_error:
        reason_parts.append("ERROR level in logs")
    if has_502:
        reason_parts.append("502 in log content")
    reason = "; ".join(reason_parts) if reason_parts else "no critical signals in context"
    decision = "retry" if retry else "abort"
    ok = retry if expect == "boolean" else True
    return {
        "ok": ok,
        "decision": decision,
        "reason": f"mock-decide: {reason}",
        "confidence": 0.82 if retry else 0.91,
        "model": "mock-decide",
        "question": question,
    }


def _parse_json_response(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _decide_messages(question: str, context_value: Any) -> list[dict[str, str]]:
    context_text = json.dumps(context_value, ensure_ascii=False, default=str)
    if len(context_text) > 12000:
        context_text = context_text[:12000] + "…"
    prompt = (
        "You are a runtime judge for automation workflows. "
        "Return JSON only with keys: ok (bool), decision (retry|abort), reason (string), confidence (0-1). "
        f"Question: {question}\n"
        f"Context:\n{context_text}"
    )
    return [{"role": "user", "content": prompt}]


def _normalize_decide(parsed: dict[str, Any], *, model: str, question: str, expect: str) -> dict[str, Any]:
    decision = str(parsed.get("decision") or ("retry" if parsed.get("ok") else "abort")).lower()
    if decision not in {"retry", "abort", "escalate"}:
        decision = "retry" if parsed.get("ok") else "abort"
    ok = bool(parsed.get("ok"))
    if expect == "boolean" and "ok" not in parsed:
        ok = decision == "retry"
    return {
        "ok": ok,
        "decision": decision,
        "reason": str(parsed.get("reason") or "llm-decide"),
        "confidence": float(parsed.get("confidence", 0.7)),
        "model": model,
        "question": question,
    }


def decide(
    *,
    question: str,
    context_value: Any,
    expect: str = "boolean",
    model: str | None = None,
    driver: str = "mock",
    dry_run: bool = False,
) -> dict[str, Any]:
    """NL judge: map question + prior step context → {ok, decision, reason}."""
    question = str(question or "").strip()
    if dry_run or driver in {"mock", "heuristic"}:
        return _mock_decide(question, context_value, expect=expect)

    try:
        import litellm  # type: ignore
    except ImportError:
        return _mock_decide(question, context_value, expect=expect)

    chosen_model = model or "openrouter/google/gemini-2.0-flash-001"
    messages = _decide_messages(question, context_value)
    try:
        response = litellm.completion(
            model=chosen_model,
            messages=messages,
            temperature=0.0,
            max_tokens=512,
        )
        parsed = _parse_json_response(response.choices[0].message.content)
        return _normalize_decide(parsed, model=chosen_model, question=question, expect=expect)
    except Exception as exc:
        fallback = _mock_decide(question, context_value, expect=expect)
        fallback["reason"] = f"llm fallback ({exc}): {fallback['reason']}"
        fallback["model"] = "heuristic-fallback"
        return fallback
