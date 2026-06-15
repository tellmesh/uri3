from uri3.protocols.schemes.base import SchemeSpec


def spec() -> SchemeSpec:
    return SchemeSpec(
        scheme="a2a",
        description="Agent-to-agent endpoint reference.",
        template="a2a://{agent}[/{path}]",
        netloc={"name": "agent", "required": True, "description": "Agent identifier or host."},
        path={"name": "path", "required": False, "default": "/", "description": "Agent sub-path."},
        actions=("resolve",),
        cli=("uri3 resolve", "uri3 schema"),
        python_api=("uri3.resolvers.protocol_resolver.resolve_a2a",),
        examples=("a2a://weather-map-agent/tasks",),
    )
