from __future__ import annotations

from urllib.parse import urlparse


def resolve_pypi(uri: str) -> dict[str, str]:
    parsed = urlparse(uri)
    package = parsed.netloc or parsed.path.strip("/")
    version = "latest"
    if "/" in parsed.path.strip("/"):
        parts = parsed.path.strip("/").split("/")
        if parts[0]:
            package = parts[0]
        if len(parts) > 1:
            version = parts[1]
    return {"package": package, "version": version, "index": "https://pypi.org/project/" + package}
