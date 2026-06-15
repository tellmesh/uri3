from __future__ import annotations

import typer

from uri3.cli.commands import discovery, doctor, explain, flow, graph, replay, resolve, workflow
from uri3.cli.helpers import quick_reference

app = typer.Typer(
    help="uri3: URI discovery, graph, validation and routing",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(quick_reference())
        raise typer.Exit(0)


discovery.register(app)
doctor.register(app)
explain.register(app)
resolve.register(app)
graph.register(app)
workflow.register(app)
flow.register(app)
replay.register(app)


def main_entry() -> None:
    app()
