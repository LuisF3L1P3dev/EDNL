"""Geração reproduzível de uma malha de ruas com pontes e destinos."""

from __future__ import annotations

import math
import random

import networkx as nx

from .modelos import Cenario

NOMES = [
    "Aurora", "Jardim Solar", "Porto Azul", "Nova Órbita", "Bosque Norte",
    "Vale Verde", "Alameda", "Horizonte", "Vila Prisma", "Distrito Atlas",
    "Serra Clara", "Parque Lunar", "Santa Luz", "Estação Sul", "Ponte Nova",
    "Costa Dourada", "Mirante", "Bela Vista", "Nova Esperança", "Vila Nexo",
]


def gerar_cenario(quantidade: int = 15, semente: int = 42,
                  metros_por_unidade: float = 100.0) -> Cenario:
    """As cidades são nós especiais de uma rede maior de cruzamentos.

    Ruas ocupam as bordas das quadras; construções e montanhas ficam dentro
    delas. Um rio divide o mapa e só pode ser atravessado pelas três pontes.
    """
    if not 3 <= quantidade <= 100:
        raise ValueError("Escolha entre 3 e 100 cidades, incluindo o depósito.")
    if metros_por_unidade <= 0:
        raise ValueError("A escala do mapa deve ser positiva.")
    sorteio = random.Random(semente)
    lado = max(5, math.ceil(math.sqrt(quantidade * 2.6)))
    espacamento = 6.0
    meio = (lado - 1) / 2
    coluna_rio = lado // 2 - 1
    pontes = {1, lado // 2, lado - 2}
    grafo = nx.Graph()
    for linha in range(lado):
        for coluna in range(lado):
            no = linha * lado + coluna
            x, z = (coluna - meio) * espacamento, (linha - meio) * espacamento
            altura = .12 + .75 * (math.sin(coluna * .7) * math.cos(linha * .6) + 1) / 2
            grafo.add_node(no, posicao=(x, altura, z), tipo="cruzamento",
                           linha=linha, coluna=coluna)
    for linha in range(lado):
        for coluna in range(lado):
            origem = linha * lado + coluna
            for dc, dl in ((1, 0), (0, 1)):
                if coluna + dc >= lado or linha + dl >= lado:
                    continue
                ponte = dc == 1 and coluna == coluna_rio
                if ponte and linha not in pontes:
                    continue
                destino = (linha + dl) * lado + coluna + dc
                a, b = grafo.nodes[origem]["posicao"], grafo.nodes[destino]["posicao"]
                pontos = [a, b]
                if ponte:
                    pontos = [a, ((a[0] + b[0]) / 2, max(a[1], b[1]) + .55, a[2]), b]
                distancia = sum(math.dist(p, q) for p, q in zip(pontos, pontos[1:])) * metros_por_unidade
                grafo.add_edge(origem, destino, distancia=distancia, custo=distancia,
                               pontos=pontos, ponte=ponte, bloqueada=False, fator=1.0)
    # Remover algumas ruas cria escolhas sem destruir a conectividade.
    candidatas = list(grafo.edges)
    sorteio.shuffle(candidatas)
    for a, b in candidatas[:len(candidatas) // 9]:
        if grafo[a][b]["ponte"]:
            continue
        dados = dict(grafo[a][b])
        grafo.remove_edge(a, b)
        if not nx.is_connected(grafo):
            grafo.add_edge(a, b, **dados)
    deposito = min(grafo, key=lambda n: math.hypot(*[grafo.nodes[n]["posicao"][i] for i in (0, 2)]))
    candidatas = sorted(set(grafo) - {deposito})
    cidades = [deposito] + sorteio.sample(candidatas, quantidade - 1)
    for indice, no in enumerate(cidades):
        nome = "Central NEXUS" if indice == 0 else NOMES[(indice - 1) % len(NOMES)]
        if indice > len(NOMES):
            nome += f" {1 + (indice - 1) // len(NOMES)}"
        grafo.nodes[no].update(tipo="cidade", nome=nome, numero=indice)
    return Cenario(grafo, cidades, deposito, semente, lado, espacamento)

