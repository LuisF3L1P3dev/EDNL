"""Geometria do mapa independente do renderizador."""
from math import dist


def posicoes_mundo(grafo):
    return {n.id: ((n.x - .5) * 46, (.5 - n.y) * 38, .12) for n in grafo.nos}


def ruas_mundo(grafo):
    """Cada aresta mantém sua identidade; cruzamentos não criam adjacências."""
    posicoes = posicoes_mundo(grafo)
    ruas = {}
    for i, aresta in enumerate(grafo.arestas):
        a, b = posicoes[aresta.origem], posicoes[aresta.destino]
        altura = .24 + i * .025
        pontos = (a, tuple(a[k] + .15 * (b[k] - a[k]) for k in range(2)) + (altura,),
                  tuple(a[k] + .85 * (b[k] - a[k]) for k in range(2)) + (altura,), b)
        ruas[aresta.origem, aresta.destino] = pontos
        ruas[aresta.destino, aresta.origem] = tuple(reversed(pontos))
    return ruas


def interpolar(pontos, fracao):
    comprimentos = [dist(a, b) for a, b in zip(pontos, pontos[1:])]
    restante = max(0., min(1., fracao)) * sum(comprimentos)
    for i, comprimento in enumerate(comprimentos):
        if restante <= comprimento or i == len(comprimentos) - 1:
            a, b = pontos[i:i + 2]
            t = restante / comprimento if comprimento else 0.
            return tuple(a[k] + (b[k] - a[k]) * t for k in range(3)), tuple(b[k] - a[k] for k in range(3))
        restante -= comprimento
    raise ValueError("Uma rua precisa de pelo menos dois pontos.")


