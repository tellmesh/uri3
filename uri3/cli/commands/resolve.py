from __future__ import annotations

import json

import typer

from uri3.resolvers.router import Uri3Router
from uri3.validators.uri_tree_validator import validate_uri_tree
from uri3.validators.uri_validator import validate_uri


def register(app: typer.Typer) -> None:
    @app.command()
    def validate(uri: str) -> None:
        validate_uri(uri)
        typer.echo("OK")

    @app.command("validate-tree")
    def validate_tree(path: str) -> None:
        errors = validate_uri_tree(path)
        if errors:
            for error in errors:
                typer.echo(error)
            raise typer.Exit(1)
        typer.echo("OK")

    @app.command()
    def resolve(uri: str) -> None:
        result = Uri3Router().resolve(uri)
        typer.echo(json.dumps(result if isinstance(result, dict) else getattr(result, "__dict__", str(result)), indent=2, ensure_ascii=False))

    @app.command()
    def call(uri: str) -> None:
        """Execute a callable URI action (docker://, python://, log://)."""
        result = Uri3Router().call(uri)
        typer.echo(json.dumps(result if isinstance(result, dict) else getattr(result, "__dict__", str(result)), indent=2, ensure_ascii=False))
