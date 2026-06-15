from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

URI_SCHEMES = {
    "env",
    "llm",
    "log",
    "python",
    "pypi",
    "http",
    "https",
    "a2a",
    "mcp",
    "resource",
    "artifact",
    "domain",
    "agent",
    "local",
    "input",
    "command",
    "event",
    "ssh",
    "docker",
    "git",
    "secret",
    "browser",
    "dom",
    "screen",
    "assertion",
    "hypervisor",
}


def is_uri(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if "://" not in value:
        return False
    scheme = urlparse(value).scheme
    return bool(scheme) and scheme in URI_SCHEMES


def unwrap_uri_yaml_document(data: dict[str, Any]) -> dict[str, Any]:
    """Return the semantic config payload from a legacy or artifact-envelope file."""
    if (
        data.get("apiVersion") == "uri3.io/v1"
        and data.get("kind")
        and isinstance(data.get("spec"), dict)
    ):
        return dict(data["spec"])
    return data


def load_uri_yaml(path: str | Path, *, unwrap_spec: bool = True) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"URI YAML must be a mapping: {path}")
    return unwrap_uri_yaml_document(data) if unwrap_spec else data


def _resolve_env_uri(value: str, *, resolve_secrets: bool) -> Any:
    if not resolve_secrets:
        return value
    from uri3.resolvers.env_resolver import resolve_env

    return resolve_env(value).get("value")


def _resolve_registered_uri(value: str) -> Any:
    from uri3.resolvers.resolve_core import resolve

    result = resolve(value)
    target = result.target if hasattr(result, "target") else result
    if isinstance(target, dict) and "value" in target:
        return target.get("value")
    return target


def _resolve_scalar_uri(value: str, *, resolve_secrets: bool) -> Any:
    parsed = urlparse(value)
    if not resolve_secrets and parsed.scheme in {"env", "secret"}:
        return value
    if resolve_secrets and parsed.scheme == "env":
        return _resolve_env_uri(value, resolve_secrets=resolve_secrets)
    try:
        return _resolve_registered_uri(value)
    except ValueError:
        return value


def resolve_uri_values(
    value: Any,
    *,
    resolve_secrets: bool = False,
    _key: str | None = None,
) -> Any:
    if isinstance(value, dict):
        return {
            key: resolve_uri_values(item, resolve_secrets=resolve_secrets, _key=key)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [resolve_uri_values(item, resolve_secrets=resolve_secrets) for item in value]
    if value is None:
        return None
    if not is_uri(value):
        return value
    return _resolve_scalar_uri(str(value), resolve_secrets=resolve_secrets)
