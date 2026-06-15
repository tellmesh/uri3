from __future__ import annotations

from pathlib import Path
from typing import Any

from uri3.doctor.checks._helpers import check_result


def check_contract_registry(root: Path) -> dict[str, Any]:
    try:
        from hypervisor.contract_registry.loader import load_contract_registry
        from hypervisor.contract_registry.schema_validator import validate_contract_files
        from hypervisor.contract_registry.validate import validate_registry
    except ImportError as exc:
        return check_result(
            "contract_registry", ok=False, errors=[f"hypervisor unavailable: {exc}"]
        )

    schema_results = validate_contract_files(root)
    schema_errors = [
        f"{item.path}: {err}" for item in schema_results if not item.ok for err in item.errors
    ]
    registry = load_contract_registry(root)
    logical_errors = validate_registry(registry)
    errors = [*schema_errors, *logical_errors]
    return check_result(
        "contract_registry",
        ok=not errors,
        counts={
            "resources": len(registry.resources),
            "views": len(registry.views),
            "capabilities": len(registry.capabilities),
        },
        errors=errors,
    )


def check_touri_registry(root: Path, registry_path: Path) -> dict[str, Any]:
    del root
    from touri.loader import iter_manifest_paths, load_registry
    from touri.validator import validate_manifest

    if not registry_path.exists():
        return check_result(
            "touri.registry",
            ok=False,
            registry=str(registry_path),
            errors=[f"registry path not found: {registry_path}"],
        )

    manifests = load_registry(registry_path)
    invalid: list[dict[str, str]] = []
    for path in iter_manifest_paths(registry_path):
        validation = validate_manifest(path)
        if not validation["ok"]:
            invalid.append({"path": str(path), "errors": "; ".join(validation.get("errors") or [])})

    return check_result(
        "touri.registry",
        ok=not invalid,
        registry=str(registry_path),
        manifests=len(manifests),
        capability_ids=[manifest.capability.id for manifest in manifests],
        invalid=invalid,
    )


def check_uri2ops_registry(root: Path) -> dict[str, Any]:
    try:
        from uri2ops.operation_registry.validator import validate_operation_registry
        from uri2ops.remote_registry.loader import list_remote_sources, resolve_operation_registry
    except ImportError as exc:
        return check_result("uri2ops.registry", ok=False, errors=[f"uri2ops unavailable: {exc}"])

    registry = resolve_operation_registry(root=root)
    errors = validate_operation_registry(registry)
    schemes = sorted({scheme for scheme, _operation in registry.operations})
    return check_result(
        "uri2ops.registry",
        ok=not errors,
        operations=len(registry.operations),
        schemes=schemes,
        remotes=list_remote_sources(root=root),
        errors=errors,
    )
