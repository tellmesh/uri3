from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from uri3.config.docker_stacks import resolve_agent_stack
from uri3.config.repo_root import config_repo_root as _repo_root
from uri3.resolvers.docker_resolver import DockerRef


def build_generate_plan(ref: DockerRef, *, root: Path | None = None) -> dict[str, Any]:
    agent_id = ref.name.removeprefix("agent://")
    profile = resolve_agent_stack(agent_id, root=root)
    repo = _repo_root(root)
    compose_path = Path(profile["output_compose"])
    compose_path.parent.mkdir(parents=True, exist_ok=True)
    dockerfile = profile.get("dockerfile") or f"agents/generated/{agent_id.replace('-', '_')}/Dockerfile"
    dockerfile = str(dockerfile).replace("\\", "/")
    build_context = os.path.relpath(repo, compose_path.parent)
    port = profile.get("port", 8101)
    container_name = profile.get("container_name", agent_id)
    compose = {
        "services": {
            container_name.replace("-", "_"): {
                "build": {"context": build_context, "dockerfile": dockerfile},
                "container_name": container_name,
                "ports": [f"{port}:{port}"],
                "environment": {"RESOURCE_RUNTIME_URL": "http://host.docker.internal:8000"},
            }
        }
    }
    output_path = profile["output_compose"]
    return {
        "agent_id": agent_id,
        "output_compose": output_path,
        "repo_root": str(repo),
        "build_context": build_context,
        "dockerfile": dockerfile,
        "port": port,
        "container_name": container_name,
        "compose": compose,
    }


def write_generated_compose(ref: DockerRef, *, root: Path | None = None) -> str:
    plan = build_generate_plan(ref, root=root)
    path = Path(plan["output_compose"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(plan["compose"], sort_keys=False, allow_unicode=True), encoding="utf-8")
    return str(path)
