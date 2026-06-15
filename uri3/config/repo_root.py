from __future__ import annotations

from pathlib import Path

_CONFIG_MARKERS = (
    "config/ssh.uri.yaml",
    "config/llm.uri.yaml",
    "config/docker.uri.yaml",
    "config/uri3.uri.yaml",
)


def _walk_up(start: Path) -> Path | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for path in (current, *current.parents):
        if (path / "contracts").is_dir() and (path / "schemas").is_dir():
            return path
        if any((path / marker).exists() for marker in _CONFIG_MARKERS):
            return path
    return None


def find_repo_root(start: Path | None = None, *, strict: bool = True) -> Path:
    """Locate monorepo root by contract/schema or config markers."""
    found = _walk_up(start or Path(__file__))
    if found is not None:
        return found
    if strict:
        raise FileNotFoundError("Repository root not found (expected contracts/ and schemas/)")
    return Path.cwd()


def config_repo_root(root: Path | None = None) -> Path:
    """Repo root for config file lookups; falls back to cwd when markers are missing."""
    if root is not None:
        return Path(root)
    found = _walk_up(Path(__file__))
    return found if found is not None else Path.cwd()


def repo_root() -> Path:
    return find_repo_root()


def ensure_repo_root_on_syspath(*, start: Path | None = None) -> Path | None:
    """Prepend monorepo root to sys.path so top-level `agents` imports resolve."""
    import sys

    try:
        root = find_repo_root(start, strict=False)
    except FileNotFoundError:
        return None
    if not (root / "agents").is_dir():
        return None
    repo_str = str(root.resolve())
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
    return root
