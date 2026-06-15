from __future__ import annotations

from pathlib import Path
from typing import Any

from uri3.config.repo_root import config_repo_root as _repo_root
from uri3.config.uri_yaml import load_uri_yaml


def cli_config_path(root: Path | None = None) -> Path:
    return _repo_root(root) / "config" / "uri3.uri.yaml"


def load_cli_config(root: Path | None = None) -> dict[str, Any]:
    path = cli_config_path(root)
    if not path.exists():
        return {"version": 1, "shortcuts": {"scan": {}}, "examples": []}
    return load_uri_yaml(path)


def scan_shortcuts(root: Path | None = None) -> dict[str, str]:
    data = load_cli_config(root)
    shortcuts = data.get("shortcuts") or {}
    scan = shortcuts.get("scan") or {}
    return {str(name): str(uri) for name, uri in scan.items()}


def resolve_scan_target(name_or_uri: str, *, root: Path | None = None) -> str:
    if "://" in name_or_uri:
        return name_or_uri
    shortcuts = scan_shortcuts(root)
    if name_or_uri not in shortcuts:
        available = ", ".join(sorted(shortcuts)) or "(none configured)"
        raise ValueError(f"Unknown scan shortcut {name_or_uri!r}. Available: {available}")
    return shortcuts[name_or_uri]


def cli_examples(root: Path | None = None) -> list[str]:
    data = load_cli_config(root)
    examples = data.get("examples") or []
    return [str(item) for item in examples]
