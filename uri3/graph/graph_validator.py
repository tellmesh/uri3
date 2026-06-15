from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from uri3.config.repo_root import find_repo_root
from uri3.graph.dependency_graph import detect_cycles, topological_sort
from uri3.graph.graph_serializer import normalize_graph_payload
from uri3.graph.models import WorkflowGraph
from uri3.validators.uri_validator import validate_uri


def _schema_path(name: str) -> Path:
    return find_repo_root() / "schemas" / name


def _resolve_graph_source_path(source: str | Path) -> Path:
    if isinstance(source, str) and source.startswith("file://"):
        from urllib.parse import unquote
        p = source[7:]
        if p.startswith("/") and len(p) > 2 and p[2] == ":":
            p = p[1:]
        return Path(unquote(p))
    return Path(source)


def _load_graph_data(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        import yaml
        return yaml.safe_load(raw)
    return json.loads(raw)


def _unwrap_graph_payload(data: dict[str, Any]) -> dict[str, Any]:
    if "uri_graph" in data:
        data = data["uri_graph"]
    if "graph" in data and isinstance(data["graph"], dict):
        data = data["graph"]
    if "task" in data and "steps" in data:
        from uri3.graph.graph_serializer import task_steps_to_graph
        # task conversion returns a full WorkflowGraph already
        return {"__task_converted__": task_steps_to_graph(data["task"], data["steps"])}
    return data


def load_workflow_graph(source: str | Path | dict[str, Any] | WorkflowGraph) -> WorkflowGraph:
    if isinstance(source, WorkflowGraph):
        return source
    if isinstance(source, dict):
        data = source
    else:
        path = _resolve_graph_source_path(source)
        data = _load_graph_data(path)
    data = _unwrap_graph_payload(data)
    if "__task_converted__" in data:
        return data["__task_converted__"]
    if not isinstance(data, dict):
        raise ValueError("Workflow graph payload must be a mapping")
    return normalize_graph_payload(data)


def validate_workflow_schema(graph: dict[str, Any]) -> list[str]:
    schema = json.loads(_schema_path("workflow_graph.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    return [f"{list(error.path)}: {error.message}" for error in sorted(validator.iter_errors(graph), key=lambda item: item.path)]


def validate_workflow_graph(source: str | Path | dict[str, Any] | WorkflowGraph) -> list[str]:
    graph = load_workflow_graph(source)
    errors = validate_workflow_schema(graph.to_dict())
    node_ids = set(graph.nodes)
    for node in graph.nodes.values():
        try:
            validate_uri(node.uri)
        except ValueError as exc:
            errors.append(f"{node.id}: invalid URI {node.uri!r}: {exc}")
        for dependency in node.depends_on:
            if dependency not in node_ids:
                errors.append(f"{node.id}: depends_on unknown node {dependency!r}")
    for edge in graph.edges:
        if edge.source not in node_ids:
            errors.append(f"edge.from unknown node {edge.source!r}")
        if edge.target not in node_ids:
            errors.append(f"edge.to unknown node {edge.target!r}")
    cycles = detect_cycles(graph)
    for cycle in cycles:
        errors.append(f"dependency cycle detected: {' -> '.join(cycle)}")
    return errors
