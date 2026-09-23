package br.edu.ifrn.labirintojava.algorithm;

import br.edu.ifrn.labirintojava.model.*;
import br.edu.ifrn.labirintojava.service.PresetMaps;
import br.edu.ifrn.labirintojava.service.ComparisonService;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class SearchAlgorithmsTest {
    private record Distance(Position position, int cost) { }

    private SearchStep finish(SearchAlgorithm algorithm, GridMap map, MovementMode mode) {
        SearchSession session = algorithm.createSession(map, mode);
        SearchStep step;
        int explored = 0;
        do {
            step = session.step();
            assertNotNull(step.expanded(), "Um passo expande um nó válido");
            assertEquals(++explored, step.explored());
            assertEquals(step.discovered() - step.explored(), step.frontier());
        } while (step.status() == SearchStatus.RUNNING);
        return step;
    }

    private void assertValidRoute(GridMap map, MovementMode mode, SearchStep result) {
        assertEquals(SearchStatus.FOUND, result.status());
        List<Position> path = result.path();
        assertEquals(map.start(), path.getFirst());
        assertEquals(map.goal(), path.getLast());
        int cost = 0;
        for (int i = 0; i < path.size(); i++) {
            Position p = path.get(i);
            assertTrue(map.isFree(p.x(), p.y()));
            if (i > 0) {
                Position previous = path.get(i - 1);
                assertTrue(mode.neighbors(map, previous).contains(p), "Movimento ilegal " + previous + " -> " + p);
                cost += mode.cost(previous, p);
            }
        }
        assertEquals(cost, result.routeCost());
    }

    @Test void pathsAndCostsAreValid() {
        for (PresetMaps.Preset preset : PresetMaps.Preset.values()) {
            GridMap map = PresetMaps.load(preset);
            for (MovementMode mode : MovementMode.values()) {
                assertValidRoute(map, mode, finish(new AStarSearch(), map, mode));
                assertValidRoute(map, mode, finish(new GreedySearch(), map, mode));
            }
        }
    }

    @Test void aStarMatchesDijkstraOnPresetsAndGeneratedMaps() {
        List<GridMap> maps = new ArrayList<>();
        for (PresetMaps.Preset preset : PresetMaps.Preset.values()) maps.add(PresetMaps.load(preset));
        Random random = new Random(328734L);
        for (int sample = 0; sample < 20; sample++) {
            GridMap map = new GridMap(10, 10);
            for (int y = 0; y < 10; y++)
                for (int x = 0; x < 10; x++)
                    if (random.nextDouble() < .27) map.setWall(new Position(x, y), true);
            maps.add(map);
        }
        for (GridMap map : maps) {
            for (MovementMode mode : MovementMode.values()) {
                int optimal = dijkstra(map, mode);
                SearchStep result = finish(new AStarSearch(), map, mode);
                if (optimal == Integer.MAX_VALUE) {
                    assertEquals(SearchStatus.NO_PATH, result.status());
                    assertTrue(result.path().isEmpty());
                } else {
                    assertValidRoute(map, mode, result);
                    assertEquals(optimal, result.routeCost());
                }
            }
        }
    }

    @Test void blockedMapHasNoRoute() {
        GridMap map = new GridMap(5, 5);
        map.setWall(new Position(1, 0), true);
        map.setWall(new Position(0, 1), true);
        for (MovementMode mode : MovementMode.values())
            for (SearchAlgorithm algorithm : List.of(new AStarSearch(), new GreedySearch())) {
                SearchStep result = finish(algorithm, map, mode);
                assertEquals(SearchStatus.NO_PATH, result.status());
                assertEquals(-1, result.routeCost());
            }
    }

    @Test void equalStartAndGoalHasZeroCost() {
        GridMap map = new GridMap(5, 5);
        map.setGoal(map.start());
        for (SearchAlgorithm algorithm : List.of(new AStarSearch(), new GreedySearch())) {
            SearchStep result = finish(algorithm, map, MovementMode.EIGHT);
            assertEquals(SearchStatus.FOUND, result.status());
            assertEquals(List.of(map.start()), result.path());
            assertEquals(0, result.routeCost());
            assertEquals(1, result.explored());
        }
    }

    @Test void diagonalRequiresBothSideCells() {
        GridMap map = new GridMap(3, 3);
        Position start = new Position(0, 0);
        Position diagonal = new Position(1, 1);
        assertEquals(14, MovementMode.EIGHT.cost(start, diagonal));
        assertTrue(MovementMode.EIGHT.neighbors(map, start).contains(diagonal));
        map.setWall(new Position(1, 0), true);
        assertFalse(MovementMode.EIGHT.neighbors(map, start).contains(diagonal));
        map.setWall(new Position(1, 0), false);
        map.setWall(new Position(0, 1), true);
        assertFalse(MovementMode.EIGHT.neighbors(map, start).contains(diagonal));
        assertFalse(MovementMode.FOUR.neighbors(map, start).contains(diagonal));
    }

    @Test void heuristicsAreConsistent() {
        GridMap map = new GridMap(6, 6);
        for (MovementMode mode : MovementMode.values())
            for (int y = 0; y < map.height(); y++)
                for (int x = 0; x < map.width(); x++) {
                    Position p = new Position(x, y);
                    for (Position neighbor : mode.neighbors(map, p))
                        assertTrue(mode.heuristic(p, map.goal()) <= mode.cost(p, neighbor)
                                + mode.heuristic(neighbor, map.goal()));
                }
        assertEquals(28, MovementMode.EIGHT.heuristic(new Position(0, 0), new Position(2, 2)));
        assertEquals(40, MovementMode.FOUR.heuristic(new Position(0, 0), new Position(2, 2)));
    }

    @Test void aStarImprovesPreviouslyDiscoveredCost() {
        GridMap map = PresetMaps.load(PresetMaps.Preset.GREEDY_TRAP);
        SearchSession session = new AStarSearch().createSession(map, MovementMode.FOUR);
        Map<Position, Integer> previous = new HashMap<>();
        boolean improved = false;
        SearchStep step;
        do {
            step = session.step();
            for (Map.Entry<Position, NodeScore> change : step.scoresChanged().entrySet()) {
                Integer old = previous.put(change.getKey(), change.getValue().g());
                if (old != null && change.getValue().g() < old) improved = true;
            }
        } while (step.status() == SearchStatus.RUNNING);
        assertTrue(improved);
        assertEquals(180, step.routeCost());
    }

    @Test void greedyTrapHasHigherCost() {
        GridMap map = PresetMaps.load(PresetMaps.Preset.GREEDY_TRAP);
        SearchStep greedy = finish(new GreedySearch(), map, MovementMode.FOUR);
        SearchStep astar = finish(new AStarSearch(), map, MovementMode.FOUR);
        assertValidRoute(map, MovementMode.FOUR, greedy);
        assertValidRoute(map, MovementMode.FOUR, astar);
        assertEquals(220, greedy.routeCost());
        assertEquals(180, astar.routeCost());
    }

    @Test void comparisonUsesIndependentCopies() {
        GridMap source = new GridMap(5, 5);
        List<ComparisonService.RunPlan> plans = new ComparisonService()
                .prepare(source, MovementMode.FOUR, new AStarSearch(), true);
        assertEquals(2, plans.size());
        assertEquals(source.start(), plans.get(0).map().start());
        assertEquals(source.goal(), plans.get(1).map().goal());
        plans.get(0).map().setWall(new Position(2, 2), true);
        assertFalse(plans.get(1).map().isWall(2, 2));
        assertFalse(source.isWall(2, 2));
    }

    private int dijkstra(GridMap map, MovementMode mode) {
        Map<Position, Integer> best = new HashMap<>();
        PriorityQueue<Distance> queue = new PriorityQueue<>(Comparator.comparingInt(Distance::cost));
        best.put(map.start(), 0);
        queue.add(new Distance(map.start(), 0));
        while (!queue.isEmpty()) {
            Distance current = queue.remove();
            if (current.cost() != best.get(current.position())) continue;
            if (current.position().equals(map.goal())) return current.cost();
            for (Position neighbor : mode.neighbors(map, current.position())) {
                int candidate = current.cost() + mode.cost(current.position(), neighbor);
                if (candidate < best.getOrDefault(neighbor, Integer.MAX_VALUE)) {
                    best.put(neighbor, candidate);
                    queue.add(new Distance(neighbor, candidate));
                }
            }
        }
        return Integer.MAX_VALUE;
    }
}
