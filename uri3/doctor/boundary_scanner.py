from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Any

import yaml

from uri3.config.repo_root import find_repo_root


def _default_repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "docs" / "PACKAGE_BOUNDARIES.yaml").is_file():
        return cwd
    return find_repo_root()


def load_boundary_rules(path: Path | None = None, *, root: Path | None = None) -> dict[str, Any]:
    repo_root = root or _default_repo_root()
    rules_path = path or repo_root / "docs" / "PACKAGE_BOUNDARIES.yaml"
    data = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    return data.get("packages") or {}


def _module_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
            for alias in node.names:
                imports.add(f"{node.module}.{alias.name}")
    return imports


def _matches_forbidden(import_name: str, forbidden: str) -> bool:
    return import_name == forbidden or import_name.startswith(f"{forbidden}.")


def _allowed(import_name: str, allowed_prefixes: list[str]) -> bool:
    return any(
        import_name == prefix or import_name.startswith(f"{prefix}.") for prefix in allowed_prefixes
    )


def _tellmesh_root(repo_root: Path) -> Path | None:
    candidates = []
    if raw := os.getenv("TELLMESH_ROOT"):
        candidates.append(Path(raw))
    candidates.append(repo_root.parent.parent / "tellmesh")
    candidates.append(Path("/home/tom/github/tellmesh"))
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def _resolve_package_root(repo_root: Path, package_name: str, root: str) -> Path:
    package_root = repo_root / root
    if package_root.is_dir():
        return package_root

    parts = Path(root).parts
    if len(parts) >= 3 and parts[0] == "packages":
        tellmesh_root = _tellmesh_root(repo_root)
        if tellmesh_root is not None:
            split_root = tellmesh_root / package_name / parts[-1]
            if split_root.is_dir():
                return split_root

    return package_root


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _validate_package_spec(
    package_name: str,
    spec: Any,
    *,
    repo_root: Path,
) -> tuple[Path | None, list[str]]:
    if not isinstance(spec, dict):
        spec_type = type(spec).__name__
        return None, [f"{package_name}: invalid boundary spec (expected mapping, got {spec_type})"]
    package_root = _resolve_package_root(repo_root, package_name, spec["root"])
    if spec.get("optional") and not package_root.exists():
        return None, []
    if not package_root.is_dir():
        return None, [f"{package_name}: missing package root {spec['root']}"]
    return package_root, []


def _scan_python_file(
    path: Path,
    *,
    package_root: Path,
    repo_root: Path,
    forbidden: list[str],
    allowed_prefixes: list[str],
    allowed_path_prefixes: list[str],
) -> list[str]:
    rel_to_package = path.relative_to(package_root).as_posix()
    skip_forbidden = any(rel_to_package.startswith(prefix) for prefix in allowed_path_prefixes)
    if skip_forbidden:
        return []
    rel = _display_path(path, repo_root)
    violations: list[str] = []
    for import_name in sorted(_module_imports(path)):
        if _allowed(import_name, allowed_prefixes):
            continue
        for rule in forbidden:
            if _matches_forbidden(import_name, rule):
                violations.append(f"{rel}: forbidden import '{import_name}' (rule: {rule})")
    return violations


def scan_package_boundaries(
    rules: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> list[str]:
    repo_root = root or _default_repo_root()
    rules = rules or load_boundary_rules(root=repo_root)
    violations: list[str] = []

    for package_name, spec in rules.items():
        package_root, spec_errors = _validate_package_spec(package_name, spec, repo_root=repo_root)
        violations.extend(spec_errors)
        if package_root is None:
            continue
        forbidden = list(spec.get("forbidden") or [])
        allowed_prefixes = list(spec.get("allowed_import_prefixes") or [])
        allowed_path_prefixes = list(spec.get("allowed_path_prefixes") or [])
        for path in sorted(package_root.rglob("*.py")):
            if path.name == "__init__.py" and path.stat().st_size < 5:
                continue
            violations.extend(
                _scan_python_file(
                    path,
                    package_root=package_root,
                    repo_root=repo_root,
                    forbidden=forbidden,
                    allowed_prefixes=allowed_prefixes,
                    allowed_path_prefixes=allowed_path_prefixes,
                )
            )
    return violations
