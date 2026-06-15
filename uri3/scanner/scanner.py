from __future__ import annotations

from uri3.logs.reader import resolve_log_path, summarize_logs
from uri3.protocols.parser import parse_uri
from uri3.resolvers.log_resolver import parse_log_uri
from uri3.scanner.base import ScanItem
from uri3.scanner.docker_scanner import scan_docker
from uri3.scanner.http_scanner import scan_http
from uri3.scanner.ssh_scanner import scan_ssh


def scan_log(uri: str) -> list[ScanItem]:
    ref = parse_log_uri(uri)
    path = resolve_log_path(ref)
    summary = summarize_logs(uri)
    return [
        ScanItem(
            uri=uri,
            kind="log",
            status="ok" if summary["exists"] else "missing",
            metadata={
                "path": summary["path"],
                "size_bytes": summary["size_bytes"],
                "matched": summary["matched"],
                "levels": summary["levels"],
                "filters": ref.to_dict(),
            },
        )
    ]


def scan(uri: str):
    scheme = parse_uri(uri).scheme
    if scheme in {"http", "https"}:
        return scan_http(uri)
    if scheme == "ssh":
        return scan_ssh(uri)
    if scheme == "docker":
        return scan_docker(uri)
    if scheme == "log":
        return scan_log(uri)
    return []
