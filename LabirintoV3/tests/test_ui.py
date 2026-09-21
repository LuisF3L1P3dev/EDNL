import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from labyrinth.search import HeuristicType, SearchAlgorithm, SearchMetrics
from labyrinth.ui import App


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = App()
        self.app._draw()

    def tearDown(self) -> None:
        pygame.quit()

    def test_custom_size_creates_empty_map_and_clears_history(self) -> None:
        self.app.history[SearchAlgorithm.ASTAR] = SearchMetrics(path_cost=3)
        self.app.size_inputs = {"rows": "17", "cols": "29"}
        self.app.size_dialog_open = True
        self.app._apply_custom_size()
        self.assertEqual((self.app.grid.rows, self.app.grid.cols), (17, 29))
        self.assertFalse(self.app.grid.walls)
        self.assertFalse(self.app.history)
        self.assertFalse(self.app.size_dialog_open)

    def test_invalid_size_keeps_current_map(self) -> None:
        original = self.app.grid
        self.app.size_inputs = {"rows": "2", "cols": "500"}
        self.app._apply_custom_size()
        self.assertIs(self.app.grid, original)
        self.assertTrue(self.app.size_error)

    def test_typing_replaces_current_dimension_then_tab_changes_field(self) -> None:
        self.app._open_size_dialog()
        self.app._handle_size_key(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1, unicode="1")
        )
        self.app._handle_size_key(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_7, unicode="7")
        )
        self.assertEqual(self.app.size_inputs["rows"], "17")
        self.app._handle_size_key(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB, unicode="")
        )
        self.assertEqual(self.app.active_size_field, "cols")

    def test_eraser_tool_removes_wall_with_left_click(self) -> None:
        cell_size = 10
        self.app.grid_views = [
            (
                pygame.Rect(
                    0,
                    0,
                    self.app.grid.cols * cell_size,
                    self.app.grid.rows * cell_size,
                ),
                SearchAlgorithm.ASTAR,
            )
        ]
        position = (1, 1)
        self.app.grid.set_wall(position)
        self.app.tool = "Borracha"
        self.app._edit_at((15, 15), erase=False)
        self.assertNotIn(position, self.app.grid.walls)

    def test_changing_heuristic_clears_results(self) -> None:
        self.app.history[SearchAlgorithm.GREEDY] = SearchMetrics(path_cost=4)
        self.app._cycle_heuristic()
        self.assertEqual(self.app.heuristic, HeuristicType.EUCLIDEAN)
        self.assertFalse(self.app.history)

    def test_window_has_minimum_size(self) -> None:
        self.assertEqual(self.app.window.minimum_size, (1180, 820))

    def test_resize_does_not_recreate_display_mode(self) -> None:
        resize_event = pygame.event.Event(
            pygame.VIDEORESIZE,
            size=(1600, 900),
            w=1600,
            h=900,
        )
        pygame.event.post(resize_event)
        with patch("pygame.display.set_mode") as set_mode:
            self.app._handle_events()
        set_mode.assert_not_called()
        self.assertIs(self.app.screen, self.app.window.get_surface())


if __name__ == "__main__":
    unittest.main()
