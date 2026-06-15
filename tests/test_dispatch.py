"""Tests for URI scheme dispatch and instance parsing."""

from __future__ import annotations

from uri3.protocols.schemes.instance_parser import parse_instance
from uri3.resolvers.dispatch import resolve_target


def test_parse_instance_env():
    result = parse_instance("env", "env://OPENROUTER_API_KEY")
    assert result["name"] == "OPENROUTER_API_KEY"


def test_parse_instance_docker_stack():
    result = parse_instance("docker", "docker://stack/ssh-testenv?action=up")
    assert result["kind"] == "stack"
    assert result["name"] == "ssh-testenv"


def test_resolve_target_pypi():
    result = resolve_target("pypi", "pypi://httpx")
    assert result["package"] == "httpx"
