"""Christofides no fecho métrico simétrico, com etapas educativas reais."""

from time import perf_counter

import networkx as nx
import numpy as np

from ..core.modelos import EtapaAlgoritmo, ResultadoRota, custo_rota, verificar_cancelamento


def verificar_hipoteses(custos):
    if not np.allclose(custos, custos.T, rtol=1e-9, atol=1e-7):
        raise ValueError("Christofides exige uma matriz simétrica.")
    for k in range(len(custos)):
        if np.any(custos > custos[:, k, None] + custos[None, k, :] + 1e-6):
            raise ValueError("Christofides exige a desigualdade triangular.")


class Christofides:
    nome = "Christofides"

    def resolver(self, custos, inicio=0, fim=None, tempo_limite=3.0,
                 cancelado=lambda: False):
        if fim is not None and fim != inicio:
            raise ValueError("O modo Christofides desta versão requer um ciclo com retorno à origem.")
        instante = perf_counter()
        verificar_cancelamento(cancelado)
        verificar_hipoteses(custos)
        if len(custos) <= 2:
            ordem = [inicio] + [i for i in range(len(custos)) if i != inicio] + [inicio]
            valor = custo_rota(custos, ordem)
            return ResultadoRota(self.nome, ordem, valor, valor, perf_counter() - instante,
                                 observacao="TSP métrico simétrico: garantia de até 1,5× o custo ótimo.")
        completo = nx.Graph()
        completo.add_nodes_from(range(len(custos)))
        completo.add_weighted_edges_from((i, j, float(custos[i, j]))
                                         for i in range(len(custos)) for j in range(i + 1, len(custos)))
        arvore = nx.minimum_spanning_tree(completo, weight="weight")
        impares = [no for no, grau in arvore.degree if grau % 2]
        emparelhamento = nx.min_weight_matching(completo.subgraph(impares), weight="weight")
        multigrafo = nx.MultiGraph(arvore)
        multigrafo.add_edges_from(emparelhamento)
        circuito = list(nx.eulerian_circuit(multigrafo, source=inicio))
        verificar_cancelamento(cancelado)
        # A rota final vem da implementação oficial do NetworkX.
        ordem = nx.approximation.christofides(completo, weight="weight", tree=arvore)
        posicao = ordem[:-1].index(inicio)
        ordem = ordem[:-1][posicao:] + ordem[:-1][:posicao] + [inicio]
        valor = custo_rota(custos, ordem)
        etapas = [
            EtapaAlgoritmo("1/4 · Árvore geradora mínima conecta todos os destinos.", adicionadas=list(arvore.edges)),
            EtapaAlgoritmo("2/4 · Emparelhamento mínimo dos vértices de grau ímpar.", adicionadas=list(emparelhamento)),
            EtapaAlgoritmo("3/4 · Circuito euleriano percorre as arestas do multigrafo.",
                           [inicio] + [b for _, b in circuito]),
            EtapaAlgoritmo("4/4 · Atalhos removem visitas repetidas e formam o ciclo de entregas.", ordem.copy(), valor),
        ]
        return ResultadoRota(self.nome, ordem, valor, valor, perf_counter() - instante,
                             etapas=etapas, observacao="TSP métrico simétrico verificado: garantia de até 1,5× o custo ótimo. Não é prova de ótimo.")

