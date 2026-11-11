"""Caminhos mínimos, reconstrução e limites da API da TSP-007."""

from dataclasses import FrozenInstanceError, replace
import math
from pathlib import Path
import unittest

from tsp_core import (
    Aresta, ErroGrafo, Grafo, GrafoInvalidoError, MapaNaoValidadoError,
    No, carregar_mapa, dijkstra,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def grafo_de_teste(ids, arestas):
    return Grafo(
        id="teste", nome="Grafo de teste", direcionado=False, validado=True,
        referencia="fixture", sistema_coordenadas="normalizadas_0_1",
        nos=tuple(No(node_id, 0, 0) for node_id in ids),
        arestas=tuple(Aresta(*aresta) for aresta in arestas),
    )


class DijkstraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapa = carregar_mapa(PROJECT_ROOT / "data" / "mapa_05.json")

    def test_caso_de_aceite_1_2_3_com_custo_6(self):
        resultado = dijkstra(self.mapa, 1, 3)
        self.assertEqual(resultado.caminho, (1, 2, 3))
        self.assertEqual(resultado.custo, 6)

    def test_todos_os_pares_do_mapa_05_com_soma_das_arestas_reais(self):
        # Distâncias conferidas manualmente, independentes da implementação.
        distancias = (
            (0, 2, 6, 3, 6), (2, 0, 4, 3, 6), (6, 4, 0, 6, 3),
            (3, 3, 6, 0, 3), (6, 6, 3, 3, 0),
        )
        adjacencia = self.mapa.adjacencia()
        for origem in self.mapa.ids:
            for destino in self.mapa.ids:
                with self.subTest(origem=origem, destino=destino):
                    resultado = dijkstra(self.mapa, origem, destino)
                    self.assertEqual(resultado.custo, distancias[origem - 1][destino - 1])
                    self.assertEqual(resultado.caminho[0], origem)
                    self.assertEqual(resultado.caminho[-1], destino)
                    self.assertEqual(len(resultado.caminho), len(set(resultado.caminho)))
                    custo_real = sum(
                        adjacencia[a][b]
                        for a, b in zip(resultado.caminho, resultado.caminho[1:])
                    )
                    self.assertEqual(custo_real, resultado.custo)

    def test_caminho_inverso_no_grafo_nao_direcionado(self):
        resultado = dijkstra(self.mapa, 3, 1)
        self.assertEqual(resultado.caminho, (3, 2, 1))
        self.assertEqual(resultado.custo, 6)

    def test_destino_so_e_aceito_ao_ser_retirado_com_menor_custo(self):
        grafo = grafo_de_teste((1, 2, 3, 4), (
            (1, 4, 20), (1, 2, 1), (2, 3, 2), (3, 4, 3),
        ))
        resultado = dijkstra(grafo, 1, 4)
        self.assertEqual(resultado.caminho, (1, 2, 3, 4))
        self.assertEqual(resultado.custo, 6)

    def test_melhoria_de_distancia_substitui_predecessor(self):
        grafo = grafo_de_teste((1, 2, 3, 4, 5), (
            (1, 2, 10), (1, 3, 1), (3, 2, 1), (2, 4, 1), (4, 5, 20),
        ))
        resultado = dijkstra(grafo, 1, 5)
        self.assertEqual(resultado.caminho, (1, 3, 2, 4, 5))
        self.assertEqual(resultado.custo, 23)

    def test_pesos_zero_ciclo_de_custo_zero_e_pesos_fracionarios(self):
        grafo = grafo_de_teste((1, 2, 3, 4), (
            (1, 2, 0), (2, 3, 0), (3, 1, 0), (3, 4, 0.25), (1, 4, 1),
        ))
        resultado = dijkstra(grafo, 1, 4)
        self.assertEqual(resultado.caminho, (1, 3, 4))
        self.assertEqual(resultado.custo, 0.25)

    def test_origem_igual_destino_retorna_um_no_e_zero(self):
        for node_id in self.mapa.ids:
            with self.subTest(node=node_id):
                resultado = dijkstra(self.mapa, node_id, node_id)
                self.assertEqual(resultado.caminho, (node_id,))
                self.assertEqual(resultado.custo, 0)

    def test_destino_inalcancavel_retorna_vazio_e_infinito(self):
        grafo = grafo_de_teste((1, 2, 3, 7), ((1, 2, 1), (2, 3, 2)))
        resultado = dijkstra(grafo, 1, 7)
        self.assertEqual(resultado.caminho, ())
        self.assertEqual(resultado.custo, math.inf)

    def test_grafo_sem_arestas_e_grafo_de_um_no(self):
        grafo = grafo_de_teste((1, 7), ())
        self.assertEqual(dijkstra(grafo, 1, 7).custo, math.inf)
        unico = dijkstra(grafo_de_teste((9,), ()), 9, 9)
        self.assertEqual(unico.caminho, (9,))
        self.assertEqual(unico.custo, 0)

    def test_rejeita_ids_ausentes_e_tipos_invalidos_nas_duas_pontas(self):
        for invalido in (99, 0, -1, True, 1.0, "1", None):
            for origem, destino in ((invalido, 3), (1, invalido)):
                with self.subTest(origem=origem, destino=destino):
                    with self.assertRaises(GrafoInvalidoError):
                        dijkstra(self.mapa, origem, destino)

    def test_mapa_18_bloqueado_mesmo_com_origem_igual_destino(self):
        mapa = carregar_mapa(PROJECT_ROOT / "data" / "mapa_18.json")
        for origem, destino in ((1, 3), (1, 1), (9, 14)):
            with self.subTest(origem=origem, destino=destino):
                with self.assertRaisesRegex(MapaNaoValidadoError, "9-14"):
                    dijkstra(mapa, origem, destino)

    def test_mapa_nao_validado_com_pesos_conhecidos_tambem_bloqueia(self):
        mapa = replace(self.mapa, validado=False)
        with self.assertRaises(MapaNaoValidadoError):
            dijkstra(mapa, 1, 3)

    def test_empates_sao_reproduziveis_independente_da_ordem_do_cadastro(self):
        arestas = ((1, 3, 1), (3, 4, 1), (1, 2, 1), (2, 4, 1))
        grafo = grafo_de_teste((4, 3, 2, 1), arestas)
        invertido = grafo_de_teste((1, 2, 3, 4), tuple(
            (b, a, peso) for a, b, peso in reversed(arestas)
        ))
        primeiro = dijkstra(grafo, 1, 4)
        self.assertEqual(primeiro.caminho, (1, 2, 4))
        self.assertEqual(primeiro, dijkstra(invertido, 1, 4))

    def test_resultado_imutavel_e_grafo_preservado_entre_execucoes(self):
        antes = self.mapa.adjacencia()
        resultado = dijkstra(self.mapa, 1, 3)
        with self.assertRaises(FrozenInstanceError):
            resultado.custo = 99
        self.assertEqual(self.mapa.adjacencia(), antes)
        self.assertEqual(resultado, dijkstra(self.mapa, 1, 3))

    def test_reconstrucao_longa_nao_depende_de_recursao(self):
        grafo = grafo_de_teste(range(1, 1102), ((i, i + 1, 1) for i in range(1, 1101)))
        resultado = dijkstra(grafo, 1, 1101)
        self.assertEqual(resultado.caminho, tuple(range(1, 1102)))
        self.assertEqual(resultado.custo, 1100)

    def test_estouro_numerico_nao_e_reportado_como_destino_inalcancavel(self):
        # Não somar uma aresta de volta para um nó já finalizado.
        finito = grafo_de_teste((1, 2, 3), ((1, 2, 1e308), (2, 3, 0)))
        self.assertEqual(dijkstra(finito, 1, 3).custo, 1e308)
        grafo = grafo_de_teste((1, 2, 3), ((1, 2, 1e308), (2, 3, 1e308)))
        with self.assertRaisesRegex(ErroGrafo, "Custo acumulado"):
            dijkstra(grafo, 1, 3)

    def test_inteiros_grandes_nao_perdem_precisao(self):
        peso = 10 ** 400
        grafo = grafo_de_teste((1, 2, 3), ((1, 2, peso), (2, 3, peso)))
        resultado = dijkstra(grafo, 1, 3)
        self.assertEqual(resultado.custo, 2 * peso)
        self.assertIs(type(resultado.custo), int)

    def test_rejeita_entrada_que_nao_e_grafo(self):
        with self.assertRaisesRegex(GrafoInvalidoError, "objeto Grafo"):
            dijkstra({}, 1, 3)


if __name__ == "__main__":
    unittest.main()
