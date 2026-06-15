from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from uri3.config.repo_root import config_repo_root as _repo_root
from uri3.config.llm_profile_builder import (
    chosen_profile_name,
    normalize_model_name,
    parse_llm_query,
    resolve_profile_api_key,
)
from uri3.config.uri_yaml import load_uri_yaml
from uri3.resolvers.llm_resolver import resolve_llm


def llm_config_path(root: Path | None = None) -> Path:
    return _repo_root(root) / "config" / "llm.uri.yaml"


def load_llm_config(root: Path | None = None) -> dict[str, Any]:
    path = llm_config_path(root)
    if not path.exists():
        return {"version": 1, "defaults": {"profile": "default"}, "profiles": {}}
    return load_uri_yaml(path)


@dataclass(frozen=True)
class LlmProfile:
    name: str
    model_uri: str
    model: str
    api_key: str | None
    provider: str | None
    base_url: str
    temperature: float = 0.1
    max_tokens: int = 8000
    response_format: str | None = None
    config_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "model_uri": self.model_uri,
            "model": self.model,
            "provider": self.provider,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": self.response_format,
            "config_path": self.config_path,
            "api_key_set": bool(self.api_key),
        }


def resolve_llm_profile(
    profile_name: str | None = None,
    *,
    root: Path | None = None,
    resolve_secrets: bool = True,
) -> LlmProfile:
    data = load_llm_config(root)
    profiles = data.get("profiles") or {}
    chosen = chosen_profile_name(profile_name, data.get("defaults") or {})
    profile = profiles.get(chosen) or profiles.get("default") or {}
    model_uri = str(profile.get("model") or "llm://openrouter/qwen/qwen3-coder-next")
    llm_data = resolve_llm(model_uri)
    query = parse_llm_query(model_uri)
    model = normalize_model_name(str(llm_data.get("model") or ""))
    return LlmProfile(
        name=chosen,
        model_uri=model_uri,
        model=model,
        api_key=resolve_profile_api_key(profile.get("api_key"), resolve_secrets=resolve_secrets),
        provider=str(profile.get("provider") or llm_data.get("provider") or ""),
        base_url=str(llm_data.get("base_url") or os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")).rstrip("/"),
        temperature=float(query.get("temperature", os.getenv("LLM_TEMPERATURE", "0.1"))),
        max_tokens=int(query.get("max_tokens", os.getenv("LLM_MAX_TOKENS", "8000"))),
        response_format=query.get("format"),
        config_path=str(llm_config_path(root)),
    )
