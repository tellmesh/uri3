from __future__ import annotations

import json

import typer

from uri2verify.replay import create_regression_test, replay_workflow_events


def register(app: typer.Typer) -> None:
    @app.command()
    def replay(
        source: str,
        json_out: bool = typer.Option(False, "--json", help="Output JSON"),
        timeline: bool = typer.Option(False, "--timeline", help="Include full event timeline"),
        create_test: str = typer.Option("", "--create-test", help="Write pytest regression file to this path"),
    ) -> None:
        """Summarize a workflow JSONL event log for debugging and regression replay."""
        if create_test:
            payload = create_regression_test(source, out=create_test)
            typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
            return
        payload = replay_workflow_events(source)
        if not timeline:
            payload = {key: value for key, value in payload.items() if key != "timeline"}
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False) if json_out else _render(payload))


def _render(payload: dict) -> str:
    lines = [
        f"workflow_id: {payload.get('workflow_id')}",
        f"event_log: {payload.get('event_log')}",
        f"event_count: {payload.get('event_count')}",
    ]
    completed = payload.get("workflow_completed") or {}
    if completed:
        lines.append(f"workflow_completed: ok={completed.get('ok')} mode={completed.get('mode')}")
    failed = payload.get("failed_steps") or []
    blocked = payload.get("blocked_steps") or []
    lines.append(f"failed_steps: {len(failed)}")
    for event in failed:
        lines.append(f"  - {event.get('step_id')}: {event.get('error') or event}")
    lines.append(f"blocked_steps: {len(blocked)}")
    for event in blocked:
        lines.append(f"  - {event.get('step_id')}: {event.get('reason') or event}")
    return "\n".join(lines)
