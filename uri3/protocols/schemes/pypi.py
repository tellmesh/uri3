from uri3.protocols.schemes.base import SchemeSpec


def spec() -> SchemeSpec:
    return SchemeSpec(
        scheme="pypi",
        description="Reference a PyPI package and optional version.",
        template="pypi://{package}[/{version}]",
        netloc={"name": "package", "required": True, "description": "PyPI distribution name."},
        path={"name": "version", "required": False, "description": "Package version; defaults to latest."},
        actions=("resolve",),
        cli=("uri3 resolve", "uri3 schema"),
        python_api=("uri3.resolvers.pypi_resolver.resolve_pypi",),
        examples=("pypi://requests", "pypi://pydantic/2.8.0"),
    )
