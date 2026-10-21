"""Encaixes das vias Kenney sem abrir janela nem alterar a rede rodoviária."""
import copy
import itertools
import math

import pytest

from tsp_3d_game.core.scenario_generator import gerar_cenario
from tsp_3d_game.graphics.geometria_ruas import (
    ABERTURAS, ALTURA_PISO, LARGURA_VIA, PerfilViario,
    dividir_triangulo, escolher_cruzamento,
)


@pytest.mark.parametrize("quantidade", [5, 15, 50, 100])
@pytest.mark.parametrize("semente", [42, 123])
def test_piso_acompanha_todos_os_caminhos_sem_modificar_grafo(quantidade, semente):
    cenario = gerar_cenario(quantidade, semente)
    assinatura = cenario.assinatura
    arestas = copy.deepcopy(list(cenario.grafo.edges(data=True)))
    perfil = PerfilViario(cenario)
    for _, _, dados in cenario.grafo.edges(data=True):
        for p, q in zip(dados["pontos"], dados["pontos"][1:]):
            for passo in range(17):
                t = passo / 16
                x, y, z = (a + (b - a) * t for a, b in zip(p, q))
                assert perfil.altura(x, z) == pytest.approx(y, abs=1e-10)
                # O GLB do caminhão tem a base das rodas em y + 0,10.
                assert y + .10 > perfil.altura(x, z) + ALTURA_PISO
    assert cenario.assinatura == assinatura
    assert list(cenario.grafo.edges(data=True)) == arestas


def test_acessos_e_pico_da_ponte_sao_continuos():
    cenario = gerar_cenario()
    perfil = PerfilViario(cenario)
    for _, _, dados in cenario.grafo.edges(data=True):
        if not dados["ponte"]:
            continue
        for x, _, z in dados["pontos"]:
            for lateral in (-1, -.5, 0, .5, 1):
                antes = perfil.altura(x - 1e-7, z + lateral)
                depois = perfil.altura(x + 1e-7, z + lateral)
                assert abs(antes - depois) < 1e-6
        p, pico, q = dados["pontos"]
        # Ambos os acessos dividem o mesmo campo de altura dos cruzamentos.
        for no in (p, q):
            assert perfil.altura(no[0], no[2]) == pytest.approx(no[1])
        assert perfil.altura(pico[0], pico[2]) == pytest.approx(pico[1])


DIRECOES = [(1, 0), (-1, 0), (0, 1), (0, -1)]
CONEXOES = [c for n in range(5) for c in itertools.combinations(DIRECOES, n)]


@pytest.mark.parametrize("direcoes", CONEXOES)
def test_modulos_tem_exatamente_as_aberturas_do_cruzamento(direcoes):
    nome, giro = escolher_cruzamento(direcoes)
    aberturas = ABERTURAS[nome]
    for _ in range(giro // 90):
        aberturas = {(z, -x) for x, z in aberturas}
    assert aberturas == set(direcoes)


def test_rejeita_conexoes_nao_suportadas():
    with pytest.raises(ValueError, match="compatível"):
        escolher_cruzamento([(1, 1)])


def test_recorte_preserva_area_uvs_e_nao_atravessa_o_pico():
    # Campos: x, y, z, nx, ny, nz, u, v.
    triangulo = [(0, 0, 0, 0, 1, 0, 0, 0),
                 (4, 0, 0, 0, 1, 0, 1, 0),
                 (0, 0, 4, 0, 1, 0, 0, 1)]
    partes = list(dividir_triangulo(triangulo, [1, 2], [1, 2]))
    area = 0
    for a, b, c in partes:
        area += abs((b[0] - a[0]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[0] - a[0])) / 2
        for eixo in (0, 2):
            for corte in (1, 2):
                assert not (min(p[eixo] for p in (a, b, c)) < corte - 1e-8
                            and max(p[eixo] for p in (a, b, c)) > corte + 1e-8)
        for p in (a, b, c):
            assert p[6] == pytest.approx(p[0] / 4)
            assert p[7] == pytest.approx(p[2] / 4)
            assert p[3:6] == (0, 1, 0)
    assert area == pytest.approx(8)


def test_cortes_incluem_topo_e_fronteiras_da_ponte():
    cenario = gerar_cenario()
    perfil = PerfilViario(cenario)
    for _, _, dados in cenario.grafo.edges(data=True):
        if not dados["ponte"]:
            continue
        p, pico, q = dados["pontos"]
        assert pico[0] in perfil.cortes(0, p[0], q[0])
        assert pico[2] in perfil.cortes(2, pico[2] - 1, pico[2] + 1)
    assert LARGURA_VIA < cenario.espacamento


def test_normal_da_rampa_e_unitaria_e_perpendicular_ao_piso():
    cenario = gerar_cenario()
    perfil = PerfilViario(cenario)
    p, q, *_ = perfil.pontes[0]
    x, z = p[0] + 1.5, p[2]
    n = perfil.normal(x, z, (0, 1, 0))
    assert math.sqrt(sum(v * v for v in n)) == pytest.approx(1)
    epsilon = 1e-4
    inclinacao = (perfil.altura(x + epsilon, z) - perfil.altura(x - epsilon, z)) / (2 * epsilon)
    assert n[0] + n[1] * inclinacao == pytest.approx(0, abs=1e-8)
