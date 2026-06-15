from __future__ import annotations

from urllib.parse import urlparse


def resolve_http_like(uri: str) -> dict[str, str]:
    return {"url": uri, "transport": "http"}


def resolve_a2a(uri: str) -> dict[str, str]:
    parsed = urlparse(uri)
    return {"agent": parsed.netloc, "path": parsed.path or "/", "protocol": "a2a"}


def resolve_mcp(uri: str) -> dict[str, str]:
    parsed = urlparse(uri)
    return {"server": parsed.netloc, "path": parsed.path or "/", "protocol": "mcp"}


def resolve_resource(uri: str) -> dict[str, str]:
    parsed = urlparse(uri)
    if parsed.scheme == "ssh":
        from uri3.resolvers.ssh_resolver import resolve_ssh

        data = resolve_ssh(uri)
        return {key: str(value) for key, value in data.items() if value is not None}
    return {"scheme": parsed.scheme, "namespace": parsed.netloc, "path": parsed.path}
