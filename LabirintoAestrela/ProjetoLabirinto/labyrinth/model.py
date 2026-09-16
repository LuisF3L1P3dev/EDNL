"""Modelo da grade e regras de movimentação do agente."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import random
from typing import Iterable, TypeAlias


Position: TypeAlias = tuple[int, int]


class Movement(str, Enum):
    """Modelos de vizinhança disponíveis na interface."""

    FOUR = "4 direções"
    EIGHT = "8 direções"


ORTHOGONAL_DIRECTIONS: tuple[Position, ...] = (
    (-1, 0),
    (0, 1),
    (1, 0),
    (0, -1),
)
DIAGONAL_DIRECTIONS: tuple[Position, ...] = (
    (-1, 1),
    (1, 1),
    (1, -1),
    (-1, -1),
)


@dataclass(slots=True)
class Grid:
    """Grade retangular compartilhada pelos algoritmos e pela interface."""

    rows: int = 21
    columns: int = 31
    start: Position | None = None
    goal: Position | None = None
    walls: set[Position] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.rows < 3 or self.columns < 3:
            raise ValueError("A grade deve possuir pelo menos 3 linhas e 3 colunas.")

        if self.start is None:
            self.start = (self.rows // 2, 2)
        if self.goal is None:
            self.goal = (self.rows // 2, self.columns - 3)

        if not self.in_bounds(self.start) or not self.in_bounds(self.goal):
            raise ValueError("Os pontos inicial e final devem pertencer à grade.")
        if self.start == self.goal:
            raise ValueError("Os pontos inicial e final devem ser diferentes.")

        self.walls = {position for position in self.walls if self.in_bounds(position)}
        self.walls.discard(self.start)
        self.walls.discard(self.goal)

    def clone(self) -> Grid:
        """Retorna uma cópia independente adequada para uma execução."""

        return Grid(
            rows=self.rows,
            columns=self.columns,
            start=self.start,
            goal=self.goal,
            walls=set(self.walls),
        )

    def in_bounds(self, position: Position) -> bool:
        row, column = position
        return 0 <= row < self.rows and 0 <= column < self.columns

    def is_walkable(self, position: Position) -> bool:
        return self.in_bounds(position) and position not in self.walls

    def set_wall(self, position: Position, blocked: bool = True) -> bool:
        """Altera uma parede e informa se o modelo foi modificado."""

        if not self.in_bounds(position) or position in (self.start, self.goal):
            return False
        if blocked:
            previous_size = len(self.walls)
            self.walls.add(position)
            return len(self.walls) != previous_size

        if position in self.walls:
            self.walls.remove(position)
            return True
        return False

    def set_start(self, position: Position) -> bool:
        if not self.in_bounds(position) or position == self.goal:
            return False
        changed = position != self.start
        self.start = position
        self.walls.discard(position)
        return changed

    def set_goal(self, position: Position) -> bool:
        if not self.in_bounds(position) or position == self.start:
            return False
        changed = position != self.goal
        self.goal = position
        self.walls.discard(position)
        return changed

    def clear_walls(self) -> None:
        self.walls.clear()

    def neighbors(
        self,
        position: Position,
        movement: Movement,
    ) -> Iterable[tuple[Position, int]]:
        """Produz vizinhos válidos e seus custos de movimento.

        Uma diagonal só é permitida quando as duas células ortogonais do
        canto estão livres. Isso impede que o agente atravesse paredes.
        """

        row, column = position
        directions = ORTHOGONAL_DIRECTIONS
        if movement is Movement.EIGHT:
            directions += DIAGONAL_DIRECTIONS

        for row_delta, column_delta in directions:
            candidate = (row + row_delta, column + column_delta)
            if not self.is_walkable(candidate):
                continue

            is_diagonal = row_delta != 0 and column_delta != 0
            if is_diagonal:
                horizontal = (row, column + column_delta)
                vertical = (row + row_delta, column)
                if not self.is_walkable(horizontal) or not self.is_walkable(vertical):
                    continue
                yield candidate, 14
            else:
                yield candidate, 10

    def has_path(self, movement: Movement = Movement.FOUR) -> bool:
        """Verifica conectividade sem executar um algoritmo informado."""

        assert self.start is not None
        assert self.goal is not None
        queue: deque[Position] = deque([self.start])
        visited = {self.start}

        while queue:
            current = queue.popleft()
            if current == self.goal:
                return True
            for neighbor, _ in self.neighbors(current, movement):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    def randomize(
        self,
        density: float = 0.28,
        *,
        rng: random.Random | None = None,
        max_attempts: int = 50,
    ) -> None:
        """Gera obstáculos aleatórios preservando uma rota ortogonal.

        Se as tentativas aleatórias não produzirem um cenário solucionável,
        um corredor Manhattan é aberto como garantia final.
        """

        if not 0.0 <= density <= 0.65:
            raise ValueError("A densidade deve estar entre 0 e 0,65.")
        if max_attempts < 1:
            raise ValueError("É necessária pelo menos uma tentativa.")

        generator = rng or random.Random()
        candidates = [
            (row, column)
            for row in range(self.rows)
            for column in range(self.columns)
            if (row, column) not in (self.start, self.goal)
        ]

        for _ in range(max_attempts):
            self.walls = {
                position for position in candidates if generator.random() < density
            }
            if self.has_path(Movement.FOUR):
                return

        # Mantém o último cenário e abre um corredor em L. O sentido do
        # corredor é sorteado para evitar que toda recuperação fique igual.
        assert self.start is not None
        assert self.goal is not None
        start_row, start_column = self.start
        goal_row, goal_column = self.goal

        if generator.choice((True, False)):
            self._clear_horizontal(start_row, start_column, goal_column)
            self._clear_vertical(goal_column, start_row, goal_row)
        else:
            self._clear_vertical(start_column, start_row, goal_row)
            self._clear_horizontal(goal_row, start_column, goal_column)

        self.walls.discard(self.start)
        self.walls.discard(self.goal)

    def _clear_horizontal(self, row: int, first: int, last: int) -> None:
        for column in range(min(first, last), max(first, last) + 1):
            self.walls.discard((row, column))

    def _clear_vertical(self, column: int, first: int, last: int) -> None:
        for row in range(min(first, last), max(first, last) + 1):
            self.walls.discard((row, column))
