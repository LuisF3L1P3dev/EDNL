"""Fachada pública para as implementações incrementais de busca."""

from __future__ import annotations

from typing import Iterator

from .model import Grid, Movement
from .search_core import (
    Algorithm,
    AStarStrategy,
    GreedyStrategy,
    SearchEngine,
    SearchEvent,
    SearchEventType,
    SearchMetrics,
    SearchResult,
    SearchStrategy,
    heuristic,
    manhattan,
    octile,
)

__all__ = [
    "Algorithm",
    "AStarStrategy",
    "GreedyStrategy",
    "SearchEngine",
    "SearchEvent",
    "SearchEventType",
    "SearchMetrics",
    "SearchResult",
    "SearchStrategy",
    "heuristic",
    "manhattan",
    "octile",
    "search_steps",
    "solve",
]


def _strategy_for(algorithm: Algorithm) -> SearchStrategy:
    """Cria a estratégia correspondente ao algoritmo solicitado."""

    if algorithm is Algorithm.GREEDY:
        return GreedyStrategy()
    if algorithm is Algorithm.ASTAR:
        return AStarStrategy()
    raise ValueError(f"Algoritmo de busca desconhecido: {algorithm!r}")


def search_steps(
    grid: Grid,
    algorithm: Algorithm,
    movement: Movement,
) -> Iterator[SearchEvent]:
    """Executa uma busca e produz um evento a cada expansão."""

    yield from SearchEngine(grid, movement, _strategy_for(algorithm)).steps()


def solve(grid: Grid, algorithm: Algorithm, movement: Movement) -> SearchResult:
    """Executa uma busca completa, útil para testes e uso sem interface."""

    return SearchEngine(grid, movement, _strategy_for(algorithm)).solve()
