from uri3.protocols.schemes.base import SchemeSpec


def spec(scheme: str) -> SchemeSpec:
    return SchemeSpec(
        scheme=scheme,
        description=f"HTTP endpoint reference via {scheme}://.",
        template=f"{scheme}://{{host}}[{{path}}][?{{query}}]",
        netloc={"name": "host", "required": True, "description": "Host and optional port."},
        path={"name": "path", "required": False, "description": "Request path."},
        actions=("resolve", "scan"),
        cli=("uri3 scan", "uri3 resolve", "uri3 schema"),
        python_api=("uri3.scanner.http_scanner.scan_http",),
        examples=(f"{scheme}://localhost:8101/.well-known/agent-card.json",),
    )
