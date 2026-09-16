import unittest

from labyrinth.model import Grid, Movement
from labyrinth.search import (
    Algorithm,
    AStarStrategy,
    GreedyStrategy,
    SearchEngine,
    SearchEventType,
    SearchStrategy,
    heuristic,
    search_steps,
    solve,
)


GREEDY_TRAP = (
    "...#.........",
    "..#.........#",
    "......#..#...",
    ".#..#..#.#...",
    "A#...#......B",
    ".......##...#",
    ".........#...",
    "........#....",
    "#.##...##.#..",
)


def grid_from_ascii(lines: tuple[str, ...]) -> Grid:
    start = None
    goal = None
    walls: set[tuple[int, int]] = set()
    for row, line in enumerate(lines):
        for column, value in enumerate(line):
            position = (row, column)
            if value == "A":
                start = position
            elif value == "B":
                goal = position
            elif value == "#":
                walls.add(position)

    if start is None or goal is None:
        raise ValueError("O mapa de teste precisa conter A e B.")
    return Grid(
        rows=len(lines),
        columns=len(lines[0]),
        start=start,
        goal=goal,
        walls=walls,
    )


class HeuristicTests(unittest.TestCase):
    def test_manhattan_for_four_directions(self) -> None:
        self.assertEqual(heuristic((1, 2), (4, 6), Movement.FOUR), 70)

    def test_octile_for_eight_directions(self) -> None:
        self.assertEqual(heuristic((1, 2), (4, 6), Movement.EIGHT), 52)


class StrategyTests(unittest.TestCase):
    def test_astar_combines_cost_and_estimate_and_accepts_better_routes(self) -> None:
        strategy = AStarStrategy()

        self.assertIsInstance(strategy, SearchStrategy)
        self.assertIs(strategy.algorithm, Algorithm.ASTAR)
        self.assertEqual(strategy.priority(path_cost=30, estimate=40), 70)
        self.assertTrue(strategy.should_update(None, 30))
        self.assertTrue(strategy.should_update(40, 30))
        self.assertFalse(strategy.should_update(30, 30))
        self.assertFalse(strategy.should_update(20, 30))

    def test_greedy_uses_estimate_and_accepts_only_first_route(self) -> None:
        strategy = GreedyStrategy()

        self.assertIsInstance(strategy, SearchStrategy)
        self.assertIs(strategy.algorithm, Algorithm.GREEDY)
        self.assertEqual(strategy.priority(path_cost=30, estimate=40), 40)
        self.assertTrue(strategy.should_update(None, 30))
        self.assertFalse(strategy.should_update(40, 30))
        self.assertFalse(strategy.should_update(20, 30))


class SearchTests(unittest.TestCase):
    def test_straight_path_has_expected_cost(self) -> None:
        grid = Grid(rows=5, columns=7, start=(2, 1), goal=(2, 5))

        for algorithm in Algorithm:
            with self.subTest(algorithm=algorithm):
                result = solve(grid, algorithm, Movement.FOUR)
                self.assertTrue(result.found)
                self.assertEqual(result.cost, 40)
                self.assertEqual(len(result.path) - 1, 4)

    def test_diagonal_path_uses_cost_fourteen(self) -> None:
        grid = Grid(rows=5, columns=5, start=(1, 1), goal=(3, 3))

        result = solve(grid, Algorithm.ASTAR, Movement.EIGHT)

        self.assertTrue(result.found)
        self.assertEqual(result.cost, 28)
        self.assertEqual(result.path, ((1, 1), (2, 2), (3, 3)))

    def test_astar_finds_better_path_than_greedy_in_trap(self) -> None:
        grid = grid_from_ascii(GREEDY_TRAP)

        greedy = solve(grid, Algorithm.GREEDY, Movement.FOUR)
        astar = solve(grid, Algorithm.ASTAR, Movement.FOUR)

        self.assertEqual(greedy.cost, 160)
        self.assertEqual(astar.cost, 140)
        self.assertGreater(greedy.cost, astar.cost)

    def test_no_path_is_reported(self) -> None:
        walls = {(row, 2) for row in range(5)}
        grid = Grid(
            rows=5,
            columns=5,
            start=(2, 0),
            goal=(2, 4),
            walls=walls,
        )

        for algorithm in Algorithm:
            with self.subTest(algorithm=algorithm):
                result = solve(grid, algorithm, Movement.FOUR)
                self.assertFalse(result.found)
                self.assertIsNone(result.cost)
                self.assertEqual(result.path, ())

    def test_incremental_events_finish_with_path_and_metrics(self) -> None:
        grid = Grid(rows=5, columns=7, start=(2, 1), goal=(2, 5))

        events = list(search_steps(grid, Algorithm.ASTAR, Movement.FOUR))

        self.assertGreater(len(events), 1)
        self.assertEqual(events[-1].kind, SearchEventType.FOUND)
        self.assertEqual(events[-1].metrics.path_cost, 40)
        self.assertEqual(events[-1].metrics.path_length, 4)
        explored_counts = [event.metrics.nodes_explored for event in events]
        self.assertEqual(explored_counts, sorted(explored_counts))
        self.assertGreaterEqual(events[-1].metrics.elapsed_ms, 0)

    def test_repeated_search_is_deterministic(self) -> None:
        grid = grid_from_ascii(GREEDY_TRAP)

        first = solve(grid, Algorithm.ASTAR, Movement.FOUR)
        second = solve(grid, Algorithm.ASTAR, Movement.FOUR)

        self.assertEqual(first.path, second.path)
        self.assertEqual(first.nodes_explored, second.nodes_explored)


