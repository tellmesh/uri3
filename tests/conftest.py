from __future__ import annotations

from pathlib import Path
import sys

import pytest


def _hypervisor_root() -> Path:
    current = Path(__file__).resolve()
    for base in (Path.cwd(), current.parent, *current.parents):
        for candidate in (base, base / "hypervisor", base / "wronai" / "hypervisor"):
            resolved = candidate.resolve()
            if (resolved / "contracts" / "registry.yaml").is_file() and (resolved / "examples").is_dir():
                return resolved
    return Path(__file__).resolve().parents[1]


HYPERVISOR_ROOT = _hypervisor_root()
TELL_MESH_ROOT = Path(__file__).resolve().parents[2]

for path in (
    HYPERVISOR_ROOT,
    HYPERVISOR_ROOT / "packages" / "resource-agent-hypervisor",
    HYPERVISOR_ROOT / "packages" / "resource-agent-factory",
    TELL_MESH_ROOT / "touri",
    TELL_MESH_ROOT / "uri2pact",
    TELL_MESH_ROOT / "uri2run",
    TELL_MESH_ROOT / "uri2flow",
    TELL_MESH_ROOT / "uri2verify",
    TELL_MESH_ROOT / "nl2uri",
    TELL_MESH_ROOT / "urigen",
):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return HYPERVISOR_ROOT
