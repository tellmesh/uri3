from uri3.protocols.schemes.base import SchemeSpec


def spec() -> SchemeSpec:
    return SchemeSpec(
        scheme="mcp",
        description="Model Context Protocol server reference.",
        template="mcp://{server}[/{path}]",
        netloc={"name": "server", "required": True, "description": "MCP server identifier or host."},
        path={"name": "path", "required": False, "default": "/", "description": "Server sub-path."},
        actions=("resolve",),
        cli=("uri3 resolve", "uri3 schema"),
        python_api=("uri3.resolvers.protocol_resolver.resolve_mcp",),
        examples=("mcp://filesystem/tools",),
    )
