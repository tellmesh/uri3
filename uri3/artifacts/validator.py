from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def _schema_repo_root(repo_root: Path) -> Path:
    if (repo_root / "schemas").is_dir():
        return repo_root
    from uri3.paths import find_repo_root

    return find_repo_root()


def schema_path(repo_root: Path, relative: str) -> Path:
    return _schema_repo_root(repo_root) / relative


def load_schema(repo_root: Path, relative: str) -> dict[str, Any]:
    return json.loads(schema_path(repo_root, relative).read_text(encoding="utf-8"))


def validate_artifact(data: dict[str, Any], repo_root: Path, schema_relative: str) -> list[str]:
    schema = load_schema(repo_root, schema_relative)
    validator = Draft202012Validator(schema)
    return [
        f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}"
        for error in validator.iter_errors(data)
    ]


def validate_artifact_file(path: Path, repo_root: Path, schema_relative: str) -> list[str]:
    import yaml

    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        payload = json.loads(text)
    else:
        payload = yaml.safe_load(text)
    if not isinstance(payload, dict):
        return [f"{path}: expected mapping root"]
    return validate_artifact(payload, repo_root, schema_relative)
