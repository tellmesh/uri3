from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class ExecutionContext:
    workflow_id: str
    run_id: str
    root: Path
    approve_commands: bool = False
    dry_run: bool = False
    browser_mode: str = "auto"
    step_outputs: dict[str, dict[str, Any]] = field(default_factory=dict)
    adapter_state: dict[str, Any] = field(default_factory=dict)

    def resolve_ref(self, ref: str) -> Any:
        if "." not in ref:
            return self.step_outputs.get(ref)
        step_id, field_name = ref.split(".", 1)
        payload = self.step_outputs.get(step_id, {})
        return payload.get(field_name)


@dataclass
class StepExecutionResult:
    id: str
    uri: str
    operation: str
    kind: str
    status: str
    ok: bool
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    artifact_uri: str | None = None

    def to_dict(self) -> dict[str, Any]:
        from uri3.results.envelope import enrich_step_dict

        payload: dict[str, Any] = {
            "id": self.id,
            "uri": self.uri,
            "operation": self.operation,
            "kind": self.kind,
            "status": self.status,
            "ok": self.ok,
        }
        if self.result:
            payload["result"] = self.result
        if self.error:
            payload["error"] = self.error
        if self.artifact_uri:
            payload["artifact_uri"] = self.artifact_uri
        return enrich_step_dict(payload)


@dataclass
class GraphExecutionPlan:
    graph_id: str
    kind: str
    order: list[str]
    steps: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "kind": self.kind,
            "order": self.order,
            "steps": self.steps,
        }


@dataclass
class GraphExecutionResult:
    id: str
    ok: bool
    started_at: str
    completed_at: str | None
    mode: str
    run_id: str | None = None
    steps: list[StepExecutionResult] = field(default_factory=list)
    pending_approval: list[str] = field(default_factory=list)
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        from uri3.results.envelope import enrich_workflow_dict

        return enrich_workflow_dict(
            {
                "workflow_result": {
                    "id": self.id,
                    **({"run_id": self.run_id} if self.run_id else {}),
                    "ok": self.ok,
                    "started_at": self.started_at,
                    "completed_at": self.completed_at,
                    "mode": self.mode,
                    **({"message": self.message} if self.message else {}),
                    **(
                        {"pending_approval": self.pending_approval}
                        if self.pending_approval
                        else {}
                    ),
                },
                "steps": [step.to_dict() for step in self.steps],
            },
            dry_run=self.mode == "dry_run",
        )


def new_execution_context(
    workflow_id: str,
    *,
    root: Path | None = None,
    approve_commands: bool = False,
    dry_run: bool = False,
    browser_mode: str = "auto",
) -> ExecutionContext:
    from uri3.config.repo_root import find_repo_root

    return ExecutionContext(
        workflow_id=workflow_id,
        run_id=uuid4().hex[:12],
        root=root or find_repo_root(),
        approve_commands=approve_commands,
        dry_run=dry_run,
        browser_mode=browser_mode,
    )
