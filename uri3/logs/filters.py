from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from uri3.resolvers.log_resolver import LOG_LEVELS, LogRef


def level_rank(level: str | None) -> int:
    if not level:
        return 1
    try:
        return LOG_LEVELS.index(level.upper())
    except ValueError:
        return 1


def entry_timestamp(entry: dict[str, Any]) -> datetime | None:
    raw = entry.get("timestamp")
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def matches_level(entry: dict[str, Any], ref: LogRef) -> bool:
    if not ref.level:
        return True
    return level_rank(entry.get("level")) >= level_rank(ref.level)


def matches_logger(entry: dict[str, Any], ref: LogRef) -> bool:
    if not ref.logger:
        return True
    logger = str(entry.get("logger") or "")
    return ref.logger.lower() in logger.lower()


def matches_grep(entry: dict[str, Any], ref: LogRef) -> bool:
    if not ref.grep:
        return True
    haystack = " ".join(str(entry.get(key) or "") for key in ("message", "logger", "raw")).lower()
    return ref.grep.lower() in haystack


def matches_time_window(
    entry: dict[str, Any],
    since_dt: datetime | None,
    until_dt: datetime | None,
) -> bool:
    ts = entry_timestamp(entry)
    if since_dt and ts and ts < since_dt:
        return False
    if until_dt and ts and ts > until_dt:
        return False
    return True


def matches_filters(
    entry: dict[str, Any],
    ref: LogRef,
    since_dt: datetime | None,
    until_dt: datetime | None,
) -> bool:
    return (
        matches_level(entry, ref)
        and matches_logger(entry, ref)
        and matches_grep(entry, ref)
        and matches_time_window(entry, since_dt, until_dt)
    )
