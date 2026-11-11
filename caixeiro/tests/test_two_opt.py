import unittest
from solvers import executar, Orcamento, ORIGINAL, FECHO
from tsp_core import ErroGrafo, carregar_mapa
from test_tsp import exemplo
from test_solvers import ROOT


class TwoOptTests(unittest.TestCase):
    def setUp(self):
        self.g = exemplo(range(1, 5), [(1, 2, 1), (2, 3, 1), (3, 4, 1),
                                      (4, 1, 1), (1, 3, 2), (2, 4, 2)])

    def test_melhoria_estrita_e_snapshots(self):
        r = executar("two_opt", self.g, 1, variante=ORIGINAL, ordem_inicial=(1, 3, 2, 4, 1))
        self.assertEqual((r.custo, r.termino), (4, "otimo_local"))
        self.assertFalse(r.otimo)
        troca = next(e for e in r.eventos if e.tipo == "troca_2opt")
        self.assertLess(troca.custo, troca.custo_anterior)
        self.assertEqual((len(troca.removidas), len(troca.adicionadas)), (2, 2))
        self.assertEqual(r.ordem[0], 1)

    def test_sem_melhoria_e_limite_preservam_rota(self):
        rota = (1, 2, 3, 4, 1)
        r = executar("two_opt", self.g, 1, ordem_inicial=rota)
        self.assertEqual((r.ordem, r.custo, r.termino), (rota, 4, "otimo_local"))
        r = executar("two_opt", self.g, 1, ordem_inicial=(1, 3, 2, 4, 1),
                     orcamento=Orcamento(max_iteracoes=1))
        self.assertEqual(r.termino, "limite_iteracoes")
        self.assertLessEqual(r.custo, 6)

    def test_pipeline_nunca_piora_e_reexpande(self):
        for arquivo in ("mapa_05.json", "mapa_18.json"):
            g = carregar_mapa(ROOT / "data" / arquivo)
            inicial = executar("nearest_neighbor", g, 1)
            r = executar("two_opt", g, 1)
            self.assertLessEqual(r.custo, inicial.custo)
            self.assertEqual(r.pipeline, ("nearest_neighbor", "two_opt"))
            self.assertEqual(set(r.ordem[:-1]), set(g.ids))
            limitado = executar("two_opt", g, 1, ordem_inicial=inicial,
                                 orcamento=Orcamento(max_estados=1))
            self.assertEqual(limitado.termino, "limite_estados")
            self.assertLessEqual(limitado.custo, inicial.custo)

    def test_valida_inicial_e_rejeita_arcos_ausentes(self):
        with self.assertRaises(ErroGrafo):
            executar("two_opt", self.g, 1, ordem_inicial=(1, 2, 1))
        inicial = executar("nearest_neighbor", self.g, 1)
        with self.assertRaisesRegex(ErroGrafo, "variante"):
            executar("two_opt", self.g, 1, variante=ORIGINAL, ordem_inicial=inicial)
        esparso = exemplo(range(1, 5), [(1, 2, 1), (2, 3, 1), (3, 4, 1), (4, 1, 1)])
        r = executar("two_opt", esparso, 1, variante=ORIGINAL, ordem_inicial=(1, 2, 3, 4, 1))
        self.assertEqual(r.custo, 4)
