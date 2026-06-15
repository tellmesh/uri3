from __future__ import annotations

import json

import typer

from uri3.doctor.runner import run_doctor


def register(app: typer.Typer) -> None:
    @app.command()
    def doctor(
        registry: str = typer.Option("", "--registry", help="touri capability registry directory"),
        json_out: bool = typer.Option(False, "--json", help="Output JSON"),
        capability_plan: bool = typer.Option(False, "--capability-plan", help="Include uri2verify capability test plan check"),
        replay_failures: bool = typer.Option(False, "--replay-failures", help="Scan workflow logs for failed/blocked steps"),
        build_registry: bool = typer.Option(False, "--build-registry", help="Write .registry/ indexes"),
        strict_envelope: bool = typer.Option(False, "--strict-envelope", help="Fail when legacy workflow logs lack status fields"),
        migrate_envelope: bool = typer.Option(False, "--migrate-envelope", help="Backfill status fields in legacy workflow JSONL logs"),
    ) -> None:
        """Validate config, registries, explain resolution, and envelope consistency."""
        payload = run_doctor(
            registry=registry or None,
            capability_plan=capability_plan,
            replay_failures=replay_failures,
            build_registry=build_registry,
            strict_envelope=strict_envelope,
            migrate_envelope=migrate_envelope,
        )
        if json_out:
            typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            typer.echo(_render(payload))
        if not payload.get("ok"):
            raise typer.Exit(code=1)


def _render(payload: dict) -> str:
    lines = [f"doctor: {'ok' if payload.get('ok') else 'FAILED'}", f"registry: {payload.get('registry')}"]
    for check in payload.get("checks") or []:
        status = "ok" if check.get("ok") else "FAIL"
        detail = _check_summary(check)
        lines.append(f"  [{status}] {check.get('id')}{detail}")
    index = payload.get("registry_index") or {}
    if index:
        lines.append(f"registry_index: {index.get('directory')}")
        for path in index.get("files") or []:
            lines.append(f"  - {path}")
    warnings = payload.get("warnings") or []
    if warnings:
        lines.append("warnings:")
        for warning in warnings[:10]:
            lines.append(f"  - {warning}")
        if len(warnings) > 10:
            lines.append(f"  ... and {len(warnings) - 10} more")
    return "\n".join(lines)


_CHECK_SUMMARY_FORMATTERS: dict[str, Any] = {
    "touri.registry": lambda check: f" ({check.get('manifests', 0)} manifests)",
    "uri2ops.registry": lambda check: f" ({check.get('operations', 0)} operations)",
    "contract_registry": lambda check: (
        f" (capabilities={(check.get('counts') or {}).get('capabilities', 0)})"
    ),
    "explain.smoke": lambda check: (
        f" ({check.get('checked', 0)} checked, {len(check.get('mismatches') or [])} mismatches)"
    ),
    "envelope.recent_logs": lambda check: (
        f" ({check.get('logs', 0)} logs, {check.get('missing_fields', 0)} missing fields)"
    ),
    "uri2verify.capability_plan": lambda check: f" ({check.get('tests', 0)} tests)",
    "uri2verify.replay_failures": lambda check: (
        f" ({len(check.get('failures') or [])} failing workflows)"
    ),
    "boundaries.imports": lambda check: f" ({check.get('violation_count', 0)} violations)",
    "runtime.uri2run_transports": lambda check: (
        f" ({len(check.get('checked') or [])} transports, {len(check.get('failures') or [])} failures)"
    ),
    "runtime.browser_delegation": lambda check: f" (adapter={check.get('adapter')})",
}


def _check_summary(check: dict) -> str:
    formatter = _CHECK_SUMMARY_FORMATTERS.get(str(check.get("id") or ""))
    return formatter(check) if formatter else ""
