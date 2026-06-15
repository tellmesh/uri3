from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from uri3.config.repo_root import config_repo_root as _repo_root
from uri3.protocols.parser import parse_uri


def _env_var_name(uri: str) -> str:
    parsed = urlparse(uri)
    name = parsed.netloc or parsed.path.lstrip("/")
    if not name:
        raise ValueError("env:// URI requires variable name")
    return name


def resolve_env(uri: str) -> dict[str, str | bool | None]:
    name = _env_var_name(uri)
    return {"name": name, "exists": name in os.environ, "value": os.environ.get(name)}


def _upsert_env_file(path: Path, name: str, value: str) -> None:
    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    pattern = re.compile(rf"^\s*{re.escape(name)}\s*=")
    updated = False
    for index, line in enumerate(lines):
        if pattern.match(line):
            lines[index] = f"{name}={value}"
            updated = True
            break
    if not updated:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(f"{name}={value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _first(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    return values[0] if values else None


def call_env(uri: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    name = _env_var_name(uri)
    query = parse_qs(urlparse(uri).query)
    action = _first(query, "action")
    if action != "set":
        raise ValueError("env:// call requires action=set (use uri3 resolve for read-only lookup)")

    value = _first(query, "value")
    if value is None and payload:
        value = payload.get("value")
    if value is None:
        raise ValueError("action=set requires value=... in URI query or call payload")

    os.environ[name] = str(value)
    result: dict[str, Any] = {
        "name": name,
        "action": "set",
        "exists": True,
        "persisted": False,
    }

    persist = _first(query, "persist")
    if persist:
        root = _repo_root()
        if persist in {"1", "true", "yes", ".env"}:
            path = root / ".env"
        else:
            path = Path(persist)
            if not path.is_absolute():
                path = root / path
        _upsert_env_file(path, name, str(value))
        result["persisted"] = True
        result["path"] = str(path.resolve())

    return result


class EnvResolver:
    scheme = "env"

    def resolve(self, uri):
        return resolve_env(uri)

    def call(self, uri, payload=None):
        return call_env(uri, payload)
