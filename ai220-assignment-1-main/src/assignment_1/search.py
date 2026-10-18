"""Search contract and student implementation. No algorithm is supplied."""

from abc import ABC, abstractmethod
import math
import itertools
from queue import PriorityQueue

from .graph import Graph, Node

class SearchAlgorithm(ABC):
    @abstractmethod
    def find_path(self, graph: Graph, start: Node, goal: Node) -> list[Node] | None:
        """Return a path including start and goal, or None if no path exists.

        Paths must use enabled nodes and graph edges. For an enabled start
        equal to goal, return [start]. A disabled endpoint has no path.
        Use graph.neighbors(node) to discover adjacent locations. Do not
        modify the graph[cite: 6]. Nodes are hashable and may be used in sets/dicts[cite: 6].
        Weighted algorithms can use graph.edge_cost(a, b), which returns
        Euclidean distance in original-image pixels for an existing edge[cite: 6].
        """
        raise NotImplementedError


class UniformCostSearch(SearchAlgorithm):
    def find_path(self, graph: Graph, start: Node, goal: Node) -> list[Node] | None:
        # Return None if either endpoint is disabled or no path exists[cite: 6]
        if not graph.is_enabled(start) or not graph.is_enabled(goal):
            return None
        if start == goal:
            return [start]

        counter = itertools.count()
        pq = PriorityQueue()
        # Elements in priority queue: (accumulated_cost, tie_breaker, current_node, path)
        pq.put((0.0, next(counter), start, [start]))
        cost_so_far = {start: 0.0}

        while not pq.empty():
            current_cost, _, current, path = pq.get()

            if current == goal:
                return path

            if current_cost > cost_so_far.get(current, float('inf')):
                continue

            for neighbor in graph.neighbors(current):
                new_cost = current_cost + graph.edge_cost(current, neighbor)
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    pq.put((new_cost, next(counter), neighbor, path + [neighbor]))

        return None


class GreedyBestFirstSearch(SearchAlgorithm):
    def find_path(self, graph: Graph, start: Node, goal: Node) -> list[Node] | None:
        # Return None if either endpoint is disabled or no path exists[cite: 6]
        if not graph.is_enabled(start) or not graph.is_enabled(goal):
            return None
        if start == goal:
            return [start]

        def heuristic(node: Node) -> float:
            # Euclidean distance from node to goal using coordinates directly
            return math.sqrt((goal.x - node.x) ** 2 + (goal.y - node.y) ** 2)

        counter = itertools.count()
        pq = PriorityQueue()
        h_start = heuristic(start)
        # Elements in priority queue: (heuristic_cost, tie_breaker, current_node, path)
        pq.put((h_start, next(counter), start, [start]))

        visited = {start}

        while not pq.empty():
            _, _, current, path = pq.get()

            if current == goal:
                return path

            for neighbor in graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    h_cost = heuristic(neighbor)
                    pq.put((h_cost, next(counter), neighbor, path + [neighbor]))

        return None