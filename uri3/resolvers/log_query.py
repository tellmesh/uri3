from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs


def first(query: dict[str, list[str]], key: str, default: str | None = None) -> str | None:
    values = query.get(key)
    if not values:
        return default
    return values[0]


def query_int(query: dict[str, list[str]], key: str, default: int) -> int:
    raw = first(query, key)
    if raw is None:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


def query_bool(query: dict[str, list[str]], key: str, default: bool = False) -> bool:
    raw = (first(query, key) or "").lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def resolve_path(parsed) -> Path | None:
    stream = parsed.netloc or "hypervisor"
    if stream == "file":
        file_path = parsed.path or ""
        if not file_path or file_path == "/":
            raise ValueError("log://file/ requires a path, e.g. log://file/output/logs/hypervisor.log")
        return Path(file_path.lstrip("/"))
    if parsed.path and parsed.path not in {"", "/"}:
        return Path(parsed.path.lstrip("/"))
    return None


def resolve_level(query: dict[str, list[str]]) -> str | None:
    level = first(query, "level") or first(query, "min_level")
    return level.upper() if level else None


def parse_query(uri: str) -> tuple[str, Path | None, dict[str, list[str]]]:
    from urllib.parse import urlparse

    parsed = urlparse(uri)
    if parsed.scheme != "log":
        raise ValueError(f"Not a log URI: {uri}")
    stream = parsed.netloc or "hypervisor"
    return stream, resolve_path(parsed), parse_qs(parsed.query)
