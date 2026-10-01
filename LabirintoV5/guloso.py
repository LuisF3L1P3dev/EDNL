from queue import PriorityQueue

"""Heurística para a busca gulosa no labirinto."""


Celula = tuple[int, int]


def heuristica(celula: Celula, objetivo: Celula) -> int:
    """Estima a distância entre duas células usando Manhattan."""
    return abs(celula[0] - objetivo[0]) + abs(celula[1] - objetivo[1])


def criar_fronteira( celula_inicial: Celula, objetivo: Celula
) -> PriorityQueue[tuple[int, Celula]]:
    """Cria a fila de prioridade e adiciona nela a célula inicial."""
    fronteira: PriorityQueue[tuple[int, Celula]] = PriorityQueue()
    prioridade_inicial = heuristica(celula_inicial, objetivo)
    fronteira.put((prioridade_inicial, celula_inicial))
    return fronteira


def iniciar_busca(
    celula_inicial: Celula, objetivo: Celula
) -> tuple[PriorityQueue[tuple[int, Celula]], set[Celula]]:
    """Cria a fronteira e o conjunto persistente de células visitadas."""
    fronteira = criar_fronteira(celula_inicial, objetivo)
    visitados: set[Celula] = set()
    return fronteira, visitados


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
    celula_atual = objetivo

    while celula_atual != celula_inicial:
        celula_anterior = antecessor.get(celula_atual)
        if celula_anterior is None:
            return {}

        caminho[celula_anterior] = celula_atual
        celula_atual = celula_anterior

    return caminho


def busca_gulosa(labirinto, objetivo: Celula = (1, 1)) -> dict[Celula, Celula]:
    """Encontra uma rota priorizando as células com menor heurística."""
    celula_inicial: Celula = (labirinto.rows, labirinto.cols)
    fronteira, visitados = iniciar_busca(celula_inicial, objetivo)
    antecessor: dict[Celula, Celula] = {}

    while not fronteira.empty():
        celula_atual = proximo_nao_visitado(fronteira, visitados)
        if celula_atual is None:
            break

        if celula_atual == objetivo:
            return reconstruir_caminho(celula_inicial, objetivo, antecessor)

        for direcao in "NSEW":
            if labirinto.maze_map[celula_atual][direcao] != 1:
                continue

            linha, coluna = celula_atual
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

            antecessor[vizinha] = celula_atual
            prioridade = heuristica(vizinha, objetivo)
            fronteira.put((prioridade, vizinha))

    return {}
