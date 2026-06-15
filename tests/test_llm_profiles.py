"""Tests for LLM profile loader."""

from __future__ import annotations

import os

import pytest

from uri3.config.llm_profiles import load_llm_config, resolve_llm_profile


def test_load_llm_config_has_domain_planner():
    data = load_llm_config()
    assert "domain_planner" in data["profiles"]
    assert data["profiles"]["domain_planner"]["model"].startswith("llm://")


def test_resolve_llm_profile_domain_planner(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    profile = resolve_llm_profile("domain_planner")
    assert profile.name == "domain_planner"
    assert profile.model_uri.startswith("llm://openrouter/")
    assert profile.api_key == "test-key"
    assert profile.max_tokens == 12000
    assert profile.response_format == "json"


def test_resolve_llm_profile_respects_default_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DEFAULT_LLM_PROFILE", "repair")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    profile = resolve_llm_profile()
    assert profile.name == "repair"
    assert profile.temperature == 0.0
