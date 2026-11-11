import math
from pathlib import Path
import unittest
from test_tsp import exemplo
from busca_limitada import tsp_branch_bound
from tsp_core import carregar_mapa, tsp_forca_bruta, MapaNaoValidadoError


class BuscaLimitadaTests(unittest.TestCase):
    def test_concorda_com_forca_bruta_em_todas_as_origens(self):
        mapa = carregar_mapa(Path(__file__).resolve().parents[1] / "data/mapa_05.json")
        for origem in mapa.ids:
            r = tsp_branch_bound(mapa, origem)
            self.assertEqual(r.custo, tsp_forca_bruta(mapa, origem).custo)
            self.assertTrue(r.otimo)
            self.assertEqual(r.estado, "otimo_comprovado")

    def test_instancia_sintetica_de_18_nos_termina_com_prova(self):
        # Instância de teste, não é o mapa da aula nem substitui seu peso ausente.
        grafo = exemplo(range(1, 19), [(i, i + 1, 1) for i in range(1, 18)] + [(18, 1, 1)])
        r = tsp_branch_bound(grafo, 1, limite_segundos=1, max_estados=1000)
        self.assertEqual(r.custo, 18)
        self.assertTrue(r.otimo)
        self.assertLess(r.nos_expandidos, 1000)

    def test_orcamento_nao_declara_inexistencia_ou_otimo(self):
        grafo = exemplo(range(1, 19), [(i, i + 1, 1) for i in range(1, 18)] + [(18, 1, 1)])
        r = tsp_branch_bound(grafo, 1, max_estados=1)
        self.assertFalse(r.otimo)
        self.assertEqual(r.estado, "limite_sem_solucao")
        r = tsp_branch_bound(grafo, 1, max_estados=18)
        self.assertEqual(r.custo, 18)
        self.assertFalse(r.otimo)
        self.assertEqual(r.estado, "melhor_conhecida")

    def test_prova_de_ausencia_e_cidade_unica(self):
        r = tsp_branch_bound(exemplo((1, 2, 3), ((1, 2, 1),)), 1)
        self.assertEqual(r.estado, "sem_ciclo_comprovado")
        self.assertEqual(r.custo, math.inf)
        self.assertTrue(r.otimo)
        self.assertEqual(tsp_branch_bound(exemplo((7,), ()), 7).custo, 0)

    def test_mapa_real_18_continua_bloqueado(self):
        mapa = carregar_mapa(Path(__file__).resolve().parents[1] / "data/mapa_18.json")
        with self.assertRaises(MapaNaoValidadoError):
            tsp_branch_bound(mapa, 1)

    def test_limites_invalidos(self):
        grafo = exemplo((1,), ())
        for limite in (0, -1, True, math.inf):
            with self.assertRaises(ValueError):
                tsp_branch_bound(grafo, 1, limite_segundos=limite)
        with self.assertRaises(ValueError):
            tsp_branch_bound(grafo, 1, max_estados=True)
