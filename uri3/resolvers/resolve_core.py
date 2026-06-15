from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from uri3.resolvers.dispatch import resolve_target, scheme_from_uri
from uri3.resolvers.env_resolver import call_env
from uri3.resolvers.python_resolver import call_python


@dataclass
class UriResolution:
    uri: str
    scheme: str
    kind: str
    target: Any
    metadata: dict[str, Any]


def resolve(uri: str) -> UriResolution:
    scheme = scheme_from_uri(uri)
    target = resolve_target(scheme, uri)
    kind = "http" if scheme in {"http", "https"} else scheme
    return UriResolution(uri, scheme, kind, target, {})


def call(uri: str, payload: dict[str, Any] | None = None) -> Any:
    parsed = urlparse(uri)
    if parsed.scheme == "python":
        return call_python(uri, payload or {})
    if parsed.scheme == "env":
        return call_env(uri, payload)
    if parsed.scheme == "docker":
        from uri3.docker.controller import control_docker

        return control_docker(uri, payload=payload)
    if parsed.scheme == "log":
        from uri3.logs.reader import read_logs, summarize_logs

        options = payload or {}
        if options.get("summary"):
            return summarize_logs(uri)
        return read_logs(uri)
    raise ValueError(f"URI scheme is resolvable but not callable by local router: {parsed.scheme}")
