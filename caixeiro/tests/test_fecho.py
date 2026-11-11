import math
from pathlib import Path
import unittest
from test_tsp import exemplo
from tsp_core import carregar_mapa, fecho_metrico, tsp_dijkstra, tsp_forca_bruta, MapaNaoValidadoError, LimiteTSPError

ROOT = Path(__file__).resolve().parents[1]


class FechoTests(unittest.TestCase):
    def test_fecho_preserva_caminhos_e_distancias_sem_mudar_original(self):
        mapa = carregar_mapa(ROOT / "data/mapa_05.json")
        fecho = fecho_metrico(mapa)
        self.assertEqual(len(fecho), 25)
        self.assertEqual(fecho[1, 3].caminho, (1, 2, 3))
        self.assertEqual(fecho[1, 3].custo, 6)
        self.assertNotIn(3, mapa.adjacencia()[1])
        with self.assertRaises(TypeError):
            fecho[1, 3] = None

    def test_tsp_mapa_05_custo_e_expansao(self):
        mapa = carregar_mapa(ROOT / "data/mapa_05.json")
        for origem in mapa.ids:
            r = tsp_dijkstra(mapa, origem)
            adj = mapa.adjacencia()
            self.assertEqual(r.custo, 15)
            self.assertEqual(sum(adj[a][b] for a, b in zip(r.caminho, r.caminho[1:])), r.custo)
            self.assertEqual(r.ordem[0], origem)
            self.assertEqual(r.ordem[-1], origem)
            self.assertEqual(set(r.ordem[:-1]), set(mapa.ids))

    def test_estrela_distingue_ciclo_hamiltoniano_e_passeio(self):
        mapa = exemplo((1, 2, 3, 4), ((1, 2, 1), (1, 3, 1), (1, 4, 1)))
        self.assertEqual(tsp_forca_bruta(mapa, 1).custo, math.inf)
        r = tsp_dijkstra(mapa, 1)
        self.assertEqual(r.custo, 6)
        self.assertGreater(r.caminho.count(1), 2)
        self.assertEqual(r.ordem, (1, 2, 3, 4, 1))

    def test_desconectado_e_cidade_unica(self):
        self.assertEqual(tsp_dijkstra(exemplo((1, 2, 3), ((1, 2, 1),)), 1).caminho, ())
        self.assertEqual(tsp_dijkstra(exemplo((7,), ()), 7).caminho, (7,))

    def test_limites_e_mapa_pendente(self):
        with self.assertRaises(LimiteTSPError):
            tsp_dijkstra(exemplo(range(1, 19), ()), 1)
        with self.assertRaises(MapaNaoValidadoError):
            tsp_dijkstra(carregar_mapa(ROOT / "data/mapa_18.json"), 1)
