"""Tests for SSH auth resolution."""

from __future__ import annotations

import pytest

from uri3.config.ssh_auth import resolve_ssh_password, ssh_auth_hint
from uri3.resolvers.ssh_resolver import build_ssh_command, parse_ssh_uri


def test_resolve_ssh_password_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HYPERVISOR_SSH_PASSWORD", "deploy")
    ref = parse_ssh_uri("ssh://deploy@localhost:2222/opt/agents")
    assert resolve_ssh_password(ref) == "deploy"


def test_resolve_ssh_password_from_profile(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("HYPERVISOR_SSH_PASSWORD", raising=False)
    monkeypatch.delenv("SSHPASS", raising=False)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "ssh.uri.yaml").write_text(
        """
version: 1
profiles:
  docker_testenv:
    match:
      user: deploy
      host: localhost
      port: 2222
    password: env://HYPERVISOR_SSH_PASSWORD
""",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("HYPERVISOR_SSH_PASSWORD=deploy\n", encoding="utf-8")
    ref = parse_ssh_uri("ssh://deploy@localhost:2222/opt/agents")
    assert resolve_ssh_password(ref, root=tmp_path) == "deploy"


def test_build_ssh_command_uses_sshpass_when_password_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HYPERVISOR_SSH_PASSWORD", "deploy")
    ref = parse_ssh_uri("ssh://deploy@localhost:2222/opt/agents")
    cmd = build_ssh_command(ref, "echo ok")
    assert cmd[0] == "sshpass"
    assert "deploy" in cmd


def test_ssh_auth_hint_on_permission_denied(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("HYPERVISOR_SSH_PASSWORD", raising=False)
    monkeypatch.delenv("SSHPASS", raising=False)
    monkeypatch.delenv("SSH_DEPLOY_PASSWORD", raising=False)
    ref = parse_ssh_uri("ssh://deploy@localhost:2222/opt/agents")
    hint = ssh_auth_hint(ref, stderr="deploy@localhost: Permission denied (publickey,password).")
    assert hint is not None
    assert "HYPERVISOR_SSH_PASSWORD" in hint
