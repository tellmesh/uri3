from uri3.protocols.schemes.base import SchemeSpec


def spec() -> SchemeSpec:
    return SchemeSpec(
        scheme="llm",
        description="Reference an LLM provider and model.",
        template="llm://{provider}/{model}",
        netloc={"name": "provider", "required": True, "description": "LLM provider, e.g. openrouter."},
        path={"name": "model", "required": True, "description": "Model identifier without provider prefix."},
        constants={"providers": ["openrouter"], "api_key_env": {"openrouter": "OPENROUTER_API_KEY"}},
        actions=("resolve",),
        cli=("uri3 resolve", "uri3 schema"),
        python_api=("uri3.resolvers.llm_resolver.resolve_llm",),
        examples=("llm://openrouter/anthropic/claude-3.5-sonnet",),
    )
