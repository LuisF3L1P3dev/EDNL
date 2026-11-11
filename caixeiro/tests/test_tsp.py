"""Ciclos completos sobre a malha original, sem completar arestas."""
from dataclasses import replace
import math
from pathlib import Path
import unittest
from fixtures import mapa_18_pendente

from tsp_core import (Aresta, Grafo, No, GrafoInvalidoError, LimiteTSPError,
                      MapaNaoValidadoError, carregar_mapa, tsp_forca_bruta)

ROOT = Path(__file__).resolve().parents[1]


def exemplo(ids, edges):
    return Grafo("teste", "Teste", False, True, "fixture", "normalizadas_0_1",
                 tuple(No(i, 0, 0) for i in ids), tuple(Aresta(*e) for e in edges))


class ForcaBrutaTests(unittest.TestCase):
    def setUp(self):
        self.mapa = carregar_mapa(ROOT / "data/mapa_05.json")

    def test_mapa_05_ciclo_otimo_e_24_ordens(self):
        r = tsp_forca_bruta(self.mapa, 1)
        self.assertEqual(r.caminho, (1, 2, 3, 5, 4, 1))
        self.assertEqual(r.custo, 15)
        self.assertEqual(r.estados_testados, 24)
        self.assertTrue(r.otimo)
        self.assertGreater(r.ciclos_validos, 0)

    def test_todas_as_origens_preservam_ciclo_e_custo(self):
        adj = self.mapa.adjacencia()
        for origem in self.mapa.ids:
            with self.subTest(origem=origem):
                r = tsp_forca_bruta(self.mapa, origem)
                self.assertEqual(r.caminho[0], origem)
                self.assertEqual(r.caminho[-1], origem)
                self.assertEqual(set(r.caminho[:-1]), set(self.mapa.ids))
                self.assertEqual(len(r.caminho), 6)
                self.assertEqual(sum(adj[a][b] for a, b in zip(r.caminho, r.caminho[1:])), 15)

    def test_sem_ciclo_nao_cria_ligacao(self):
        r = tsp_forca_bruta(exemplo((1, 2, 3), ((1, 2, 1), (2, 3, 1))), 1)
        self.assertEqual(r.caminho, ())
        self.assertEqual(r.custo, math.inf)
        self.assertEqual(r.ciclos_validos, 0)

    def test_cidade_unica_e_ciclo_de_duas_cidades(self):
        self.assertEqual(tsp_forca_bruta(exemplo((7,), ()), 7).custo, 0)
        self.assertEqual(tsp_forca_bruta(exemplo((1, 2), ((1, 2, 2),)), 1).caminho, (1, 2, 1))

    def test_peso_zero_e_fracionario(self):
        r = tsp_forca_bruta(exemplo((1, 2, 3), ((1, 2, 0), (2, 3, .5), (3, 1, .25))), 1)
        self.assertEqual(r.custo, .75)

    def test_limite_antes_de_enumerar_18_nos(self):
        with self.assertRaises(LimiteTSPError):
            tsp_forca_bruta(exemplo(range(1, 19), ()), 1)

    def test_mapa_real_18_pendente_e_recusado(self):
        with self.assertRaises(MapaNaoValidadoError):
            tsp_forca_bruta(mapa_18_pendente(), 1)
        with self.assertRaises(LimiteTSPError):
            tsp_forca_bruta(carregar_mapa(ROOT / "data/mapa_18.json"), 1)

    def test_origem_invalida_e_mapa_pendente(self):
        for origem in (True, 0, 99, "1"):
            with self.subTest(origem=origem), self.assertRaises(GrafoInvalidoError):
                tsp_forca_bruta(self.mapa, origem)
        with self.assertRaises(MapaNaoValidadoError):
            tsp_forca_bruta(replace(self.mapa, validado=False), 1)
