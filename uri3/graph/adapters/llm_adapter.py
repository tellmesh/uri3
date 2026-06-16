from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from uri3.graph.execution_models import ExecutionContext
from uri3.graph.models import GraphNode
from uri3.graph.payload_context import extract_transcript, resolve_step_payload
from uri3.llm.decide import decide
from uri3.llm.plan import plan


class LlmAdapter:
    """Execute llm:// query steps (text/decide, future: text/plan)."""

    schemes = frozenset({"llm"})

    def execute(self, node: GraphNode, context: ExecutionContext) -> dict[str, Any]:
        payload = resolve_step_payload(node.payload, context)
        path = urlparse(node.uri).path.rstrip("/")
        operation = (node.operation or "").lower()

        if path.endswith("/text/query/decide") or operation == "decide":
            return self._decide(node, context, payload)

        if path.endswith("/text/query/plan") or operation == "plan":
            return self._plan(node, context, payload)

        if path.endswith("/vision/query/analyze") or operation in {"analyze", "llm.vision.analyze"}:
            return {
                "ok": True,
                "mock": True,
                "uri": node.uri,
                "message": "vision/analyze is executed by urirdp runtime; workflow adapter returns plan-only mock",
            }

        return {"ok": False, "error": f"unsupported llm workflow operation: {node.uri}"}

    def _decide(self, node: GraphNode, context: ExecutionContext, payload: dict[str, Any]) -> dict[str, Any]:
        question = str(payload.get("question") or "")
        context_value = payload.get("context")
        expect = str(payload.get("expect") or "boolean")
        driver = str(payload.get("driver") or ("mock" if context.dry_run else "mock"))
        model = payload.get("model")
        if not question:
            return {"ok": False, "error": "payload.question is required for llm decide"}

        result = decide(
            question=question,
            context_value=context_value,
            expect=expect,
            model=str(model) if model else None,
            driver=driver,
            dry_run=context.dry_run,
        )
        return {"ok": bool(result.get("ok")), **result}

    def _plan(self, node: GraphNode, context: ExecutionContext, payload: dict[str, Any]) -> dict[str, Any]:
        transcript = extract_transcript(payload.get("transcript"))
        if not transcript and payload.get("context") is not None:
            transcript = extract_transcript(payload.get("context"))
        allowed = payload.get("allowed_schemes")
        schemes = list(allowed) if isinstance(allowed, list) else None
        driver = str(payload.get("driver") or ("mock" if context.dry_run else "mock"))
        if not transcript:
            return {"ok": False, "error": "payload.transcript or transcript_from is required for llm plan"}
        result = plan(
            transcript=transcript,
            allowed_schemes=schemes,
            driver=driver,
            dry_run=context.dry_run,
        )
        return {"ok": bool(result.get("ok")), **result}
