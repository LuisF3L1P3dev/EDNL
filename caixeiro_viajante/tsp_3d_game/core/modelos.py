"""Contratos compartilhados: nenhuma classe aqui depende da renderização."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Callable, Protocol

import networkx as nx
import numpy as np

Posicao = tuple[float, float, float]


@dataclass
class Cenario:
    grafo: nx.Graph
    cidades: list[int]
    deposito: int
    semente: int
    lado: int
    espacamento: float
    revisao: int = 0
    bloqueios: set[tuple[int, int]] = field(default_factory=set)

    def posicao(self, no: int) -> Posicao:
        return tuple(self.grafo.nodes[no]["posicao"])

    def nome(self, no: int) -> str:
        return self.grafo.nodes[no].get("nome", f"Cruzamento {no}")

    @property
    def assinatura(self) -> str:
        # A revisão sozinha não distingue dois cenários reabertos com alterações
        # diferentes. A assinatura também inclui a rede e seus pesos reais.
        estado = (tuple((no, self.posicao(no)) for no in self.grafo),
                  tuple(sorted((min(a, b), max(a, b), d["custo"], d["distancia"], d["bloqueada"])
                               for a, b, d in self.grafo.edges(data=True))))
        resumo = hashlib.blake2b(repr(estado).encode(), digest_size=12).hexdigest()
        return f"{self.semente}:{self.revisao}:{resumo}"


@dataclass
class MatrizDistancias:
    destinos: list[int]
    custos: np.ndarray
    distancias: np.ndarray
    caminhos: dict[tuple[int, int], list[int]]
    modo: str
    revisao: int
    assinatura: str

    def indice(self, no: int) -> int:
        return self.destinos.index(no)


@dataclass
class EtapaAlgoritmo:
    descricao: str
    rota: list[int] = field(default_factory=list)
    custo: float | None = None
    removidas: list[tuple[int, int]] = field(default_factory=list)
    adicionadas: list[tuple[int, int]] = field(default_factory=list)
    antes: float | None = None


@dataclass
class ResultadoRota:
    algoritmo: str
    ordem: list[int]
    custo: float
    distancia: float
    tempo_segundos: float
    otima_comprovada: bool = False
    melhorias: int | None = None
    etapas: list[EtapaAlgoritmo] = field(default_factory=list)
    observacao: str = "Solução aproximada; sem prova de ótimo global."
    reotimizacao: bool = False


class Estrategia(Protocol):
    """Concorde e LKH poderão implementar este mesmo contrato no futuro."""

    nome: str

    def resolver(
        self, custos: np.ndarray, inicio: int = 0, fim: int | None = None,
        tempo_limite: float = 3.0, cancelado: Callable[[], bool] = lambda: False,
    ) -> ResultadoRota: ...


def custo_rota(custos: np.ndarray, ordem: list[int]) -> float:
    return float(sum(custos[a, b] for a, b in zip(ordem, ordem[1:])))


def verificar_cancelamento(cancelado: Callable[[], bool]) -> None:
    if cancelado():
        raise InterruptedError("Cálculo cancelado.")

