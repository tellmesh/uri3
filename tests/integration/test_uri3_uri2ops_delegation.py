"""Compatibility tests: uri3 workflow executor delegates operator schemes to uri2ops."""

from __future__ import annotations

from pathlib import Path

from uri3.graph import run_workflow
from uri3.graph.adapters.registry import adapter_for_uri
from uri3.graph.adapters.uri2ops_adapter import Uri2OpsAdapter


def test_default_operator_adapter_is_uri2ops():
    adapter = adapter_for_uri("browser://chrome/page/open")
    assert isinstance(adapter, Uri2OpsAdapter)


def test_uri2ops_delegation_mock_browser_workflow(tmp_path: Path):
    payload = {
        "task": {"id": "uri2ops-delegation", "description": "Delegate browser to uri2ops"},
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
    artifacts_dir = tmp_path / "output" / "artifacts" / "workflows" / "uri2ops-delegation"
    assert artifacts_dir.exists()
    assert any(path.name == "open.json" for path in artifacts_dir.rglob("open.json"))
    assert any(path.name == "dom.json" for path in artifacts_dir.rglob("dom.json"))
