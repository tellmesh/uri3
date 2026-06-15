from __future__ import annotations

from typing import Any

from uri3.protocols.schemes.instance_parser import normalize_scheme, parse_instance
from uri3.protocols.schemes.spec_registry import (
    SCHEME_REGISTRY,
    get_scheme_schema,
    is_concrete_uri,
    query_names,
)


def _analyze_query(uri: str, spec) -> dict[str, Any]:
    from urllib.parse import urlparse

    parsed = urlparse(uri)
    query_keys = {key.split("=", 1)[0] for key in parsed.query.split("&") if key} if parsed.query else set()
    if spec and spec.query:
        known = query_names(spec)
        canonical = {option.name for option in spec.query}
        used = sorted(key for key in query_keys if key in known)
        unknown = sorted(key for key in query_keys if key not in known)
        available = sorted(name for name in canonical if name not in used)
        return {
            "used": used,
            "unknown": unknown,
            "available": available,
            "options": [option.to_dict() for option in spec.query],
        }
    return {
        "used": sorted(query_keys),
        "unknown": [],
        "available": [],
        "options": [],
    }


def analyze_uri(uri: str) -> dict[str, Any]:
    from urllib.parse import urlparse

    scheme = normalize_scheme(uri)
    schema = get_scheme_schema(scheme)
    spec = SCHEME_REGISTRY.get(scheme)
    parsed = urlparse(uri)
    try:
        parsed_value = parse_instance(scheme, uri)
        valid = True
        errors: list[str] = []
    except ValueError as exc:
        parsed_value = None
        valid = False
        errors = [str(exc)]
    return {
        "uri": uri,
        "scheme": scheme,
        "schema": schema,
        "components": {
            "netloc": parsed.netloc,
            "path": parsed.path,
            "query": parsed.query,
        },
        "parsed": parsed_value,
        "valid": valid,
        "errors": errors,
        "query": _analyze_query(uri, spec),
    }


def describe_uri(value: str) -> dict[str, Any]:
    if is_concrete_uri(value):
        return analyze_uri(value)
    return get_scheme_schema(value)
