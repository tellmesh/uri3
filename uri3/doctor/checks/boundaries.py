from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any

from uri3.doctor.boundary_scanner import scan_package_boundaries
from uri3.doctor.checks._helpers import check_result
from uri3.graph.adapters.registry import adapter_for_uri
from uri3.graph.adapters.uri2ops_adapter import Uri2OpsAdapter, _use_legacy_browser_adapter

_PACKAGE_MODULES = (
    "uri3",
    "uri2ops",
    "hypervisor",
    "nl2uri",
    "touri",
    "uri2run",
    "uri2verify",
    "uri2flow",
    "uri2pact",
    "urigen",
)

_LEGACY_TOP_LEVEL = (
    "generator",
    "hypervisor",
    "meta_agent",
    "nl2a",
    "uri2ops",
    "uri3",
    "runtime_client",
)


def check_package_boundaries(root: Path) -> dict[str, Any]:
    violations = scan_package_boundaries(root=root)
    return check_result(
        "boundaries.imports",
        ok=not violations,
        violations=violations[:20],
        violation_count=len(violations),
    )


def check_legacy_import_roots(root: Path) -> dict[str, Any]:
    del root
    mismatches: list[dict[str, str]] = []
    for name in _PACKAGE_MODULES:
        try:
            module = importlib.import_module(name)
        except ImportError as exc:
            mismatches.append({"module": name, "path": "", "error": str(exc)})
            continue
        module_file = getattr(module, "__file__", None)
        if not module_file:
            mismatches.append({"module": name, "path": "", "error": "missing __file__"})
            continue
        path = Path(module_file).resolve().as_posix()
        if "/packages/" not in path:
            mismatches.append({"module": name, "path": path, "error": "not under packages/"})
    return check_result(
        "imports.package_roots",
        ok=not mismatches,
        checked=list(_PACKAGE_MODULES),
        mismatches=mismatches,
    )


def check_duplicate_top_level_modules(root: Path) -> dict[str, Any]:
    duplicates: list[str] = []
    for name in _LEGACY_TOP_LEVEL:
        legacy = root / name
        if legacy.is_dir() and any(legacy.rglob("*.py")):
            duplicates.append(str(legacy.relative_to(root)))
    return check_result(
        "imports.legacy_top_level",
        ok=not duplicates,
        legacy_paths=duplicates,
        note="legacy top-level Python trees can shadow packages/* installs" if duplicates else "",
    )


def check_browser_delegation() -> dict[str, Any]:
    legacy_enabled = _use_legacy_browser_adapter()
    adapter = adapter_for_uri("browser://chrome/page/open")
    adapter_name = type(adapter).__name__ if adapter is not None else "none"
    uses_uri2ops = isinstance(adapter, Uri2OpsAdapter)
    ok = uses_uri2ops and not legacy_enabled
    return check_result(
        "runtime.browser_delegation",
        ok=ok,
        legacy_env=os.getenv("URI3_USE_LEGACY_BROWSER", ""),
        adapter=adapter_name,
        expected="Uri2OpsAdapter",
    )


def check_runtime_transports(root: Path) -> dict[str, Any]:
    from uri2run import run_backend

    required = frozenset(
        {
            "ok",
            "execution_status",
            "service_result_status",
            "result_type",
            "errors",
            "warnings",
            "meta",
        }
    )
    failures: list[dict[str, str]] = []
    cases = [
        (
            "python",
            {"type": "python", "target": "python://touri_examples.weather:handler"},
            {"place": "Gdansk", "days": 14},
        ),
        ("shell", {"type": "shell", "command": "echo uri2run-smoke"}, {}),
        ("mock", {"type": "mock"}, {"x": 1}),
        (
            "docker",
            {"type": "docker", "target": "docker://stack/ssh-testenv?action=status&dry_run=1"},
            {},
        ),
        ("ssh", {"type": "ssh", "target": "ssh://deploy@localhost:2222/opt/agents"}, {}),
    ]
    for transport, backend, payload in cases:
        try:
            result = run_backend(backend, payload, {"root": str(root)})
            body = result.to_dict()
            body.setdefault("errors", [])
            body.setdefault("warnings", [])
            body.setdefault("meta", {})
            missing = required - set(body)
            if missing:
                failures.append(
                    {"transport": transport, "error": f"missing fields: {sorted(missing)}"}
                )
                continue
            if body["meta"].get("runtime") != "uri2run":
                failures.append({"transport": transport, "error": "missing meta.runtime=uri2run"})
            if body["meta"].get("transport") != transport:
                failures.append(
                    {
                        "transport": transport,
                        "error": f"meta.transport={body['meta'].get('transport')}",
                    }
                )
        except Exception as exc:
            failures.append({"transport": transport, "error": str(exc)})
    return check_result(
        "runtime.uri2run_transports",
        ok=not failures,
        checked=[name for name, _, _ in cases],
        failures=failures,
    )
