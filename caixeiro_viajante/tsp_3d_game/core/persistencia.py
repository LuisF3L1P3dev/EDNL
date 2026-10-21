"""Exportação de cenários, configurações e resultados em JSON legível."""

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path

import networkx as nx

from .modelos import Cenario

RAIZ = Path(__file__).resolve().parents[2]


def carregar_configuracoes():
    return json.loads((RAIZ / "config" / "settings.json").read_text(encoding="utf-8"))


def salvar_sessao(cenario, resultados, manual=None, pasta=None, configuracoes=None):
    pasta = Path(pasta) if pasta else RAIZ / "resultados"
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"missao_{cenario.semente}_{datetime.now():%Y%m%d_%H%M%S_%f}.json"
    dados = {
        "versao": 1,
        "configuracoes": configuracoes or {},
        "cenario": {"semente": cenario.semente, "lado": cenario.lado,
            "espacamento": cenario.espacamento, "revisao": cenario.revisao,
            "cidades": cenario.cidades, "deposito": cenario.deposito,
            "grafo": nx.node_link_data(cenario.grafo, edges="arestas")},
        "resultados": [asdict(resultado) for resultado in resultados],
        "rota_manual": asdict(manual) if manual else None,
    }
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho


def carregar_cenario(caminho):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))["cenario"]
    grafo = nx.node_link_graph(dados["grafo"], edges="arestas")
    for no in grafo:
        grafo.nodes[no]["posicao"] = tuple(grafo.nodes[no]["posicao"])
    for a, b in grafo.edges:
        grafo[a][b]["pontos"] = [tuple(p) for p in grafo[a][b]["pontos"]]
    bloqueios = {tuple(sorted((a, b))) for a, b, d in grafo.edges(data=True) if d["bloqueada"]}
    return Cenario(grafo, dados["cidades"], dados["deposito"], dados["semente"],
                   dados["lado"], dados["espacamento"], dados["revisao"], bloqueios)

