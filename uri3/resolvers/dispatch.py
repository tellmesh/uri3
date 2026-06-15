from __future__ import annotations

from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

from uri3.resolvers.env_resolver import resolve_env
from uri3.resolvers.file_resolver import resolve_file
from uri3.resolvers.llm_resolver import resolve_llm
from uri3.resolvers.log_resolver import resolve_log
from uri3.resolvers.protocol_resolver import (
    resolve_a2a,
    resolve_http_like,
    resolve_mcp,
    resolve_resource,
)
from uri3.resolvers.pypi_resolver import resolve_pypi
from uri3.resolvers.python_resolver import resolve_python

RESOURCE_SCHEMES = frozenset(
    {
        "resource",
        "domain",
        "artifact",
        "command",
        "event",
        "input",
        "agent",
        "local",
        "ssh",
        "git",
        "browser",
        "dom",
        "screen",
        "assertion",
        "hypervisor",
    }
)


def _resolve_docker(uri: str) -> Any:
    from uri3.resolvers.docker_resolver import resolve_docker

    return resolve_docker(uri)


RESOLVE_BY_SCHEME: dict[str, Callable[[str], Any]] = {
    "env": resolve_env,
    "llm": resolve_llm,
    "python": resolve_python,
    "pypi": resolve_pypi,
    "log": resolve_log,
    "http": resolve_http_like,
    "https": resolve_http_like,
    "a2a": resolve_a2a,
    "mcp": resolve_mcp,
    "docker": _resolve_docker,
    "file": resolve_file,
}


def resolve_target(scheme: str, uri: str) -> Any:
    if scheme in RESOURCE_SCHEMES:
        return resolve_resource(uri)
    resolver = RESOLVE_BY_SCHEME.get(scheme)
    if resolver is None:
        raise ValueError(f"Unsupported URI scheme: {scheme}")
    return resolver(uri)


def scheme_from_uri(uri: str) -> str:
    scheme = urlparse(uri).scheme
    if not scheme:
        raise ValueError(f"URI has no scheme: {uri}")
    return scheme
