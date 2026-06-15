"""Tests for docker URI resolver and controller."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from uri3.docker.compose_generator import build_generate_plan
from uri3.docker.controller import control_docker
from uri3.resolvers.docker_resolver import parse_docker_uri, resolve_docker


def test_parse_docker_stack_uri():
    ref = parse_docker_uri("docker://stack/ssh-testenv?action=up")
    assert ref.kind == "stack"
    assert ref.name == "ssh-testenv"
    assert ref.action == "up"
    assert ref.compose_file.endswith("examples/03_ssh_remote_agent/docker-compose.yml")
    assert ref.container_name == "hypervisor-ssh-agent-host"


def test_resolve_docker_generate_plan():
    payload = resolve_docker("docker://generate/weather-map-agent?action=generate")
    assert payload["kind"] == "generate"
    assert "generate_plan" in payload
    assert payload["generate_plan"]["container_name"] == "weather-map-agent"


def test_control_docker_up_dry_run():
    result = control_docker("docker://stack/ssh-testenv?action=up&dry_run=1")
    assert result["dry_run"] is True
    assert result["action"] == "up"
    assert "docker compose" in result["command_string"]


def test_control_docker_generate_writes_file(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "docker.uri.yaml").write_text(
        """
version: 1
agents:
  weather-map-agent:
    dockerfile: agents/generated/weather_map_agent/Dockerfile
    output_compose: output/deployments/weather-map-agent/docker-compose.yaml
    port: 8101
    container_name: weather-map-agent
""",
        encoding="utf-8",
    )
    (tmp_path / "agents" / "generated" / "weather_map_agent").mkdir(parents=True)
    (tmp_path / "agents" / "generated" / "weather_map_agent" / "Dockerfile").write_text(
        "FROM scratch\n",
        encoding="utf-8",
    )
    result = control_docker("docker://generate/weather-map-agent?action=generate", root=tmp_path)
    assert result["ok"] is True
    compose_path = tmp_path / "output/deployments/weather-map-agent/docker-compose.yaml"
    assert compose_path.exists()
    import yaml

    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    build = compose["services"]["weather_map_agent"]["build"]
    context_root = (compose_path.parent / build["context"]).resolve()
    assert context_root == tmp_path.resolve()
    assert (context_root / build["dockerfile"]).exists()


def test_control_docker_container_stop_dry_run():
    result = control_docker("docker://container/demo?action=stop&dry_run=1")
    assert result["command"] == ["docker", "stop", "demo"]


def test_control_docker_up_recovers_from_name_conflict(monkeypatch: pytest.MonkeyPatch):
    calls: list[list[str]] = []

    def fake_run(cmd, *, dry_run=False):
        calls.append(cmd)
        if cmd[0:3] == ["docker", "compose", "-f"] and "up" in cmd:
            if cmd[-1] == "-d" and len(calls) > 1:
                return {
                    "command": cmd,
                    "command_string": " ".join(cmd),
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                    "ok": True,
                }
            return {
                "command": cmd,
                "command_string": " ".join(cmd),
                "returncode": 1,
                "stdout": "",
                "stderr": 'Conflict. The container name "/hypervisor-ssh-agent-host" is already in use',
                "ok": False,
            }
        if cmd[0:2] == ["docker", "start"]:
            return {
                "command": cmd,
                "command_string": " ".join(cmd),
                "returncode": 0,
                "stdout": "hypervisor-ssh-agent-host",
                "stderr": "",
                "ok": True,
            }
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr("uri3.docker.actions.compose.run_command", fake_run)
    result = control_docker("docker://stack/ssh-testenv?action=up&build=1")
    assert result["ok"] is True
    assert result["recovered"] == "compose_up"
    assert calls[-1][0:3] == ["docker", "compose", "-f"]
    assert "-d" in calls[-1]