class SearchEngineTests(unittest.TestCase):
    def test_engine_results_match_functional_facade(self) -> None:
        blocked = Grid(
            rows=5,
            columns=5,
            start=(2, 0),
            goal=(2, 4),
            walls={(row, 2) for row in range(5)},
        )
        scenarios = (
            (
                Grid(rows=5, columns=7, start=(2, 1), goal=(2, 5)),
                Movement.FOUR,
                Algorithm.ASTAR,
                AStarStrategy,
            ),
            (
                Grid(rows=5, columns=5, start=(1, 1), goal=(3, 3)),
                Movement.EIGHT,
                Algorithm.ASTAR,
                AStarStrategy,
            ),
            (
                grid_from_ascii(GREEDY_TRAP),
                Movement.FOUR,
                Algorithm.GREEDY,
                GreedyStrategy,
            ),
            (blocked, Movement.FOUR, Algorithm.ASTAR, AStarStrategy),
            (blocked, Movement.FOUR, Algorithm.GREEDY, GreedyStrategy),
        )

        for grid, movement, algorithm, strategy_type in scenarios:
            with self.subTest(
                movement=movement,
                algorithm=algorithm,
                blocked=grid is blocked,
            ):
                engine_result = SearchEngine(
                    grid,
                    movement,
                    strategy_type(),
                ).solve()
                facade_result = solve(grid, algorithm, movement)

                self.assertEqual(engine_result.algorithm, facade_result.algorithm)
                self.assertEqual(engine_result.movement, facade_result.movement)
                self.assertEqual(engine_result.found, facade_result.found)
                self.assertEqual(engine_result.path, facade_result.path)
                self.assertEqual(engine_result.cost, facade_result.cost)
                self.assertEqual(
                    engine_result.nodes_explored,
                    facade_result.nodes_explored,
                )

    def test_engine_steps_match_facade_events(self) -> None:
        grid = grid_from_ascii(GREEDY_TRAP)

        engine_events = list(
            SearchEngine(grid, Movement.FOUR, AStarStrategy()).steps()
        )
        facade_events = list(
            search_steps(grid, Algorithm.ASTAR, Movement.FOUR)
        )

        def stable_event_data(events):
            return [
                (
                    event.kind,
                    event.current,
                    event.opened,
                    event.path,
                    event.metrics.nodes_explored,
                    event.metrics.frontier_size,
                    event.metrics.path_cost,
                    event.metrics.path_length,
                )
                for event in events
            ]

        self.assertEqual(
            stable_event_data(engine_events),
            stable_event_data(facade_events),
        )

    def test_old_and_new_public_imports_refer_to_same_classes(self) -> None:
        import labyrinth
        from labyrinth.search_core import (
            AStarStrategy as CoreAStarStrategy,
            GreedyStrategy as CoreGreedyStrategy,
            SearchEngine as CoreSearchEngine,
            SearchStrategy as CoreSearchStrategy,
        )

        self.assertIs(labyrinth.AStarStrategy, CoreAStarStrategy)
        self.assertIs(labyrinth.GreedyStrategy, CoreGreedyStrategy)
        self.assertIs(labyrinth.SearchEngine, CoreSearchEngine)
        self.assertIs(labyrinth.SearchStrategy, CoreSearchStrategy)


if __name__ == "__main__":
    unittest.main()
