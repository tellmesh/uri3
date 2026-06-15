from __future__ import annotations

from urllib.parse import urlparse, urlunparse

import httpx

from uri3.scanner.base import ScanItem

KNOWN_ROOT_PATHS = (
    ("/health", "health"),
    ("/capabilities", "capabilities"),
    ("/.well-known/agent-card.json", "agent_card"),
    ("/.well-known/agent.json", "agent_card"),
)


def _origin(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, "", "", "", "")).rstrip("/")


def _kind_for_path(path: str) -> str:
    for known_path, kind in KNOWN_ROOT_PATHS:
        if path.rstrip("/") == known_path.rstrip("/"):
            return kind
    if "agent" in path:
        return "agent_card"
    return path.strip("/") or "root"


def _status_for(kind: str, status_code: int) -> str:
    if kind == "health":
        return "ok" if status_code == 200 else "error"
    if status_code >= 500:
        return "error"
    if status_code == 404:
        return "missing"
    return "reachable"


def _probe(url: str) -> ScanItem:
    parsed = urlparse(url)
    kind = _kind_for_path(parsed.path or "/")
    try:
        response = httpx.get(url, timeout=3)
        status = _status_for(kind, response.status_code)
        return ScanItem(
            url,
            kind,
            status,
            {"status_code": response.status_code},
        )
    except Exception as exc:
        return ScanItem(url, kind, "unreachable", {"error": str(exc)})


def health_scan_ok(items: list[ScanItem]) -> bool:
    health_items = [item for item in items if item.kind == "health"]
    if health_items:
        return any(item.status == "ok" for item in health_items)
    return any(item.metadata.get("status_code") == 200 for item in items)


def scan_http(base_url: str) -> list[ScanItem]:
    parsed = urlparse(base_url)
    origin = _origin(base_url)
    path = parsed.path or "/"

    if path not in {"", "/"}:
        found = [_probe(base_url.rstrip("/") if path != "/" else origin + "/")]
        if path.rstrip("/") == "/health":
            for extra_path, _kind in KNOWN_ROOT_PATHS[1:]:
                found.append(_probe(origin + extra_path))
        return found

    return [_probe(origin + known_path) for known_path, _kind in KNOWN_ROOT_PATHS]
