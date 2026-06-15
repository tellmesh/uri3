"""Tests for hypervisor lifecycle ServiceResult envelope."""

from __future__ import annotations

from uri3.results import enrich_lifecycle_dict


def test_lifecycle_plan_payload_has_status_envelope():
    payload = enrich_lifecycle_dict(
        {
            "command_string": "uvicorn weather.main:app",
            "module": "weather.main",
            "port": 8101,
        }
    )
    assert payload["ok"] is True
    assert payload["workflow_status"] == "completed"
    assert payload["execution_status"] == "completed"
    assert payload["service_result_status"] == "succeeded"
    assert payload["result_type"] == "lifecycle"


def test_lifecycle_stopped_payload_has_status_envelope():
    payload = enrich_lifecycle_dict(
        {
            "id": "weather-map-agent.local",
            "status": "stopped",
            "message": "No runtime state found",
        }
    )
    assert payload["ok"] is True
    assert payload["service_result_status"] == "succeeded"
