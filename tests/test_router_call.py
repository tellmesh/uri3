"""Tests for uri3 router call routing."""

from __future__ import annotations

from uri3.resolvers.router import call, resolve


def test_resolve_docker_stack():
    result = resolve("docker://stack/ssh-testenv?action=up")
    assert result.scheme == "docker"
    assert result.target["kind"] == "stack"
    assert result.target["name"] == "ssh-testenv"


def test_call_docker_stack_dry_run():
    result = call("docker://stack/ssh-testenv?action=up&dry_run=1")
    assert result["action"] == "up"
    assert result["dry_run"] is True
    assert "docker compose" in result["command_string"]
