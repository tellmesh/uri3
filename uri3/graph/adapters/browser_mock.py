from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from uri3.graph.artifacts import artifact_uri, mock_screenshot_png, write_artifact
from uri3.graph.execution_models import ExecutionContext
from uri3.graph.models import GraphNode


class BrowserMockAdapter:
    schemes = frozenset({"browser", "dom", "screen"})

    def execute(self, node: GraphNode, context: ExecutionContext) -> dict[str, Any]:
        scheme = urlparse(node.uri).scheme
        if scheme == "browser" and node.operation == "open":
            url = node.payload.get("url", "about:blank")
            _, artifact = write_artifact(
                context,
                node.id,
                "open.json",
                json_dumps({"ok": True, "mock": True, "url": url, "title": "mock-browser-page"}),
            )
            return {
                "ok": True,
                "mock": True,
                "url": url,
                "title": "mock-browser-page",
                "artifact_uri": artifact,
            }
        if scheme == "dom" or (scheme == "browser" and node.operation in {"read", "extract", "extract_dom"}):
            body = {"ok": True, "mock": True, "text": "ok", "html": "<body>ok</body>"}
            _, artifact = write_artifact(context, node.id, "dom.json", json_dumps(body))
            return {**body, "artifact_uri": artifact}
        if scheme == "screen" or node.operation in {"screenshot", "capture"}:
            png_bytes = mock_screenshot_png()
            _, artifact = write_artifact(context, node.id, "screenshot.png", png_bytes)
            return {"ok": True, "mock": True, "artifact_uri": artifact}
        return {"ok": True, "mock": True, "message": f"mock browser adapter handled {node.uri}"}


def json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, indent=2, ensure_ascii=False)
