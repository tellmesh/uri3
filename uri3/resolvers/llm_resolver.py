from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from uri3.protocols.parser import parse_uri


def resolve_llm(uri: str) -> dict[str, str | None]:
    parsed = urlparse(uri)
    provider = parsed.netloc
    model = parsed.path.lstrip("/")
    base_url = (
        os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
        if provider == "openrouter"
        else os.getenv("LLM_BASE_URL")
    )
    api_key_env = "OPENROUTER_API_KEY" if provider == "openrouter" else "LLM_API_KEY"
    return {
        "provider": provider,
        "model": f"{provider}/{model}" if provider and model else uri.removeprefix("llm://"),
        "base_url": base_url,
        "api_key_uri": f"env://{api_key_env}",
    }


@dataclass
class LLMRef:
    provider: str
    model: str
    raw_uri: str


class LLMResolver:
    scheme = "llm"

    def resolve(self, uri) -> LLMRef:
        data = resolve_llm(uri)
        parsed = parse_uri(uri)
        return LLMRef(
            provider=data["provider"] or parsed.netloc,
            model=parsed.path.lstrip("/"),
            raw_uri=uri,
        )
