"""Busca Gulosa e A* expostas como geradores incrementais."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import heapq
from itertools import count
from math import hypot
from time import perf_counter_ns
from typing import Iterator

from .model import Grid, Position


class SearchAlgorithm(str, Enum):
    GREEDY = "Busca Gulosa"
    ASTAR = "Algoritmo A*"


class HeuristicType(str, Enum):
    MANHATTAN = "Manhattan"
    EUCLIDEAN = "Euclidiana"


class EventKind(str, Enum):
    STEP = "step"
    FOUND = "found"
    NO_PATH = "no_path"


@dataclass(slots=True)
class SearchMetrics:
    elapsed_ms: float = 0.0
    nodes_explored: int = 0
    frontier_size: int = 0
    path_cost: int | None = None
    path_steps: int | None = None


@dataclass(slots=True)
class SearchEvent:
    kind: EventKind
    current: Position | None
    frontier: set[Position]
    explored: set[Position]
    metrics: SearchMetrics
    path: list[Position] = field(default_factory=list)
    g_values: dict[Position, int] = field(default_factory=dict)
    h_values: dict[Position, float] = field(default_factory=dict)
    scores: dict[Position, float] = field(default_factory=dict)


def manhattan(origin: Position, target: Position) -> int:
    return abs(origin[0] - target[0]) + abs(origin[1] - target[1])


def euclidean(origin: Position, target: Position) -> float:
    return hypot(origin[0] - target[0], origin[1] - target[1])


def heuristic_distance(
    origin: Position,
    target: Position,
    heuristic: HeuristicType,
) -> float:
    if heuristic is HeuristicType.EUCLIDEAN:
        return euclidean(origin, target)
    return float(manhattan(origin, target))


def search_steps(
    grid: Grid,
    algorithm: SearchAlgorithm,
    heuristic: HeuristicType = HeuristicType.MANHATTAN,
) -> Iterator[SearchEvent]:
    """Emite um retrato depois de cada expansão sem incluir atrasos visuais."""

    start, goal = grid.start, grid.goal
    sequence = count()
    g_values: dict[Position, int] = {start: 0}
    h_values: dict[Position, float] = {
        start: heuristic_distance(start, goal, heuristic)
    }
    scores: dict[Position, float] = {start: h_values[start]}
    parents: dict[Position, Position] = {}
    frontier_heap: list[tuple[float, float, int, Position, int]] = []
    heapq.heappush(frontier_heap, (h_values[start], h_values[start], next(sequence), start, 0))
    frontier_set = {start}
    explored: set[Position] = set()
    elapsed_ns = 0

    while frontier_heap:
        tick_start = perf_counter_ns()
        current: Position | None = None
        while frontier_heap:
            _, _, _, candidate, recorded_g = heapq.heappop(frontier_heap)
            if candidate in explored:
                continue
            if algorithm is SearchAlgorithm.ASTAR and recorded_g != g_values.get(candidate):
                continue
            current = candidate
            break

        if current is None:
            elapsed_ns += perf_counter_ns() - tick_start
            break

        frontier_set.discard(current)
        explored.add(current)

        if current == goal:
            path = _reconstruct_path(parents, goal)
            elapsed_ns += perf_counter_ns() - tick_start
            yield _event(
                EventKind.FOUND, current, frontier_set, explored, elapsed_ns,
                g_values, h_values, scores, path,
            )
            return

        for neighbor in grid.neighbors(current):
            if neighbor in explored:
                continue
            tentative_g = g_values[current] + 1
            known_g = g_values.get(neighbor)
            if algorithm is SearchAlgorithm.GREEDY:
                if known_g is not None:
                    continue
            elif known_g is not None and tentative_g >= known_g:
                continue

            parents[neighbor] = current
            g_values[neighbor] = tentative_g
            heuristic_value = heuristic_distance(neighbor, goal, heuristic)
            h_values[neighbor] = heuristic_value
            score = (
                heuristic_value
                if algorithm is SearchAlgorithm.GREEDY
                else tentative_g + heuristic_value
            )
            scores[neighbor] = score
            heapq.heappush(
                frontier_heap,
                (score, heuristic_value, next(sequence), neighbor, tentative_g),
            )
            frontier_set.add(neighbor)

        elapsed_ns += perf_counter_ns() - tick_start
        yield _event(
            EventKind.STEP, current, frontier_set, explored, elapsed_ns,
            g_values, h_values, scores,
        )

    yield _event(
        EventKind.NO_PATH, None, set(), explored, elapsed_ns,
        g_values, h_values, scores,
    )


def solve(
    grid: Grid,
    algorithm: SearchAlgorithm,
    heuristic: HeuristicType = HeuristicType.MANHATTAN,
) -> SearchEvent:
    final_event: SearchEvent | None = None
    for final_event in search_steps(grid, algorithm, heuristic):
        pass
    if final_event is None:
        raise RuntimeError("A busca terminou sem produzir resultado.")
    return final_event


def _event(
    kind: EventKind,
    current: Position | None,
    frontier: set[Position],
    explored: set[Position],
    elapsed_ns: int,
    g_values: dict[Position, int],
    h_values: dict[Position, float],
    scores: dict[Position, float],
    path: list[Position] | None = None,
) -> SearchEvent:
    final_path = path or []
    metrics = SearchMetrics(
        elapsed_ms=elapsed_ns / 1_000_000,
        nodes_explored=len(explored),
        frontier_size=len(frontier),
        path_cost=len(final_path) - 1 if final_path else None,
        path_steps=len(final_path) - 1 if final_path else None,
    )
    return SearchEvent(
        kind=kind,
        current=current,
        frontier=set(frontier),
        explored=set(explored),
        metrics=metrics,
        path=list(final_path),
        g_values=dict(g_values),
        h_values=dict(h_values),
        scores=dict(scores),
    )


def _reconstruct_path(parents: dict[Position, Position], goal: Position) -> list[Position]:
    path = [goal]
    while path[-1] in parents:
        path.append(parents[path[-1]])
    path.reverse()
    return path
