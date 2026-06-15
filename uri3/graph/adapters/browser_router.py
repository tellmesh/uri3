"""Browser adapter routing for uri3 workflow executor.

Deprecated: browser execution belongs in uri2ops. uri3 should delegate via
uri2ops_adapter; these adapters remain for mock/playwright workflow tests.
"""
from __future__ import annotations

import os
import warnings
from typing import Any

from uri3.graph.adapters.browser_mock import BrowserMockAdapter
from uri3.graph.adapters.browser_playwright import (
    PlaywrightBrowserAdapter,
    close_playwright_session,
)
from uri3.graph.execution_models import ExecutionContext
from uri3.graph.models import GraphNode


def _uri2ops_playwright_ready() -> bool:
    try:
        from agents.operators.browser_operator.adapters.browser_router import playwright_ready
    except ImportError:
        return False
    return playwright_ready()


def resolve_browser_mode(context: ExecutionContext) -> str:
    mode = (context.browser_mode or os.getenv("URI3_BROWSER_ADAPTER", "auto")).lower()
    if mode == "mock":
        return "mock"
    if mode == "playwright":
        return "playwright"
    return "playwright" if _uri2ops_playwright_ready() else "mock"


class BrowserRouterAdapter:
    """Deprecated: uri3 delegates operator schemes to uri2ops (see Uri2OpsAdapter)."""

    schemes = frozenset({"browser", "dom", "screen"})

    def __init__(self) -> None:
        self._mock = BrowserMockAdapter()
        self._playwright = PlaywrightBrowserAdapter()

    def execute(self, node: GraphNode, context: ExecutionContext) -> dict[str, Any]:
        warnings.warn(
            "BrowserRouterAdapter is deprecated; operator schemes delegate to uri2ops",
            DeprecationWarning,
            stacklevel=2,
        )
        mode = resolve_browser_mode(context)
        if mode == "playwright":
            return self._playwright.execute(node, context)
        return self._mock.execute(node, context)


def cleanup_browser_adapters(context: ExecutionContext) -> None:
    if context.adapter_state.get("playwright"):
        close_playwright_session(context)
