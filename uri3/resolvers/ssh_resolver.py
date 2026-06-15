from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from typing import Any
from urllib.parse import urlparse

def parse_ssh_uri(uri: str) -> dict[str, Any]:
    parsed = urlparse(uri)
    if parsed.scheme != "ssh":
        raise ValueError(f"Not an ssh:// URI: {uri}")
    if not parsed.netloc:
        raise ValueError("ssh:// URI requires user@host[:port]/path")
    netloc = parsed.netloc
    user = None
    host_port = netloc
    if "@" in netloc:
        user, host_port = netloc.rsplit("@", 1)
    if ":" in host_port:
        host, port_raw = host_port.rsplit(":", 1)
        port = int(port_raw)
    else:
        host = host_port
        port = 22
    path = parsed.path or "/"
    target = f"{user}@{host}" if user else host
    return {
        "uri": uri,
        "user": user,
        "host": host,
        "port": port,
        "path": path.rstrip("/") or "/",
        "target": target,
        "transport": "ssh",
    }


def _resolve_ssh_password(ref: dict[str, Any]) -> str | None:
    from uri3.config.ssh_auth import resolve_ssh_password

    return resolve_ssh_password(ref)


def resolve_ssh(uri: str) -> dict[str, Any]:
    ref = parse_ssh_uri(uri)
    password = _resolve_ssh_password(ref)
    payload = dict(ref)
    payload["password_configured"] = bool(password)
    payload["sshpass_available"] = bool(shutil.which("sshpass"))
    return payload


def _ssh_options(ref: dict[str, Any], *, password: str | None) -> list[str]:
    options = [
        "ssh",
        "-p",
        str(ref["port"]),
        "-o",
        "ConnectTimeout=5",
        "-o",
        "StrictHostKeyChecking=accept-new",
    ]
    if password:
        options.extend(
            [
                "-o",
                "PreferredAuthentications=password,keyboard-interactive",
                "-o",
                "PubkeyAuthentication=no",
            ]
        )
    else:
        options.extend(["-o", "BatchMode=yes"])
    return options


def build_ssh_command(ref: dict[str, Any], remote_command: str | None = None) -> list[str]:
    password = _resolve_ssh_password(ref)
    ssh_cmd = _ssh_options(ref, password=password)
    target = ref["target"]
    cmd = ssh_cmd + ([target, remote_command] if remote_command else [target])
    if password:
        if not shutil.which("sshpass"):
            raise RuntimeError(
                "SSH password is configured but sshpass is not installed. "
                "Install sshpass or use SSH key authentication."
            )
        return ["sshpass", "-p", password, *cmd]
    return cmd


def ssh_transport_option(ref: dict[str, Any]) -> str:
    password = _resolve_ssh_password(ref)
    ssh_cmd = " ".join(shlex.quote(part) for part in _ssh_options(ref, password=password))
    if password:
        if not shutil.which("sshpass"):
            raise RuntimeError("SSH password is configured but sshpass is not installed.")
        return f"sshpass -p {shlex.quote(password)} {ssh_cmd}"
    return ssh_cmd


def run_ssh(ref: dict[str, Any], remote_command: str, *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        build_ssh_command(ref, remote_command),
        capture_output=True,
        text=True,
        check=check,
    )
