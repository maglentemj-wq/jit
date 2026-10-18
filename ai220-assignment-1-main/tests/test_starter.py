import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

from assignment_1.app import DATA_DIR, HEADER, MapApp
from assignment_1.graph import Graph, Node
from assignment_1.search import Search, SearchAlgorithm


class GraphTests(unittest.TestCase):
    def test_euclidean_cost_and_invalid_edges(self):
        a, b, c = Node("A", 0, 0), Node("B", 3, 4), Node("C", 10, 10)
        graph = Graph([a, b, c], [("A", "B"), ("C", "C")])
        self.assertEqual(graph.edge_cost(a, b), 5.0)
        self.assertEqual(graph.edge_cost(b, a), 5.0)
        self.assertEqual(graph.edge_cost(c, c), 0.0)
        graph.toggle(b)
        self.assertEqual(graph.edge_cost(a, b), 5.0)
        self.assertEqual(graph.neighbors(a), [])
        for source, target in [(a, c), (a, Node("X", 3, 4)), (Node("X", 3, 4), a)]:
            with self.assertRaises(ValueError):
                graph.edge_cost(source, target)

    def test_toggle_filters_both_directions_and_preserves_edges(self):
        a, b = Node("A", 0, 0), Node("B", 1, 1)
        graph = Graph([a, b], [("A", "B")])
        self.assertEqual(graph.neighbors(a), [b])
        self.assertEqual(graph.neighbors(b), [a])
        graph.neighbors(a).clear()
        self.assertEqual(graph.neighbors(a), [b])
        graph.toggle(b)
        self.assertEqual(graph.neighbors(a), [])
        self.assertEqual(graph.neighbors(b), [])
        graph.toggle(b)
        self.assertEqual(graph.neighbors(a), [b])

    def test_save_round_trip(self):
        graph = Graph.load(DATA_DIR / "graph.json")
        graph.toggle(graph.nodes["2"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.json"
            graph.save(path)
            restored = Graph.load(path)
        self.assertFalse(restored.is_enabled(restored.nodes["2"]))
        self.assertEqual(restored.edges, graph.edges)

    def test_contract_and_stub(self):
        with self.assertRaises(TypeError):
            SearchAlgorithm()
        graph = Graph.load(DATA_DIR / "graph.json")
        with self.assertRaises(NotImplementedError):
            Search().find_path(graph, graph.nodes["1"], graph.nodes["2"])


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        self.app = MapApp(DATA_DIR / "map.png", DATA_DIR / "graph.json", Search())

    def tearDown(self):
        pygame.quit()

    def test_edge_hover_after_resize_and_in_help(self):
        app = self.app
        a, b = app.graph.nodes["1"], app.graph.nodes["2"]
        cost = app.graph.edge_cost(a, b)
        for size in [(550, 620), (650, 720)]:
            app.resize(size)
            start, end = app.position(a), app.position(b)
            midpoint = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)
            self.assertEqual(app.edge_at(midpoint), (a, b))
            self.assertIsNone(app.edge_at(start))
            self.assertIsNone(app.edge_at(app.buttons["help"].center))
            self.assertEqual(app.graph.edge_cost(a, b), cost)
        app.graph.toggle(a)
        self.assertEqual(app.edge_at(midpoint), (a, b))
        app.draw_edge_tooltip(midpoint)
        app.action("help")
        self.assertIsNone(app.edge_at(midpoint))

    def test_entire_map_fits_short_desktop(self):
        with patch("pygame.display.get_desktop_sizes", return_value=[(1280, 720)]):
            app = MapApp(DATA_DIR / "map.png", DATA_DIR / "graph.json", Search())
        self.assertLessEqual(app.screen.get_height(), 600)
        self.assertLessEqual(app.screen.get_width(), 1200)
        map_rect = app.map_image.get_rect(topleft=(app.offset_x, app.offset_y))
        self.assertTrue(app.screen.get_rect().contains(map_rect))
        for node in app.graph.nodes.values():
            self.assertTrue(map_rect.collidepoint(app.position(node)))
        # Clicking the lowest node must still use its scaled coordinates.
        bottom_node = max(app.graph.nodes.values(), key=lambda n: n.y)
        app.click(app.position(bottom_node))
        self.assertFalse(app.graph.is_enabled(bottom_node))
        app.draw()

    def test_map_refits_after_window_shrinks(self):
        app = self.app
        original_scale = app.scale
        app.screen = pygame.display.set_mode((800, 480), pygame.RESIZABLE)
        app.draw()
        self.assertLess(app.scale, original_scale)
        map_rect = app.map_image.get_rect(topleft=(app.offset_x, app.offset_y))
        self.assertTrue(app.screen.get_rect().contains(map_rect))
        self.assertGreaterEqual(map_rect.top, HEADER)
        bottom_node = max(app.graph.nodes.values(), key=lambda n: n.y)
        app.click(app.position(bottom_node))
        self.assertFalse(app.graph.is_enabled(bottom_node))

    def test_edit_selection_stub_and_draw(self):
        app = self.app
        a, b = app.graph.nodes["1"], app.graph.nodes["2"]
        app.click(app.position(a))
        self.assertFalse(app.graph.is_enabled(a))
        app.action("search")
        app.click(app.position(a))
        self.assertIsNone(app.start)
        app.click(app.position(b))
        app.click(app.position(b))
        self.assertIn("stub", app.status)
        app.draw()
        app.action("edit")
        self.assertIsNone(app.start)

    def test_supplied_path_and_no_path(self):
        class FixedSearch(SearchAlgorithm):
            def find_path(self, graph, start, goal):
                return [start, goal]  # A fixed fixture, not a search algorithm.

        app = self.app
        app.search = FixedSearch()
        app.action("search")
        app.click(app.position(app.graph.nodes["1"]))
        app.click(app.position(app.graph.nodes["2"]))
        self.assertEqual([n.id for n in app.path], ["1", "2"])
        app.draw()

        class NoPath(SearchAlgorithm):
            def find_path(self, graph, start, goal):
                return None

        app.search = NoPath()
        app.run_search()
        self.assertEqual(app.path, [])
        self.assertIn("No path", app.status)


if __name__ == "__main__":
    unittest.main()
