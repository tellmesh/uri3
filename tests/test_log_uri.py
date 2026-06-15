"""Tests for log:// URI support."""

from __future__ import annotations

import json
from pathlib import Path

from uri3.logs.reader import read_logs, summarize_logs
from uri3.resolvers.router import call, resolve
from uri3.scanner.scanner import scan


def _write_sample_log(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = [
        {"timestamp": "2026-06-14T10:00:00Z", "level": "INFO", "logger": "hypervisor", "message": "started"},
        {"timestamp": "2026-06-14T10:01:00Z", "level": "ERROR", "logger": "hypervisor.deployment", "message": "deployment failed"},
        {"timestamp": "2026-06-14T10:02:00Z", "level": "WARNING", "logger": "uri3", "message": "slow resolver"},
    ]
    path.write_text("\n".join(json.dumps(item) for item in entries) + "\n", encoding="utf-8")


def test_resolve_log_uri():
    result = resolve("log://hypervisor/runtime?level=ERROR&grep=deployment&limit=20")
    assert result.kind == "log"
    assert result.target["stream"] == "hypervisor"
    assert result.target["path"] == "runtime"
    assert result.target["level"] == "ERROR"
    assert result.target["grep"] == "deployment"
    assert result.target["limit"] == 20


def test_read_logs_with_filters(tmp_path: Path, monkeypatch):
    log_file = tmp_path / "output" / "logs" / "hypervisor.log"
    _write_sample_log(log_file)
    monkeypatch.setattr("uri3.logs.reader.find_repo_root", lambda start=None: tmp_path)

    errors = read_logs("log://hypervisor?level=ERROR", root=tmp_path)
    assert len(errors) == 1
    assert errors[0]["message"] == "deployment failed"

    grep_hits = read_logs("log://hypervisor?grep=resolver", root=tmp_path)
    assert len(grep_hits) == 1
    assert grep_hits[0]["logger"] == "uri3"


def test_read_logs_from_explicit_file(tmp_path: Path, monkeypatch):
    log_file = tmp_path / "custom.log"
    _write_sample_log(log_file)
    monkeypatch.setattr("uri3.logs.reader.find_repo_root", lambda start=None: tmp_path)

    entries = read_logs("log://file/custom.log?limit=2", root=tmp_path)
    assert len(entries) == 2


def test_call_log_uri_returns_entries(tmp_path: Path, monkeypatch):
    log_file = tmp_path / "output" / "logs" / "hypervisor.log"
    _write_sample_log(log_file)
    monkeypatch.setattr("uri3.logs.reader.find_repo_root", lambda start=None: tmp_path)

    summary = call("log://hypervisor?grep=deployment", {"summary": True})
    assert summary["matched"] == 1
    assert summary["levels"]["ERROR"] == 1


def test_scan_log_uri(tmp_path: Path, monkeypatch):
    log_file = tmp_path / "output" / "logs" / "hypervisor.log"
    _write_sample_log(log_file)
    monkeypatch.setattr("uri3.logs.reader.find_repo_root", lambda start=None: tmp_path)

    items = scan("log://hypervisor?level=WARNING")
    assert len(items) == 1
    assert items[0].kind == "log"
    assert items[0].status == "ok"
    assert items[0].metadata["matched"] >= 1


def test_summarize_logs(tmp_path: Path, monkeypatch):
    log_file = tmp_path / "output" / "logs" / "hypervisor.log"
    _write_sample_log(log_file)
    monkeypatch.setattr("uri3.logs.reader.find_repo_root", lambda start=None: tmp_path)

    summary = summarize_logs("log://hypervisor", root=tmp_path)
    assert summary["exists"] is True
    assert summary["matched"] == 3
    assert summary["levels"]["INFO"] == 1
