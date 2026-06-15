"""Tests for uri3 doctor governance command."""

from __future__ import annotations

from pathlib import Path

from uri3.doctor.runner import run_doctor
from uri3.doctor.registry_index import write_registry_indexes


def test_doctor_passes_on_repo(repo_root: Path):
    payload = run_doctor(root=repo_root)
    assert payload["ok"] is True
    check_ids = {item["id"] for item in payload["checks"]}
    assert "config" in check_ids
    assert "contract_registry" in check_ids
    assert "touri.registry" in check_ids
    assert "uri2ops.registry" in check_ids
    assert "explain.smoke" in check_ids
    assert "envelope.exports" in check_ids


def test_doctor_build_registry_writes_indexes(tmp_path: Path, repo_root: Path):
    payload = run_doctor(
        root=repo_root,
        build_registry=True,
        registry=str(repo_root / "examples" / "20_touri_capabilities"),
    )
    assert payload["ok"] is True
    index = payload["registry_index"]
    assert index["ok"] is True
    for name in ("capability_index.json", "operation_index.json", "uri_index.json"):
        path = repo_root / ".registry" / name
        assert path.is_file(), name


def test_build_registry_indexes_content(repo_root: Path):
    registry = repo_root / "examples" / "20_touri_capabilities"
    payload = write_registry_indexes(repo_root, registry_path=registry)
    assert payload["ok"] is True
    assert payload["counts"]["capability_index.json"] > 0
    assert payload["counts"]["operation_index.json"] > 0
