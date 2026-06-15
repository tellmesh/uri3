"""Tests for shared ServiceResult envelope."""

from uri3.results import ServiceResult, service_result


def test_service_result_finalize_sets_three_status_levels():
    result = service_result(
        ok=False,
        result_type="error",
        errors=[{"code": "PRICE_RESULT_NOT_RELEVANT", "recoverable": True}],
    )
    payload = result.to_dict()
    assert payload["ok"] is False
    assert payload["workflow_status"] == "completed_with_service_error"
    assert payload["execution_status"] == "completed"
    assert payload["service_result_status"] == "failed"
    assert payload["errors"][0]["code"] == "PRICE_RESULT_NOT_RELEVANT"


def test_error_envelope_normalizes_legacy_detail():
    result = ServiceResult(ok=False, result_type="error", errors=[{"detail": "legacy message"}])
    payload = result.finalize().to_dict()
    assert payload["errors"][0]["code"] == "UNKNOWN"
    assert payload["errors"][0]["detail"] == "legacy message"


def test_success_service_result():
    result = service_result(ok=True, result_type="artifact", data={"place": "Gdansk"})
    payload = result.to_dict()
    assert payload["service_result_status"] == "succeeded"
    assert payload["workflow_status"] == "completed"
