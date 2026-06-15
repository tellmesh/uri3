from __future__ import annotations

from typing import Any


def check_result(id: str, ok: bool, **detail: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"id": id, "ok": ok}
    payload.update(detail)
    return payload
