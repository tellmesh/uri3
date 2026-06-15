from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from uri3.artifacts.validator import validate_artifact


def ensure_artifact_envelope(
    payload: dict[str, Any],
    *,
    kind: str,
    schema_relative: str,
    uri_self: str | None = None,
) -> dict[str, Any]:
    body = dict(payload)
    body.setdefault("$schema", schema_relative)
    body.setdefault("apiVersion", "uri3.io/v1")
    body.setdefault("kind", kind)
    if uri_self:
        uri = dict(body.get("uri") or {})
        uri.setdefault("self", uri_self)
        body["uri"] = uri
    return body


def write_yaml_artifact(
    path: Path,
    payload: dict[str, Any],
    *,
    repo_root: Path,
    schema_relative: str,
    validate: bool = True,
) -> Path:
    if validate:
        errors = validate_artifact(payload, repo_root, schema_relative)
        if errors:
            raise ValueError(f"{path}: schema validation failed: {'; '.join(errors)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return path


def write_json_artifact(
    path: Path,
    payload: dict[str, Any],
    *,
    repo_root: Path,
    schema_relative: str,
    validate: bool = True,
) -> Path:
    if validate:
        errors = validate_artifact(payload, repo_root, schema_relative)
        if errors:
            raise ValueError(f"{path}: schema validation failed: {'; '.join(errors)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
