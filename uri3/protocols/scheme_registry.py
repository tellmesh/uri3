"""Backward-compatible re-export of URI scheme registry."""

from uri3.protocols.schemes.base import QueryOption, SchemeSpec
from uri3.protocols.schemes.registry import (
    SCHEME_REGISTRY,
    analyze_uri,
    describe_uri,
    get_scheme_schema,
    is_concrete_uri,
    list_schemes,
    normalize_scheme,
)

__all__ = [
    "QueryOption",
    "SchemeSpec",
    "SCHEME_REGISTRY",
    "analyze_uri",
    "describe_uri",
    "get_scheme_schema",
    "is_concrete_uri",
    "list_schemes",
    "normalize_scheme",
]
