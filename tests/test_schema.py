"""Tests for uri3 scheme schema introspection."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from uri3.cli import app
from uri3.protocols.scheme_registry import (
    analyze_uri,
    describe_uri,
    get_scheme_schema,
    list_schemes,
    normalize_scheme,
)


def test_normalize_scheme():
    assert normalize_scheme("log://") == "log"
    assert normalize_scheme("log") == "log"
    assert normalize_scheme("log://hypervisor?level=ERROR") == "log"


def test_get_scheme_schema_log():
    schema = get_scheme_schema("log://")
    assert schema["scheme"] == "log"
    assert schema["documented"] is True
    assert schema["format"]["netloc"]["default"] == "hypervisor"
    assert "level" in {item["name"] for item in schema["format"]["query"]}
    assert "ERROR" in schema["constants"]["levels"]
    assert "uri3 logs" in schema["api"]["cli"]


def test_get_scheme_schema_unknown():
    with pytest.raises(ValueError, match="Unsupported URI scheme"):
        get_scheme_schema("unknown://")


def test_list_schemes_includes_log():
    schemes = list_schemes()
    assert any(item["scheme"] == "log" for item in schemes)
    assert any(item["scheme"] == "ssh" for item in schemes)


def test_analyze_concrete_log_uri():
    result = analyze_uri("log://hypervisor?level=ERROR&grep=deployment&limit=20")
    assert result["valid"] is True
    assert result["parsed"]["stream"] == "hypervisor"
    assert result["parsed"]["level"] == "ERROR"
    assert result["query"]["used"] == ["grep", "level", "limit"]
    assert "logger" in result["query"]["available"]
    assert result["schema"]["scheme"] == "log"


def test_analyze_invalid_log_uri():
    result = analyze_uri("log://file/")
    assert result["valid"] is False
    assert result["errors"]


def test_describe_scheme_only():
    schema = describe_uri("log://")
    assert schema["scheme"] == "log"
    assert "template" in schema


def test_describe_concrete_uri():
    result = describe_uri("log://hypervisor?level=WARNING")
    assert result["scheme"] == "log"
    assert result["parsed"]["level"] == "WARNING"


def test_cli_schema_log_scheme():
    runner = CliRunner()
    result = runner.invoke(app, ["schema", "log://"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["scheme"] == "log"
    assert payload["format"]["query"]


def test_cli_schema_list():
    runner = CliRunner()
    result = runner.invoke(app, ["schema", "--list"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "log" in {item["scheme"] for item in payload["schemes"]}


def test_cli_schema_analyze():
    runner = CliRunner()
    result = runner.invoke(app, ["schema", "log://hypervisor?level=ERROR", "--analyze"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["parsed"]["level"] == "ERROR"
