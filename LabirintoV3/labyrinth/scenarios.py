"""Cenários educacionais responsivos às dimensões da grade."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
import random

from .model import Grid, Position


MIN_ROWS = 5
MAX_ROWS = 61
MIN_COLS = 7
MAX_COLS = 81
DEFAULT_ROWS = 21
DEFAULT_COLS = 31

# Fonte única para a ordem do seletor e para seus rótulos compactos.
SCENARIO_LABELS = {
    "Mundo aberto": "Aberto",
    "Armadilha Gulosa": "Armadilha",
    "Labirinto clássico": "Clássico",
    "Aleatório": "Aleatório",
    "Zigue-zague": "Zigue-zague",
    "Salas e portas": "Salas",
    "Espiral": "Espiral",
    "Duas rotas": "2 rotas",
    "Ponte estreita": "Ponte",
    "Becos sem saída": "Becos",
    "Tabuleiro": "Tabuleiro",
    "Arquipélago": "Ilhas",
}
SCENARIOS = tuple(SCENARIO_LABELS)


def create_empty_grid(rows: int = DEFAULT_ROWS, cols: int = DEFAULT_COLS) -> Grid:
    """Cria uma grade vazia válida, com A e B proporcionais à largura."""

    _validate_dimensions(rows, cols)
    center = rows // 2
    return Grid(rows, cols, (center, 2), (center, cols - 3))


def create_scenario(
    name: str,
    seed: int | None = None,
    rows: int = DEFAULT_ROWS,
    cols: int = DEFAULT_COLS,
) -> Grid:
    """Cria o cenário solicitado exatamente em rows × cols.

    Cenários fixos ignoram seed e são determinísticos para as mesmas
    dimensões. O cenário Aleatório aceita a semente para permitir a repetição
    de uma variação específica.
    """

    _validate_dimensions(rows, cols)
    builders: dict[str, Callable[[], Grid]] = {
        "Mundo aberto": lambda: create_empty_grid(rows, cols),
        "Armadilha Gulosa": lambda: _greedy_trap(rows, cols),
        "Labirinto clássico": lambda: _perfect_maze(rows, cols, 20260921),
        "Aleatório": lambda: _random_obstacles(rows, cols, seed),
        "Zigue-zague": lambda: _zigzag(rows, cols),
        "Salas e portas": lambda: _rooms_and_doors(rows, cols),
        "Espiral": lambda: _spiral(rows, cols),
        "Duas rotas": lambda: _two_routes(rows, cols),
        "Ponte estreita": lambda: _narrow_bridge(rows, cols),
        "Becos sem saída": lambda: _dead_ends(rows, cols),
        "Tabuleiro": lambda: _checkerboard(rows, cols),
        "Arquipélago": lambda: _archipelago(rows, cols),
    }
    try:
        grid = builders[name]()
    except KeyError as error:
        raise ValueError(f"Cenário desconhecido: {name}") from error
    return _ensure_connected(grid)


def _validate_dimensions(rows: int, cols: int) -> None:
    if not isinstance(rows, int) or isinstance(rows, bool):
        raise TypeError("Linhas devem ser um número inteiro.")
    if not isinstance(cols, int) or isinstance(cols, bool):
        raise TypeError("Colunas devem ser um número inteiro.")
    if not MIN_ROWS <= rows <= MAX_ROWS:
        raise ValueError(f"Linhas devem estar entre {MIN_ROWS} e {MAX_ROWS}.")
    if not MIN_COLS <= cols <= MAX_COLS:
        raise ValueError(f"Colunas devem estar entre {MIN_COLS} e {MAX_COLS}.")


def _scale(rows: int, cols: int) -> float:
    """Retorna 0..1 para suavizar a densidade em grades muito pequenas."""

    row_scale = (rows - MIN_ROWS) / (DEFAULT_ROWS - MIN_ROWS)
    col_scale = (cols - MIN_COLS) / (DEFAULT_COLS - MIN_COLS)
    return max(0.0, min(1.0, min(row_scale, col_scale)))


def _greedy_trap(rows: int, cols: int) -> Grid:
    grid = create_empty_grid(rows, cols)
    # A semente e a densidade padrão preservam a demonstração clássica de
    # 21 × 31, na qual a Gulosa percorre dez passos a mais que o A*.
    rng = random.Random(21)
    density = 0.20 + 0.08 * _scale(rows, cols)
    for row in range(grid.rows):
        for col in range(grid.cols):
            position = row, col
            if position not in (grid.start, grid.goal) and rng.random() < density:
                grid.walls.add(position)
    return grid


def _perfect_maze(rows: int, cols: int, seed: int) -> Grid:
    rng = random.Random(seed)
    walls = {(row, col) for row in range(rows) for col in range(cols)}
    start_cell = (1, 1)
    walls.remove(start_cell)
    stack = [start_cell]
    visited = {start_cell}
    deltas = [(-2, 0), (0, 2), (2, 0), (0, -2)]

    while stack:
        row, col = stack[-1]
        candidates: list[tuple[Position, Position]] = []
        for delta_row, delta_col in deltas:
            nxt = row + delta_row, col + delta_col
            if (
                1 <= nxt[0] < rows - 1
                and 1 <= nxt[1] < cols - 1
                and nxt not in visited
            ):
                between = row + delta_row // 2, col + delta_col // 2
                candidates.append((nxt, between))
        if not candidates:
            stack.pop()
            continue
        nxt, between = rng.choice(candidates)
        visited.add(nxt)
        walls.discard(nxt)
        walls.discard(between)
        stack.append(nxt)

    goal_row = rows - 2 if (rows - 2) % 2 else rows - 3
    goal_col = cols - 2 if (cols - 2) % 2 else cols - 3
    return Grid(rows, cols, start_cell, (goal_row, goal_col), walls)


def _random_obstacles(rows: int, cols: int, seed: int | None) -> Grid:
    rng = random.Random(seed)
    grid = create_empty_grid(rows, cols)
    density = 0.19 + 0.08 * _scale(rows, cols)

    # Um corredor direto protegido dá ao cenário aleatório uma garantia de
    # solução independente da semente, sem impedir desvios alternativos.
    protected: set[Position] = set()
    row, col = grid.start
    protected.add((row, col))
    while col != grid.goal[1]:
        col += 1 if col < grid.goal[1] else -1
        protected.add((row, col))
    while row != grid.goal[0]:
        row += 1 if row < grid.goal[0] else -1
        protected.add((row, col))

    for row in range(grid.rows):
        for col in range(grid.cols):
            position = row, col
            if position in protected or position in (grid.start, grid.goal):
                continue
            if rng.random() < density:
                grid.walls.add(position)
    return grid


def _zigzag(rows: int, cols: int) -> Grid:
    grid = create_empty_grid(rows, cols)
    span = grid.goal[1] - grid.start[1]
    spacing = max(2, round(span / 6))
    top_gap = max(1, rows // 6)
    bottom_gap = min(rows - 2, rows - 1 - top_gap)

    for index, col in enumerate(range(grid.start[1] + 1, grid.goal[1], spacing)):
        gap = top_gap if index % 2 == 0 else bottom_gap
        grid.walls.update((row, col) for row in range(rows) if row != gap)
    return grid


def _rooms_and_doors(rows: int, cols: int) -> Grid:
    grid = create_empty_grid(rows, cols)
    grid.walls.update((0, col) for col in range(cols))
    grid.walls.update((rows - 1, col) for col in range(cols))
    grid.walls.update((row, 0) for row in range(rows))
    grid.walls.update((row, cols - 1) for row in range(rows))

    horizontal = _dividers(rows, 2)
    vertical = _dividers(cols, 2)
    for row in horizontal:
        grid.walls.update((row, col) for col in range(1, cols - 1))
    for col in vertical:
        grid.walls.update((row, col) for row in range(1, rows - 1))

    row_bands = _bands(1, rows - 1, horizontal)
    col_bands = _bands(1, cols - 1, vertical)
    for divider_index, col in enumerate(vertical):
        for band_index, (first, last) in enumerate(row_bands):
            if first < last:
                door = first + (last - first - 1) // 2
                if (divider_index + band_index) % 2:
                    door = last - 1 - (last - first - 1) // 2
                grid.walls.discard((door, col))
    for divider_index, row in enumerate(horizontal):
        for band_index, (first, last) in enumerate(col_bands):
            if first < last:
                door = first + (last - first - 1) // 2
                if (divider_index + band_index) % 2:
                    door = last - 1 - (last - first - 1) // 2
                grid.walls.discard((row, door))
    return grid


def _dividers(length: int, count: int) -> list[int]:
    candidates = {
        round(length * index / (count + 1))
        for index in range(1, count + 1)
    }
    return sorted(position for position in candidates if 1 < position < length - 2)


def _bands(first: int, last: int, dividers: list[int]) -> list[tuple[int, int]]:
    boundaries = [first, *(divider + 1 for divider in dividers), last]
    return [
        (boundaries[index], dividers[index] if index < len(dividers) else last)
        for index in range(len(boundaries) - 1)
    ]


def _spiral(rows: int, cols: int) -> Grid:
    grid = create_empty_grid(rows, cols)
    layer = 1
    ring_index = 0
    while rows - 1 - layer - layer >= 2 and cols - 1 - layer - layer >= 2:
        top = left = layer
        bottom = rows - 1 - layer
        right = cols - 1 - layer
        grid.walls.update((top, col) for col in range(left, right + 1))
        grid.walls.update((bottom, col) for col in range(left, right + 1))
        grid.walls.update((row, left) for row in range(top, bottom + 1))
        grid.walls.update((row, right) for row in range(top, bottom + 1))

        if ring_index % 2 == 0:
            door = top, max(left + 1, right - 1)
        else:
            door = bottom, min(right - 1, left + 1)
        grid.walls.discard(door)
        layer += 2
        ring_index += 1
    return grid


def _two_routes(rows: int, cols: int) -> Grid:
    grid = create_empty_grid(rows, cols)
    barrier_col = cols // 2
    center = rows // 2
    efficient_gap = max(0, center - max(1, rows // 6))
    scenic_gap = rows - 1
    grid.walls.update(
        (row, barrier_col)
        for row in range(rows)
        if row not in (efficient_gap, scenic_gap)
    )

    # Uma pequena entrada voltada para B torna a rota longa visualmente
    # convidativa, enquanto a abertura superior continua sendo mais eficiente.
    if cols >= 11 and rows >= 9:
        pocket_end = min(grid.goal[1] - 1, barrier_col + max(2, cols // 8))
        pocket_row = min(rows - 2, center + max(1, rows // 5))
        grid.walls.update(
            (pocket_row, col)
            for col in range(barrier_col + 1, pocket_end + 1)
        )
        grid.walls.discard((pocket_row, pocket_end))
    return grid


def _narrow_bridge(rows: int, cols: int) -> Grid:
    grid = create_empty_grid(rows, cols)
    band_width = max(1, min(5, cols // 12))
    band_start = cols // 2 - band_width // 2
    gate_row = max(1, min(rows - 2, rows // 4))
    for col in range(band_start, band_start + band_width):
        grid.walls.update((row, col) for row in range(rows) if row != gate_row)
    return grid


def _dead_ends(rows: int, cols: int) -> Grid:
    grid = create_empty_grid(rows, cols)
    span = grid.goal[1] - grid.start[1]
    if span < 6 or rows < 7:
        barrier_col = (grid.start[1] + grid.goal[1]) // 2
        grid.walls.update((row, barrier_col) for row in range(1, rows))
        return grid

    spine_col = grid.goal[1] - max(2, cols // 12)
    gate_row = max(1, rows // 8)
    grid.walls.update((row, spine_col) for row in range(rows) if row != gate_row)

    tooth_start = max(grid.start[1] + 1, cols // 5)
    spacing = max(3, rows // 6)
    for row in range(gate_row + spacing, rows - 1, spacing):
        grid.walls.update((row, col) for col in range(tooth_start, spine_col + 1))
    return grid


def _checkerboard(rows: int, cols: int) -> Grid:
    grid = create_empty_grid(rows, cols)
    block_size = max(1, min(rows, cols) // 8)
    gap = max(2, block_size)
    stride = block_size + gap
    for block_row, top in enumerate(range(1, rows - 1, stride)):
        for block_col, left in enumerate(range(1, cols - 1, stride)):
            if (block_row + block_col) % 2:
                continue
            for row in range(top, min(rows - 1, top + block_size)):
                for col in range(left, min(cols - 1, left + block_size)):
                    grid.walls.add((row, col))
    return grid


def _archipelago(rows: int, cols: int) -> Grid:
    grid = create_empty_grid(rows, cols)
    island_height = max(2, rows // 6)
    island_width = max(2, cols // 10)
    centers = (
        (0.45, 0.22),
        (0.55, 0.36),
        (0.45, 0.50),
        (0.55, 0.64),
        (0.45, 0.78),
    )
    for row_ratio, col_ratio in centers:
        center_row = round((rows - 1) * row_ratio)
        center_col = round((cols - 1) * col_ratio)
        top = max(1, center_row - island_height // 2)
        left = max(1, center_col - island_width // 2)
        bottom = min(rows - 1, top + island_height)
        right = min(cols - 1, left + island_width)
        for row in range(top, bottom):
            for col in range(left, right):
                grid.walls.add((row, col))
    return grid


def _ensure_connected(grid: Grid) -> Grid:
    """Valida a saída e abre o mínimo de paredes se um desenho a bloquear."""

    grid.walls.discard(grid.start)
    grid.walls.discard(grid.goal)
    if grid.has_path():
        return grid

    # Busca 0-1: entrar em espaço livre custa zero; atravessar parede custa um.
    # Assim mapas pequenos são simplificados apenas onde for indispensável.
    pending = deque([grid.start])
    costs = {grid.start: 0}
    parents: dict[Position, Position] = {}
    while pending:
        current = pending.popleft()
        if current == grid.goal:
            break
        row, col = current
        for delta_row, delta_col in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            neighbor = row + delta_row, col + delta_col
            if not grid.in_bounds(neighbor):
                continue
            step_cost = int(neighbor in grid.walls)
            new_cost = costs[current] + step_cost
            if new_cost >= costs.get(neighbor, new_cost + 1):
                continue
            costs[neighbor] = new_cost
            parents[neighbor] = current
            if step_cost:
                pending.append(neighbor)
            else:
                pending.appendleft(neighbor)

    current = grid.goal
    while current != grid.start:
        grid.walls.discard(current)
        current = parents[current]
    grid.walls.discard(grid.start)
    if not grid.has_path():
        raise RuntimeError("O cenário gerado não contém um caminho entre A e B.")
    return grid
