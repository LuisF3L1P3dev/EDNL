"""Implementações incrementais de Busca Gulosa e A*."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import heapq
from itertools import count
from time import perf_counter
from typing import Iterator

from .model import Grid, Movement, Position


class Algorithm(str, Enum):
    GREEDY = "Busca Gulosa"
    ASTAR = "A*"


class SearchEventType(str, Enum):
    EXPANDED = "expanded"
    FOUND = "found"
    NO_PATH = "no_path"


@dataclass(frozen=True, slots=True)
class SearchMetrics:
    nodes_explored: int = 0
    frontier_size: int = 0
    elapsed_ms: float = 0.0
    path_cost: int | None = None
    path_length: int | None = None


@dataclass(frozen=True, slots=True)
class SearchEvent:
    kind: SearchEventType
    current: Position | None
    opened: tuple[Position, ...]
    metrics: SearchMetrics
    path: tuple[Position, ...] = ()


@dataclass(frozen=True, slots=True)
class SearchResult:
    algorithm: Algorithm
    movement: Movement
    found: bool
    path: tuple[Position, ...]
    cost: int | None
    nodes_explored: int
    elapsed_ms: float


def manhattan(position: Position, goal: Position) -> int:
    """Distância Manhattan usando custo ortogonal igual a 10."""

    return 10 * (
        abs(position[0] - goal[0]) + abs(position[1] - goal[1])
    )


def octile(position: Position, goal: Position) -> int:
    """Distância octil usando custos 10 (reto) e 14 (diagonal)."""

    row_distance = abs(position[0] - goal[0])
    column_distance = abs(position[1] - goal[1])
    diagonal_steps = min(row_distance, column_distance)
    straight_steps = max(row_distance, column_distance) - diagonal_steps
    return 14 * diagonal_steps + 10 * straight_steps


def heuristic(position: Position, goal: Position, movement: Movement) -> int:
    if movement is Movement.EIGHT:
        return octile(position, goal)
    return manhattan(position, goal)


def search_steps(
    grid: Grid,
    algorithm: Algorithm,
    movement: Movement,
) -> Iterator[SearchEvent]:
    """Executa uma busca e produz um evento a cada expansão.

    O tempo registrado considera apenas o trabalho executado entre duas
    suspensões do gerador, excluindo o atraso visual controlado pelo Tkinter.
    """

    assert grid.start is not None
    assert grid.goal is not None
    start = grid.start
    goal = grid.goal
    sequence = count()
    frontier: list[tuple[int, int, int, Position, int]] = []
    open_positions: set[Position] = {start}
    closed: set[Position] = set()
    parents: dict[Position, Position] = {}
    costs: dict[Position, int] = {start: 0}
    elapsed_seconds = 0.0
    explored = 0

    initial_h = heuristic(start, goal, movement)
    initial_priority = initial_h
    heapq.heappush(
        frontier,
        (initial_priority, initial_h, next(sequence), start, 0),
    )

    while frontier:
        operation_started = perf_counter()
        current: Position | None = None

        while frontier:
            _, _, _, candidate, recorded_cost = heapq.heappop(frontier)
            if candidate in closed:
                continue
            if recorded_cost != costs.get(candidate):
                continue
            current = candidate
            break

        if current is None:
            elapsed_seconds += perf_counter() - operation_started
            break

        open_positions.discard(current)
        closed.add(current)
        explored += 1

        if current == goal:
            path = _reconstruct_path(parents, current)
            elapsed_seconds += perf_counter() - operation_started
            metrics = SearchMetrics(
                nodes_explored=explored,
                frontier_size=len(open_positions),
                elapsed_ms=elapsed_seconds * 1000,
                path_cost=costs[current],
                path_length=max(0, len(path) - 1),
            )
            yield SearchEvent(
                kind=SearchEventType.FOUND,
                current=current,
                opened=(),
                metrics=metrics,
                path=path,
            )
            return

        opened: list[Position] = []
        current_cost = costs[current]
        for neighbor, movement_cost in grid.neighbors(current, movement):
            if neighbor in closed:
                continue

            tentative_cost = current_cost + movement_cost
            known_cost = costs.get(neighbor)
            if algorithm is Algorithm.GREEDY:
                should_update = known_cost is None
            else:
                should_update = known_cost is None or tentative_cost < known_cost

            if not should_update:
                continue

            costs[neighbor] = tentative_cost
            parents[neighbor] = current
            estimate = heuristic(neighbor, goal, movement)
            priority = estimate
            if algorithm is Algorithm.ASTAR:
                priority += tentative_cost
            heapq.heappush(
                frontier,
                (
                    priority,
                    estimate,
                    next(sequence),
                    neighbor,
                    tentative_cost,
                ),
            )
            if neighbor not in open_positions:
                opened.append(neighbor)
                open_positions.add(neighbor)

        elapsed_seconds += perf_counter() - operation_started
        yield SearchEvent(
            kind=SearchEventType.EXPANDED,
            current=current,
            opened=tuple(opened),
            metrics=SearchMetrics(
                nodes_explored=explored,
                frontier_size=len(open_positions),
                elapsed_ms=elapsed_seconds * 1000,
            ),
        )

    yield SearchEvent(
        kind=SearchEventType.NO_PATH,
        current=None,
        opened=(),
        metrics=SearchMetrics(
            nodes_explored=explored,
            frontier_size=0,
            elapsed_ms=elapsed_seconds * 1000,
        ),
    )


def solve(grid: Grid, algorithm: Algorithm, movement: Movement) -> SearchResult:
    """Executa uma busca completa, útil para testes e uso sem interface."""

    final_event: SearchEvent | None = None
    for event in search_steps(grid, algorithm, movement):
        final_event = event

    if final_event is None:
        raise RuntimeError("A busca terminou sem produzir um resultado.")

    return SearchResult(
        algorithm=algorithm,
        movement=movement,
        found=final_event.kind is SearchEventType.FOUND,
        path=final_event.path,
        cost=final_event.metrics.path_cost,
        nodes_explored=final_event.metrics.nodes_explored,
        elapsed_ms=final_event.metrics.elapsed_ms,
    )


def _reconstruct_path(
    parents: dict[Position, Position],
    current: Position,
) -> tuple[Position, ...]:
    path = [current]
    while current in parents:
        current = parents[current]
        path.append(current)
    path.reverse()
    return tuple(path)
