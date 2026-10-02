"""Tipos compartilhados pelos eventos das buscas do labirinto."""

from dataclasses import dataclass


Celula = tuple[int, int]


@dataclass(frozen=True, slots=True)
class SearchEvent:
    """Estado da busca após expandir uma célula ou concluir a procura."""

    current: Celula | None
    frontier: frozenset[Celula]
    visited: frozenset[Celula]
    expanded_count: int
    done: bool = False
    found: bool | None = None
    path: dict[Celula, Celula] | None = None
