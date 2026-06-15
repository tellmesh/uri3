"""Doctor check modules grouped by concern."""

from __future__ import annotations

from uri3.doctor.checks.boundaries import (
    check_browser_delegation,
    check_duplicate_top_level_modules,
    check_legacy_import_roots,
    check_package_boundaries,
    check_runtime_transports,
)
from uri3.doctor.checks.config import check_config
from uri3.doctor.checks.envelope import check_recent_workflow_logs, check_result_envelope
from uri3.doctor.checks.explain import check_explain_smoke
from uri3.doctor.checks.registry import (
    check_contract_registry,
    check_touri_registry,
    check_uri2ops_registry,
)
from uri3.doctor.checks.verify import check_capability_plan, check_replay_failures

__all__ = [
    "check_browser_delegation",
    "check_capability_plan",
    "check_config",
    "check_contract_registry",
    "check_duplicate_top_level_modules",
    "check_explain_smoke",
    "check_legacy_import_roots",
    "check_package_boundaries",
    "check_recent_workflow_logs",
    "check_replay_failures",
    "check_result_envelope",
    "check_runtime_transports",
    "check_touri_registry",
    "check_uri2ops_registry",
]
