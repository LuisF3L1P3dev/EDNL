"""Valida os algoritmos sem depender de Pygame, assets ou mapas externos."""

import math
import threading
import unittest

from solvers import executar


class GrafoTeste:
    def __init__(self, ids, arestas):
        self.ids = tuple(ids)
        self._adj = {no: {} for no in ids}
        for a, b, peso in arestas:
            self._adj[a][b] = self._adj[b][a] = peso

    def adjacencia(self):
        return {no: dict(vizinhos) for no, vizinhos in self._adj.items()}

    def custo(self, caminho):
        return sum(self._adj[a][b] for a, b in zip(caminho, caminho[1:]))


ARESTAS_5 = [
    (1, 2, 2), (1, 4, 3), (1, 5, 6), (2, 3, 4),
    (2, 4, 3), (3, 4, 7), (3, 5, 3), (4, 5, 3),
]


class TestSolvers(unittest.TestCase):
    def setUp(self):
        self.grafo = GrafoTeste(range(1, 6), ARESTAS_5)

    def assertCaminhoValido(self, grafo, caminho):
        for a, b in zip(caminho, caminho[1:]):
            self.assertIn(b, grafo.adjacencia()[a])

    def test_forca_bruta_custo_15(self):
        resultado = executar("forca", self.grafo, 1)
        self.assertEqual(resultado.termino, "concluido")
        self.assertEqual(resultado.custo, 15)
        self.assertIn(resultado.caminho, [(1, 2, 3, 5, 4, 1), (1, 4, 5, 3, 2, 1)])
        self.assertEqual(resultado.candidatas, math.factorial(4))
        self.assertCaminhoValido(self.grafo, resultado.caminho)

    def test_forca_bruta_origem_fixa(self):
        resultado = executar("forca", self.grafo, 3)
        self.assertEqual(resultado.custo, 15)
        self.assertEqual(resultado.caminho[0], 3)
        self.assertEqual(resultado.caminho[-1], 3)
        self.assertEqual(len(set(resultado.caminho[:-1])), 5)

    def test_forca_bruta_limite_nove(self):
        with self.assertRaisesRegex(ValueError, "9"):
            executar("forca", GrafoTeste(range(18), []), 0)

    def test_dijkstra_menor_caminho(self):
        resultado = executar("dijkstra", self.grafo, 1, 3)
        self.assertEqual(resultado.caminho, (1, 2, 3))
        self.assertEqual(resultado.custo, 6)
        self.assertEqual(resultado.distancias[3], 6)
        self.assertEqual(resultado.custo, self.grafo.custo(resultado.caminho))
        self.assertIn(3, resultado.explorados)
        self.assertEqual(resultado.garantia, "caminho mínimo")

    def test_dijkstra_nao_e_circuito_tsp(self):
        resultado = executar("dijkstra", self.grafo, 1, 1)
        self.assertEqual(resultado.caminho, (1,))
        self.assertEqual(resultado.custo, 0)
        with self.assertRaisesRegex(ValueError, "destino"):
            executar("dijkstra", self.grafo, 1)

    def test_dijkstra_melhora_distancia_ja_descoberta(self):
        grafo = GrafoTeste(range(4), [(0, 1, 10), (0, 2, 1), (2, 1, 1), (1, 3, 1)])
        resultado = executar("dijkstra", grafo, 0, 3)
        self.assertEqual(resultado.caminho, (0, 2, 1, 3))
        self.assertEqual(resultado.custo, 3)

    def test_desconexo_nao_tem_solucao(self):
        grafo = GrafoTeste(range(3), [(0, 1, 1)])
        for metodo, destino in [("forca", None), ("heuristica", None), ("dijkstra", 2)]:
            with self.subTest(metodo=metodo):
                resultado = executar(metodo, grafo, 0, destino)
                self.assertEqual(resultado.termino, "sem_solucao")
                self.assertIsNone(resultado.custo)
                self.assertEqual(resultado.caminho, ())

    def test_heuristica_expande_ruas_e_pode_revisitar_nos(self):
        # Em uma estrela não existe ciclo hamiltoniano, mas há passeio fechado.
        grafo = GrafoTeste(range(1, 19), [(1, no, no) for no in range(2, 19)])
        resultado = executar("heuristica", grafo, 7)
        self.assertEqual(resultado.termino, "concluido")
        self.assertEqual(set(resultado.caminho), set(grafo.ids))
        self.assertEqual(resultado.caminho[0], 7)
        self.assertEqual(resultado.caminho[-1], 7)
        self.assertCaminhoValido(grafo, resultado.caminho)
        self.assertEqual(resultado.custo, grafo.custo(resultado.caminho))
        self.assertEqual(resultado.custo, 2 * sum(range(2, 19)))
        self.assertIn("sem garantia", resultado.garantia)

    def test_eventos_sao_snapshots_e_usam_arestas_reais(self):
        for metodo, destino in [("forca", None), ("heuristica", None), ("dijkstra", 3)]:
            eventos = []
            with self.subTest(metodo=metodo):
                resultado = executar(metodo, self.grafo, 1, destino, progresso=eventos.append)
                self.assertTrue(eventos)
                self.assertEqual(eventos[-1].fase, "concluido")
                self.assertEqual(eventos[-1].caminho, resultado.caminho)
                for evento in eventos:
                    self.assertCaminhoValido(self.grafo, evento.caminho)
                eventos[-1].distancias[99] = 999
                self.assertNotIn(99, resultado.distancias)
                self.assertNotIn(99, eventos[0].distancias)

    def test_2opt_melhora_rota_do_vizinho_proximo(self):
        pontos = {1: (0, 0), 2: (1, 0), 3: (0, 2), 4: (2, 2)}
        grafo = GrafoTeste(pontos, [
            (a, b, math.dist(pontos[a], pontos[b]))
            for a in pontos for b in pontos if a < b
        ])
        eventos = []
        resultado = executar("heuristica", grafo, 1, progresso=eventos.append)
        custo_inicial = [e.custo for e in eventos if e.fase == "vizinho_proximo"][-1]
        self.assertTrue(any(e.fase == "2-opt" for e in eventos))
        self.assertLess(resultado.custo, custo_inicial)
        self.assertAlmostEqual(resultado.custo, 5 + math.sqrt(5))

    def test_circuito_trivial_sem_aresta_inventada(self):
        grafo = GrafoTeste([1], [])
        for metodo in ["forca", "heuristica", "dijkstra"]:
            resultado = executar(metodo, grafo, 1, 1)
            self.assertEqual(resultado.caminho, (1,))
            self.assertEqual(resultado.custo, 0)

    def test_cancelamento_antes_de_iniciar(self):
        sinal = threading.Event()
        sinal.set()
        for metodo in ["forca", "dijkstra", "heuristica"]:
            resultado = executar(metodo, self.grafo, 1, 3, cancelar=sinal)
            self.assertEqual(resultado.termino, "cancelado")
            self.assertIsNone(resultado.custo)
            self.assertEqual(resultado.caminho, ())

    def test_cancelamento_cooperativo_durante_calculo(self):
        for metodo in ["forca", "dijkstra", "heuristica"]:
            eventos = []
            resultado = executar(
                metodo, self.grafo, 1, 3,
                cancelar=lambda: bool(eventos), progresso=eventos.append,
            )
            self.assertEqual(resultado.termino, "cancelado")
            self.assertEqual(eventos[-1].fase, "cancelado")
            self.assertIn("sem garantia", resultado.garantia)
            if resultado.caminho:
                self.assertCaminhoValido(self.grafo, resultado.caminho)

    def test_pesos_invalidos_rejeitados(self):
        for peso in [-1, math.inf, math.nan]:
            with self.subTest(peso=peso), self.assertRaises(ValueError):
                executar("dijkstra", GrafoTeste([1, 2], [(1, 2, peso)]), 1, 2)

    def test_metodo_e_origem_invalidos(self):
        with self.assertRaises(ValueError):
            executar("inexistente", self.grafo, 1)
        with self.assertRaises(ValueError):
            executar("heuristica", self.grafo, 99)

    def test_grafo_nao_e_modificado(self):
        antes = self.grafo.adjacencia()
        for metodo in ["forca", "dijkstra", "heuristica"]:
            executar(metodo, self.grafo, 1, 3)
        self.assertEqual(antes, self.grafo.adjacencia())


if __name__ == "__main__":
    unittest.main()
