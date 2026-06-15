from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from uri3.resolvers.explain import default_touri_registry, explain_uri


def build_capability_index(root: Path, registry_path: Path) -> dict[str, Any]:
    from touri.loader import load_registry

    entries = []
    for manifest in load_registry(registry_path):
        cap = manifest.capability
        entries.append(
            {
                "id": cap.id,
                "scheme": cap.scheme,
                "uri_template": cap.uri_template,
                "operation": cap.operation,
                "kind": cap.kind,
                "backend_type": manifest.backend.type,
                "backend_target": manifest.backend.target,
                "has_data_quality": bool(manifest.data_quality),
                "fallbacks": len(manifest.fallbacks or []),
            }
        )
    return {"registry": str(registry_path), "count": len(entries), "capabilities": entries}


def build_operation_index(root: Path) -> dict[str, Any]:
    from uri2ops.remote_registry.loader import resolve_operation_registry

    registry = resolve_operation_registry(root=root)
    by_scheme: dict[str, list[str]] = {}
    for scheme, operation in sorted(registry.operations):
        by_scheme.setdefault(scheme, []).append(operation)
    return {
        "count": len(registry.operations),
        "schemes": {scheme: sorted(ops) for scheme, ops in sorted(by_scheme.items())},
    }


def build_uri_index(root: Path, registry_path: Path) -> dict[str, Any]:
    from touri.loader import load_registry
    from touri.register import sample_uri_from_template

    entries = []
    for manifest in load_registry(registry_path):
        sample_uri = sample_uri_from_template(manifest.capability.uri_template)
        explain = explain_uri(sample_uri, registry_root=registry_path, root=root)
        entries.append(
            {
                "uri": sample_uri,
                "capability": manifest.capability.id,
                "matched_registry": explain.get("matched_registry"),
                "backend_type": (explain.get("backend") or {}).get("type"),
            }
        )
    return {"count": len(entries), "entries": entries}


def write_registry_indexes(root: Path, *, registry_path: Path | None = None) -> dict[str, Any]:
    registry = registry_path or default_touri_registry(root)
    out_dir = root / ".registry"
    out_dir.mkdir(parents=True, exist_ok=True)

    indexes = {
        "capability_index.json": build_capability_index(root, registry),
        "operation_index.json": build_operation_index(root),
        "uri_index.json": build_uri_index(root, registry),
    }
    written: list[str] = []
    for name, payload in indexes.items():
        path = out_dir / name
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(str(path))
    return {
        "ok": True,
        "directory": str(out_dir),
        "files": written,
        "counts": {name: payload.get("count", 0) for name, payload in indexes.items()},
    }
