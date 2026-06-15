from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from uri3.graph.artifacts import write_artifact
from uri3.graph.adapters.browser_mock import json_dumps
from uri3.graph.execution_models import ExecutionContext
from uri3.graph.models import GraphNode


def _session_state(context: ExecutionContext) -> dict[str, Any]:
    return context.adapter_state.setdefault("playwright", {})


def close_playwright_session(context: ExecutionContext) -> None:
    state = context.adapter_state.get("playwright") or {}
    page = state.get("page")
    browser = state.get("browser")
    playwright = state.get("playwright")
    if page is not None:
        page.close()
    if browser is not None:
        browser.close()
    if playwright is not None:
        playwright.stop()
    context.adapter_state.pop("playwright", None)


class PlaywrightBrowserAdapter:
    schemes = frozenset({"browser", "dom", "screen"})

    def execute(self, node: GraphNode, context: ExecutionContext) -> dict[str, Any]:
        if context.dry_run:
            from uri3.graph.adapters.browser_mock import BrowserMockAdapter

            payload = BrowserMockAdapter().execute(node, context)
            payload["dry_run"] = True
            return payload

        from playwright.sync_api import sync_playwright

        scheme = urlparse(node.uri).scheme
        state = _session_state(context)

        if scheme == "browser" and node.operation == "open":
            url = str(node.payload.get("url") or "about:blank")
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            response = page.goto(url, wait_until="domcontentloaded")
            state.update({"playwright": playwright, "browser": browser, "page": page, "url": url})
            meta = {
                "ok": True,
                "url": url,
                "title": page.title(),
                "status_code": response.status if response else None,
            }
            _, artifact = write_artifact(context, node.id, "open.json", json_dumps(meta))
            return {**meta, "artifact_uri": artifact}

        page = state.get("page")
        if page is None:
            return {"ok": False, "error": "browser session not open; run browser://.../open first"}

        if scheme == "dom" or node.operation in {"read", "extract", "extract_dom"}:
            text = page.inner_text("body")
            html = page.content()
            meta = {"ok": True, "text": text, "html": html}
            _, artifact = write_artifact(context, node.id, "dom.json", json_dumps(meta))
            return {**meta, "artifact_uri": artifact}

        if scheme == "screen" or node.operation in {"screenshot", "capture"}:
            path, artifact = write_artifact(context, node.id, "screenshot.png", page.screenshot(full_page=True))
            return {"ok": True, "artifact_uri": artifact, "path": str(path)}

        return {"ok": False, "error": f"unsupported browser operation for {node.uri}"}
