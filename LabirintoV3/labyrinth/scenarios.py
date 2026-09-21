"""Cenários demonstrativos e geração de labirintos."""

from __future__ import annotations

import random

from .model import Grid, Position


SCENARIOS = ("Mundo aberto", "Armadilha Gulosa", "Labirinto clássico", "Aleatório")


def create_scenario(name: str, seed: int | None = None) -> Grid:
    if name == "Mundo aberto":
        return Grid()
    if name == "Armadilha Gulosa":
        return _greedy_trap()
    if name == "Labirinto clássico":
        return _perfect_maze(20260921)
    if name == "Aleatório":
        return _random_obstacles(seed)
    raise ValueError(f"Cenário desconhecido: {name}")


def _greedy_trap() -> Grid:
    grid = Grid(start=(10, 2), goal=(10, 28))
    # Arranjo determinístico encontrado para expor a fraqueza da prioridade
    # puramente heurística: a Gulosa chega ao alvo, mas percorre 10 passos a
    # mais que o A*. A densidade irregular também força várias decisões locais.
    rng = random.Random(21)
    for row in range(grid.rows):
        for col in range(grid.cols):
            position = row, col
            if position not in (grid.start, grid.goal) and rng.random() < 0.28:
                grid.walls.add(position)
    return grid


def _perfect_maze(seed: int) -> Grid:
    rng = random.Random(seed)
    rows, cols = 21, 31
    walls = {(row, col) for row in range(rows) for col in range(cols)}
    start_cell = (1, 1)
    walls.remove(start_cell)
    stack = [start_cell]
    visited = {start_cell}
    deltas = [(-2, 0), (0, 2), (2, 0), (0, -2)]

    while stack:
        row, col = stack[-1]
        candidates: list[tuple[Position, Position]] = []
        for dr, dc in deltas:
            nxt = row + dr, col + dc
            if 1 <= nxt[0] < rows - 1 and 1 <= nxt[1] < cols - 1 and nxt not in visited:
                candidates.append((nxt, (row + dr // 2, col + dc // 2)))
        if not candidates:
            stack.pop()
            continue
        nxt, between = rng.choice(candidates)
        visited.add(nxt)
        walls.discard(nxt)
        walls.discard(between)
        stack.append(nxt)

    grid = Grid(rows, cols, (1, 1), (rows - 2, cols - 2), walls)
    return grid


def _random_obstacles(seed: int | None) -> Grid:
    rng = random.Random(seed)
    grid = Grid()
    # Mantém um corredor garantido de A até B e espalha obstáculos no restante.
    protected: set[Position] = set()
    row, col = grid.start
    protected.add((row, col))
    while col != grid.goal[1]:
        col += 1 if col < grid.goal[1] else -1
        protected.add((row, col))
    while row != grid.goal[0]:
        row += 1 if row < grid.goal[0] else -1
        protected.add((row, col))

    for r in range(grid.rows):
        for c in range(grid.cols):
            position = (r, c)
            if position not in protected and position not in (grid.start, grid.goal):
                if rng.random() < 0.27:
                    grid.walls.add(position)
    return grid
