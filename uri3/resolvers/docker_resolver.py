from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from uri3.config.repo_root import config_repo_root


DOCKER_ACTIONS = (
    "status",
    "ps",
    "inspect",
    "up",
    "down",
    "start",
    "stop",
    "restart",
    "logs",
    "generate",
)


@dataclass(frozen=True)
class DockerRef:
    uri: str
    kind: str
    name: str
    action: str = "status"
    compose_file: str | None = None
    project: str | None = None
    container_name: str | None = None
    dry_run: bool = False
    build: bool = True
    detach: bool = True
    remove_volumes: bool = False
    tail: int = 100
    query: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "kind": self.kind,
            "name": self.name,
            "action": self.action,
            "compose_file": self.compose_file,
            "project": self.project,
            "container_name": self.container_name,
            "dry_run": self.dry_run,
            "build": self.build,
            "detach": self.detach,
            "remove_volumes": self.remove_volumes,
            "tail": self.tail,
        }


def _first(query: dict[str, list[str]], key: str, default: str | None = None) -> str | None:
    values = query.get(key)
    if not values:
        return default
    return values[0]


def _bool(query: dict[str, list[str]], key: str, default: bool = False) -> bool:
    raw = (_first(query, key) or "").lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _int(query: dict[str, list[str]], key: str, default: int) -> int:
    raw = _first(query, key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def parse_docker_uri(uri: str, *, root: Path | None = None) -> DockerRef:
    parsed = urlparse(uri)
    if parsed.scheme != "docker":
        raise ValueError(f"Not a docker:// URI: {uri}")
    kind = parsed.netloc or "stack"
    name = parsed.path.lstrip("/")
    if not name:
        raise ValueError(f"docker:// URI requires a target name/path: {uri}")
    query = parse_qs(parsed.query)
    action = _first(query, "action", "status") or "status"
    if action not in DOCKER_ACTIONS:
        raise ValueError(f"Unsupported docker action: {action}")

    compose_file = None
    project = None
    container_name = None

    if kind == "stack":
        from uri3.config.docker_stacks import resolve_stack

        stack = resolve_stack(name, root=root)
        compose_file = stack["compose_file"]
        project = stack.get("project")
        container_name = stack.get("container_name")
    elif kind == "compose":
        repo_root = root or config_repo_root()
        compose_file = str((repo_root / name).resolve())
    elif kind == "container":
        container_name = name
    elif kind == "agent":
        from uri3.config.docker_stacks import resolve_agent_stack

        agent = resolve_agent_stack(name, root=root)
        compose_file = agent.get("compose_file")
        container_name = agent.get("container_name")
    elif kind == "generate":
        pass
    else:
        raise ValueError(f"Unsupported docker URI kind: {kind}")

    return DockerRef(
        uri=uri,
        kind=kind,
        name=name,
        action=action,
        compose_file=compose_file,
        project=project,
        container_name=container_name,
        dry_run=_bool(query, "dry_run"),
        build=_bool(query, "build", True),
        detach=_bool(query, "detach", True),
        remove_volumes=_bool(query, "remove_volumes"),
        tail=_int(query, "tail", 100),
        query=query,
    )


def resolve_docker(uri: str, *, root: Path | None = None) -> dict[str, Any]:
    ref = parse_docker_uri(uri, root=root)
    payload = ref.to_dict()
    payload["actions"] = list(DOCKER_ACTIONS)
    if ref.kind == "generate":
        from uri3.docker.compose_generator import build_generate_plan

        payload["generate_plan"] = build_generate_plan(ref, root=root)
    return payload


def resolve_docker_target(uri: str, *, root: Path | None = None) -> DockerRef:
    return parse_docker_uri(uri, root=root)
