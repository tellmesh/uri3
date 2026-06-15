from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GraphNode:
    id: str
    uri: str
    operation: str
    kind: str | None = None
    type: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    condition: dict[str, Any] | None = None
    emits: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphNode:
        return cls(
            id=str(data["id"]),
            uri=str(data["uri"]),
            operation=str(data["operation"]),
            kind=data.get("kind"),
            type=data.get("type"),
            payload=dict(data.get("payload") or {}),
            depends_on=list(data.get("depends_on") or []),
            condition=data.get("condition"),
            emits=list(data.get("emits") or []),
            produces=list(data.get("produces") or []),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "uri": self.uri,
            "operation": self.operation,
        }
        if self.kind:
            payload["kind"] = self.kind
        if self.type:
            payload["type"] = self.type
        if self.payload:
            payload["payload"] = self.payload
        if self.depends_on:
            payload["depends_on"] = self.depends_on
        if self.condition:
            payload["condition"] = self.condition
        if self.emits:
            payload["emits"] = self.emits
        if self.produces:
            payload["produces"] = self.produces
        return payload


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str = "depends_on"

    def to_dict(self) -> dict[str, Any]:
        return {"from": self.source, "to": self.target, "type": self.relation}


@dataclass
class WorkflowGraph:
    id: str
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)
    version: int = 1
    kind: str = "task"
    description: str | None = None

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "kind": self.kind,
            **({"description": self.description} if self.description else {}),
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
        }
