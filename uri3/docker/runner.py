from __future__ import annotations

import subprocess
from typing import Any


def run_command(cmd: list[str], *, dry_run: bool = False) -> dict[str, Any]:
    payload = {"command": cmd, "command_string": " ".join(cmd)}
    if dry_run:
        payload["dry_run"] = True
        return payload
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    payload.update(
        {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }
    )
    if completed.returncode != 0:
        payload["error"] = completed.stderr.strip() or completed.stdout.strip()
    return payload
