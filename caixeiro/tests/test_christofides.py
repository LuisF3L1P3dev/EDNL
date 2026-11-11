from dataclasses import replace
import random
from threading import Event
import unittest
from solvers import executar, Contexto, Orcamento, _matching_exato, ORIGINAL, FECHO
from tsp_core import ErroGrafo, carregar_mapa
from test_solvers import ROOT
from test_tsp import exemplo


class ChristofidesTests(unittest.TestCase):
    def test_matching_exato_supera_escolha_gulosa(self):
        custos = {(1, 2): 2, (1, 3): 3, (1, 4): 3,
                  (2, 3): 3, (2, 4): 3, (3, 4): 6}
        ctx = Contexto("christofides", Orcamento(), Event(), None)
        custo, pares = _matching_exato((1, 2, 3, 4), custos, ctx)
        self.assertEqual(custo, 6)  # guloso escolheria 1-2 + 3-4 = 8
        self.assertEqual(len(pares), 2)

    def test_limite_3_2_contra_held_karp_mesmo_fecho(self):
        rng = random.Random(30)
        for n in range(2, 9):
            for _ in range(3):
                g = exemplo(range(1, n + 1), [(a, b, rng.randrange(0, 30))
                           for a in range(1, n + 1) for b in range(a + 1, n + 1)])
                r = executar("christofides", g, n)
                otimo = executar("held_karp", g, n, variante=FECHO)
                self.assertLessEqual(r.custo, 1.5 * otimo.custo)
                self.assertFalse(r.otimo)
                self.assertEqual(r.termino, "aproximacao")

    def test_mapas_e_etapas_multigrafo(self):
        for arquivo in ("mapa_05.json", "mapa_18.json"):
            g = carregar_mapa(ROOT / "data" / arquivo)
            r = executar("christofides", g, 1)
            self.assertEqual(len(r.ordem), len(g.ids) + 1)
            self.assertTrue({"mst", "vertices_impares", "matching_minimo", "circuito_euleriano", "atalhamento"}
                            <= {e.tipo for e in r.eventos})
        self.assertEqual(executar("christofides", exemplo([1], []), 1).custo, 0)

    def test_precondicoes(self):
        g = exemplo([1, 2, 3], [(1, 2, 1), (2, 3, 1), (1, 3, 10)])
        with self.assertRaisesRegex(ErroGrafo, "triangular"):
            executar("christofides", g, 1, variante=ORIGINAL)
        with self.assertRaisesRegex(ErroGrafo, "completa"):
            executar("christofides", exemplo([1, 2, 3], [(1, 2, 1), (2, 3, 1)]), 1, variante=ORIGINAL)
        with self.assertRaisesRegex(ErroGrafo, "direcionado"):
            executar("christofides", replace(g, direcionado=True), 1, variante=ORIGINAL)
        with self.assertRaisesRegex(ErroGrafo, "conectado"):
            executar("christofides", exemplo([1, 2], []), 1)
