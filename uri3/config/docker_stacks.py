from __future__ import annotations

from pathlib import Path
from typing import Any

from uri3.config.repo_root import config_repo_root as _repo_root
from uri3.config.uri_yaml import load_uri_yaml


def docker_config_path(root: Path | None = None) -> Path:
    return _repo_root(root) / "config" / "docker.uri.yaml"


def load_docker_config(root: Path | None = None) -> dict[str, Any]:
    path = docker_config_path(root)
    if not path.exists():
        return {"version": 1, "defaults": {}, "stacks": {}, "agents": {}}
    return load_uri_yaml(path)


def resolve_stack(stack_id: str, *, root: Path | None = None) -> dict[str, Any]:
    data = load_docker_config(root)
    stacks = data.get("stacks") or {}
    stack = stacks.get(stack_id)
    if not stack:
        raise ValueError(f"Unknown docker stack: {stack_id}")
    repo = _repo_root(root)
    compose_file = stack.get("compose_file")
    if not compose_file:
        raise ValueError(f"Stack {stack_id} has no compose_file")
    return {
        "stack_id": stack_id,
        "compose_file": str((repo / compose_file).resolve()),
        "project": stack.get("project"),
        "container_name": stack.get("container_name"),
        "services": stack.get("services") or [],
        "description": stack.get("description"),
    }


def resolve_agent_stack(agent_id: str, *, root: Path | None = None) -> dict[str, Any]:
    data = load_docker_config(root)
    agents = data.get("agents") or {}
    agent_key = agent_id.removeprefix("agent://")
    agent = agents.get(agent_key)
    if not agent:
        raise ValueError(f"Unknown docker agent profile: {agent_key}")
    repo = _repo_root(root)
    compose_file = agent.get("compose_file")
    return {
        "agent_id": agent_key,
        "compose_file": str((repo / compose_file).resolve()) if compose_file else None,
        "output_compose": str((repo / agent.get("output_compose", f"output/deployments/{agent_key}/docker-compose.yaml")).resolve()),
        "dockerfile": agent.get("dockerfile"),
        "port": agent.get("port", 8101),
        "container_name": agent.get("container_name", agent_key),
    }
