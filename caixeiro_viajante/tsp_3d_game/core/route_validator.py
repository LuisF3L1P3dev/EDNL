"""Invariantes do ciclo de entregas e da expansão para a rede de ruas."""

from __future__ import annotations

import math

import numpy as np

from .graph_manager import grafo_transitavel
from .modelos import Cenario, MatrizDistancias, ResultadoRota, custo_rota


def validar_matriz(custos: np.ndarray) -> None:
    if custos.ndim != 2 or custos.shape[0] != custos.shape[1] or not len(custos):
        raise ValueError("A matriz de custos precisa ser quadrada e não vazia.")
    if not np.all(np.isfinite(custos)) or np.any(custos < 0):
        raise ValueError("Custos devem ser finitos e não negativos.")
    if not np.allclose(np.diag(custos), 0):
        raise ValueError("A diagonal da matriz deve ser zero.")


def validar_ordem(ordem: list[int], quantidade: int, inicio: int = 0,
                  fim: int | None = None) -> None:
    fim = inicio if fim is None else fim
    if inicio == fim:
        correta = len(ordem) == quantidade + 1 and ordem[0] == inicio and ordem[-1] == inicio
        visitados = ordem[:-1]
    else:
        correta = len(ordem) == quantidade and ordem[0] == inicio and ordem[-1] == fim
        visitados = ordem
    if not correta or len(set(visitados)) != quantidade or set(visitados) != set(range(quantidade)):
        raise ValueError("A sequência deve visitar cada destino uma vez e terminar no depósito indicado.")


def validar_resultado(resultado: ResultadoRota, matriz: MatrizDistancias,
                      cenario: Cenario, inicio: int | None = None,
                      fim: int | None = None) -> None:
    inicio = cenario.deposito if inicio is None else inicio
    fim = cenario.deposito if fim is None else fim
    indices = [matriz.indice(no) for no in resultado.ordem]
    validar_ordem(indices, len(matriz.destinos), matriz.indice(inicio), matriz.indice(fim))
    if not math.isclose(resultado.custo, custo_rota(matriz.custos, indices), rel_tol=1e-8, abs_tol=1e-5):
        raise ValueError("O custo informado não corresponde à sequência de entregas.")
    if not math.isclose(resultado.distancia, custo_rota(matriz.distancias, indices), rel_tol=1e-8, abs_tol=1e-5):
        raise ValueError("A distância informada não corresponde aos caminhos físicos.")
    if matriz.revisao != cenario.revisao or matriz.assinatura != cenario.assinatura:
        raise ValueError("A malha viária mudou: a rota está desatualizada.")
    if matriz.modo == "rodoviario":
        rede = grafo_transitavel(cenario)
        for a, b in zip(resultado.ordem, resultado.ordem[1:]):
            caminho = matriz.caminhos[a, b]
            if caminho[0] != a or caminho[-1] != b:
                raise ValueError("Extremos incorretos no caminho rodoviário.")
            if any(not rede.has_edge(u, v) for u, v in zip(caminho, caminho[1:])):
                raise ValueError("O veículo não pode atravessar uma ligação bloqueada ou inexistente.")

