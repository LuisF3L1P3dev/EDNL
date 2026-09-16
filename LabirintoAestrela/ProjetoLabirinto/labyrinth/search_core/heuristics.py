"""Heurísticas usadas para estimar o custo restante até o destino."""

from ..model import Movement, Position


def manhattan(position: Position, goal: Position) -> int:
    """Distância Manhattan usando custo ortogonal igual a 10."""

    # Soma a distância entre linhas e colunas, pois movimentos diagonais não
    # são permitidos nesse modelo. Cada passo ortogonal custa 10.
    return 10 * (
        abs(position[0] - goal[0]) + abs(position[1] - goal[1])
    )


def octile(position: Position, goal: Position) -> int:
    """Distância octil usando custos 10 (reto) e 14 (diagonal)."""

    # Separa quantos deslocamentos são necessários em cada eixo.
    row_distance = abs(position[0] - goal[0])
    column_distance = abs(position[1] - goal[1])

    # A parte comum aos dois eixos pode ser percorrida na diagonal; o restante
    # precisa ser percorrido em linha reta.
    diagonal_steps = min(row_distance, column_distance)
    straight_steps = max(row_distance, column_distance) - diagonal_steps
    return 14 * diagonal_steps + 10 * straight_steps


def heuristic(position: Position, goal: Position, movement: Movement) -> int:
    """Estima o custo até o destino conforme o modelo de movimento."""

    # A distância octil considera diagonais; Manhattan considera apenas os
    # quatro vizinhos ortogonais.
    if movement is Movement.EIGHT:
        return octile(position, goal)
    return manhattan(position, goal)
