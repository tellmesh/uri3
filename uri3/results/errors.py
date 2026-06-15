from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any


@dataclass
class ErrorEnvelope:
    code: str
    source: str = ""
    recoverable: bool = False
    detail: str = ""
    data_quality: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if not payload["data_quality"]:
            del payload["data_quality"]
        return payload


def normalize_error(item: Any, *, default_source: str = "") -> ErrorEnvelope:
    if isinstance(item, ErrorEnvelope):
        if default_source and not item.source:
            return replace(item, source=default_source)
        return item
    if isinstance(item, dict):
        return ErrorEnvelope(
            code=str(item.get("code") or "UNKNOWN"),
            source=str(item.get("source") or default_source),
            recoverable=bool(item.get("recoverable", False)),
            detail=str(item.get("detail") or item.get("message") or ""),
            data_quality=dict(item.get("data_quality") or {}),
        )
    return ErrorEnvelope(code="UNKNOWN", source=default_source, detail=str(item))
