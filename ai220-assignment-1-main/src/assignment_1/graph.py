"""An undirected graph with Euclidean costs, independent of the interface."""

from dataclasses import dataclass
import json
from math import hypot
from pathlib import Path


@dataclass(frozen=True)
class Node:
    """A hashable location. Coordinates are pixels in the original map image."""

    id: str
    x: float
    y: float


class Graph:
    def __init__(self, nodes: list[Node], edges: list[tuple[str, str]],
                 disabled: list[str] | None = None):
        self.nodes = {node.id: node for node in nodes}
        if len(self.nodes) != len(nodes):
            raise ValueError("Node IDs must be unique")
        self._adjacency: dict[Node, list[Node]] = {node: [] for node in nodes}
        self.edges: list[tuple[Node, Node]] = []
        for source, target in edges:
            if source not in self.nodes or target not in self.nodes:
                raise ValueError(f"Unknown endpoint in edge {source!r}, {target!r}")
            a, b = self.nodes[source], self.nodes[target]
            if b not in self._adjacency[a]:
                self._adjacency[a].append(b)
                if a != b:
                    self._adjacency[b].append(a)
                self.edges.append((a, b))
        self._disabled = set(disabled or [])
        if not self._disabled <= self.nodes.keys():
            raise ValueError("Disabled nodes must exist in the graph")

    @classmethod
    def load(cls, path: Path) -> "Graph":
        data = json.loads(path.read_text())
        return cls([Node(**node) for node in data["nodes"]],
                   data["edges"], data.get("disabled", []))

    def save(self, path: Path) -> None:
        data = {
            "nodes": [{"id": n.id, "x": n.x, "y": n.y} for n in self.nodes.values()],
            "edges": [[a.id, b.id] for a, b in self.edges],
            "disabled": sorted(self._disabled),
        }
        path.write_text(json.dumps(data, indent=2) + "\n")

    def is_enabled(self, node: Node) -> bool:
        if node not in self._adjacency:
            raise ValueError("Node does not belong to this graph")
        return node.id not in self._disabled

    def toggle(self, node: Node) -> None:
        if self.is_enabled(node):
            self._disabled.add(node.id)
        else:
            self._disabled.remove(node.id)

    def neighbors(self, node: Node) -> list[Node]:
        """Return enabled neighbors, or [] if node itself is disabled.

        The returned list is a copy; changing it does not change the graph.
        """
        if not self.is_enabled(node):
            return []
        return [other for other in self._adjacency[node] if self.is_enabled(other)]

    def edge_cost(self, source: Node, target: Node) -> float:
        """Return an existing edge's Euclidean length in original-image pixels.

        Costs are symmetric and independent of display scaling or node state.
        Disabled edges retain their cost; use neighbors() for traversability.
        Raise ValueError for unknown nodes or pairs without an edge.
        """
        if source not in self._adjacency or target not in self._adjacency[source]:
            raise ValueError("The nodes must be connected by an edge in this graph")
        return hypot(target.x - source.x, target.y - source.y)
