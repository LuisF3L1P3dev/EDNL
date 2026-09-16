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
    """Resultado final simplificado retornado por :func:`solve`."""

    algorithm: Algorithm
    movement: Movement
    found: bool
    path: tuple[Position, ...]
    cost: int | None
    nodes_explored: int
    elapsed_ms: float


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


def search_steps(
    grid: Grid,
    algorithm: Algorithm,
    movement: Movement,
) -> Iterator[SearchEvent]:
    """Executa uma busca e produz um evento a cada expansão.

    O tempo registrado considera apenas o trabalho executado entre duas
    suspensões do gerador, excluindo o atraso visual controlado pelo Tkinter.
    """

    # A grade é validada pela interface antes da busca. Estas verificações
    # também ajudam o analisador de tipos a reconhecer posições não nulas.
    assert grid.start is not None
    assert grid.goal is not None
    start = grid.start
    goal = grid.goal

    # Cada item da fila de prioridade contém:
    # (prioridade, heurística, ordem de inserção, posição, custo acumulado).
    # A heurística e a ordem de inserção também resolvem empates de modo
    # determinístico. O heap sempre remove primeiro o item de menor prioridade.
    sequence = count()
    frontier: list[tuple[int, int, int, Position, int]] = []

    # open_positions espelha as posições presentes na fronteira para alimentar
    # a visualização; closed reúne os nós que já foram efetivamente expandidos.
    open_positions: set[Position] = {start}
    closed: set[Position] = set()

    # parents permite reconstruir o caminho final. costs armazena g(n), isto é,
    # o custo real conhecido desde o ponto inicial até cada posição.
    parents: dict[Position, Position] = {}
    costs: dict[Position, int] = {start: 0}

    # O cronômetro soma apenas o processamento da busca, desconsiderando o
    # intervalo entre os yields usado pela animação da interface.
    elapsed_seconds = 0.0
    explored = 0

    # No ponto inicial g(n) é zero; portanto, tanto A* quanto Guloso começam
    # com prioridade igual à estimativa heurística h(n).
    initial_h = heuristic(start, goal, movement)
    initial_priority = initial_h
    heapq.heappush(
        frontier,
        (initial_priority, initial_h, next(sequence), start, 0),
    )

    while frontier:
        operation_started = perf_counter()
        current: Position | None = None

        # Retira o próximo candidato válido. Como heapq não atualiza itens já
        # inseridos, uma posição pode ter registros antigos na fila; eles são
        # ignorados quando já fechados ou quando seu custo deixou de ser o melhor.
        while frontier:
            _, _, _, candidate, recorded_cost = heapq.heappop(frontier)
            if candidate in closed:
                continue
            if recorded_cost != costs.get(candidate):
                continue
            current = candidate
            break

        # Se restavam apenas registros inválidos, a fronteira útil acabou.
        if current is None:
            elapsed_seconds += perf_counter() - operation_started
            break

        # O nó escolhido deixa a fronteira, entra no conjunto fechado e passa
        # a contar como explorado.
        open_positions.discard(current)
        closed.add(current)
        explored += 1

        # Ao alcançar o destino, refaz o caminho seguindo os pais e emite o
        # evento final com todas as métricas acumuladas.
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

        # Expande cada vizinho caminhável ainda não fechado. A lista opened
        # contém somente as novas posições que a interface deve destacar.
        opened: list[Position] = []
        current_cost = costs[current]
        for neighbor, movement_cost in grid.neighbors(current, movement):
            if neighbor in closed:
                continue

            # tentative_cost é o novo g(n): custo até o nó atual mais o custo
            # do movimento necessário para chegar ao vizinho.
            tentative_cost = current_cost + movement_cost
            known_cost = costs.get(neighbor)

            # A Busca Gulosa mantém a primeira rota encontrada para cada nó.
            # O A* também atualiza um nó aberto quando encontra uma rota de
            # menor custo, condição necessária para preservar o melhor caminho.
            if algorithm is Algorithm.GREEDY:
                should_update = known_cost is None
            else:
                should_update = known_cost is None or tentative_cost < known_cost

            if not should_update:
                continue

            # Registra o melhor custo aceito e de qual nó o vizinho foi alcançado.
            costs[neighbor] = tentative_cost
            parents[neighbor] = current

            # No Guloso, prioridade = h(n): considera apenas a proximidade do
            # destino. No A*, prioridade = g(n) + h(n): combina o custo já
            # percorrido com a estimativa do custo restante.
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

            # Um nó atualizado pode ter mais de um registro no heap, mas deve
            # aparecer apenas uma vez como aberto na interface.
            if neighbor not in open_positions:
                opened.append(neighbor)
                open_positions.add(neighbor)

        # Suspende o gerador após cada expansão para permitir que o Tkinter
        # desenhe a etapa sem bloquear a janela.
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

    # A fronteira foi esgotada sem que o objetivo fosse alcançado.
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

    # Consome todos os eventos incrementais e preserva apenas o último, que
    # será obrigatoriamente FOUND ou NO_PATH em uma execução normal.
    final_event: SearchEvent | None = None
    for event in search_steps(grid, algorithm, movement):
        final_event = event

    if final_event is None:
        raise RuntimeError("A busca terminou sem produzir um resultado.")

    # Converte o evento terminal no formato de resultado usado fora da animação.
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
      """Reconstrói o caminho do início ao destino usando o mapa de pais."""

      path = [current]
      while current in parents:
          current = parents[current]
          path.append(current)

      path.reverse()
      return tuple(path)