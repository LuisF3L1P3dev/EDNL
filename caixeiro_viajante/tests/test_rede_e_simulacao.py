import math
import copy

import networkx as nx
import numpy as np
import pytest

from tsp_3d_game.algorithms.registro import resolver_matriz
from tsp_3d_game.core.distance_matrix import CacheDistancias
from tsp_3d_game.core.game_state import SimulacaoPercurso, economia_percentual, pontuar
from tsp_3d_game.core.graph_manager import alterar_estrada, expandir_percurso, grafo_transitavel
from tsp_3d_game.core.modelos import Cenario, ResultadoRota
from tsp_3d_game.core.persistencia import carregar_cenario, salvar_sessao
from tsp_3d_game.core.route_validator import validar_resultado
from tsp_3d_game.core.scenario_generator import gerar_cenario


@pytest.mark.parametrize("quantidade", [5, 15, 30, 50, 100])
def test_cenario_conectado_reproduzivel(quantidade):
    a, b = gerar_cenario(quantidade, 42), gerar_cenario(quantidade, 42)
    assert nx.is_connected(a.grafo)
    assert a.cidades == b.cidades
    assert list(a.grafo.edges(data=True)) == list(b.grafo.edges(data=True))
    assert len(a.cidades) == quantidade
    assert len(a.grafo) > quantidade


def test_dijkstra_e_expansao_conferem_custos():
    cenario = gerar_cenario(15, 8)
    matriz = CacheDistancias().calcular(cenario)
    assert np.allclose(matriz.custos, matriz.custos.T)
    for (a, b), caminho in matriz.caminhos.items():
        custo = sum(cenario.grafo[u][v]["custo"] for u, v in zip(caminho, caminho[1:]))
        assert custo == pytest.approx(matriz.custos[matriz.indice(a), matriz.indice(b)])
    resultado = resolver_matriz("Vizinho mais próximo", matriz, cenario.deposito)
    pernas = expandir_percurso(cenario, matriz.caminhos, resultado.ordem)
    distancia = sum(math.dist(p, q) * 100 for pontos, _ in pernas for p, q in zip(pontos, pontos[1:]))
    assert distancia == pytest.approx(resultado.distancia)


def test_cache_e_invalidacao_por_bloqueio():
    cenario = gerar_cenario(8)
    cache = CacheDistancias()
    original = cache.calcular(cenario)
    assert cache.calcular(cenario) is original
    a, b = next(iter(cenario.grafo.edges))
    alterar_estrada(cenario, a, b, bloquear=True)
    alterada = cache.calcular(cenario)
    assert alterada is not original
    assert all(not (u == a and v == b or u == b and v == a) for caminho in alterada.caminhos.values()
               for u, v in zip(caminho, caminho[1:]))
    resultado_antigo = resolver_matriz("2-opt", original, cenario.deposito)
    with pytest.raises(ValueError, match="desatualizada"):
        validar_resultado(resultado_antigo, original, cenario)


def test_rede_desconectada_nao_cria_caminho_ficticio():
    cenario = gerar_cenario(8)
    deposito = cenario.deposito
    for vizinho in list(cenario.grafo.neighbors(deposito)):
        alterar_estrada(cenario, deposito, vizinho, bloquear=True)
    with pytest.raises(ValueError, match="desconectada"):
        CacheDistancias().calcular(cenario)


def test_custo_de_obras_nao_muda_comprimento_fisico():
    cenario = gerar_cenario(5)
    a, b = next(iter(cenario.grafo.edges))
    distancia = cenario.grafo[a][b]["distancia"]
    alterar_estrada(cenario, a, b, fator=2)
    assert cenario.grafo[a][b]["distancia"] == distancia
    assert cenario.grafo[a][b]["custo"] == 2 * distancia


def test_veiculo_entrega_todos_e_retorna_sem_saltar():
    cenario = gerar_cenario(15)
    matriz = CacheDistancias().calcular(cenario)
    resultado = resolver_matriz("2-opt", matriz, cenario.deposito)
    sim = SimulacaoPercurso(cenario, matriz, resultado.ordem)
    posicao_antes = sim.posicao
    sim.avancar(.02, 7)
    assert math.dist(posicao_antes, sim.posicao) <= .14 + 1e-7
    sim.pausada = True
    posicao = sim.posicao
    sim.avancar(100)
    assert sim.posicao == posicao
    sim.pausada = False
    sim.avancar(1000)
    assert sim.concluida
    assert sim.posicao == pytest.approx(cenario.posicao(cenario.deposito))
    assert sim.distancia == pytest.approx(resultado.distancia)
    assert sim.entregues == set(cenario.cidades) - {cenario.deposito}


