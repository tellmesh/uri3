"""Tests for log reader metadata responses."""

from __future__ import annotations

from pathlib import Path

import pytest

from uri3.logs.reader import read_logs_result


def test_read_logs_result_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("uri3.logs.reader.find_repo_root", lambda start=None: tmp_path)
    result = read_logs_result("log://hypervisor?level=ERROR&limit=50", root=tmp_path)
    assert isinstance(result, dict)
    assert result["exists"] is False
    assert result["entries"] == []
    assert "hint" in result
    assert str(result["path"]).endswith("output/logs/hypervisor.log")
