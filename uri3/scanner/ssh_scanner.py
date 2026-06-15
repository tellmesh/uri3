from __future__ import annotations

import shlex
import shutil

from uri3.config.ssh_auth import resolve_ssh_password, ssh_auth_hint
from uri3.resolvers.ssh_resolver import parse_ssh_uri, run_ssh
from uri3.scanner.base import ScanItem


def _invalid_ssh_item(uri: str, exc: ValueError) -> list[ScanItem]:
    return [
        ScanItem(
            uri=uri,
            kind="ssh_connectivity",
            status="invalid",
            metadata={"errors": [str(exc)], "hint": "Use ssh://user@host:port/path"},
        )
    ]


def _connectivity_item(uri: str, ref: dict) -> tuple[ScanItem, bool]:
    ping = run_ssh(ref, "echo hypervisor-ssh-ok")
    reachable = ping.returncode == 0 and "hypervisor-ssh-ok" in (ping.stdout or "")
    auth_hint = ssh_auth_hint(ref, stderr=ping.stderr or "")
    item = ScanItem(
        uri=uri,
        kind="ssh_connectivity",
        status="reachable" if reachable else "unreachable",
        metadata={
            "target": ref["target"],
            "port": ref["port"],
            "stdout": (ping.stdout or "").strip(),
            "stderr": (ping.stderr or "").strip(),
            "returncode": ping.returncode,
            "password_configured": bool(resolve_ssh_password(ref)),
            "sshpass_available": bool(shutil.which("sshpass")),
            **({"hint": auth_hint} if auth_hint else {}),
        },
    )
    return item, reachable


def _remote_item_uri(uri: str, remote_path: str) -> str:
    base_uri = uri.rstrip("/")
    return base_uri if base_uri.endswith(remote_path) else f"{base_uri}{remote_path}"


def _remote_path_item(item_uri: str, ref: dict) -> ScanItem:
    remote_path = ref["path"]
    path_check = run_ssh(ref, f"test -d {shlex.quote(remote_path)} && echo dir || echo missing")
    path_exists = "dir" in (path_check.stdout or "")
    return ScanItem(
        uri=item_uri,
        kind="remote_path",
        status="present" if path_exists else "missing",
        metadata={
            "path": remote_path,
            "stdout": (path_check.stdout or "").strip(),
            "stderr": (path_check.stderr or "").strip(),
        },
    )


def _remote_listing_item(item_uri: str, ref: dict) -> ScanItem:
    remote_path = ref["path"]
    listing = run_ssh(ref, f"ls -la {shlex.quote(remote_path)} 2>/dev/null | head -n 8")
    return ScanItem(
        uri=item_uri,
        kind="remote_listing",
        status="ok" if listing.returncode == 0 else "error",
        metadata={
            "stdout": (listing.stdout or "").strip(),
            "stderr": (listing.stderr or "").strip(),
        },
    )


def scan_ssh(uri: str) -> list[ScanItem]:
    try:
        ref = parse_ssh_uri(uri)
    except ValueError as exc:
        return _invalid_ssh_item(uri, exc)

    connectivity, reachable = _connectivity_item(uri, ref)
    if not reachable:
        return [connectivity]

    item_uri = _remote_item_uri(uri, ref["path"])
    return [connectivity, _remote_path_item(item_uri, ref), _remote_listing_item(item_uri, ref)]
