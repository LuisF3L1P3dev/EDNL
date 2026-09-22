import unittest

from labyrinth.model import Grid
from labyrinth.scenarios import create_scenario
from labyrinth.search import (
    EventKind,
    HeuristicType,
    SearchAlgorithm,
    euclidean,
    manhattan,
    search_steps,
    solve,
)


class SearchTests(unittest.TestCase):
    def test_manhattan(self) -> None:
        self.assertEqual(manhattan((2, 3), (7, 1)), 7)

    def test_euclidean(self) -> None:
        self.assertEqual(euclidean((0, 0), (3, 4)), 5.0)

    def test_open_grid_has_optimal_path(self) -> None:
        grid = Grid(rows=7, cols=9, start=(1, 1), goal=(5, 7))
        for heuristic in HeuristicType:
            with self.subTest(heuristic=heuristic):
                result = solve(grid, SearchAlgorithm.ASTAR, heuristic)
                self.assertEqual(result.kind, EventKind.FOUND)
                self.assertEqual(result.metrics.path_cost, 10)
                self.assertEqual(result.path[0], grid.start)
                self.assertEqual(result.path[-1], grid.goal)

    def test_astar_is_optimal_in_greedy_trap(self) -> None:
        grid = create_scenario("Armadilha Gulosa")
        astar = solve(grid, SearchAlgorithm.ASTAR)
        greedy = solve(grid, SearchAlgorithm.GREEDY)
        self.assertEqual(astar.metrics.path_cost, 48)
        self.assertEqual(greedy.metrics.path_cost, 58)
        self.assertLess(astar.metrics.path_cost, greedy.metrics.path_cost)

    def test_new_educational_scenarios_are_solved_by_both_algorithms(self) -> None:
        names = (
            "Ponte estreita",
            "Becos sem saída",
            "Tabuleiro",
            "Arquipélago",
        )
        for name in names:
            grid = create_scenario(name)
            for algorithm in (SearchAlgorithm.GREEDY, SearchAlgorithm.ASTAR):
                with self.subTest(name=name, algorithm=algorithm):
                    result = solve(grid, algorithm)
                    self.assertEqual(result.kind, EventKind.FOUND)
                    self.assertEqual(result.path[0], grid.start)
                    self.assertEqual(result.path[-1], grid.goal)

    def test_tabuleiro_and_archipelago_expose_greedy_suboptimality(self) -> None:
        for name in ("Tabuleiro", "Arquipélago"):
            with self.subTest(name=name):
                grid = create_scenario(name)
                greedy = solve(grid, SearchAlgorithm.GREEDY)
                astar = solve(grid, SearchAlgorithm.ASTAR)
                self.assertLess(astar.metrics.path_cost, greedy.metrics.path_cost)

    def test_scores_follow_each_algorithm_definition(self) -> None:
        grid = Grid(rows=5, cols=7, start=(2, 1), goal=(2, 5))
        for heuristic in HeuristicType:
            with self.subTest(heuristic=heuristic):
                greedy_event = next(
                    search_steps(grid, SearchAlgorithm.GREEDY, heuristic)
                )
                astar_event = next(
                    search_steps(grid, SearchAlgorithm.ASTAR, heuristic)
                )
                for position, score in greedy_event.scores.items():
                    self.assertEqual(score, greedy_event.h_values[position])
                for position, score in astar_event.scores.items():
                    self.assertEqual(
                        score,
                        astar_event.g_values[position]
                        + astar_event.h_values[position],
                    )

    def test_no_path(self) -> None:
        grid = Grid(rows=5, cols=5, start=(2, 1), goal=(2, 3))
        grid.walls = {(row, 2) for row in range(5)}
        result = solve(grid, SearchAlgorithm.ASTAR)
        self.assertEqual(result.kind, EventKind.NO_PATH)
        self.assertIsNone(result.metrics.path_cost)
        self.assertEqual(result.metrics.frontier_size, 0)


if __name__ == "__main__":
    unittest.main()
