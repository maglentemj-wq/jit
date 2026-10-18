"""Pygame map viewer. Search logic belongs in search.py."""

import argparse
from pathlib import Path

import pygame

from .graph import Graph, Node
from .search import Search, SearchAlgorithm


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
HEADER = 0
FOOTER = 80
RADIUS = 8
PADDING = 4


class MapApp:
    def __init__(self, map_path: Path, graph_path: Path, search: SearchAlgorithm):
        self.graph_path = graph_path
        self.graph = Graph.load(graph_path)
        self.search = search
        source = pygame.image.load(str(map_path))
        width, height = source.get_size()
        desktop_width, desktop_height = pygame.display.get_desktop_sizes()[0]
        # Leave room for the title bar, menu bar, and taskbar/dock. The
        # footer is part of the window, so subtract it before fitting the map.
        available_width = max(1, desktop_width - 80)
        available_height = max(1, desktop_height - 120 - FOOTER - 2 * PADDING)
        self.max_scale = min(max(1, available_width - 2 * PADDING) / width,
                             available_height / height)
        initial_scale = min(self.max_scale, (720 - FOOTER - 2 * PADDING) / height)
        window_size = (round(width * initial_scale) + 2 * PADDING,
                       round(height * initial_scale) + FOOTER + 2 * PADDING)
        self.screen = pygame.display.set_mode(
            window_size, pygame.RESIZABLE)
        pygame.display.set_caption("Map Search Lab")
        self.source_image = source.convert()
        self._layout_size = None
        for node in self.graph.nodes.values():
            if not (0 <= node.x < width and 0 <= node.y < height):
                raise ValueError(f"Node {node.id!r} lies outside the map image")
        self.font = pygame.font.Font(None, 23)
        self.node_font = pygame.font.Font(None, 16)
        self.show_help = False
        self.mode = "edit"
        self.start: Node | None = None
        self.goal: Node | None = None
        self.path: list[Node] = []
        self.status = "Click a node to turn it on or off."
        self.buttons = {action: pygame.Rect(0, 0, 100, 32)
                        for action in ("edit", "search", "clear", "help")}
        self.back_button = pygame.Rect(0, 0, 100, 32)
        self.fit_map()

    def resize(self, requested_size: tuple[int, int]) -> None:
        """Constrain the map viewport's ratio, keeping the footer a fixed height."""
        width, height = self.source_image.get_size()
        previous_width, previous_height = self._layout_size
        requested_width, requested_height = requested_size
        if abs(requested_width - previous_width) >= abs(requested_height - previous_height):
            scale = (requested_width - 2 * PADDING) / width
        else:
            scale = (requested_height - FOOTER - 2 * PADDING) / height
        scale = min(self.max_scale, max(480 / width, scale))
        size = (round(width * scale) + 2 * PADDING,
                round(height * scale) + FOOTER + 2 * PADDING)
        if self.screen.get_size() != size:
            self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.fit_map()

    def fit_map(self) -> None:
        """Fit the map above the footer and center its controls on resize."""
        window_size = self.screen.get_size()
        if window_size == self._layout_size:
            return
        self._layout_size = window_size
        button_width = min(100, max(1, (window_size[0] - 20
                                      - (len(self.buttons) - 1) * 10) // len(self.buttons)))
        row_width = len(self.buttons) * button_width + (len(self.buttons) - 1) * 10
        row_left = (window_size[0] - row_width) // 2
        for index, rect in enumerate(self.buttons.values()):
            rect.update(row_left + index * (button_width + 10),
                        window_size[1] - 44, button_width, 32)
        self.back_button.midbottom = (window_size[0] // 2, window_size[1] - 12)
        width, height = self.source_image.get_size()
        padding = PADDING
        available_width = max(1, window_size[0] - 2 * padding)
        available_height = max(1, window_size[1] - HEADER - FOOTER - 2 * padding)
        self.scale = min(available_width / width, available_height / height)
        size = (max(1, int(width * self.scale)), max(1, int(height * self.scale)))
        self.map_image = pygame.transform.smoothscale(self.source_image, size)
        self.offset_x = (window_size[0] - size[0]) // 2
        self.offset_y = HEADER + padding

    def position(self, node: Node) -> tuple[int, int]:
        return (self.offset_x + round(node.x * self.scale),
                self.offset_y + round(node.y * self.scale))

    def clear(self) -> None:
        self.start = self.goal = None
        self.path = []

    def action(self, action: str) -> None:
        if action == "help":
            self.show_help = not self.show_help
            return
        if self.show_help:
            return
        if action in ("edit", "search"):
            self.mode = action
            self.clear()
            self.status = ("Click a node to turn it on or off." if action == "edit"
                           else "Click an enabled start node, then a goal node.")
        elif action == "clear":
            self.clear()
            self.status = "Selection cleared."
        elif action == "save":
            try:
                self.graph.save(self.graph_path)
                self.status = "Node states saved."
            except OSError as error:
                self.status = f"Could not save: {error}"

    def click(self, position: tuple[int, int]) -> None:
        self.fit_map()
        if self.show_help:
            if self.back_button.collidepoint(position):
                self.action("help")
            return
        for action, rect in self.buttons.items():
            if rect.collidepoint(position):
                self.action(action)
                return
        nearby = [n for n in self.graph.nodes.values()
                  if pygame.Vector2(self.position(n)).distance_to(position) <= RADIUS + 4]
        if not nearby:
            return
        node = min(nearby, key=lambda n: pygame.Vector2(self.position(n)).distance_to(position))
        if self.mode == "edit":
            self.graph.toggle(node)
            self.clear()
            state = "on" if self.graph.is_enabled(node) else "off"
            self.status = f"{node.id} is {state}. Press S to save changes."
        elif not self.graph.is_enabled(node):
            self.status = "Choose an enabled node, or turn this node on in edit mode."
        elif self.start is None or self.goal is not None:
            self.clear()
            self.start = node
            self.status = f"Start: {node.id}. Choose a goal (the same node is allowed)."
        else:
            self.goal = node
            self.run_search()

    def run_search(self) -> None:
        assert self.start is not None and self.goal is not None
        self.path = []
        try:
            result = self.search.find_path(self.graph, self.start, self.goal)
            if result is None:
                self.status = "No path found. Click a node to start again."
                return
            if (not isinstance(result, list) or not result
                    or result[0] != self.start or result[-1] != self.goal
                    or any(not self.graph.is_enabled(n) for n in result)
                    or any(b not in self.graph.neighbors(a) for a, b in zip(result, result[1:]))):
                raise ValueError("Return a valid list of Nodes from start to goal, or None")
            self.path = result
            self.status = f"Path: {len(result) - 1} edges. Click a node to start again."
        except NotImplementedError:
            self.status = "Search is a stub. Implement Search.find_path() in search.py."
        except Exception as error:
            # Keep the UI usable while students debug their implementations.
            import traceback
            traceback.print_exc()
            self.status = f"Search error: {error} (see terminal)"

    def label(self, text: str, position: tuple[int, int], color=(225, 232, 240)) -> None:
        self.screen.blit(self.font.render(text, True, color), position)

    def edge_at(self, position: tuple[int, int]) -> tuple[Node, Node] | None:
        """Find the nearest edge within six screen pixels of the pointer."""
        self.fit_map()
        map_rect = self.map_image.get_rect(topleft=(self.offset_x, self.offset_y))
        if self.show_help or not map_rect.collidepoint(position):
            return None
        pointer = pygame.Vector2(position)
        # Nodes take precedence over their incident edges.
        if any(pointer.distance_to(self.position(n)) <= RADIUS + 2
               for n in self.graph.nodes.values()):
            return None
        closest = None
        closest_distance = 6.0
        for a, b in self.graph.edges:
            start = pygame.Vector2(self.position(a))
            segment = pygame.Vector2(self.position(b)) - start
            length_squared = segment.length_squared()
            fraction = (max(0.0, min(1.0, (pointer - start).dot(segment) / length_squared))
                        if length_squared else 0.0)
            distance = pointer.distance_to(start + fraction * segment)
            if distance <= closest_distance:
                closest, closest_distance = (a, b), distance
        return closest

    def draw_edge_tooltip(self, position: tuple[int, int]) -> None:
        edge = self.edge_at(position)
        if edge is None:
            return
        a, b = edge
        disabled = not (self.graph.is_enabled(a) and self.graph.is_enabled(b))
        message = f"{a.id} - {b.id}: {self.graph.edge_cost(a, b):.2f}"
        if disabled:
            message += " (disabled)"
        text = self.font.render(message, True, (248, 250, 252))
        rect = pygame.Rect(position[0] + 14, position[1] + 18,
                           text.get_width() + 20, text.get_height() + 16)
        rect.clamp_ip(self.screen.get_rect().inflate(-8, -8))
        pygame.draw.rect(self.screen, (20, 30, 45), rect, border_radius=5)
        pygame.draw.rect(self.screen, (248, 250, 252), rect, width=1, border_radius=5)
        self.screen.blit(text, (rect.x + 10, rect.y + 8))

    def draw(self) -> None:
        self.fit_map()
        self.screen.fill((25, 34, 46))
        if self.show_help:
            self.draw_help()
            pygame.display.flip()
            return
        for action, rect in self.buttons.items():
            color = (42, 119, 153) if action == self.mode else (52, 65, 82)
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            text = self.font.render(action.title(), True, (225, 232, 240))
            self.screen.blit(text, text.get_rect(center=rect.center))
        legend = self.font.render(
            "On: white   Off: gray / X   Start: green   Goal: orange   Path: blue",
            True, (225, 232, 240))
        if legend.get_width() > self.screen.get_width() - 16:
            factor = (self.screen.get_width() - 16) / legend.get_width()
            legend = pygame.transform.smoothscale(
                legend, (round(legend.get_width() * factor), round(legend.get_height() * factor)))
        self.screen.blit(legend, legend.get_rect(
            midtop=(self.screen.get_width() // 2, self.screen.get_height() - FOOTER + 8)))
        self.screen.blit(self.map_image, (self.offset_x, self.offset_y))
        for a, b in self.graph.edges:
            enabled = self.graph.is_enabled(a) and self.graph.is_enabled(b)
            start, end = self.position(a), self.position(b)
            if enabled:
                pygame.draw.line(self.screen, (248, 250, 252), start, end, 6)
                pygame.draw.line(self.screen, (20, 30, 45), start, end, 3)
            else:
                pygame.draw.line(self.screen, (182, 184, 181), start, end, 1)
        for a, b in zip(self.path, self.path[1:]):
            pygame.draw.line(self.screen, (28, 130, 233), self.position(a), self.position(b), 7)
        for node in self.graph.nodes.values():
            pos = self.position(node)
            enabled = self.graph.is_enabled(node)
            color = (248, 250, 252) if enabled else (157, 163, 166)
            if node in self.path:
                color = (77, 166, 250)
            if node == self.start:
                color = (73, 201, 133)
            if node == self.goal:
                color = (255, 178, 79)
            pygame.draw.circle(self.screen, (36, 52, 63), pos, RADIUS + 2)
            pygame.draw.circle(self.screen, color, pos, RADIUS)
            text = self.node_font.render(node.id if enabled else "X", True, (25, 34, 46))
            self.screen.blit(text, text.get_rect(center=pos))
            if node == self.start == self.goal:
                pygame.draw.circle(self.screen, (73, 201, 133), pos, RADIUS + 4, 2)
        if pygame.mouse.get_focused():
            self.draw_edge_tooltip(pygame.mouse.get_pos())
        pygame.display.flip()

    def draw_help(self) -> None:
        rect = self.back_button
        pygame.draw.rect(self.screen, (42, 119, 153), rect, border_radius=6)
        text = self.font.render("Back", True, (225, 232, 240))
        self.screen.blit(text, text.get_rect(center=rect.center))
        paragraphs = [
            "E: Edit   /   F: Search   /   C: Clear   /   S: Save   /   Esc: Quit",
            "Edit: click a node to turn it on or off. Press S to save node states.",
            "Search: click an enabled start node, then an enabled goal node. "
            "Click another node to begin a new search.",
            "Hover over an edge to see its cost: Euclidean distance in original-map pixels.",
            "Current status: " + self.status,
            "H or F1: open or close help. Escape returns to the map from this screen.",
        ]
        y = HEADER + 16
        for paragraph in paragraphs:
            line = ""
            for word in paragraph.split():
                candidate = f"{line} {word}".strip()
                if line and self.font.size(candidate)[0] > self.screen.get_width() - 40:
                    self.label(line, (20, y))
                    y += 25
                    line = word
                else:
                    line = candidate
            self.label(line, (20, y))
            y += 41

    def run(self) -> None:
        clock = pygame.time.Clock()
        running = True
        shortcuts = {pygame.K_e: "edit", pygame.K_f: "search",
                     pygame.K_c: "clear", pygame.K_s: "save",
                     pygame.K_h: "help", pygame.K_F1: "help"}
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.resize(event.size)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.show_help:
                            self.show_help = False
                        else:
                            running = False
                    elif event.key in shortcuts:
                        self.action(shortcuts[event.key])
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.click(event.pos)
            self.draw()
            clock.tick(60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Map search assignment starter")
    parser.add_argument("--map", type=Path, default=DATA_DIR / "map.png")
    parser.add_argument("--graph", type=Path, default=DATA_DIR / "graph.json")
    args = parser.parse_args()
    pygame.display.init()
    pygame.font.init()
    try:
        # TODO - Replace Search with a class that you implement.
        MapApp(args.map, args.graph, Search()).run()
    finally:
        pygame.quit()
