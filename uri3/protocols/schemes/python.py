from uri3.protocols.schemes.base import SchemeSpec


def spec() -> SchemeSpec:
    return SchemeSpec(
        scheme="python",
        description="Reference a Python callable as module:function.",
        template="python://{module}:{function}",
        netloc={"name": "target", "required": True, "description": "Module path before colon."},
        path={"name": "function", "required": True, "description": "Function name after colon."},
        actions=("resolve", "call"),
        cli=("uri3 resolve", "uri3 schema"),
        python_api=(
            "uri3.resolvers.python_resolver.resolve_python",
            "uri3.resolvers.python_resolver.call_python",
        ),
        examples=("python://hypervisor.core:Hypervisor",),
    )
