from __future__ import annotations

from pathlib import Path

from uri3.resolvers.explain import explain_uri
from uri3.routing import UriKind, explain_semantic_uri, normalize_route


def test_browser_alias_normalizes_to_tellmesh_command(repo_root: Path):
    route = normalize_route("browser://open?url=https://example.com", root=repo_root)

    assert route.canonical_uri == "tellmesh://operators/browser/command/open"
    assert route.domain == "operators/browser"
    assert route.kind == UriKind.command
    assert route.action == "open"
    assert route.query == {"url": "https://example.com"}


def test_browser_registry_uri_explains_contract_and_policy(repo_root: Path):
    resolution = explain_semantic_uri("browser://chrome/page/open", root=repo_root)

    assert resolution.route.canonical_uri == "tellmesh://operators/browser/command/open"
    assert resolution.contract_uri == "contract://operator/browser/v1/BrowserPageOpenCommand"
    assert resolution.policy_uri == "policy://operators/browser/open"
    assert resolution.side_effects is True
    assert resolution.requires_approval is True


def test_explain_uri_exposes_semantic_route(repo_root: Path):
    payload = explain_uri("browser://chrome/page/open", root=repo_root)

    assert payload["canonical_uri"] == "tellmesh://operators/browser/command/open"
    assert payload["semantic_route"]["domain"] == "operators/browser"
    assert payload["semantic_route"]["action"] == "open"
