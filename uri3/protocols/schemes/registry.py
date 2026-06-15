"""Backward-compatible exports for URI scheme registry and analysis."""

from uri3.protocols.schemes.analyze import analyze_uri, describe_uri
from uri3.protocols.schemes.instance_parser import normalize_scheme, parse_instance
from uri3.protocols.schemes.spec_registry import (
    SCHEME_REGISTRY,
    get_scheme_schema,
    is_concrete_uri,
    list_schemes,
    query_names,
)

_parse_instance = parse_instance
_query_names = query_names

__all__ = [
    "SCHEME_REGISTRY",
    "analyze_uri",
    "describe_uri",
    "get_scheme_schema",
    "is_concrete_uri",
    "list_schemes",
    "normalize_scheme",
    "parse_instance",
    "_parse_instance",
    "_query_names",
]
