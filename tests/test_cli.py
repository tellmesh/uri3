"""Tests for uri3 CLI UX helpers."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from uri3.cli import app
from uri3.config.cli_shortcuts import resolve_scan_target, scan_shortcuts


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_scan_shortcuts_load_defaults():
    shortcuts = scan_shortcuts()
    assert "http" in shortcuts
    assert shortcuts["http"].startswith("http://")


def test_resolve_scan_target_by_name():
    uri = resolve_scan_target("http")
    assert uri.startswith("http://")


def test_resolve_scan_target_full_uri():
    uri = resolve_scan_target("ssh://deploy@localhost:2222/opt/agents")
    assert uri.startswith("ssh://")


def test_cli_list_command(runner: CliRunner):
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "uri3 scan http" in result.stdout
    assert "http://" in result.stdout


def test_cli_list_json(runner: CliRunner):
    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "schemes" in payload
    assert "http" in payload["shortcuts"]["scan"]


def test_cli_no_args_shows_quick_reference(runner: CliRunner):
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "quick reference" in result.stdout


def test_cli_scan_without_args_shows_help(runner: CliRunner, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("uri3.cli.commands.discovery.scan_uri", lambda uri: [])
    result = runner.invoke(app, ["scan"])
    assert result.exit_code == 1
    assert "uri3 scan http" in result.stdout


def test_cli_scan_shortcut_name(runner: CliRunner, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "uri3.cli.commands.discovery.scan_uri",
        lambda uri: [type("Item", (), {"__dict__": {"uri": uri, "kind": "health", "status": "ok", "metadata": {}}})()],
    )
    result = runner.invoke(app, ["scan", "http"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]["uri"].startswith("http://")


def test_cli_scan_all(runner: CliRunner, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("uri3.cli.commands.discovery.scan_uri", lambda uri: [])
    result = runner.invoke(app, ["scan", "--all"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert set(payload) >= {"http", "ssh", "docker"}


def test_cli_call_docker_dry_run(runner: CliRunner):
    result = runner.invoke(app, ["call", "docker://stack/ssh-testenv?action=up&dry_run=1"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "up"
    assert payload["dry_run"] is True
