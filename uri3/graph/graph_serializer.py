from __future__ import annotations

from typing import Any

from uri3.graph.models import GraphEdge, GraphNode, WorkflowGraph


def edges_from_depends_on(nodes: dict[str, GraphNode]) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    seen: set[tuple[str, str, str]] = set()
    for node in nodes.values():
        for dependency in node.depends_on:
            key = (dependency, node.id, "depends_on")
            if key in seen:
                continue
            seen.add(key)
            edges.append(GraphEdge(source=dependency, target=node.id, relation="depends_on"))
    return edges


def normalize_graph_payload(data: dict[str, Any]) -> WorkflowGraph:
    graph_id = str(data.get("id") or "workflow")
    graph = WorkflowGraph(
        id=graph_id,
        version=int(data.get("version") or 1),
        kind=str(data.get("kind") or "task"),
        description=data.get("description"),
    )
    raw_nodes = data.get("nodes")
    if isinstance(raw_nodes, dict):
        node_items = [dict(value, id=node_id) for node_id, value in raw_nodes.items()]
    elif isinstance(raw_nodes, list):
        node_items = raw_nodes
    else:
        raise ValueError("Workflow graph requires nodes as list or mapping")
    for item in node_items:
        node = GraphNode.from_dict(item)
        graph.add_node(node)
    graph.edges = list(data.get("edges") or [])
    if not graph.edges:
        graph.edges = edges_from_depends_on(graph.nodes)
    else:
        graph.edges = [
            GraphEdge(source=str(edge["from"]), target=str(edge["to"]), relation=str(edge.get("type") or "depends_on"))
            for edge in graph.edges
        ]
    return graph


def task_steps_to_graph(task: dict[str, Any], steps: list[dict[str, Any]]) -> WorkflowGraph:
    graph = WorkflowGraph(
        id=str(task.get("id") or "task"),
        kind="task",
        description=task.get("description"),
    )
    for step in steps:
        graph.add_node(GraphNode.from_dict(step))
    graph.edges = edges_from_depends_on(graph.nodes)
    return graph


def workflow_manifest(graph: WorkflowGraph) -> dict[str, Any]:
    return {"uri_graph": graph.to_dict()}
