"""Tests for HTTP scanner."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from uri3.scanner.http_scanner import health_scan_ok, scan_http


def test_scan_http_health_uri_does_not_double_path(monkeypatch: pytest.MonkeyPatch):
    requested: list[str] = []

    def fake_get(url, timeout=3):
        requested.append(url)
        response = MagicMock()
        response.status_code = 200 if url.endswith("/health") else 404
        return response

    monkeypatch.setattr("uri3.scanner.http_scanner.httpx.get", fake_get)
    items = scan_http("http://localhost:8101/health")
    assert requested[0] == "http://localhost:8101/health"
    assert all("/health/health" not in url for url in requested)
    health = next(item for item in items if item.kind == "health")
    assert health.status == "ok"


def test_scan_http_404_health_is_error(monkeypatch: pytest.MonkeyPatch):
    response = MagicMock(status_code=404)
    monkeypatch.setattr("uri3.scanner.http_scanner.httpx.get", lambda url, timeout=3: response)
    items = scan_http("http://localhost:8101/health")
    health = next(item for item in items if item.kind == "health")
    assert health.status == "error"
    assert health_scan_ok(items) is False


def test_health_scan_ok_requires_200():
    items = [
        MagicMock(kind="health", status="error", metadata={"status_code": 404}),
    ]
    assert health_scan_ok(items) is False
