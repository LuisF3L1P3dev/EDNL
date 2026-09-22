"""Modelo de dados do labirinto ortogonal."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterator


Position = tuple[int, int]


@dataclass(slots=True)
class Grid:
    """Grade editável com paredes, origem e destino."""

    rows: int = 21
    cols: int = 31
    start: Position = (10, 2)
    goal: Position = (10, 28)
    walls: set[Position] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Valida origem e destino e remove paredes sobre esses pontos."""
        if self.rows < 3 or self.cols < 3:
            raise ValueError("A grade deve ter ao menos 3 linhas e 3 colunas.")
        if not self.in_bounds(self.start) or not self.in_bounds(self.goal):
            raise ValueError("Os pontos A e B devem estar dentro da grade.")
        if self.start == self.goal:
            raise ValueError("Os pontos A e B devem ser diferentes.")
        self.walls.discard(self.start)
        self.walls.discard(self.goal)

    def clone(self) -> Grid:
        """Retorna uma cópia independente da grade e de suas paredes."""
        return Grid(self.rows, self.cols, self.start, self.goal, set(self.walls))

    def in_bounds(self, position: Position) -> bool:
        """Informa se a posição está dentro dos limites da grade."""
        row, col = position
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_walkable(self, position: Position) -> bool:
        """Informa se a posição existe e não contém parede."""
        return self.in_bounds(position) and position not in self.walls

    def neighbors(self, position: Position) -> Iterator[Position]:
        """Percorre vizinhos livres nas quatro direções ortogonais."""
        row, col = position
        for delta_row, delta_col in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            candidate = row + delta_row, col + delta_col
            if self.is_walkable(candidate):
                yield candidate

    def set_wall(self, position: Position, enabled: bool = True) -> bool:
        """Altera uma parede válida e retorna se o estado da célula mudou."""
        if not self.in_bounds(position) or position in (self.start, self.goal):
            return False
        before = position in self.walls
        if enabled:
            self.walls.add(position)
        else:
            self.walls.discard(position)
        return before != enabled

    def set_start(self, position: Position) -> bool:
        """Move A para uma posição válida e livre; retorna se foi aceita."""
        if not self.in_bounds(position) or position == self.goal:
            return False
        self.start = position
        self.walls.discard(position)
        return True

    def set_goal(self, position: Position) -> bool:
        """Move B para uma posição válida e livre; retorna se foi aceita."""
        if not self.in_bounds(position) or position == self.start:
            return False
        self.goal = position
        self.walls.discard(position)
        return True

    def clear(self) -> None:
        """Remove todas as paredes da grade."""
        self.walls.clear()

    def has_path(self) -> bool:
        """Verifica por busca em largura se A alcança B."""
        pending = deque([self.start])
        visited = {self.start}
        while pending:
            current = pending.popleft()
            if current == self.goal:
                return True
            for neighbor in self.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append(neighbor)
        return False
