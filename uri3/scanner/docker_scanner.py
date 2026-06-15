from __future__ import annotations

import json
import subprocess
from typing import Any

from uri3.resolvers.docker_resolver import DockerRef, parse_docker_uri
from uri3.scanner.base import ScanItem


def _inspect_container(name: str) -> tuple[str, dict[str, Any]]:
    completed = subprocess.run(
        ["docker", "inspect", name],
        capture_output=True,
        text=True,
        check=False,
    )
    metadata: dict[str, Any] = {"container": name, "returncode": completed.returncode}
    if completed.returncode != 0:
        return "missing", metadata
    try:
        inspection = json.loads(completed.stdout)[0]
        state = inspection.get("State", {})
        running = bool(state.get("Running"))
        metadata["state"] = state.get("Status")
        metadata["health"] = (inspection.get("State") or {}).get("Health", {}).get("Status")
        return ("running" if running else "stopped"), metadata
    except (json.JSONDecodeError, IndexError):
        return "error", metadata


def scan_container(uri: str, ref: DockerRef) -> ScanItem:
    name = ref.container_name or ref.name
    status, metadata = _inspect_container(name)
    return ScanItem(uri=uri, kind="container", status=status, metadata=metadata)


def _compose_ps(ref: DockerRef) -> tuple[list[dict[str, Any]], str]:
    base_cmd = ["docker", "compose", "-f", ref.compose_file]
    if ref.project:
        base_cmd.extend(["-p", ref.project])
    completed = subprocess.run(
        base_cmd + ["ps", "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    services: list[dict[str, Any]] = []
    if completed.returncode == 0:
        for line in completed.stdout.splitlines():
            if not line.strip():
                continue
            try:
                services.append(json.loads(line))
            except json.JSONDecodeError:
                services.append({"raw": line})
    return services, completed.stderr.strip()


def scan_compose_stack(uri: str, ref: DockerRef) -> ScanItem:
    services, stderr = _compose_ps(ref)
    running_count = sum(1 for svc in services if svc.get("State") == "running")
    status = "running" if running_count else ("stopped" if services else "empty")
    return ScanItem(
        uri=uri,
        kind="compose_stack",
        status=status,
        metadata={
            "compose_file": ref.compose_file,
            "project": ref.project,
            "services": services,
            "running_count": running_count,
            "stderr": stderr,
        },
    )


def scan_docker(uri: str) -> list[ScanItem]:
    ref = parse_docker_uri(uri)
    if ref.kind == "container" or ref.container_name:
        return [scan_container(uri, ref)]
    if ref.compose_file:
        return [scan_compose_stack(uri, ref)]
    return [
        ScanItem(
            uri=uri,
            kind=ref.kind,
            status="unknown",
            metadata={"hint": "No compose file or container resolved for scan"},
        )
    ]
