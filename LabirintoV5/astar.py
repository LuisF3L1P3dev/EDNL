"""Implementação da busca A* para labirintos do pyamaze."""

from queue import PriorityQueue


Celula = tuple[int, int]
DESTINO: Celula = (1, 1)


def h_score(celula: Celula, destino: Celula) -> int:
    """Retorna a distância Manhattan entre duas células."""
    return abs(celula[0] - destino[0]) + abs(celula[1] - destino[1])


def astar(labirinto) -> dict[Celula, Celula]:
    """Encontra a rota do canto inferior direito até ``(1, 1)``.

    O resultado segue o formato esperado por ``pyamaze.tracePath``: cada
    célula da rota aponta para a próxima. Retorna ``{}`` se não houver rota
    ou se o início já for o destino.
    """
    celula_inicial: Celula = (labirinto.rows, labirinto.cols)
    destino = DESTINO

    g_score = {celula: float("inf") for celula in labirinto.grid}
    f_score = {celula: float("inf") for celula in labirinto.grid}
    g_score[celula_inicial] = 0
    f_score[celula_inicial] = h_score(celula_inicial, destino)

    fila: PriorityQueue[tuple[float, int, Celula]] = PriorityQueue()
    fila.put((f_score[celula_inicial], h_score(celula_inicial, destino), celula_inicial))
    antecessor: dict[Celula, Celula] = {}
    destino_alcancado = False

    while not fila.empty():
        f_enfileirado, _, celula = fila.get()

        # Uma célula pode ter entradas antigas na fila após uma rota melhor.
        if f_enfileirado != f_score[celula]:
            continue

        if celula == destino:
            destino_alcancado = True
            break

        for direcao in "NSEW":
            if labirinto.maze_map[celula][direcao] != 1:
                continue

            linha, coluna = celula
            if direcao == "N":
                prox_celula = (linha - 1, coluna)
            elif direcao == "S":
                prox_celula = (linha + 1, coluna)
            elif direcao == "W":
                prox_celula = (linha, coluna - 1)
            else:
                prox_celula = (linha, coluna + 1)

            novo_g_score = g_score[celula] + 1
            if novo_g_score >= g_score[prox_celula]:
                continue

            antecessor[prox_celula] = celula
            g_score[prox_celula] = novo_g_score
            prox_h_score = h_score(prox_celula, destino)
            f_score[prox_celula] = novo_g_score + prox_h_score
            fila.put((f_score[prox_celula], prox_h_score, prox_celula))

    if not destino_alcancado:
        return {}

    caminho_final: dict[Celula, Celula] = {}
    celula_analisada = destino
    while celula_analisada != celula_inicial:
        celula_anterior = antecessor[celula_analisada]
        caminho_final[celula_anterior] = celula_analisada
        celula_analisada = celula_anterior

    return caminho_final
