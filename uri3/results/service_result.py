from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import ErrorEnvelope, normalize_error
from .statuses import derive_statuses


@dataclass
class ServiceResult:
    ok: bool
    result_type: str = "data"
    workflow_status: str | None = None
    execution_status: str | None = None
    service_result_status: str | None = None
    uri: str | None = None
    capability: str | None = None
    backend: str | None = None
    data: Any = None
    artifact_uri: str | None = None
    errors: list[ErrorEnvelope] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def finalize(
        self,
        *,
        execution_completed: bool = True,
        refresh_statuses: bool = False,
    ) -> ServiceResult:
        if (
            refresh_statuses
            or self.workflow_status is None
            or self.execution_status is None
            or self.service_result_status is None
        ):
            workflow_status, execution_status, service_result_status = derive_statuses(
                self.ok,
                execution_completed=execution_completed,
            )
            if refresh_statuses or self.workflow_status is None:
                self.workflow_status = workflow_status
            if refresh_statuses or self.execution_status is None:
                self.execution_status = execution_status
            if refresh_statuses or self.service_result_status is None:
                self.service_result_status = service_result_status
        self.errors = [
            normalize_error(item, default_source=self._default_error_source())
            for item in self.errors
        ]
        return self

    def _default_error_source(self) -> str:
        if self.capability:
            return f"touri://capability/{self.capability}"
        if self.uri:
            return self.uri
        return ""

    def to_dict(self) -> dict[str, Any]:
        finalized = self.finalize()
        payload: dict[str, Any] = {
            "ok": finalized.ok,
            "workflow_status": finalized.workflow_status,
            "execution_status": finalized.execution_status,
            "service_result_status": finalized.service_result_status,
            "result_type": finalized.result_type,
        }
        if finalized.uri:
            payload["uri"] = finalized.uri
        if finalized.capability:
            payload["capability"] = finalized.capability
        if finalized.backend:
            payload["backend"] = finalized.backend
        if finalized.data is not None:
            payload["data"] = finalized.data
        if finalized.artifact_uri:
            payload["artifact_uri"] = finalized.artifact_uri
        if finalized.errors:
            payload["errors"] = [error.to_dict() for error in finalized.errors]
        if finalized.warnings:
            payload["warnings"] = finalized.warnings
        if finalized.meta:
            payload["meta"] = finalized.meta
        return payload


def service_result(ok: bool, result_type: str = "data", **kwargs: Any) -> ServiceResult:
    errors = kwargs.pop("errors", [])
    warnings = kwargs.pop("warnings", [])
    execution_completed = bool(kwargs.pop("execution_completed", True))
    has_explicit_status = any(
        kwargs.get(key) is not None
        for key in ("workflow_status", "execution_status", "service_result_status")
    )
    result = ServiceResult(ok=ok, result_type=result_type, warnings=list(warnings), **kwargs)
    result.errors = [normalize_error(item) for item in errors]
    return result.finalize(
        execution_completed=execution_completed,
        refresh_statuses=not has_explicit_status,
    )
