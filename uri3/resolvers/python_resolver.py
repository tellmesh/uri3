from __future__ import annotations

import importlib
from urllib.parse import urlparse
from typing import Any


def _split_python_uri(uri: str) -> tuple[str, str]:
    parsed = urlparse(uri)
    target = parsed.netloc + parsed.path
    if ":" not in target:
        raise ValueError("python:// URI must be python://module.path:function")
    module, func = target.split(":", 1)
    return module.strip("/"), func


def resolve_python(uri: str) -> dict[str, str]:
    module, func = _split_python_uri(uri)
    return {"module": module, "function": func}


def call_python(uri: str, payload: dict[str, Any]) -> Any:
    module, func = _split_python_uri(uri)
    mod = importlib.import_module(module)
    fn = getattr(mod, func)
    return fn(payload)


class PythonResolver:
    scheme = "python"

    def resolve(self, uri):
        return resolve_python(uri)

    def call(self, uri, payload=None):
        return call_python(uri, payload or {})
