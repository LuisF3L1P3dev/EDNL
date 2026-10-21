"""Provas pequenas e propriedades compartilhadas pelos cinco métodos."""

from itertools import permutations

import numpy as np
import pytest

from tsp_3d_game.algorithms.christofides import Christofides, verificar_hipoteses
from tsp_3d_game.algorithms.held_karp import HeldKarp
from tsp_3d_game.algorithms.nearest_neighbor import VizinhoMaisProximo
from tsp_3d_game.algorithms.ortools_solver import SolucionadorORTools
from tsp_3d_game.algorithms.registro import ALGORITMOS, criar_estrategia, resolver_matriz
from tsp_3d_game.algorithms.two_opt import DoisOpt
from tsp_3d_game.core.distance_matrix import CacheDistancias
from tsp_3d_game.core.modelos import custo_rota
from tsp_3d_game.core.route_validator import validar_matriz, validar_ordem, validar_resultado
from tsp_3d_game.core.scenario_generator import gerar_cenario


@pytest.fixture
def quadrado():
    posicoes = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
    return np.linalg.norm(posicoes[:, None] - posicoes[None, :], axis=2)


@pytest.mark.parametrize("nome", ALGORITMOS)
def test_todos_visitam_cada_destino_e_retornam(nome):
    cenario = gerar_cenario(8, 17)
    matriz = CacheDistancias().calcular(cenario)
    resultado = resolver_matriz(nome, matriz, cenario.deposito, tempo_limite=.12)
    validar_resultado(resultado, matriz, cenario)
    assert resultado.ordem[0] == resultado.ordem[-1] == cenario.deposito
    assert len(set(resultado.ordem[:-1])) == len(cenario.cidades)
    assert resultado.distancia > 0
    assert resultado.otima_comprovada == (nome == "Held–Karp (exato)")


def test_held_karp_encontra_perimetro(quadrado):
    resultado = HeldKarp().resolver(quadrado)
    assert resultado.custo == pytest.approx(4)
    assert resultado.otima_comprovada


@pytest.mark.parametrize("inicio,fim", [(0, 0), (2, 2), (1, 3)])
def test_exato_confere_com_forca_bruta_assimetrica(inicio, fim):
    custos = np.random.default_rng(21).integers(1, 100, size=(7, 7)).astype(float)
    np.fill_diagonal(custos, 0)
    internos = [i for i in range(7) if i not in {inicio, fim}]
    otimo = min(custo_rota(custos, [inicio, *p, fim]) for p in permutations(internos))
    resultado = HeldKarp().resolver(custos, inicio, fim)
    validar_ordem(resultado.ordem, 7, inicio, fim)
    assert resultado.custo == pytest.approx(otimo)


def test_held_karp_respeita_limite():
    with pytest.raises(ValueError, match="limitado"):
        HeldKarp(12).resolver(np.zeros((13, 13)))


def test_dois_opt_remove_cruzamento(quadrado):
    inicial = [0, 2, 1, 3, 0]
    resultado = DoisOpt().resolver(quadrado, rota_inicial=inicial)
    assert resultado.custo == pytest.approx(4)
    assert resultado.melhorias > 0
    assert all(e.custo < e.antes for e in resultado.etapas if e.antes is not None)
    assert any(e.removidas and e.adicionadas for e in resultado.etapas)


def test_christofides_garantia_e_etapas_reais():
    cenario = gerar_cenario(8, 127)
    matriz = CacheDistancias().calcular(cenario)
    otimo = HeldKarp().resolver(matriz.custos).custo
    resultado = Christofides().resolver(matriz.custos)
    assert resultado.custo <= 1.5 * otimo + 1e-7
    assert len(resultado.etapas) == 4
    assert len(resultado.etapas[0].adicionadas) == len(matriz.destinos) - 1
    assert not resultado.otima_comprovada


def test_christofides_rejeita_hipoteses_invalidas(quadrado):
    assimetrica = quadrado.copy()
    assimetrica[0, 1] = 10
    with pytest.raises(ValueError, match="simétrica"):
        verificar_hipoteses(assimetrica)
    nao_metrica = quadrado.copy()
    nao_metrica[0, 1] = nao_metrica[1, 0] = 10
    with pytest.raises(ValueError, match="triangular"):
        verificar_hipoteses(nao_metrica)
    with pytest.raises(ValueError, match="ciclo"):
        Christofides().resolver(quadrado, 0, 3)


@pytest.mark.parametrize("classe", [VizinhoMaisProximo, DoisOpt, HeldKarp, SolucionadorORTools])
def test_reotimizacao_com_inicio_e_fim_distintos(classe, quadrado):
    resultado = classe().resolver(quadrado, 1, 3, tempo_limite=.08)
    validar_ordem(resultado.ordem, 4, 1, 3)
    assert resultado.ordem[0] == 1 and resultado.ordem[-1] == 3


@pytest.mark.parametrize("classe", [VizinhoMaisProximo, DoisOpt, HeldKarp, SolucionadorORTools, Christofides])
def test_caso_minimo_um_no(classe):
    resultado = classe().resolver(np.zeros((1, 1)), tempo_limite=.04)
    assert resultado.ordem == [0, 0]
    assert resultado.custo == 0


def test_cancelamento_cooperativo(quadrado):
    with pytest.raises(InterruptedError):
        VizinhoMaisProximo().resolver(quadrado, cancelado=lambda: True)


@pytest.mark.parametrize("matriz", [np.ones((2, 3)), np.array([[0, -1], [1, 0]]),
                                    np.array([[0, np.inf], [1, 0]]), np.ones((3, 3))])
def test_rejeita_matriz_invalida(matriz):
    with pytest.raises(ValueError):
        validar_matriz(matriz)


def test_solucionador_futuro_nao_e_fingido():
    with pytest.raises(ValueError, match="não está implementado"):
        criar_estrategia("Concorde")


@pytest.mark.parametrize("ordem", [[0, 1, 1, 0], [0, 1, 2], [0, 1, 3, 0]])
def test_rejeita_entregas_repetidas_ou_faltantes(ordem):
    with pytest.raises(ValueError):
        validar_ordem(ordem, 3)

