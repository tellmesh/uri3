from __future__ import annotations

from typing import Any, Callable
from urllib.parse import urlparse

RESOURCE_LIKE_SCHEMES = frozenset(
    {
        "resource",
        "artifact",
        "domain",
        "agent",
        "local",
        "input",
        "command",
        "event",
        "git",
    }
)


def _parse_log(uri: str) -> dict[str, Any]:
    from uri3.resolvers.log_resolver import parse_log_uri

    return parse_log_uri(uri).to_dict()


def _parse_env(uri: str) -> dict[str, Any]:
    from uri3.resolvers.env_resolver import resolve_env

    return resolve_env(uri)


def _parse_python(uri: str) -> dict[str, Any]:
    from uri3.resolvers.python_resolver import resolve_python

    return resolve_python(uri)


def _parse_llm(uri: str) -> dict[str, Any]:
    from uri3.resolvers.llm_resolver import resolve_llm

    return resolve_llm(uri)


def _parse_pypi(uri: str) -> dict[str, Any]:
    from uri3.resolvers.pypi_resolver import resolve_pypi

    return resolve_pypi(uri)


def _parse_http(uri: str) -> dict[str, Any]:
    from uri3.resolvers.protocol_resolver import resolve_http_like

    return resolve_http_like(uri)


def _parse_a2a(uri: str) -> dict[str, Any]:
    from uri3.resolvers.protocol_resolver import resolve_a2a

    return resolve_a2a(uri)


def _parse_mcp(uri: str) -> dict[str, Any]:
    from uri3.resolvers.protocol_resolver import resolve_mcp

    return resolve_mcp(uri)


def _parse_docker(uri: str) -> dict[str, Any]:
    from uri3.resolvers.docker_resolver import resolve_docker

    return resolve_docker(uri)


def _parse_ssh(uri: str) -> dict[str, Any]:
    from uri3.resolvers.ssh_resolver import resolve_ssh

    return resolve_ssh(uri)


def _parse_resource(uri: str) -> dict[str, Any]:
    from uri3.resolvers.protocol_resolver import resolve_resource

    return resolve_resource(uri)


_SCHEME_PARSERS: dict[str, Callable[[str], dict[str, Any]]] = {
    "log": _parse_log,
    "env": _parse_env,
    "python": _parse_python,
    "llm": _parse_llm,
    "pypi": _parse_pypi,
    "http": _parse_http,
    "https": _parse_http,
    "a2a": _parse_a2a,
    "mcp": _parse_mcp,
    "docker": _parse_docker,
    "ssh": _parse_ssh,
}


def parse_instance(scheme: str, uri: str) -> dict[str, Any]:
    parser = _SCHEME_PARSERS.get(scheme)
    if parser is not None:
        return parser(uri)
    if scheme in RESOURCE_LIKE_SCHEMES:
        return _parse_resource(uri)
    raise ValueError(f"No parser available for scheme: {scheme}")


def normalize_scheme(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise ValueError("Scheme or URI is required")
    if "://" in raw:
        scheme = urlparse(raw).scheme
        if scheme:
            return scheme.lower()
    return raw.rstrip(":/").lower()
