from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


@dataclass(frozen=True)
class LogRef:
    uri: str
    stream: str
    path: Path | None
    level: str | None = None
    grep: str | None = None
    logger: str | None = None
    since: str | None = None
    until: str | None = None
    limit: int = 100
    offset: int = 0
    tail: bool = False
    format: str = "auto"
    query: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "stream": self.stream,
            "path": str(self.path) if self.path else None,
            "level": self.level,
            "grep": self.grep,
            "logger": self.logger,
            "since": self.since,
            "until": self.until,
            "limit": self.limit,
            "offset": self.offset,
            "tail": self.tail,
            "format": self.format,
        }


from uri3.resolvers.log_query import first, parse_query, query_bool, query_int, resolve_level


def parse_log_uri(uri: str) -> LogRef:
    stream, path, query = parse_query(uri)
    return LogRef(
        uri=uri,
        stream=stream,
        path=path,
        level=resolve_level(query),
        grep=first(query, "grep") or first(query, "q") or first(query, "contain"),
        logger=first(query, "logger") or first(query, "component"),
        since=first(query, "since") or first(query, "from"),
        until=first(query, "until") or first(query, "to"),
        limit=query_int(query, "limit", 100),
        offset=query_int(query, "offset", 0),
        tail=query_bool(query, "tail", False),
        format=first(query, "format", "auto") or "auto",
        query=query,
    )


def resolve_log(uri: str) -> dict[str, Any]:
    ref = parse_log_uri(uri)
    payload = ref.to_dict()
    payload["scheme"] = "log"
    payload["transport"] = "file"
    return payload


class LogResolver:
    scheme = "log"

    def resolve(self, uri: str):
        return resolve_log(uri)

    def read(self, uri: str, *, summary: bool = False):
        from uri3.logs.reader import read_logs, summarize_logs

        if summary:
            return summarize_logs(uri)
        return read_logs(uri)
