from __future__ import annotations

from pathlib import Path
from typing import Any

from uri3.doctor import checks
from uri3.doctor.envelope_migrate import migrate_workflow_logs
from uri3.doctor.registry_index import write_registry_indexes
from uri3.resolvers.explain import default_touri_registry


def _collect_warnings(results: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for item in results:
        if not item.get("ok"):
            note = item.get("note")
            if note:
                warnings.append(f"{item['id']}: {note}")
        for error in item.get("errors") or []:
            if not item.get("ok"):
                warnings.append(f"{item['id']}: {error}")
        for mismatch in item.get("mismatches") or []:
            warnings.append(f"{item['id']}: {mismatch}")
        for failure in item.get("failures") or []:
            warnings.append(f"{item['id']}: {failure}")
    return warnings


def _standard_checks(
    repo_root: Path, registry_path: Path, *, strict_envelope: bool
) -> list[dict[str, Any]]:
    return [
        checks.check_config(repo_root),
        checks.check_contract_registry(repo_root),
        checks.check_touri_registry(repo_root, registry_path),
        checks.check_uri2ops_registry(repo_root),
        checks.check_explain_smoke(repo_root, registry_path),
        checks.check_result_envelope(),
        checks.check_recent_workflow_logs(repo_root, strict=strict_envelope),
    ]


def _hardening_checks(repo_root: Path) -> list[dict[str, Any]]:
    return [
        checks.check_package_boundaries(repo_root),
        checks.check_legacy_import_roots(repo_root),
        checks.check_duplicate_top_level_modules(repo_root),
        checks.check_browser_delegation(),
        checks.check_runtime_transports(repo_root),
    ]


def _optional_checks(
    repo_root: Path,
    *,
    capability_plan: bool,
    replay_failures: bool,
) -> list[dict[str, Any]]:
    optional: list[dict[str, Any]] = []
    if capability_plan:
        optional.append(checks.check_capability_plan(repo_root))
    if replay_failures:
        optional.append(checks.check_replay_failures(repo_root))
    return optional


def run_doctor(
    *,
    root: Path | None = None,
    registry: str | Path | None = None,
    capability_plan: bool = False,
    replay_failures: bool = False,
    build_registry: bool = False,
    strict_envelope: bool = False,
    migrate_envelope: bool = False,
) -> dict[str, Any]:
    from uri3.config.repo_root import find_repo_root

    repo_root = root or find_repo_root()
    registry_path = Path(registry) if registry else default_touri_registry(repo_root)
    migration: dict[str, Any] | None = None
    if migrate_envelope:
        migration = migrate_workflow_logs(repo_root)

    results = [
        *_standard_checks(repo_root, registry_path, strict_envelope=strict_envelope),
        *_hardening_checks(repo_root),
        *_optional_checks(
            repo_root, capability_plan=capability_plan, replay_failures=replay_failures
        ),
    ]

    payload: dict[str, Any] = {
        "ok": all(item["ok"] for item in results),
        "checks": results,
        "warnings": _collect_warnings(results),
        "registry": str(registry_path),
    }
    if build_registry:
        index_result = write_registry_indexes(repo_root, registry_path=registry_path)
        payload["registry_index"] = index_result
        if not index_result.get("ok"):
            payload["ok"] = False
    if migration is not None:
        payload["envelope_migration"] = migration
        if migration.get("updated_events"):
            results.append(
                {
                    "id": "envelope.migration",
                    "ok": True,
                    "updated_events": migration.get("updated_events"),
                    "files": migration.get("files"),
                }
            )
            payload["checks"] = results
    return payload
