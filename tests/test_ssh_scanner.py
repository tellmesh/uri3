"""Tests for SSH URI resolver and scanner."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from uri3.resolvers.ssh_resolver import parse_ssh_uri, resolve_ssh
from uri3.scanner.ssh_scanner import scan_ssh


def test_parse_ssh_uri():
    ref = parse_ssh_uri("ssh://deploy@localhost:2222/opt/agents/weather-map-agent")
    assert ref["user"] == "deploy"
    assert ref["host"] == "localhost"
    assert ref["port"] == 2222
    assert ref["path"] == "/opt/agents/weather-map-agent"
    assert ref["target"] == "deploy@localhost"


def test_parse_ssh_uri_requires_host():
    with pytest.raises(ValueError, match="requires user@host"):
        parse_ssh_uri("ssh://")


def test_scan_ssh_invalid_uri():
    items = scan_ssh("ssh://")
    assert len(items) == 1
    assert items[0].status == "invalid"
    assert items[0].kind == "ssh_connectivity"


def test_resolve_ssh_alias():
    data = resolve_ssh("ssh://deploy@localhost:2222/opt/agents")
    assert data["transport"] == "ssh"


def test_scan_ssh_unreachable(monkeypatch: pytest.MonkeyPatch):
    mock_result = MagicMock(returncode=255, stdout="", stderr="connection refused")

    def fake_run_ssh(ref, remote_command, *, check=False):
        return mock_result

    monkeypatch.setattr("uri3.scanner.ssh_scanner.run_ssh", fake_run_ssh)
    items = scan_ssh("ssh://deploy@localhost:2222/opt/agents")
    assert items[0].kind == "ssh_connectivity"
    assert items[0].status == "unreachable"
    assert len(items) == 1


def test_scan_ssh_success(monkeypatch: pytest.MonkeyPatch):
    def fake_run_ssh(ref, remote_command, *, check=False):
        if remote_command == "echo hypervisor-ssh-ok":
            return MagicMock(returncode=0, stdout="hypervisor-ssh-ok\n", stderr="")
        if remote_command.startswith("test -d"):
            return MagicMock(returncode=0, stdout="dir\n", stderr="")
        if remote_command.startswith("ls -la"):
            return MagicMock(returncode=0, stdout="total 0\n", stderr="")
        return MagicMock(returncode=1, stdout="", stderr="unexpected")

    monkeypatch.setattr("uri3.scanner.ssh_scanner.run_ssh", fake_run_ssh)
    items = scan_ssh("ssh://deploy@localhost:2222/opt/agents/weather-map-agent")
    assert any(item.kind == "remote_path" and item.status == "present" for item in items)
