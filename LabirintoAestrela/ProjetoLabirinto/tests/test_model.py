import random
import unittest

from labyrinth.model import Grid, Movement


class GridTests(unittest.TestCase):
    def test_default_markers_are_valid_and_distinct(self) -> None:
        grid = Grid()

        self.assertTrue(grid.in_bounds(grid.start))
        self.assertTrue(grid.in_bounds(grid.goal))
        self.assertNotEqual(grid.start, grid.goal)
        self.assertNotIn(grid.start, grid.walls)
        self.assertNotIn(grid.goal, grid.walls)

    def test_four_direction_neighbors_have_orthogonal_cost(self) -> None:
        grid = Grid(rows=5, columns=5, start=(2, 2), goal=(4, 4))

        neighbors = dict(grid.neighbors((2, 2), Movement.FOUR))

        self.assertEqual(
            set(neighbors),
            {(1, 2), (2, 3), (3, 2), (2, 1)},
        )
        self.assertEqual(set(neighbors.values()), {10})

    def test_diagonal_cost_and_corner_cutting_rule(self) -> None:
        grid = Grid(rows=3, columns=3, start=(0, 0), goal=(2, 2))

        open_neighbors = dict(grid.neighbors((0, 0), Movement.EIGHT))
        self.assertEqual(open_neighbors[(1, 1)], 14)

        grid.set_wall((0, 1))
        blocked_neighbors = dict(grid.neighbors((0, 0), Movement.EIGHT))
        self.assertNotIn((1, 1), blocked_neighbors)
        self.assertIn((1, 0), blocked_neighbors)

    def test_endpoints_cannot_become_walls(self) -> None:
        grid = Grid(rows=5, columns=5, start=(2, 1), goal=(2, 3))

        self.assertFalse(grid.set_wall(grid.start))
        self.assertFalse(grid.set_wall(grid.goal))
        self.assertFalse(grid.set_start(grid.goal))
        self.assertFalse(grid.set_goal(grid.start))

    def test_moving_endpoint_removes_existing_wall(self) -> None:
        grid = Grid(rows=5, columns=5, start=(2, 1), goal=(2, 3))
        grid.set_wall((1, 1))

        changed = grid.set_start((1, 1))

        self.assertTrue(changed)
        self.assertEqual(grid.start, (1, 1))
        self.assertNotIn((1, 1), grid.walls)

    def test_random_maze_is_always_solvable_in_four_directions(self) -> None:
        for seed in range(20):
            with self.subTest(seed=seed):
                grid = Grid(rows=13, columns=19)
                grid.randomize(0.42, rng=random.Random(seed), max_attempts=3)
                self.assertTrue(grid.has_path(Movement.FOUR))

    def test_random_density_is_validated(self) -> None:
        grid = Grid()

        with self.assertRaises(ValueError):
            grid.randomize(0.8)


if __name__ == "__main__":
    unittest.main()
