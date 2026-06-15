from __future__ import annotations

from urllib.parse import urlparse

from uri3.resolvers.registry import build_resolver_registry
from uri3.resolvers.resolve_core import UriResolution, call, resolve

__all__ = ["Uri3Router", "UriResolution", "call", "resolve"]


class Uri3Router:
    def __init__(self):
        self.resolvers = build_resolver_registry()

    def resolve(self, uri):
        try:
            return resolve(uri)
        except ValueError as exc:
            scheme = urlparse(uri).scheme
            return {
                "uri": uri,
                "scheme": scheme,
                "status": "unresolved",
                "reason": str(exc),
            }

    def call(self, uri, payload=None):
        return call(uri, payload)
