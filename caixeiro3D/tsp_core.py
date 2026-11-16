"""Dados imutáveis dos grafos; geometria decorativa nunca cria adjacências."""
from dataclasses import dataclass
import json
from math import isfinite
from pathlib import Path


@dataclass(frozen=True)
class No:
    id: int
    x: float
    y: float


@dataclass(frozen=True)
class Aresta:
    origem: int
    destino: int
    peso: float


@dataclass(frozen=True)
class Grafo:
    id: str
    nome: str
    nos: tuple[No, ...]
    arestas: tuple[Aresta, ...]
    observacoes: tuple[str, ...] = ()
    pendencias: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.nos or len(set(self.ids)) != len(self.nos):
            raise ValueError("O grafo precisa de nós com identificadores únicos.")
        for no in self.nos:
            if not all(isfinite(v) and 0 <= v <= 1 for v in (no.x, no.y)):
                raise ValueError("Coordenadas devem ser finitas e normalizadas entre 0 e 1.")
        vistas = set()
        for aresta in self.arestas:
            par = tuple(sorted((aresta.origem, aresta.destino)))
            if aresta.origem == aresta.destino or not set(par) <= set(self.ids):
                raise ValueError("Aresta com extremos inválidos.")
            if par in vistas:
                raise ValueError("Aresta duplicada em grafo não direcionado.")
            if not isfinite(aresta.peso) or aresta.peso <= 0:
                raise ValueError("Pesos devem ser positivos e finitos; valores ausentes não são zero.")
            vistas.add(par)

    @property
    def ids(self):
        return tuple(n.id for n in self.nos)

    def adjacencia(self):
        adj = {n: {} for n in self.ids}
        for a in self.arestas:
            adj[a.origem][a.destino] = a.peso
            adj[a.destino][a.origem] = a.peso
        return adj

    def custo(self, caminho):
        caminho = tuple(caminho)
        if not caminho or not set(caminho) <= set(self.ids):
            raise ValueError("Percurso vazio ou com nós desconhecidos.")
        adj = self.adjacencia()
        try:
            return sum(adj[a][b] for a, b in zip(caminho, caminho[1:]))
        except KeyError as erro:
            raise ValueError("Percurso contém uma aresta inexistente.") from erro


def carregar_mapa(caminho):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return Grafo(
        id=dados["id"], nome=dados["nome"],
        nos=tuple(No(**n) for n in dados["nos"]),
        arestas=tuple(Aresta(*a) for a in dados["arestas"]),
        observacoes=tuple(dados.get("observacoes", ())),
        pendencias=tuple(dados.get("pendencias", ())),
    )
