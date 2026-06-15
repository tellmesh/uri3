"""Tests for uri3 explain URI resolution."""

from __future__ import annotations

from pathlib import Path

from uri3.resolvers.explain import explain_uri


def test_explain_weather_uri_matches_touri(repo_root: Path):
    payload = explain_uri("weather://forecast/Gdansk/14/html", root=repo_root)
    assert payload["matched_registry"] == "touri"
    assert payload["capability"] == "weather.forecast.html"
    assert payload["backend"]["type"] == "python"
    assert payload["params"] == {"place": "Gdansk", "days": "14"}


def test_explain_http_uri_matches_uri3(repo_root: Path):
    payload = explain_uri("http://localhost:8101/health", root=repo_root)
    assert payload["matched_registry"] == "uri3"
    assert payload["scheme"] == "http"


def test_explain_file_uri_matches_uri3(tmp_path: Path, repo_root: Path):
    source = tmp_path / "source.md"
    source.write_text("# Source\n", encoding="utf-8")
    payload = explain_uri(f"file://{source.as_posix()}", root=repo_root)
    assert payload["matched_registry"] == "uri3"
    assert payload["scheme"] == "file"


def test_explain_browser_uri_matches_uri2ops(repo_root: Path):
    payload = explain_uri("browser://chrome/page/open", root=repo_root)
    assert payload["matched_registry"] == "uri2ops"
    assert "open" in payload["operations"]


def test_explain_unknown_scheme_denied(repo_root: Path):
    payload = explain_uri("unknown://resource/action", root=repo_root)
    assert payload["matched_registry"] is None
    assert payload["resolution"] == "denied"
