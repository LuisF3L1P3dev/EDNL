"""Contratos compartilhados pelas buscas e por seus consumidores."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..model import Movement, Position


class Algorithm(str, Enum):
    """Algoritmos de busca informada disponíveis na aplicação."""

    GREEDY = "Busca Gulosa"
    ASTAR = "A*"


class SearchEventType(str, Enum):
    """Tipos de atualização enviados pela busca incremental à interface."""

    EXPANDED = "expanded"
    FOUND = "found"
    NO_PATH = "no_path"


@dataclass(frozen=True, slots=True)
class SearchMetrics:
    """Medições acumuladas durante a execução de uma busca."""

    nodes_explored: int = 0
    frontier_size: int = 0
    elapsed_ms: float = 0.0
    path_cost: int | None = None
    path_length: int | None = None


@dataclass(frozen=True, slots=True)
class SearchEvent:
    """Representa uma etapa da busca consumida pela animação da interface."""

    kind: SearchEventType
    current: Position | None
    opened: tuple[Position, ...]
    metrics: SearchMetrics
    path: tuple[Position, ...] = ()


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Resultado final simplificado retornado por uma busca completa."""

    algorithm: Algorithm
    movement: Movement
    found: bool
    path: tuple[Position, ...]
    cost: int | None
    nodes_explored: int
    elapsed_ms: float
