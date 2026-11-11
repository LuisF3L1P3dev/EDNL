from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest
from tsp_core import carregar_mapa, dijkstra, tsp_forca_bruta, tsp_dijkstra

ROOT = Path(__file__).resolve().parents[1]


class EventosTests(unittest.TestCase):
    def setUp(self):
        self.mapa = carregar_mapa(ROOT / "data/mapa_05.json")

    def test_dijkstra_historico_reproduzivel_e_snapshot(self):
        a, b = [], []
        dijkstra(self.mapa, 1, 3, eventos=a)
        dijkstra(self.mapa, 1, 3, eventos=b)
        self.assertEqual(a, b)
        self.assertEqual(a[0].fila, ((0, 1),))
        self.assertEqual(a[0].visitados, ())
        self.assertEqual(a[-1].candidato, (1, 2, 3))
        self.assertEqual(a[-1].custo, 6)
        relaxa = next(p for p in a if p.relaxamento == (1, 2))
        self.assertEqual(dict(relaxa.predecessores)[2], 1)
        self.assertEqual(dict(relaxa.distancias)[2], 2)
        with self.assertRaises(FrozenInstanceError):
            a[0].tipo = "mudou"

    def test_forca_bruta_registra_24_candidatos_e_melhor(self):
        eventos = []
        r = tsp_forca_bruta(self.mapa, 1, eventos=eventos)
        self.assertEqual([p.contador for p in eventos[:-1]], list(range(1, 25)))
        self.assertEqual(eventos[-1].melhor, r.caminho)
        self.assertEqual(eventos[-1].melhor_custo, 15)
        self.assertTrue(all(a.melhor_custo >= b.melhor_custo for a, b in zip(eventos, eventos[1:])))

    def test_gravacao_nao_altera_resultado_e_fecho_e_reproduzivel(self):
        a, b = [], []
        self.assertEqual(tsp_dijkstra(self.mapa, 1), tsp_dijkstra(self.mapa, 1, eventos=a))
        tsp_dijkstra(self.mapa, 1, eventos=b)
        self.assertEqual(a, b)
