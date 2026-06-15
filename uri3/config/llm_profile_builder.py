from __future__ import annotations

import os
from typing import Any
from urllib.parse import parse_qs, urlparse

from uri3.resolvers.llm_resolver import resolve_llm


def parse_llm_query(model_uri: str) -> dict[str, Any]:
    parsed = urlparse(model_uri)
    query = parse_qs(parsed.query, keep_blank_values=True)
    result: dict[str, Any] = {}
    if "temp" in query or "temperature" in query:
        raw = (query.get("temp") or query.get("temperature") or ["0.1"])[0]
        result["temperature"] = float(raw)
    if "max_tokens" in query:
        result["max_tokens"] = int(query["max_tokens"][0])
    if "format" in query:
        result["format"] = query["format"][0]
    return result


def chosen_profile_name(profile_name: str | None, defaults: dict[str, Any]) -> str:
    return (
        profile_name
        or os.environ.get("DEFAULT_LLM_PROFILE")
        or defaults.get("profile", "default")
    )


def resolve_profile_api_key(api_key_uri: Any, *, resolve_secrets: bool) -> str | None:
    if not resolve_secrets or not isinstance(api_key_uri, str) or not api_key_uri.startswith("env://"):
        return None
    from uri3.resolvers.env_resolver import resolve_env

    env = resolve_env(api_key_uri)
    return env.get("value")


def normalize_model_name(model: str) -> str:
    if model.startswith("openrouter/"):
        return model.removeprefix("openrouter/")
    return model
