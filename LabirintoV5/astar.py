"""Busca A* com eventos para animação em labirintos do pyamaze."""

from collections.abc import Iterator
from queue import PriorityQueue

from busca_eventos import Celula, SearchEvent


DESTINO: Celula = (1, 1)


def h_score(celula: Celula, destino: Celula) -> int:
    """Retorna a distância Manhattan entre duas células."""
    return abs(celula[0] - destino[0]) + abs(celula[1] - destino[1])


def reconstruir_caminho(
    inicio: Celula, destino: Celula, antecessor: dict[Celula, Celula]
) -> dict[Celula, Celula]:
    """Monta o mapa de próximo passo esperado por ``pyamaze.tracePath``."""
    caminho: dict[Celula, Celula] = {}
    atual = destino
    while atual != inicio:
        anterior = antecessor.get(atual)
        if anterior is None:
            return {}
        caminho[anterior] = atual
        atual = anterior
    return caminho


def eventos_astar(labirinto) -> Iterator[SearchEvent]:
    """Emite um evento após cada expansão de A* e um evento final."""
    inicio: Celula = (labirinto.rows, labirinto.cols)
    destino = DESTINO

    g_score = {celula: float("inf") for celula in labirinto.grid}
    f_score = {celula: float("inf") for celula in labirinto.grid}
    g_score[inicio] = 0
    f_score[inicio] = h_score(inicio, destino)

    fronteira: PriorityQueue[tuple[float, int, Celula]] = PriorityQueue()
    fronteira.put((f_score[inicio], h_score(inicio, destino), inicio))
    abertos = {inicio}
    visitados: set[Celula] = set()
    antecessor: dict[Celula, Celula] = {}
    expandidos = 0

    while not fronteira.empty():
        f_enfileirado, _, celula = fronteira.get()

        # Ignora entradas antigas quando a célula recebeu uma rota melhor.
        if f_enfileirado != f_score[celula]:
            continue

        abertos.discard(celula)
        visitados.add(celula)
        expandidos += 1

        if celula == destino:
            caminho = reconstruir_caminho(inicio, destino, antecessor)
            yield SearchEvent(
                current=celula,
                frontier=frozenset(),
                visited=frozenset(visitados),
                expanded_count=expandidos,
                done=True,
                found=True,
                path=caminho,
            )
            return

        for direcao in "NSEW":
            if labirinto.maze_map[celula][direcao] != 1:
                continue

            linha, coluna = celula
            if direcao == "N":
                vizinha = (linha - 1, coluna)
            elif direcao == "S":
                vizinha = (linha + 1, coluna)
            elif direcao == "W":
                vizinha = (linha, coluna - 1)
            else:
                vizinha = (linha, coluna + 1)

            novo_g_score = g_score[celula] + 1
            if novo_g_score >= g_score[vizinha]:
                continue

            antecessor[vizinha] = celula
            g_score[vizinha] = novo_g_score
            prox_h_score = h_score(vizinha, destino)
            f_score[vizinha] = novo_g_score + prox_h_score
            fronteira.put((f_score[vizinha], prox_h_score, vizinha))
            abertos.add(vizinha)

        yield SearchEvent(
            current=celula,
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


def astar(labirinto) -> dict[Celula, Celula]:
    """Retorna a rota A* no formato aceito por ``pyamaze.tracePath``."""
    for evento in eventos_astar(labirinto):
        if evento.done:
            return evento.path or {}
    return {}
