from __future__ import annotations

import json
from typing import Any

from uri3.docker.runner import run_command
from uri3.resolvers.docker_resolver import DockerRef


def _container_name(ref: DockerRef) -> str:
    return ref.container_name or ref.name


def handles_container_action(ref: DockerRef) -> bool:
    return ref.kind == "container" or (
        ref.action in {"start", "stop", "restart", "logs", "inspect"} and bool(ref.container_name)
    )


def control_container(ref: DockerRef, *, dry_run: bool = False) -> dict[str, Any]:
    name = _container_name(ref)
    if ref.action == "logs":
        cmd = ["docker", "logs", "--tail", str(ref.tail), name]
        return {"action": ref.action, "container": name, **run_command(cmd, dry_run=dry_run)}
    if ref.action == "inspect":
        cmd = ["docker", "inspect", name]
        result = run_command(cmd, dry_run=dry_run)
        if not dry_run and result.get("ok") and result.get("stdout"):
            try:
                result["inspection"] = json.loads(result["stdout"])[0]
            except json.JSONDecodeError:
                pass
        return {"action": ref.action, "container": name, **result}
    if ref.action in {"start", "stop", "restart"}:
        cmd = ["docker", ref.action, name]
        return {"action": ref.action, "container": name, **run_command(cmd, dry_run=dry_run)}
    raise ValueError(f"Unsupported container action {ref.action!r} for URI {ref.uri}")
