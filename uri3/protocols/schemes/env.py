from uri3.protocols.schemes.base import SchemeSpec


def spec() -> SchemeSpec:
    return SchemeSpec(
        scheme="env",
        description="Resolve environment variable names to values.",
        template="env://{name}",
        netloc={"name": "name", "required": True, "description": "Environment variable name."},
        path={"name": "name", "required": False, "description": "Alternative location for variable name."},
        actions=("resolve", "set"),
        cli=("uri3 resolve", "uri3 call", "uri3 schema"),
        python_api=(
            "uri3.resolvers.env_resolver.resolve_env",
            "uri3.resolvers.env_resolver.call_env",
        ),
        examples=(
            "env://OPENROUTER_API_KEY",
            "env:///PATH",
            "env://HYPERVISOR_SSH_PASSWORD?action=set&value=deploy&persist=1",
        ),
    )
