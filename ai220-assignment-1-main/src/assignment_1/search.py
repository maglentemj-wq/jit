"""Search contract and student implementation. No algorithm is supplied."""

from abc import ABC, abstractmethod

from .graph import Graph, Node

class SearchAlgorithm(ABC):
    @abstractmethod
    def find_path(self, graph: Graph, start: Node, goal: Node) -> list[Node] | None:
        """Return a path including start and goal, or None if no path exists.

        Paths must use enabled nodes and graph edges. For an enabled start
        equal to goal, return [start]. A disabled endpoint has no path.
        Use graph.neighbors(node) to discover adjacent locations. Do not
        modify the graph. Nodes are hashable and may be used in sets/dicts.
        Weighted algorithms can use graph.edge_cost(a, b), which returns
        Euclidean distance in original-image pixels for an existing edge.
        """
        raise NotImplementedError


class Search(SearchAlgorithm):
    def find_path(self, graph: Graph, start: Node, goal: Node) -> list[Node] | None:
        # TODO: Implement a search algorithm using graph.neighbors(node).
        # Use graph.edge_cost(current, neighbor) to get the cost between two connected Nodes.
        raise NotImplementedError("Implement Search.find_path() in search.py")