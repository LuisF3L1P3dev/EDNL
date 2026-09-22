import unittest

from labyrinth.model import Grid
from labyrinth.search import HeuristicType, SearchAlgorithm
from labyrinth.simulation import Simulation, SimulationState


class SimulationTests(unittest.TestCase):
    def test_search_then_walk_to_goal(self) -> None:
        grid = Grid(rows=5, cols=7, start=(2, 1), goal=(2, 5))
        simulation = Simulation(SearchAlgorithm.ASTAR)
        simulation.start(grid)
        for _ in range(200):
            simulation.advance()
            if simulation.terminal:
                break
        self.assertEqual(simulation.state, SimulationState.FINISHED)
        self.assertEqual(simulation.agent_position, grid.goal)
        self.assertEqual(simulation.metrics.path_cost, 4)

    def test_pause_and_resume(self) -> None:
        grid = Grid(rows=5, cols=7, start=(2, 1), goal=(2, 5))
        simulation = Simulation(SearchAlgorithm.GREEDY)
        simulation.start(grid)
        simulation.pause()
        self.assertEqual(simulation.state, SimulationState.PAUSED)
        simulation.resume()
        self.assertEqual(simulation.state, SimulationState.SEARCHING)

    def test_selected_heuristic_is_used(self) -> None:
        grid = Grid(rows=5, cols=7, start=(2, 1), goal=(2, 5))
        simulation = Simulation(SearchAlgorithm.ASTAR)
        simulation.start(grid, HeuristicType.EUCLIDEAN)
        simulation.advance()
        self.assertEqual(simulation.heuristic, HeuristicType.EUCLIDEAN)
        diagonal_position = (1, 1)
        self.assertAlmostEqual(
            simulation.h_values[diagonal_position],
            4.1231056256,
        )


if __name__ == "__main__":
    unittest.main()
