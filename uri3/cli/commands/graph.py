from __future__ import annotations

import json

import typer

from uri3.graph import build_graph_from_tree


def register(app: typer.Typer) -> None:
    @app.command()
    def graph(path: str) -> None:
        graph_obj = build_graph_from_tree(path)
        typer.echo(
            json.dumps(
                {
                    "nodes": [node.__dict__ for node in graph_obj.nodes.values()],
                    "edges": [edge.__dict__ for edge in graph_obj.edges],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
