"""Regressões do mapa real após a definição 9-14=1 pelo usuário."""
from pathlib import Path
import math
import unittest
from busca_limitada import tsp_branch_bound
from tsp_core import carregar_mapa, dijkstra


class Mapa18AlgoritmosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapa = carregar_mapa(Path(__file__).resolve().parents[1] / "data/mapa_18.json")

    def test_dijkstra_todos_os_pares_contra_floyd_warshall(self):
        ids = self.mapa.ids
        adj = self.mapa.adjacencia()
        dist = {(a, b): 0 if a == b else adj[a].get(b, math.inf) for a in ids for b in ids}
        for k in ids:
            for a in ids:
                for b in ids:
                    dist[a, b] = min(dist[a, b], dist[a, k] + dist[k, b])
        for a in ids:
            for b in ids:
                with self.subTest(origem=a, destino=b):
                    r = dijkstra(self.mapa, a, b)
                    self.assertEqual(r.custo, dist[a, b])
                    self.assertEqual(sum(adj[i][j] for i, j in zip(r.caminho, r.caminho[1:])), r.custo)

    def test_branch_bound_ciclo_real_otimo_391(self):
        # Custo também verificado por Held–Karp independente no script de auditoria.
        r = tsp_branch_bound(self.mapa, 1, limite_segundos=5)
        self.assertEqual(r.custo, 391)
        self.assertTrue(r.otimo)
        self.assertEqual(r.estado, "otimo_comprovado")
        self.assertEqual(len(r.caminho), 19)
        self.assertEqual(set(r.caminho[:-1]), set(self.mapa.ids))
        self.assertEqual(r.caminho[0], r.caminho[-1])
        adj = self.mapa.adjacencia()
        self.assertEqual(sum(adj[i][j] for i, j in zip(r.caminho, r.caminho[1:])), 391)
