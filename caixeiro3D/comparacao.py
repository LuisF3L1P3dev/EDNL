"""Execuções e métricas exibidas pelo painel de comparação."""

from solvers import executar


CORES_ROTAS = {'forca': (35, 105, 201), 'dijkstra': (35, 105, 201), 'heuristica': (163, 60, 118)}


def metodos_comparaveis(indice_mapa, metodo):
    if indice_mapa == 1:
        return ('dijkstra', 'heuristica')
    return ('forca', 'heuristica') if metodo in ('forca', 'heuristica') else ()


def calcular_comparacao(grafo, metodos, origem, destino, cancelar):
    """Mede os dois métodos no mesmo trabalhador, sem reproduzir eventos do HUD."""
    resultados = {}
    for metodo in metodos:
        if cancelar.is_set():
            break
        resultados[metodo] = executar(metodo, grafo, origem, destino=destino, cancelar=cancelar)
    return resultados


def diferenca_custos(exato, heuristico):
    diferenca = heuristico - exato
    percentual = 100 * diferenca / exato if exato else None
    return abs(diferenca), percentual
