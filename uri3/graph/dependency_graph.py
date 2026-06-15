from __future__ import annotations

from collections import deque
from typing import Any

from uri3.graph.models import WorkflowGraph


def adjacency(graph: WorkflowGraph) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {node_id: [] for node_id in graph.nodes}
    for edge in graph.edges:
        mapping.setdefault(edge.source, []).append(edge.target)
        mapping.setdefault(edge.target, mapping.get(edge.target, []))
    return mapping


def reverse_adjacency(graph: WorkflowGraph) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {node_id: [] for node_id in graph.nodes}
    for edge in graph.edges:
        mapping.setdefault(edge.target, []).append(edge.source)
        mapping.setdefault(edge.source, mapping.get(edge.source, []))
    return mapping


def _indegree_outgoing(graph: WorkflowGraph) -> tuple[dict[str, int], dict[str, list[str]]]:
    indegree = {node_id: 0 for node_id in graph.nodes}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in graph.nodes}
    for edge in graph.edges:
        if edge.source not in graph.nodes or edge.target not in graph.nodes:
            continue
        outgoing[edge.source].append(edge.target)
        indegree[edge.target] += 1
    return indegree, outgoing


def _visit_acyclic_nodes(indegree: dict[str, int], outgoing: dict[str, list[str]]) -> int:
    queue = deque(node_id for node_id, count in indegree.items() if count == 0)
    visited = 0
    while queue:
        node_id = queue.popleft()
        visited += 1
        for target in outgoing[node_id]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    return visited


def _remaining_cycle_nodes(indegree: dict[str, int]) -> list[list[str]]:
    remaining = [node_id for node_id, count in indegree.items() if count > 0]
    return [remaining] if remaining else []


def detect_cycles(graph: WorkflowGraph) -> list[list[str]]:
    indegree, outgoing = _indegree_outgoing(graph)
    visited = _visit_acyclic_nodes(indegree, outgoing)
    if visited == len(graph.nodes):
        return []
    return _remaining_cycle_nodes(indegree)


def _raise_if_cycles(graph: WorkflowGraph) -> None:
    cycles = detect_cycles(graph)
    if cycles:
        raise ValueError(f"Workflow graph contains dependency cycle: {cycles[0]}")


def _topological_order(indegree: dict[str, int], outgoing: dict[str, list[str]]) -> list[str]:
    queue = deque(sorted(node_id for node_id, count in indegree.items() if count == 0))
    order: list[str] = []
    while queue:
        node_id = queue.popleft()
        order.append(node_id)
        for target in sorted(outgoing[node_id]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    return order


def topological_sort(graph: WorkflowGraph) -> list[str]:
    _raise_if_cycles(graph)
    indegree, outgoing = _indegree_outgoing(graph)
    order = _topological_order(indegree, outgoing)
    if len(order) != len(graph.nodes):
        raise ValueError("Unable to produce topological order for workflow graph")
    return order


def _root_nodes(graph: WorkflowGraph) -> list[str]:
    return [
        node_id
        for node_id in graph.nodes
        if not any(edge.target == node_id for edge in graph.edges)
    ]


def _leaf_nodes(graph: WorkflowGraph) -> list[str]:
    return [
        node_id
        for node_id in graph.nodes
        if not any(edge.source == node_id for edge in graph.edges)
    ]


def dependency_summary(graph: WorkflowGraph) -> dict[str, Any]:
    cycles = detect_cycles(graph)
    return {
        "id": graph.id,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "roots": _root_nodes(graph),
        "leaves": _leaf_nodes(graph),
        "cycles": cycles,
        "order": topological_sort(graph) if not cycles else [],
    }
