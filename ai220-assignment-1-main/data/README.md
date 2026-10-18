# CUA campus map and graph

Source: [Richard Kelley's graph search demo](https://richardkelley.io/AI109_slides/demos/graph-search/index.html)

Data: [cua-map-graph.json](https://richardkelley.io/AI109_slides/demos/graph-search/cua-map-graph.json)

Imported on September 23, 2026:

- `map.png` contains the embedded JPEG decoded and saved as PNG at its
  original 1000 × 977 resolution.
- `graph.json` contains all 65 nodes and 87 undirected edges. Original
  floating-point pixel coordinates are preserved. The unique visible
  labels `1`–`65` replace the demo's generated internal IDs, and edge
  endpoints use those same labels.
- All nodes initially are enabled. Saving in the app updates `disabled`.

Only map and graph data were imported; the demo's search implementation
is not included in this assignment starter.
