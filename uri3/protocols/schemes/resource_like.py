from uri3.protocols.schemes.base import SchemeSpec


def resource_like_spec(scheme: str, description: str) -> SchemeSpec:
    return SchemeSpec(
        scheme=scheme,
        description=description,
        template=f"{scheme}://{{namespace}}/{{path}}",
        netloc={"name": "namespace", "required": False, "description": "Logical namespace or host."},
        path={"name": "path", "required": False, "description": "Resource path within namespace."},
        actions=("resolve",),
        cli=("uri3 resolve", "uri3 schema"),
        python_api=("uri3.resolvers.protocol_resolver.resolve_resource",),
        documented=False,
        examples=(f"{scheme}://example/resource",),
    )
