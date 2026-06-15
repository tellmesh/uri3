from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from uri3.config.repo_root import config_repo_root as _repo_root
from uri3.config.uri_yaml import load_uri_yaml, resolve_uri_values


def ssh_config_path(root: Path | None = None) -> Path:
    return _repo_root(root) / "config" / "ssh.uri.yaml"


def load_ssh_config(root: Path | None = None) -> dict[str, Any]:
    path = ssh_config_path(root)
    if not path.exists():
        return {"version": 1, "defaults": {}, "profiles": {}}
    return load_uri_yaml(path)


def _profile_matches(ref: dict[str, Any], match: dict[str, Any]) -> bool:
    for key in ("user", "host", "port"):
        expected = match.get(key)
        if expected is None:
            continue
        if str(ref.get(key)) != str(expected):
            return False
    return True


def _password_from_env_file(root: Path) -> str | None:
    env_path = root / ".env"
    if not env_path.exists():
        return None
    try:
        from dotenv import dotenv_values
    except ImportError:
        return None
    values = dotenv_values(env_path)
    for key in ("HYPERVISOR_SSH_PASSWORD", "SSHPASS", "SSH_DEPLOY_PASSWORD"):
        value = values.get(key)
        if value:
            return str(value)
    return None


def _resolve_password_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and value.startswith("env://"):
        from uri3.resolvers.env_resolver import resolve_env

        resolved = resolve_env(value).get("value")
        return str(resolved) if resolved else None
    if isinstance(value, str) and value.startswith("secret://"):
        resolved = resolve_uri_values(value, resolve_secrets=True)
        return str(resolved) if resolved else None
    return str(value)


def resolve_ssh_password(ref: dict[str, Any] | None = None, *, root: Path | None = None) -> str | None:
    for env_key in ("HYPERVISOR_SSH_PASSWORD", "SSHPASS", "SSH_DEPLOY_PASSWORD"):
        value = os.environ.get(env_key)
        if value:
            return value

    repo = _repo_root(root)
    file_password = _password_from_env_file(repo)
    if file_password:
        return file_password

    data = load_ssh_config(repo)
    profiles = data.get("profiles") or {}
    if ref is not None:
        for profile in profiles.values():
            match = profile.get("match") or {}
            if match and _profile_matches(ref, match):
                password = _resolve_password_value(profile.get("password"))
                if password:
                    return password

    defaults = data.get("defaults") or {}
    return _resolve_password_value(defaults.get("password"))


def ssh_auth_hint(ref: dict[str, Any] | None = None, *, stderr: str = "") -> str | None:
    if "Permission denied" not in stderr:
        return None
    repo = _repo_root(None)
    if resolve_ssh_password(ref, root=repo):
        return (
            "SSH password is configured (HYPERVISOR_SSH_PASSWORD or .env) but sshpass may be missing. "
            "Install sshpass or configure SSH keys."
        )
    return (
        "SSH authentication failed. For docker testenv set "
        "HYPERVISOR_SSH_PASSWORD=deploy (or add it to .env), or configure SSH keys."
    )
