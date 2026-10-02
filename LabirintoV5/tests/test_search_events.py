import unittest

from astar import astar, eventos_astar
from guloso import busca_gulosa, eventos_gulosa


class MazeStub:
    def __init__(self, connected: bool = True) -> None:
        self.rows = 2
        self.cols = 2
        self.grid = [(1, 1), (1, 2), (2, 1), (2, 2)]
        directions = "NSEW"
        self.maze_map = {
            cell: {direction: 0 for direction in directions}
            for cell in self.grid
        }
        if connected:
            self._connect((2, 2), "N", (1, 2))
            self._connect((2, 2), "W", (2, 1))
            self._connect((1, 2), "W", (1, 1))
            self._connect((2, 1), "N", (1, 1))

    def _connect(self, cell, direction, neighbor) -> None:
        opposite = {"N": "S", "S": "N", "E": "W", "W": "E"}
        self.maze_map[cell][direction] = 1
        self.maze_map[neighbor][opposite[direction]] = 1


class SearchEventTests(unittest.TestCase):
    def assert_valid_path(self, maze, path) -> None:
        cell = (maze.rows, maze.cols)
        goal = (1, 1)
        visited = set()
        while cell != goal:
            self.assertIn(cell, path)
            self.assertNotIn(cell, visited)
            visited.add(cell)
            next_cell = path[cell]
            self.assertEqual(abs(cell[0] - next_cell[0]) + abs(cell[1] - next_cell[1]), 1)
            cell = next_cell

    def test_greedy_emits_frontier_and_final_route(self) -> None:
        maze = MazeStub()
        events = list(eventos_gulosa(maze))

        self.assertEqual(events[0].current, (2, 2))
        self.assertEqual(events[0].frontier, frozenset({(1, 2), (2, 1)}))
        self.assertIn((2, 2), events[0].visited)
        self.assertTrue(events[-1].done)
        self.assertTrue(events[-1].found)
        self.assert_valid_path(maze, events[-1].path)
        self.assertEqual(busca_gulosa(maze), events[-1].path)

    def test_astar_emits_frontier_and_final_route(self) -> None:
        maze = MazeStub()
        events = list(eventos_astar(maze))

        self.assertEqual(events[0].current, (2, 2))
        self.assertEqual(events[0].frontier, frozenset({(1, 2), (2, 1)}))
        self.assertIn((2, 2), events[0].visited)
        self.assertTrue(events[-1].done)
        self.assertTrue(events[-1].found)
        self.assert_valid_path(maze, events[-1].path)
        self.assertEqual(astar(maze), events[-1].path)
        self.assertLessEqual(len(events[-1].path), len(busca_gulosa(maze)))

    def test_both_searches_report_unreachable_goal(self) -> None:
        maze = MazeStub(connected=False)

        for events in (list(eventos_gulosa(maze)), list(eventos_astar(maze))):
            self.assertTrue(events[-1].done)
            self.assertFalse(events[-1].found)
            self.assertEqual(events[-1].path, {})
            self.assertEqual(events[-1].frontier, frozenset())


if __name__ == "__main__":
    unittest.main()
