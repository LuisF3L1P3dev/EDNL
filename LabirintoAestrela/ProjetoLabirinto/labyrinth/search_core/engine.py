"""Motor compartilhado de execução das buscas informadas."""

from __future__ import annotations

import heapq
from itertools import count
from time import perf_counter
from typing import Iterator

from ..model import Grid, Movement, Position
from .base import SearchStrategy
from .contracts import SearchEvent, SearchEventType, SearchMetrics, SearchResult
from .heuristics import heuristic


class SearchEngine:
    """Executa incrementalmente uma busca configurada por uma estratégia."""

    def __init__(
        self,
        grid: Grid,
        movement: Movement,
        strategy: SearchStrategy,
    ) -> None:
        self.grid = grid
        self.movement = movement
        self.strategy = strategy

    def steps(self) -> Iterator[SearchEvent]:
        """Produz um evento a cada expansão da busca.

        O tempo registrado considera apenas o trabalho executado entre duas
        suspensões do gerador, excluindo o atraso visual controlado pelo Tkinter.
        """

        # A grade é validada pela interface antes da busca. Estas verificações
        # também ajudam o analisador de tipos a reconhecer posições não nulas.
        assert self.grid.start is not None
        assert self.grid.goal is not None
        start = self.grid.start
        goal = self.grid.goal

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
        initial_h = heuristic(start, goal, self.movement)
        initial_priority = self.strategy.priority(0, initial_h)
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
            for neighbor, movement_cost in self.grid.neighbors(
                current,
                self.movement,
            ):
                if neighbor in closed:
                    continue

                # tentative_cost é o novo g(n): custo até o nó atual mais o custo
                # do movimento necessário para chegar ao vizinho.
                tentative_cost = current_cost + movement_cost
                known_cost = costs.get(neighbor)

                # A estratégia decide se a rota candidata deve ser aceita. O A*
                # atualiza custos melhores; o Guloso mantém a primeira descoberta.
                if not self.strategy.should_update(known_cost, tentative_cost):
                    continue

                # Registra o custo aceito e de qual nó o vizinho foi alcançado.
                costs[neighbor] = tentative_cost
                parents[neighbor] = current

                # A estratégia também define se a fila considera somente h(n) ou
                # combina o custo percorrido g(n) com a estimativa restante.
                estimate = heuristic(neighbor, goal, self.movement)
                priority = self.strategy.priority(tentative_cost, estimate)
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

    def solve(self) -> SearchResult:
        """Executa a busca completa e retorna somente seu resultado final."""

        # Consome todos os eventos incrementais e preserva apenas o último, que
        # será obrigatoriamente FOUND ou NO_PATH em uma execução normal.
        final_event: SearchEvent | None = None
        for event in self.steps():
            final_event = event

        if final_event is None:
            raise RuntimeError("A busca terminou sem produzir um resultado.")

        # Converte o evento terminal no formato usado fora da animação.
        return SearchResult(
            algorithm=self.strategy.algorithm,
            movement=self.movement,
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
