from __future__ import annotations

import json
from typing import Any

from uri3.docker.runner import run_command
from uri3.resolvers.docker_resolver import DockerRef


def compose_base(ref: DockerRef) -> list[str]:
    if not ref.compose_file:
        raise ValueError(f"No compose file resolved for docker URI: {ref.uri}")
    cmd = ["docker", "compose", "-f", ref.compose_file]
    if ref.project:
        cmd.extend(["-p", ref.project])
    return cmd


def _parse_ps_stdout(stdout: str) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError:
            parsed.append({"raw": line})
    return parsed


def control_compose_ps(ref: DockerRef, *, dry_run: bool = False) -> dict[str, Any]:
    base = compose_base(ref)
    result = run_command(base + ["ps", "--format", "json"], dry_run=dry_run)
    if not dry_run and result.get("stdout"):
        result["services"] = _parse_ps_stdout(result["stdout"])
    return {"action": ref.action, "compose_file": ref.compose_file, **result}


def control_compose_up(ref: DockerRef, *, dry_run: bool = False) -> dict[str, Any]:
    base = compose_base(ref)
    cmd = base + ["up"]
    if ref.detach:
        cmd.append("-d")
    if ref.build:
        cmd.append("--build")
    result = run_command(cmd, dry_run=dry_run)
    if (
        not dry_run
        and not result.get("ok")
        and "Conflict" in (result.get("stderr") or "")
        and ref.container_name
    ):
        start = run_command(base + ["up", "-d"], dry_run=dry_run)
        if start.get("ok"):
            return {
                "action": "up",
                "compose_file": ref.compose_file,
                "recovered": "compose_up",
                **start,
            }
        remove = run_command(["docker", "rm", "-f", ref.container_name], dry_run=dry_run)
        if remove.get("ok"):
            recreate = run_command(base + ["up", "-d"], dry_run=dry_run)
            if recreate.get("ok"):
                return {
                    "action": "up",
                    "compose_file": ref.compose_file,
                    "recovered": "recreate",
                    **recreate,
                }
        start = run_command(["docker", "start", ref.container_name], dry_run=dry_run)
        if start.get("ok"):
            return {
                "action": "up",
                "compose_file": ref.compose_file,
                "recovered": "start",
                "container": ref.container_name,
                **start,
            }
    return {"action": "up", "compose_file": ref.compose_file, **result}


def control_compose_down(ref: DockerRef, *, dry_run: bool = False) -> dict[str, Any]:
    base = compose_base(ref)
    cmd = base + ["down"]
    if ref.remove_volumes:
        cmd.append("-v")
    return {"action": "down", "compose_file": ref.compose_file, **run_command(cmd, dry_run=dry_run)}


def control_compose_lifecycle(ref: DockerRef, *, dry_run: bool = False) -> dict[str, Any]:
    base = compose_base(ref)
    return {
        "action": ref.action,
        "compose_file": ref.compose_file,
        **run_command(base + [ref.action], dry_run=dry_run),
    }


def control_compose_logs(ref: DockerRef, *, dry_run: bool = False) -> dict[str, Any]:
    base = compose_base(ref)
    cmd = base + ["logs", "--tail", str(ref.tail)]
    return {"action": "logs", "compose_file": ref.compose_file, **run_command(cmd, dry_run=dry_run)}


def control_compose(ref: DockerRef, *, dry_run: bool = False) -> dict[str, Any]:
    if ref.action in {"status", "ps"}:
        return control_compose_ps(ref, dry_run=dry_run)
    if ref.action == "up":
        return control_compose_up(ref, dry_run=dry_run)
    if ref.action == "down":
        return control_compose_down(ref, dry_run=dry_run)
    if ref.action in {"start", "stop", "restart"}:
        return control_compose_lifecycle(ref, dry_run=dry_run)
    if ref.action == "logs":
        return control_compose_logs(ref, dry_run=dry_run)
    raise ValueError(f"Unsupported compose action {ref.action!r} for URI {ref.uri}")
