from __future__ import annotations

from typing import Any, Protocol

from uri3.graph.execution_models import ExecutionContext
from uri3.graph.models import GraphNode


class StepAdapter(Protocol):
    schemes: frozenset[str]

    def execute(self, node: GraphNode, context: ExecutionContext) -> dict[str, Any]: ...
