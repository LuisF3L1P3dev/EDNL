import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from labyrinth.scenarios import MAX_COLS, MAX_ROWS, SCENARIOS, create_scenario
from labyrinth.search import HeuristicType, SearchAlgorithm, SearchMetrics
from labyrinth.simulation import SimulationState
from labyrinth.ui import App, DUEL_GAP, OUTER_MARGIN, PANEL_GAP


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

    def test_custom_size_preserves_scenario_and_resets_all_results(self) -> None:
        self.app.scenario_index = SCENARIOS.index("Zigue-zague")
        self.app.grid = create_scenario("Zigue-zague")
        for simulation in self.app.simulations.values():
            simulation.start(self.app.grid)
            simulation.advance()
        self.app.history[SearchAlgorithm.ASTAR] = SearchMetrics(path_cost=3)
        self.app.step_accumulator = 0.75
        self.app.size_inputs = {"rows": "17", "cols": "29"}
        self.app.size_dialog_open = True

        self.app._apply_custom_size()

        self.assertEqual(SCENARIOS[self.app.scenario_index], "Zigue-zague")
        self.assertEqual((self.app.grid.rows, self.app.grid.cols), (17, 29))
        self.assertTrue(self.app.grid.walls)
        self.assertFalse(self.app.history)
        self.assertEqual(self.app.step_accumulator, 0.0)
        self.assertTrue(
            all(
                simulation.state is SimulationState.IDLE
                and not simulation.frontier
                and not simulation.explored
                and not simulation.path
                and simulation.metrics == SearchMetrics()
                for simulation in self.app.simulations.values()
            )
        )

    def test_changing_scenario_preserves_current_size(self) -> None:
        self.app.grid = create_scenario("Mundo aberto", rows=17, cols=29)
        self.app.scenario_index = SCENARIOS.index("Mundo aberto")
        self.app._cycle_scenario()
        self.assertEqual(SCENARIOS[self.app.scenario_index], "Armadilha Gulosa")
        self.assertEqual((self.app.grid.rows, self.app.grid.cols), (17, 29))

    def test_scenario_selector_cycles_through_full_catalog(self) -> None:
        self.app.grid = create_scenario("Mundo aberto", rows=17, cols=29)
        self.app.scenario_index = 0
        visited = []
        for _ in SCENARIOS:
            self.app._cycle_scenario()
            visited.append(SCENARIOS[self.app.scenario_index])
            self.assertEqual((self.app.grid.rows, self.app.grid.cols), (17, 29))
        self.assertEqual(tuple(visited), (*SCENARIOS[1:], SCENARIOS[0]))

    def test_selecting_random_scenario_generates_a_new_variation(self) -> None:
        before_random = SCENARIOS.index("Aleatório") - 1
        self.app.grid = create_scenario("Mundo aberto", rows=17, cols=29)
        self.app.scenario_index = before_random
        with patch("labyrinth.ui.random.randrange", side_effect=(101, 202)):
            self.app._cycle_scenario()
            first_walls = set(self.app.grid.walls)
            self.app.scenario_index = before_random
            self.app._cycle_scenario()
        self.assertNotEqual(first_walls, self.app.grid.walls)

    def test_clear_selects_open_world_and_preserves_current_size(self) -> None:
        self.app.grid = create_scenario("Espiral", rows=17, cols=29)
        self.app.scenario_index = SCENARIOS.index("Espiral")
        self.app._clear_grid()
        self.assertEqual(SCENARIOS[self.app.scenario_index], "Mundo aberto")
        self.assertEqual((self.app.grid.rows, self.app.grid.cols), (17, 29))
        self.assertFalse(self.app.grid.walls)

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

    def test_graphical_smoke_in_individual_and_duel_modes(self) -> None:
        self.app.grid = create_scenario(
            "Espiral", rows=MAX_ROWS, cols=MAX_COLS
        )
        for simulation in self.app.simulations.values():
            simulation.reset(self.app.grid)
        for mode, expected_views in (("Individual", 1), ("Duelo", 2)):
            with self.subTest(mode=mode):
                self.app.mode = mode
                self.app._draw()
                self.assertEqual(len(self.app.grid_views), expected_views)

    def test_new_scenarios_render_in_both_modes(self) -> None:
        names = (
            "Ponte estreita",
            "Becos sem saída",
            "Tabuleiro",
            "Arquipélago",
        )
        for name in names:
            self.app.grid = create_scenario(name)
            self.app.scenario_index = SCENARIOS.index(name)
            for simulation in self.app.simulations.values():
                simulation.reset(self.app.grid)
            for mode, expected_views in (("Individual", 1), ("Duelo", 2)):
                with self.subTest(name=name, mode=mode):
                    self.app.mode = mode
                    self.app._draw()
                    self.assertEqual(len(self.app.grid_views), expected_views)

    def test_layout_uses_full_height_without_header_band(self) -> None:
        width, height = self.app.screen.get_size()
        content, sidebar = self.app._layout_rects(width, height)
        self.assertEqual(content.top, OUTER_MARGIN)
        self.assertEqual(sidebar.top, OUTER_MARGIN)
        self.assertEqual(content.bottom, height - OUTER_MARGIN)
        self.assertEqual(sidebar.bottom, height - OUTER_MARGIN)
        self.assertEqual(sidebar.left - content.right, PANEL_GAP)

    def test_duel_grids_are_top_aligned_and_separated_by_small_gap(self) -> None:
        self.app.mode = "Duelo"
        self.app._draw()
        content, sidebar = self.app._layout_rects(*self.app.screen.get_size())
        greedy_rect, astar_rect = (view[0] for view in self.app.grid_views)
        self.assertEqual(greedy_rect.top, astar_rect.top)
        self.assertLess(greedy_rect.top, content.top + 50)
        self.assertEqual(astar_rect.left - greedy_rect.right, DUEL_GAP)
        self.assertLessEqual(astar_rect.right, content.right)
        self.assertLess(content.right, sidebar.left)

    def test_compact_layout_is_valid_at_minimum_window_size(self) -> None:
        content, sidebar = self.app._layout_rects(*self.app.window.minimum_size)
        self.assertGreater(content.width, sidebar.width)
        self.assertEqual(
            content.height,
            self.app.window.minimum_size[1] - 2 * OUTER_MARGIN,
        )
        self.assertEqual(sidebar.width, 300)
        self.assertEqual(sidebar.right, self.app.window.minimum_size[0] - OUTER_MARGIN)
        _, wide_sidebar = self.app._layout_rects(2000, 1000)
        self.assertEqual(wide_sidebar.width, 330)


if __name__ == "__main__":
    unittest.main()
