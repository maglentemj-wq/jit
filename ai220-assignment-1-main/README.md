# Map Search Lab

Starter code for implementing graph search algorithms in Python. The Pygame
interface is complete; **no search algorithm is provided**.

## Run

From this project directory, with Python 3.13+ and uv installed:

```sh
uv sync
uv run assignment-1
```

You can also run `uv run python -m assignment_1`. The dependency is
`pygame-ce`, which supplies the `pygame` module. See the
[Pygame documentation](https://pyga.me/docs/) for the graphics API.

## Controls

Click the toolbar buttons or use these keys:

| Key | Action |
| --- | --- |
| E | Edit mode: click a node to toggle it on/off |
| F | Search mode: click an enabled start, then an enabled goal |
| C | Clear endpoints and the displayed path |
| S | Save node states to the loaded graph JSON file |
| H / F1 | Open or close the Help screen (instructions and current status) |
| Esc | Return from Help, or quit from the map |

After selecting a goal, the next node click starts a new search. A node can
be both start and goal. Changing modes clears the selection. Toggles take
effect immediately in memory; press S to preserve them between runs.
Disabled nodes and their incident edges cannot be traversed. The initial
search stub displays an explanatory message instead of a path.

Hover over an edge to see its endpoints and cost in a tooltip. Costs are
Euclidean distances in original-map pixels, so resizing does not change them.
Disabled edges also show their cost and are marked disabled.

## Student task

Implement `Search.find_path()` in `src/assignment_1/search.py`. `Search` inherits
the provided `SearchAlgorithm` abstract base class. Its contract is:

```python
def find_path(self, graph: Graph, start: Node, goal: Node) -> list[Node] | None:
    ...
```

- Use `graph.neighbors(node)` to get a **list of enabled neighboring Nodes**.
  A disabled node has no neighbors.
- Return a list containing both endpoints, in traversal order, or `None`
  when no path exists. Return `[start]` when an enabled start equals goal.
- Do not mutate the graph. Nodes are immutable and hashable, so they work
  as set members and dictionary keys for tracking visited nodes and parents.
- The graph is undirected and weighted. Use `graph.edge_cost(a, b)` for an
  existing edge's cost: `sqrt((b.x - a.x)**2 + (b.y - a.y)**2)` in original-image
  pixels. The API returns full precision; tooltips display two decimal places.
  Nonadjacent or unknown nodes raise `ValueError`. Disabled edges retain their
  costs, but `neighbors()` excludes them from traversal.

The interface checks returned paths and draws valid paths in blue. Status
messages and errors appear on the Help screen, with debugging tracebacks in the terminal.
Search runs synchronously, so an implementation must terminate to keep the
window responsive. To try multiple algorithms, create other subclasses of
`SearchAlgorithm` and change the instance passed to `MapApp` in `app.py`.

## Map and graph data

`data/map.png` and `data/graph.json` use the CUA campus map and all 65 nodes
and 87 undirected edges from the
[graph search demo](https://richardkelley.io/AI109_slides/demos/graph-search/index.html).
The demo's visible labels (`"1"` through `"65"`) serve as node IDs; its original
pixel coordinates and connections are preserved. See `data/README.md` for
source and conversion details. The graph file uses this format:

```json
{
  "nodes": [{"id": "A", "x": 100, "y": 100}, {"id": "B", "x": 300, "y": 100}],
  "edges": [["A", "B"]],
  "disabled": []
}
```

Node IDs must be unique. Each edge names two existing nodes; list each
undirected edge once. Coordinates are pixels in the original image, with
the origin at the upper left. The viewer scales large maps and overlays
together to fit the drawing area above the bottom controls. Window resizing
preserves the map area's aspect ratio with a four-pixel border and a fixed-height
footer; the map and clickable nodes automatically rescale with it. Short node IDs
work best inside the node circles.

To use your own data, replace these files or pass explicit paths:

```sh
uv run assignment-1 --map data/my-map.png --graph data/my-graph.json
```

Keep the top-level `data/` directory with the source checkout. These assets
are not bundled in an installed wheel; use explicit paths for that setup.

## Check the starter infrastructure

```sh
uv run python -m unittest discover -s tests -v
```

Tests use a headless display and fixed path fixtures, without supplying a
search algorithm. Add your own algorithm tests as you implement the assignment.
