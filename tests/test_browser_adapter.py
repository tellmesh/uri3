"""Tests for Playwright browser adapter (optional)."""

from __future__ import annotations

import http.server
import os
import socket
import threading
from pathlib import Path

import pytest

from uri3.graph import run_workflow
from uri3.graph.adapters.browser_router import resolve_browser_mode
from uri3.graph.execution_models import new_execution_context


def test_resolve_browser_mode_mock():
    context = new_execution_context("demo", browser_mode="mock")
    assert resolve_browser_mode(context) == "mock"


def test_mock_adapter_writes_artifact_files(tmp_path: Path):
    payload = {
        "task": {"id": "check-agent-health", "description": "Check health"},
        "steps": [
            {
                "id": "open_health",
                "uri": "browser://chrome/page/open",
                "operation": "open",
                "kind": "command",
                "payload": {"url": "http://localhost:8101/health"},
            },
            {
                "id": "extract_body",
                "uri": "dom://chrome/active/body",
                "operation": "read",
                "kind": "query",
                "depends_on": ["open_health"],
            },
        ],
    }
    result = run_workflow(payload, approve=True, browser_mode="mock", root=tmp_path)
    assert result.ok is True
    artifacts_dir = tmp_path / "output" / "artifacts" / "workflows" / "check-agent-health"
    assert artifacts_dir.exists()
    assert any(path.name == "open.json" for path in artifacts_dir.rglob("open.json"))
    assert any(path.name == "dom.json" for path in artifacts_dir.rglob("dom.json"))


@pytest.mark.skipif(os.environ.get("URI3_PLAYWRIGHT_E2E") != "1", reason="set URI3_PLAYWRIGHT_E2E=1 for Playwright e2e")
def test_playwright_browser_workflow(tmp_path: Path):
    pytest.importorskip("playwright")
    body = b"ok"
    host = "127.0.0.1"

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>ok</body></html>")

        def log_message(self, format, *args):  # noqa: A003
            return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, 0))
    port = sock.getsockname()[1]
    sock.close()
    server = http.server.ThreadingHTTPServer((host, port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        payload = {
            "task": {"id": "browser-health-check", "description": "Browser workflow"},
            "steps": [
                {
                    "id": "open_health",
                    "uri": "browser://chrome/page/open",
                    "operation": "open",
                    "kind": "command",
                    "payload": {"url": f"http://{host}:{port}/health"},
                },
                {
                    "id": "extract_body",
                    "uri": "dom://chrome/active/body",
                    "operation": "read",
                    "kind": "query",
                    "depends_on": ["open_health"],
                },
                {
                    "id": "verify_ok",
                    "uri": "assertion://contains",
                    "operation": "check",
                    "kind": "assertion",
                    "depends_on": ["extract_body"],
                    "payload": {"actual_from": "extract_body.text", "expected": "ok"},
                },
            ],
        }
        result = run_workflow(payload, approve=True, browser_mode="playwright", root=tmp_path)
        assert result.ok is True
        assert result.steps[-1].ok is True
        dom_artifact = tmp_path / "output" / "artifacts" / "workflows" / "browser-health-check"
        assert any(path.name == "dom.json" for path in dom_artifact.rglob("dom.json"))
    finally:
        server.shutdown()
