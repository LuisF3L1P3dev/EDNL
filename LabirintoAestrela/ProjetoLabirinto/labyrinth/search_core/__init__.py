"""Componentes orientados a objetos dos algoritmos de busca."""

from .astar import AStarStrategy
from .base import SearchStrategy
from .contracts import (
    Algorithm,
    SearchEvent,
    SearchEventType,
    SearchMetrics,
    SearchResult,
)
from .engine import SearchEngine
from .greedy import GreedyStrategy
from .heuristics import heuristic, manhattan, octile

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
]