def test_transito_nao_e_entrega():
    grafo = nx.Graph()
    for no in range(3):
        grafo.add_node(no, posicao=(float(no), 0., 0.), nome=str(no))
    for a, b in ((0, 1), (1, 2)):
        grafo.add_edge(a, b, custo=100., distancia=100., pontos=[grafo.nodes[a]["posicao"], grafo.nodes[b]["posicao"]], bloqueada=False)
    cenario = Cenario(grafo, [0, 1, 2], 0, 1, 3, 1)
    matriz = CacheDistancias().calcular(cenario)
    sim = SimulacaoPercurso(cenario, matriz, [0, 2, 1, 0])
    sim.avancar(1, 1)
    assert sim.ultimo_no == 1
    assert sim.entregues == set()
    sim.avancar(1, 1)
    assert sim.entregues == {2}
    sim.avancar(10, 1)
    assert sim.entregues == {1, 2}


def test_evento_para_no_proximo_cruzamento():
    cenario = gerar_cenario(7)
    matriz = CacheDistancias().calcular(cenario)
    resultado = resolver_matriz("Vizinho mais próximo", matriz, cenario.deposito)
    sim = SimulacaoPercurso(cenario, matriz, resultado.ordem)
    sim.avancar(.1)
    sim.parar_no_proximo_no = True
    sim.avancar(100)
    assert sim.aguardando_evento
    assert sim.posicao == pytest.approx(cenario.posicao(sim.ultimo_no))
    assert sim.progresso == 0


def test_modo_euclidiano():
    cenario = gerar_cenario(7)
    matriz = CacheDistancias().calcular(cenario, modo="euclidiano")
    for i, a in enumerate(matriz.destinos):
        for j, b in enumerate(matriz.destinos):
            assert matriz.custos[i, j] == pytest.approx(math.dist(cenario.posicao(a), cenario.posicao(b)) * 100)


def test_exportar_reabrir_cenario(tmp_path):
    cenario = gerar_cenario(7)
    a, b = next(iter(cenario.grafo.edges))
    alterar_estrada(cenario, a, b, bloquear=True)
    matriz = CacheDistancias().calcular(cenario)
    resultado = resolver_matriz("Vizinho mais próximo", matriz, cenario.deposito)
    arquivo = salvar_sessao(cenario, [resultado], pasta=tmp_path)
    recuperado = carregar_cenario(arquivo)
    assert recuperado.cidades == cenario.cidades
    assert recuperado.bloqueios == cenario.bloqueios
    assert np.allclose(CacheDistancias().calcular(recuperado).custos, matriz.custos)


def test_pontuacao_e_economia():
    assert pontuar(100, 100, 14, 14, True) == 1000
    assert pontuar(200, 100, 14, 14, True) < 1000
    assert pontuar(100, 100, 0, 14, False) == 0
    assert economia_percentual(100, 80) == pytest.approx(20)
    assert economia_percentual(None, 80) is None


def test_cache_nao_confunde_alteracoes_distintas_com_mesma_revisao():
    original = gerar_cenario(8, 91)
    a, b = copy.deepcopy(original), copy.deepcopy(original)
    primeira, segunda = list(original.grafo.edges)[:2]
    alterar_estrada(a, *primeira, fator=2)
    alterar_estrada(b, *segunda, fator=2)
    assert a.revisao == b.revisao
    cache = CacheDistancias()
    assert cache.calcular(a) is not cache.calcular(b)


def test_reotimizacao_pode_entregar_na_cidade_atual():
    cenario = gerar_cenario(7)
    origem = cenario.cidades[2]
    restantes = list(dict.fromkeys([origem] + cenario.cidades))
    matriz = CacheDistancias().calcular(cenario, restantes)
    resultado = resolver_matriz("OR-Tools + GLS", matriz, origem, cenario.deposito, tempo_limite=.05)
    sim = SimulacaoPercurso(cenario, matriz, resultado.ordem, entregar_origem=True)
    assert sim.entregues == {origem}
    sim.avancar(1000)
    assert sim.entregues == set(cenario.cidades) - {cenario.deposito}


def test_validador_rejeita_distancia_incorreta():
    cenario = gerar_cenario(5)
    matriz = CacheDistancias().calcular(cenario)
    resultado = resolver_matriz("Vizinho mais próximo", matriz, cenario.deposito)
    resultado.distancia += 100
    with pytest.raises(ValueError, match="distância"):
        validar_resultado(resultado, matriz, cenario)


