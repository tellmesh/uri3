from __future__ import annotations

from typing import Any


def build_resolver_registry() -> dict[str, Any]:
    from uri3.resolvers.env_resolver import EnvResolver
    from uri3.resolvers.http_resolver import HttpResolver
    from uri3.resolvers.llm_resolver import LLMResolver
    from uri3.resolvers.log_resolver import LogResolver
    from uri3.resolvers.python_resolver import PythonResolver

    http = HttpResolver()
    return {
        "env": EnvResolver(),
        "llm": LLMResolver(),
        "log": LogResolver(),
        "python": PythonResolver(),
        "http": http,
        "https": http,
    }
