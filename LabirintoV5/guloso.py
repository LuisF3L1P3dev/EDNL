"""Busca gulosa com eventos para animação em labirintos do pyamaze."""

from collections.abc import Iterator
from queue import PriorityQueue

from busca_eventos import Celula, SearchEvent


def heuristica(celula: Celula, objetivo: Celula) -> int:
    """Estima a distância entre duas células usando Manhattan."""
    return abs(celula[0] - objetivo[0]) + abs(celula[1] - objetivo[1])


def criar_fronteira(
    celula_inicial: Celula, objetivo: Celula
) -> PriorityQueue[tuple[int, Celula]]:
    """Cria a fila de prioridade e adiciona nela a célula inicial."""
    fronteira: PriorityQueue[tuple[int, Celula]] = PriorityQueue()
    fronteira.put((heuristica(celula_inicial, objetivo), celula_inicial))
    return fronteira


def iniciar_busca(
    celula_inicial: Celula, objetivo: Celula
) -> tuple[PriorityQueue[tuple[int, Celula]], set[Celula]]:
    """Cria a fronteira e o conjunto persistente de células visitadas."""
    return criar_fronteira(celula_inicial, objetivo), set()


def proximo_nao_visitado(
    fronteira: PriorityQueue[tuple[int, Celula]], visitados: set[Celula]
) -> Celula | None:
    """Retira e registra a próxima célula ainda não visitada."""
    while not fronteira.empty():
        _, celula = fronteira.get()
        if celula in visitados:
            continue
        visitados.add(celula)
        return celula
    return None


def reconstruir_caminho(
    celula_inicial: Celula,
    objetivo: Celula,
    antecessor: dict[Celula, Celula],
) -> dict[Celula, Celula]:
    """Monta o caminho no formato esperado por ``pyamaze.tracePath``."""
    caminho: dict[Celula, Celula] = {}
    atual = objetivo
    while atual != celula_inicial:
        anterior = antecessor.get(atual)
        if anterior is None:
            return {}
        caminho[anterior] = atual
        atual = anterior
    return caminho


def eventos_gulosa(
    labirinto, objetivo: Celula = (1, 1)
) -> Iterator[SearchEvent]:
    """Emite um evento após cada expansão da busca gulosa e um evento final."""
    inicio: Celula = (labirinto.rows, labirinto.cols)
    fronteira, visitados = iniciar_busca(inicio, objetivo)
    abertos = {inicio}
    antecessor: dict[Celula, Celula] = {}
    expandidos = 0

    while not fronteira.empty():
        atual = proximo_nao_visitado(fronteira, visitados)
        if atual is None:
            break
        abertos.discard(atual)
        expandidos += 1

        if atual == objetivo:
            caminho = reconstruir_caminho(inicio, objetivo, antecessor)
            yield SearchEvent(
                current=atual,
                frontier=frozenset(),
                visited=frozenset(visitados),
                expanded_count=expandidos,
                done=True,
                found=True,
                path=caminho,
            )
            return

        for direcao in "NSEW":
            if labirinto.maze_map[atual][direcao] != 1:
                continue

            linha, coluna = atual
            if direcao == "N":
                vizinha = (linha - 1, coluna)
            elif direcao == "S":
                vizinha = (linha + 1, coluna)
            elif direcao == "W":
                vizinha = (linha, coluna - 1)
            else:
                vizinha = (linha, coluna + 1)

            if vizinha in visitados or vizinha in antecessor:
                continue

            antecessor[vizinha] = atual
            fronteira.put((heuristica(vizinha, objetivo), vizinha))
            abertos.add(vizinha)

        yield SearchEvent(
            current=atual,
            frontier=frozenset(abertos),
            visited=frozenset(visitados),
            expanded_count=expandidos,
        )

    yield SearchEvent(
        current=None,
        frontier=frozenset(),
        visited=frozenset(visitados),
        expanded_count=expandidos,
        done=True,
        found=False,
        path={},
    )


def busca_gulosa(
    labirinto, objetivo: Celula = (1, 1)
) -> dict[Celula, Celula]:
    """Retorna a rota gulosa no formato aceito por ``pyamaze.tracePath``."""
    for evento in eventos_gulosa(labirinto, objetivo):
        if evento.done:
            return evento.path or {}
    return {}
