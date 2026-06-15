from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

TEXT_FILE_MAX_BYTES = 64 * 1024
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".json",
    ".md",
    ".proto",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def path_from_file_uri(uri: str) -> Path:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        raise ValueError(f"Expected file:// URI, got: {uri}")
    if parsed.netloc and parsed.netloc != "localhost":
        path = f"//{parsed.netloc}{parsed.path}"
    else:
        path = parsed.path
    path = unquote(path)
    if path.startswith("/") and len(path) > 2 and path[2] == ":":
        path = path[1:]
    return Path(path)


def resolve_file(uri: str) -> dict[str, Any]:
    path = path_from_file_uri(uri)
    data: dict[str, Any] = {
        "scheme": "file",
        "uri": uri,
        "path": str(path),
        "exists": path.exists(),
        "name": path.name,
        "suffix": path.suffix,
        "mime_type": mimetypes.guess_type(path.name)[0],
    }
    if path.exists():
        stat = path.stat()
        data.update(
            {
                "resolved_path": str(path.resolve()),
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "size_bytes": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        )
        if path.is_file() and _looks_like_text(path, data["mime_type"]):
            raw = path.read_bytes()[:TEXT_FILE_MAX_BYTES]
            data.update(
                {
                    "encoding": "utf-8",
                    "content": raw.decode("utf-8", errors="replace"),
                    "content_truncated": stat.st_size > TEXT_FILE_MAX_BYTES,
                    "content_max_bytes": TEXT_FILE_MAX_BYTES,
                }
            )
    return data


def _looks_like_text(path: Path, mime_type: str | None) -> bool:
    if mime_type and mime_type.startswith("text/"):
        return True
    return path.suffix.lower() in TEXT_SUFFIXES
