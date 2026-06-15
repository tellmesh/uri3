from __future__ import annotations

import json

import typer

from uri3.resolvers.explain import explain_uri


def register(app: typer.Typer) -> None:
    @app.command()
    def explain(
        uri: str,
        registry: str = typer.Option("", "--registry", help="touri capability registry directory"),
        json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    ) -> None:
        """Show which registry resolves a URI and how it would be executed."""
        payload = explain_uri(uri, registry_root=registry or None)
        if json_out:
            typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            typer.echo(_render(payload))


def _header_lines(payload: dict) -> list[str]:
    return [
        f"uri: {payload.get('uri')}",
        (
            "matched_registry: "
            f"{payload.get('matched_registry') or payload.get('resolution', 'unknown')}"
        ),
    ]


def _backend_line(payload: dict) -> list[str]:
    if not payload.get("backend"):
        return []
    backend = payload["backend"]
    target = backend.get("target") or backend.get("command") or backend.get("url") or "-"
    return [f"backend: {backend.get('type')} -> {target}"]


def _json_field_lines(payload: dict, key: str, label: str) -> list[str]:
    if not payload.get(key):
        return []
    return [f"{label}: {json.dumps(payload[key], ensure_ascii=False)}"]


def _verification_lines(payload: dict) -> list[str]:
    if not payload.get("verification"):
        return []
    verification = payload["verification"]
    lines = [
        "verification: "
        f"data_quality={verification.get('data_quality_enabled')} "
        f"fallbacks={verification.get('fallback_count', 0)}"
    ]
    if verification.get("data_quality"):
        lines.append(f"  failure_code: {verification['data_quality'].get('failure_code')}")
    for item in verification.get("fallbacks") or []:
        lines.append(f"  - when={item.get('when')} backend={item.get('backend_type')}")
    return lines


def _checks_lines(payload: dict) -> list[str]:
    if not payload.get("checks"):
        return []
    lines = ["checks:"]
    lines.extend(f"  - {check['registry']}: matched={check.get('matched')}" for check in payload["checks"])
    return lines


def _render(payload: dict) -> str:
    lines = _header_lines(payload)
    if payload.get("capability"):
        lines.append(f"capability: {payload['capability']}")
    lines.extend(_backend_line(payload))
    lines.extend(_json_field_lines(payload, "policy", "policy"))
    lines.extend(_json_field_lines(payload, "data_quality", "data_quality"))
    lines.extend(_json_field_lines(payload, "fallbacks", "fallbacks"))
    lines.extend(_verification_lines(payload))
    if payload.get("runtime_transport"):
        lines.append(f"runtime_transport: {payload['runtime_transport']}")
    if payload.get("operations"):
        lines.append(f"uri2ops operations: {', '.join(payload['operations'])}")
    lines.extend(_checks_lines(payload))
    return "\n".join(lines)
