"""Fecho métrico por Dijkstra: custos e caminhos guardados juntos em cache."""

from __future__ import annotations

from collections import OrderedDict
from typing import Callable

import networkx as nx
import numpy as np

from .graph_manager import grafo_transitavel
from .modelos import Cenario, MatrizDistancias, verificar_cancelamento


class CacheDistancias:
    def __init__(self, capacidade: int = 6):
        self.capacidade = capacidade
        self._cache: OrderedDict[tuple, MatrizDistancias] = OrderedDict()

    def calcular(self, cenario: Cenario, destinos: list[int] | None = None,
                 modo: str = "rodoviario", metros_por_unidade: float = 100.0,
                 cancelado: Callable[[], bool] = lambda: False) -> MatrizDistancias:
        destinos = list(cenario.cidades if destinos is None else destinos)
        if modo not in ("rodoviario", "euclidiano"):
            raise ValueError("Modalidade de distância desconhecida.")
        if len(set(destinos)) != len(destinos) or not destinos or not set(destinos) <= set(cenario.grafo):
            raise ValueError("Os destinos devem ser nós existentes e distintos.")
        chave = (cenario.assinatura, tuple(destinos), modo, metros_por_unidade)
        if chave in self._cache:
            self._cache.move_to_end(chave)
            return self._cache[chave]
        quantidade = len(destinos)
        custos = np.zeros((quantidade, quantidade), dtype=np.float64)
        distancias = np.zeros_like(custos)
        caminhos = {}
        if modo == "euclidiano":
            posicoes = np.array([cenario.posicao(no) for no in destinos])
            custos = np.linalg.norm(posicoes[:, None] - posicoes[None, :], axis=2) * metros_por_unidade
            distancias = custos.copy()
            caminhos = {(a, b): [a] if a == b else [a, b] for a in destinos for b in destinos}
        else:
            rede = grafo_transitavel(cenario)
            for i, origem in enumerate(destinos):
                verificar_cancelamento(cancelado)
                valores, percursos = nx.single_source_dijkstra(rede, origem, weight="custo")
                for j, destino in enumerate(destinos):
                    if destino not in valores:
                        raise ValueError(f"Rede desconectada: não existe caminho entre {cenario.nome(origem)} e {cenario.nome(destino)}.")
                    caminho = percursos[destino]
                    custos[i, j] = valores[destino]
                    distancias[i, j] = sum(rede[a][b]["distancia"] for a, b in zip(caminho, caminho[1:]))
                    caminhos[origem, destino] = caminho
        resultado = MatrizDistancias(destinos, custos, distancias, caminhos, modo,
                                     cenario.revisao, cenario.assinatura)
        self._cache[chave] = resultado
        while len(self._cache) > self.capacidade:
            self._cache.popitem(last=False)
        return resultado

