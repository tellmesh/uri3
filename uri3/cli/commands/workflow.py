from __future__ import annotations

import json

import typer

from uri3.graph import (
    build_execution_plan,
    load_workflow_graph,
    run_workflow,
    validate_workflow_graph,
)


def register(app: typer.Typer) -> None:
    @app.command("validate-workflow")
    def validate_workflow(path: str) -> None:
        errors = validate_workflow_graph(path)
        if errors:
            for error in errors:
                typer.echo(error)
            raise typer.Exit(1)
        typer.echo("OK")

    @app.command("plan-workflow")
    def plan_workflow(path: str) -> None:
        payload = build_execution_plan(load_workflow_graph(path))
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))

    @app.command("run-workflow")
    def run_workflow_cmd(
        path: str,
        dry_run: bool = typer.Option(False, "--dry-run", help="Simulate all steps without policy blocks"),
        approve: bool = typer.Option(False, "--approve", help="Allow command nodes with side effects"),
        browser: str = typer.Option("auto", "--browser", help="Browser adapter: auto, mock, playwright"),
    ) -> None:
        result = run_workflow(
            load_workflow_graph(path),
            approve=approve,
            dry_run=dry_run,
            browser_mode=browser,
        )
        typer.echo(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        if not result.ok:
            raise typer.Exit(1)
