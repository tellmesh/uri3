from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

_DEFAULT_MONOREPO = Path("/home/tom/github/tellmesh/tellmesh")


def _hypervisor_root() -> Path:
    env = os.environ.get("HYPERVISOR_REPO_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    current = Path(__file__).resolve()
    for base in (Path.cwd(), current.parent, *current.parents):
        for candidate in (
            base,
            base / "tellmesh" / "tellmesh",
            base / "hypervisor",
            base / "wronai" / "hypervisor",
        ):
            resolved = candidate.resolve()
            if (resolved / "contracts").is_dir() and (resolved / "examples").is_dir():
                return resolved
    if _DEFAULT_MONOREPO.is_dir():
        return _DEFAULT_MONOREPO.resolve()
    return Path(__file__).resolve().parents[1]


HYPERVISOR_ROOT = _hypervisor_root()
TELL_MESH_ROOT = (
    HYPERVISOR_ROOT.parent
    if HYPERVISOR_ROOT.name == "tellmesh"
    else Path(__file__).resolve().parents[2]
)

for path in (
    HYPERVISOR_ROOT,
    TELL_MESH_ROOT / "hypervisor",
    TELL_MESH_ROOT / "resource-agent-hypervisor",
    TELL_MESH_ROOT / "resource-agent-factory",
    TELL_MESH_ROOT / "touri",
    TELL_MESH_ROOT / "uri2pact",
    TELL_MESH_ROOT / "uri2run",
    TELL_MESH_ROOT / "uri2flow",
    TELL_MESH_ROOT / "uri2verify",
    TELL_MESH_ROOT / "nl2uri",
    TELL_MESH_ROOT / "urigen",
):
    if path.is_dir() and str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return HYPERVISOR_ROOT
