from __future__ import annotations

import json

import typer

from uri3.cli.helpers import list_payload, quick_reference
from uri3.config.cli_shortcuts import resolve_scan_target, scan_shortcuts
from uri3.logs.reader import read_logs_result, summarize_logs
from uri3.protocols.scheme_registry import analyze_uri, describe_uri, list_schemes
from uri3.scanner.scanner import scan as scan_uri


def register(app: typer.Typer) -> None:
    @app.command()
    def list_cmd(
        schemes: bool = typer.Option(False, "--schemes", help="Show only URI schemes"),
        json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    ) -> None:
        """List schemes, scan shortcuts, and common examples."""
        payload = list_payload(schemes_only=schemes)
        if json_out:
            typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
            return
        if schemes:
            for item in payload["schemes"]:
                typer.echo(f"{item['scheme']:<10} {item.get('summary', '')}")
            return
        typer.echo(quick_reference())

    app.command("list", help="List schemes, scan shortcuts, and common examples")(list_cmd)

    @app.command()
    def scan(
        target: str = typer.Argument("", help="Shortcut name (http, ssh, docker) or full URI"),
        all_shortcuts: bool = typer.Option(False, "--all", help="Run all configured scan shortcuts"),
    ) -> None:
        if all_shortcuts:
            shortcuts = scan_shortcuts()
            if not shortcuts:
                typer.echo("No scan shortcuts configured. Edit config/uri3.uri.yaml")
                raise typer.Exit(1)
            payload = {name: [item.__dict__ for item in scan_uri(uri)] for name, uri in shortcuts.items()}
            typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
            return
        if not target:
            typer.echo(quick_reference())
            typer.echo("\nTip: run `uri3 scan http` or `uri3 scan --all`")
            raise typer.Exit(1)
        try:
            uri = resolve_scan_target(target)
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(1) from exc
        typer.echo(json.dumps([item.__dict__ for item in scan_uri(uri)], indent=2, ensure_ascii=False))

    @app.command()
    def logs(
        uri: str,
        summary: bool = typer.Option(False, "--summary", help="Return aggregate counts instead of entries"),
    ) -> None:
        """Read and filter logs via log:// URI."""
        payload = summarize_logs(uri) if summary else read_logs_result(uri)
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))

    @app.command()
    def schema(
        target: str = typer.Argument("", help="Scheme (log://) or concrete URI to analyze"),
        list_all: bool = typer.Option(False, "--list", "-l", help="List supported schemes"),
        analyze: bool = typer.Option(False, "--analyze", help="Force full URI analysis"),
    ) -> None:
        """Describe URI format, options, and API for a scheme or concrete URI."""
        if list_all or not target:
            payload = {"schemes": list_schemes()}
        elif analyze:
            payload = analyze_uri(target)
        else:
            payload = describe_uri(target)
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
