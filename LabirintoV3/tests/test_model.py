import unittest

from labyrinth.model import Grid
from labyrinth.scenarios import SCENARIOS, create_scenario


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

    def test_all_scenarios_have_a_path(self) -> None:
        for name in SCENARIOS:
            with self.subTest(name=name):
                grid = create_scenario(name, seed=42)
                self.assertTrue(grid.has_path())
                self.assertNotIn(grid.start, grid.walls)
                self.assertNotIn(grid.goal, grid.walls)


if __name__ == "__main__":
    unittest.main()
