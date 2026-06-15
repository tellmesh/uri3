from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from uri2flow import expand_flow
from uri2flow.expander import dump_yaml
from uri3.graph import (
    build_execution_plan,
    dry_run_workflow,
    load_workflow_graph,
    run_workflow,
    validate_workflow_graph,
)


def expand_flow_cmd(
    path: str,
    *,
    out: str = "",
    json_out: bool = False,
) -> None:
    """Expand compact *.uri.flow.yaml to workflow_graph via uri2flow."""
    graph = expand_flow(path)
    rendered = json.dumps(graph, indent=2, ensure_ascii=False) if json_out else dump_yaml(graph)
    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        typer.echo(str(out_path))
        return
    typer.echo(rendered)


def run_flow_cmd(
    path: str,
    *,
    dry_run: bool = False,
    approve: bool = False,
    browser: str = "auto",
    out: str = "",
    json_out: bool = False,
) -> None:
    """Expand compact flow then validate/plan/run workflow (delegates to uri2flow + uri3)."""
    graph = expand_flow(path)
    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(dump_yaml(graph), encoding="utf-8")

    errors = validate_workflow_graph(graph)
    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(1)

    if dry_run:
        payload: dict[str, Any] = {
            "phase": "dry_run",
            "flow": str(path),
            "plan": build_execution_plan(load_workflow_graph(graph)),
            "simulation": dry_run_workflow(graph),
        }
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    result = run_workflow(
        load_workflow_graph(graph),
        approve=approve,
        dry_run=False,
        browser_mode=browser,
    )
    payload = result.to_dict()
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    if not result.ok:
        raise typer.Exit(1)


def register(app: typer.Typer) -> None:
    @app.command("expand-flow")
    def expand_flow_command(
        path: str,
        out: str = typer.Option("", "--out", help="Write expanded workflow graph YAML"),
        json_out: bool = typer.Option(False, "--json", help="Output JSON instead of YAML"),
    ) -> None:
        expand_flow_cmd(path, out=out, json_out=json_out)

    @app.command("run-flow")
    def run_flow_command(
        path: str,
        dry_run: bool = typer.Option(False, "--dry-run", help="Expand and build execution plan only"),
        approve: bool = typer.Option(False, "--approve", help="Allow command nodes with side effects"),
        browser: str = typer.Option("auto", "--browser", help="Browser adapter: auto, mock, playwright"),
        out: str = typer.Option("", "--out", help="Optional path to write expanded graph YAML"),
        json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    ) -> None:
        run_flow_cmd(path, dry_run=dry_run, approve=approve, browser=browser, out=out, json_out=json_out)
