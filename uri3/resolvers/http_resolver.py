from __future__ import annotations

import httpx

from uri3.resolvers.protocol_resolver import resolve_http_like


class HttpResolver:
    scheme = "http"

    def resolve(self, uri):
        return resolve_http_like(uri)

    def fetch(self, uri):
        response = httpx.get(uri, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            return response.json()
        return response.text
