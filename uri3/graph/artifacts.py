from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from uri3.graph.execution_models import ExecutionContext
from uri3.results.statuses import EXECUTION_COMPLETED, SERVICE_SUCCEEDED

WORKFLOW_ARTIFACT_SCHEMA = "schemas/workflow_artifact.schema.json"


def artifact_path(context: ExecutionContext, step_id: str, suffix: str) -> Path:
    return (
        context.root
        / "output"
        / "artifacts"
        / "workflows"
        / context.workflow_id
        / context.run_id
        / step_id
        / suffix
    )


def artifact_uri(context: ExecutionContext, step_id: str, suffix: str) -> str:
    return f"artifact://workflow/{context.workflow_id}/{context.run_id}/{step_id}/{suffix}"


def build_workflow_step_artifact(
    context: ExecutionContext,
    step_id: str,
    suffix: str,
    *,
    payload: dict[str, Any] | None = None,
    ok: bool = True,
) -> dict[str, Any]:
    artifact_id = suffix.rsplit(".", 1)[0]
    return {
        "$schema": WORKFLOW_ARTIFACT_SCHEMA,
        "apiVersion": "uri3.io/v1",
        "kind": "WorkflowStepArtifact",
        "metadata": {
            "workflow_id": context.workflow_id,
            "step_id": step_id,
            "run_id": context.run_id,
            "artifact_id": artifact_id,
        },
        "uri": {
            "self": artifact_uri(context, step_id, suffix),
            "source_step": f"workflow://{context.workflow_id}/step/{step_id}",
        },
        "result": {
            "ok": ok,
            "execution_status": EXECUTION_COMPLETED,
            "service_result_status": SERVICE_SUCCEEDED if ok else "failed",
            "workflow_status": "completed" if ok else "failed",
            "result_type": "artifact",
        },
        "payload": payload or {},
    }


def write_artifact(
    context: ExecutionContext,
    step_id: str,
    suffix: str,
    content: bytes | str | dict[str, Any],
    *,
    structured: bool = False,
    validate: bool = False,
) -> tuple[Path, str]:
    path = artifact_path(context, step_id, suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    uri = artifact_uri(context, step_id, suffix)

    if structured or isinstance(content, dict):
        payload = content if isinstance(content, dict) else build_workflow_step_artifact(
            context,
            step_id,
            suffix,
            payload={"text": str(content)},
        )
        if validate:
            from uri3.artifacts.writer import write_yaml_artifact

            write_yaml_artifact(
                path.with_suffix(".yaml") if not str(path).endswith(".yaml") else path,
                payload,
                repo_root=context.root,
                schema_relative=WORKFLOW_ARTIFACT_SCHEMA,
                validate=True,
            )
            final_path = path.with_suffix(".yaml") if not str(path).endswith(".yaml") else path
            return final_path, uri
        text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
        path = path.with_suffix(".yaml") if not str(path).endswith(".yaml") else path
        path.write_text(text, encoding="utf-8")
        return path, uri

    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    return path, uri


# --- mock helpers (stdlib only, no external deps for mock adapters) ---

import struct
import zlib


def mock_screenshot_png(width: int = 640, height: int = 360) -> bytes:
    """Return a valid PNG image bytes for mock browser/screen screenshots.

    Produces a small placeholder image (dark banner + banded body) that is
    loadable by any PNG reader (file(1), browsers, PIL, etc). Used instead of
    writing literal "mock-screenshot" text into .png artifacts.
    """
    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data) & 0xffffffff
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

    # IHDR: 8-bit RGB
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    banner_h = max(1, height // 8)
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0
        for x in range(width):
            if y < banner_h:
                # dark top banner (typical browser chrome feel)
                r, g, b = 0x1E, 0x3A, 0x5F
            elif y >= height - max(1, banner_h // 2):
                # subtle bottom strip
                r, g, b = 0x4A, 0x6A, 0x8A
            else:
                # main "page" area with faint horizontal banding so it looks like content
                base = 0xE8
                tint = ((x * 2) + (y * 3)) % 24
                r = min(255, base - 10 + tint)
                g = min(255, base - 2 + (tint // 2))
                b = min(255, base + 6)
            raw.extend((r, g, b))

    idat = zlib.compress(bytes(raw), 9)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", idat)
        + _chunk(b"IEND", b"")
    )
