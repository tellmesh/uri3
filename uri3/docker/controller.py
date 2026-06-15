from __future__ import annotations

from pathlib import Path
from typing import Any

from uri3.docker.actions.compose import control_compose
from uri3.docker.actions.container import control_container, handles_container_action
from uri3.docker.compose_generator import write_generated_compose
from uri3.resolvers.docker_resolver import parse_docker_uri


def control_docker(uri: str, *, root: Path | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    from dataclasses import replace

    ref = parse_docker_uri(uri, root=root)
    if payload:
        updates = {key: value for key, value in payload.items() if key in ref.__dataclass_fields__}
        if updates:
            ref = replace(ref, **updates)
    dry_run = ref.dry_run or bool((payload or {}).get("dry_run"))

    if ref.action == "generate":
        if dry_run:
            from uri3.docker.compose_generator import build_generate_plan

            return {"action": "generate", "dry_run": True, **build_generate_plan(ref, root=root)}
        path = write_generated_compose(ref, root=root)
        return {"action": "generate", "ok": True, "compose_file": path}

    if handles_container_action(ref):
        return control_container(ref, dry_run=dry_run)

    if ref.compose_file:
        return control_compose(ref, dry_run=dry_run)

    raise ValueError(f"Cannot execute docker action {ref.action!r} for URI {ref.uri}")
