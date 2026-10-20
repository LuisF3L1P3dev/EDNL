"""Alterações explícitas na malha viária e geometria dos percursos."""

from __future__ import annotations

import math

import networkx as nx

from .modelos import Cenario, Posicao


def grafo_transitavel(cenario: Cenario) -> nx.Graph:
    return nx.subgraph_view(cenario.grafo, filter_edge=lambda a, b: not cenario.grafo[a][b]["bloqueada"])


def alterar_estrada(cenario: Cenario, a: int, b: int, *, bloquear: bool = False,
                    fator: float = 1.0) -> None:
    if not cenario.grafo.has_edge(a, b):
        raise ValueError("A estrada selecionada não existe.")
    if not math.isfinite(fator) or fator < 1:
        raise ValueError("O multiplicador de custo deve ser finito e maior ou igual a 1.")
    dados = cenario.grafo[a][b]
    dados.update(bloqueada=bloquear, fator=fator, custo=dados["distancia"] * fator)
    chave = tuple(sorted((a, b)))
    if bloquear:
        cenario.bloqueios.add(chave)
    else:
        cenario.bloqueios.discard(chave)
    cenario.revisao += 1


def pontos_estrada(cenario: Cenario, a: int, b: int) -> list[Posicao]:
    dados = cenario.grafo[a][b]
    pontos = list(dados["pontos"])
    if pontos[0] != cenario.posicao(a):
        pontos.reverse()
    return pontos


def expandir_percurso(cenario: Cenario, caminhos: dict, ordem: list[int],
                      modo: str = "rodoviario") -> list[tuple[list[Posicao], int]]:
    """Uma perna termina com uma entrega; trânsito intermediário não entrega."""
    pernas = []
    for a, b in zip(ordem, ordem[1:]):
        if modo == "euclidiano":
            pernas.append(([cenario.posicao(a), cenario.posicao(b)], b))
            continue
        nos = caminhos[a, b]
        pontos = [cenario.posicao(nos[0])]
        for u, v in zip(nos, nos[1:]):
            if not cenario.grafo.has_edge(u, v) or cenario.grafo[u][v]["bloqueada"]:
                raise ValueError("A rota contém uma estrada inexistente ou bloqueada. Recalcule.")
            pontos.extend(pontos_estrada(cenario, u, v)[1:])
        pernas.append((pontos, b))
    return pernas

