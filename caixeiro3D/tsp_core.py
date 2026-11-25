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
    grade: tuple[int, int] | None = None

    def __post_init__(self):
        if self.grade is not None:
            grade = tuple(self.grade)
            if len(grade) != 2 or any(type(valor) is not int for valor in grade):
                raise ValueError("A célula visual precisa de coluna e linha inteiras.")
            object.__setattr__(self, 'grade', grade)


@dataclass(frozen=True)
class Aresta:
    origem: int
    destino: int
    peso: float

    @property
    def identificacao(self):
        return tuple(sorted((self.origem, self.destino)))


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
            par = aresta.identificacao
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


# Arquivos autoritativos; o registro nao duplica os pesos dos grafos.
CENARIOS = (("mapa_05.json", "mapa_05", 5, 8),
            ("mapa_18.json", "mapa_18", 18, 45))


def carregar_cenarios(pasta):
    """Carrega e valida os dois cenarios na ordem do seletor da aplicacao.

    Verifica identidade, nos, conectividade, pendencias e contagem de arestas;
    a validacao exata das arestas e pesos pertence aos testes de transcricao.
    """
    mapas = []
    for arquivo, identificador, quantidade, total_arestas in CENARIOS:
        caminho = Path(pasta) / arquivo
        grafo = carregar_mapa(caminho)
        if grafo.id != identificador:
            raise ValueError(f"{arquivo}: identificador esperado {identificador}.")
        if set(grafo.ids) != set(range(1, quantidade + 1)):
            raise ValueError(f"{arquivo}: esperados nos de 1 a {quantidade}.")
        if grafo.pendencias:
            raise ValueError(f"{arquivo}: existem pendencias de transcricao.")
        adj = grafo.adjacencia()
        vistos, fila = {1}, [1]
        while fila:
            for vizinho in adj[fila.pop()]:
                if vizinho not in vistos:
                    vistos.add(vizinho)
                    fila.append(vizinho)
        if len(vistos) != quantidade:
            raise ValueError(f"{arquivo}: grafo desconectado.")
        if len(grafo.arestas) != total_arestas:
            raise ValueError(f"{arquivo}: esperadas {total_arestas} arestas.")
        mapas.append(grafo)
    return tuple(mapas)
