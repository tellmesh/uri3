from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from uri3.protocols.schemes.base import SchemeSpec
from uri3.protocols.schemes.constants import SUPPORTED_SCHEMES
from uri3.protocols.schemes import a2a, docker, env, http, llm, log, mcp, python, pypi, resource_like


def build_scheme_registry() -> dict[str, SchemeSpec]:
    specs = [
        log.spec(),
        env.spec(),
        python.spec(),
        llm.spec(),
        pypi.spec(),
        http.spec("http"),
        http.spec("https"),
        a2a.spec(),
        mcp.spec(),
        resource_like.resource_like_spec("resource", "Generic in-repo or logical resource reference."),
        resource_like.resource_like_spec("artifact", "Build or generation artifact reference."),
        resource_like.resource_like_spec("domain", "Domain pack or bounded context reference."),
        resource_like.resource_like_spec("agent", "Generated or deployed agent reference."),
        resource_like.resource_like_spec("local", "Local filesystem resource reference."),
        resource_like.resource_like_spec("input", "Pipeline input reference."),
        resource_like.resource_like_spec("command", "Command or action reference."),
        resource_like.resource_like_spec("event", "Event source or channel reference."),
        resource_like.resource_like_spec("ssh", "Remote host path accessed over SSH."),
        docker.spec(),
        resource_like.resource_like_spec("git", "Git repository reference."),
        resource_like.resource_like_spec("browser", "Browser automation target (page, tab, screenshot)."),
        resource_like.resource_like_spec("dom", "DOM fragment or active page content."),
        resource_like.resource_like_spec("screen", "Screen or viewport capture target."),
        resource_like.resource_like_spec("assertion", "Verification/assertion step in a workflow graph."),
        resource_like.resource_like_spec("hypervisor", "Hypervisor deployment or lifecycle operation."),
    ]
    return {spec.scheme: spec for spec in specs}


SCHEME_REGISTRY: dict[str, SchemeSpec] = build_scheme_registry()


def is_concrete_uri(value: str) -> bool:
    if "://" not in value:
        return False
    parsed = urlparse(value)
    return bool(parsed.netloc or parsed.path.strip("/") or parsed.query)


def get_scheme_schema(scheme_or_uri: str) -> dict[str, Any]:
    from uri3.protocols.schemes.instance_parser import normalize_scheme

    scheme = normalize_scheme(scheme_or_uri)
    if scheme not in SUPPORTED_SCHEMES:
        raise ValueError(f"Unsupported URI scheme: {scheme}")
    spec = SCHEME_REGISTRY.get(scheme)
    if spec is None:
        spec = resource_like.resource_like_spec(scheme, f"Supported scheme `{scheme}` without detailed schema yet.")
    return spec.to_dict()


def list_schemes(*, documented_only: bool = False) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for scheme in sorted(SUPPORTED_SCHEMES):
        spec = SCHEME_REGISTRY.get(scheme)
        if spec is None:
            items.append(
                {
                    "scheme": scheme,
                    "supported": True,
                    "documented": False,
                    "description": f"Supported scheme `{scheme}` without detailed schema yet.",
                    "template": f"{scheme}://{{target}}",
                }
            )
            continue
        if documented_only and not spec.documented:
            continue
        items.append(
            {
                "scheme": spec.scheme,
                "supported": True,
                "documented": spec.documented,
                "description": spec.description,
                "template": spec.template,
                "actions": list(spec.actions),
            }
        )
    return items


def query_names(spec: SchemeSpec) -> set[str]:
    names: set[str] = set()
    for option in spec.query:
        names.add(option.name)
        names.update(option.aliases)
    return names
