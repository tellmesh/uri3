from __future__ import annotations

EXECUTION_COMPLETED = "completed"
EXECUTION_FAILED = "failed"
SERVICE_SUCCEEDED = "succeeded"
SERVICE_FAILED = "failed"
WORKFLOW_COMPLETED = "completed"
WORKFLOW_COMPLETED_WITH_SERVICE_ERROR = "completed_with_service_error"
WORKFLOW_FAILED = "failed"


def derive_statuses(ok: bool, *, execution_completed: bool = True) -> tuple[str, str, str]:
    execution_status = EXECUTION_COMPLETED if execution_completed else EXECUTION_FAILED
    service_result_status = SERVICE_SUCCEEDED if ok else SERVICE_FAILED
    if ok:
        workflow_status = WORKFLOW_COMPLETED
    elif execution_completed:
        workflow_status = WORKFLOW_COMPLETED_WITH_SERVICE_ERROR
    else:
        workflow_status = WORKFLOW_FAILED
    return workflow_status, execution_status, service_result_status
