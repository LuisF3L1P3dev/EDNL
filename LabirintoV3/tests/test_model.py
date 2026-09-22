import unittest

from labyrinth.model import Grid
from labyrinth.scenarios import (
    MAX_COLS,
    MAX_ROWS,
    MIN_COLS,
    MIN_ROWS,
    SCENARIOS,
    SCENARIO_LABELS,
    create_empty_grid,
    create_scenario,
)


class GridTests(unittest.TestCase):
    def test_neighbors_are_orthogonal_and_respect_walls(self) -> None:
        grid = Grid(rows=5, cols=5, start=(2, 1), goal=(2, 4), walls={(1, 2)})
        self.assertEqual(
            set(grid.neighbors((2, 2))),
            {(2, 1), (2, 3), (3, 2)},
        )

    def test_endpoints_cannot_become_walls(self) -> None:
        grid = Grid()
        self.assertFalse(grid.set_wall(grid.start))
        self.assertFalse(grid.set_wall(grid.goal))

    def test_clone_is_independent(self) -> None:
        grid = Grid(walls={(1, 1)})
        clone = grid.clone()
        clone.set_wall((2, 2))
        self.assertNotIn((2, 2), grid.walls)

    def test_catalog_has_all_twelve_scenarios_in_selector_order(self) -> None:
        self.assertEqual(
            SCENARIOS,
            (
                "Mundo aberto",
                "Armadilha Gulosa",
                "Labirinto clássico",
                "Aleatório",
                "Zigue-zague",
                "Salas e portas",
                "Espiral",
                "Duas rotas",
                "Ponte estreita",
                "Becos sem saída",
                "Tabuleiro",
                "Arquipélago",
            ),
        )
        self.assertEqual(tuple(SCENARIO_LABELS), SCENARIOS)

    def test_all_scenarios_have_exact_size_valid_endpoints_and_path(self) -> None:
        sizes = ((MIN_ROWS, MIN_COLS), (21, 31), (MAX_ROWS, MAX_COLS))
        for name in SCENARIOS:
            for rows, cols in sizes:
                with self.subTest(name=name, rows=rows, cols=cols):
                    grid = create_scenario(name, seed=42, rows=rows, cols=cols)
                    self.assertEqual((grid.rows, grid.cols), (rows, cols))
                    self.assertTrue(grid.in_bounds(grid.start))
                    self.assertTrue(grid.in_bounds(grid.goal))
                    self.assertNotEqual(grid.start, grid.goal)
                    self.assertTrue(all(grid.in_bounds(wall) for wall in grid.walls))
                    self.assertNotIn(grid.start, grid.walls)
                    self.assertNotIn(grid.goal, grid.walls)
                    self.assertTrue(grid.has_path())

    def test_fixed_scenarios_are_deterministic_for_the_same_size(self) -> None:
        for name in (scenario for scenario in SCENARIOS if scenario != "Aleatório"):
            with self.subTest(name=name):
                first = create_scenario(name, seed=1, rows=17, cols=29)
                second = create_scenario(name, seed=999, rows=17, cols=29)
                self.assertEqual(first.start, second.start)
                self.assertEqual(first.goal, second.goal)
                self.assertEqual(first.walls, second.walls)

    def test_random_scenario_repeats_with_seed(self) -> None:
        first = create_scenario("Aleatório", seed=42, rows=17, cols=29)
        second = create_scenario("Aleatório", seed=42, rows=17, cols=29)
        other = create_scenario("Aleatório", seed=43, rows=17, cols=29)
        self.assertEqual(first.walls, second.walls)
        self.assertNotEqual(first.walls, other.walls)

    def test_new_scenarios_have_distinct_obstacle_patterns(self) -> None:
        names = (
            "Ponte estreita",
            "Becos sem saída",
            "Tabuleiro",
            "Arquipélago",
        )
        patterns = []
        for name in names:
            with self.subTest(name=name):
                grid = create_scenario(name)
                self.assertTrue(grid.walls)
                patterns.append(frozenset(grid.walls))
        self.assertEqual(len(set(patterns)), len(names))

    def test_custom_grid_accepts_boundary_sizes(self) -> None:
        for rows, cols in ((MIN_ROWS, MIN_COLS), (MAX_ROWS, MAX_COLS)):
            with self.subTest(rows=rows, cols=cols):
                grid = create_empty_grid(rows, cols)
                self.assertEqual((grid.rows, grid.cols), (rows, cols))
                self.assertTrue(grid.in_bounds(grid.start))
                self.assertTrue(grid.in_bounds(grid.goal))
                self.assertNotEqual(grid.start, grid.goal)
                self.assertFalse(grid.walls)

    def test_custom_grid_rejects_sizes_outside_limits(self) -> None:
        for rows, cols in (
            (MIN_ROWS - 1, MIN_COLS),
            (MAX_ROWS + 1, MIN_COLS),
            (MIN_ROWS, MIN_COLS - 1),
            (MIN_ROWS, MAX_COLS + 1),
        ):
            with self.subTest(rows=rows, cols=cols):
                with self.assertRaises(ValueError):
                    create_empty_grid(rows, cols)


if __name__ == "__main__":
    unittest.main()
