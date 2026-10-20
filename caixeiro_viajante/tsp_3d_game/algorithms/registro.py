"""Ponto único de integração dos solucionadores atuais e futuros."""

from .christofides import Christofides
from .held_karp import HeldKarp
from .nearest_neighbor import VizinhoMaisProximo
from .ortools_solver import SolucionadorORTools
from .two_opt import DoisOpt
from ..core.modelos import custo_rota
from ..core.route_validator import validar_matriz, validar_ordem

ALGORITMOS = ["OR-Tools + GLS", "Vizinho mais próximo", "2-opt", "Held–Karp (exato)", "Christofides"]
FUTUROS = ["Concorde", "LKH", "Algoritmos genéticos", "Colônia de formigas", "Recozimento simulado"]


def criar_estrategia(nome, limite_held_karp=12):
    fabricas = {"OR-Tools + GLS": SolucionadorORTools, "Vizinho mais próximo": VizinhoMaisProximo,
                "2-opt": DoisOpt, "Held–Karp (exato)": lambda: HeldKarp(limite_held_karp),
                "Christofides": Christofides}
    if nome not in fabricas:
        raise ValueError(f"{nome}: solucionador futuro ou desconhecido; não está implementado.")
    return fabricas[nome]()


def resolver_matriz(nome, matriz, inicio, fim=None, tempo_limite=3.0,
                    limite_held_karp=12, cancelado=lambda: False):
    validar_matriz(matriz.custos)
    fim = inicio if fim is None else fim
    i, f = matriz.indice(inicio), matriz.indice(fim)
    estrategia = criar_estrategia(nome, limite_held_karp)
    resultado = estrategia.resolver(matriz.custos, i, f, tempo_limite, cancelado)
    validar_ordem(resultado.ordem, len(matriz.destinos), i, f)
    resultado.distancia = custo_rota(matriz.distancias, resultado.ordem)
    resultado.ordem = [matriz.destinos[j] for j in resultado.ordem]
    for etapa in resultado.etapas:
        etapa.rota = [matriz.destinos[j] for j in etapa.rota]
        etapa.removidas = [(matriz.destinos[a], matriz.destinos[b]) for a, b in etapa.removidas]
        etapa.adicionadas = [(matriz.destinos[a], matriz.destinos[b]) for a, b in etapa.adicionadas]
    resultado.reotimizacao = inicio != fim
    if resultado.reotimizacao:
        resultado.observacao = "Reotimização dinâmica com origem atual e término no depósito. " + resultado.observacao
    return resultado

