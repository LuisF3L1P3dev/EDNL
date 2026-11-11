from threading import Event, Timer
from unittest.mock import patch
import unittest
from solvers import executar, disponibilidade, dependencia_ortools, Orcamento, ORIGINAL, FECHO, _custos_inteiros
from tsp_core import ErroGrafo, carregar_mapa
from test_solvers import ROOT
from test_tsp import exemplo


class DependenciaTests(unittest.TestCase):
    def test_ausencia_de_dependencia_nao_impede_demais_solvers(self):
        g = carregar_mapa(ROOT / "data/mapa_05.json")
        with patch("solvers.importlib.util.find_spec", return_value=None):
            self.assertIn("opcional ausente", disponibilidade("ortools_solver", g))
            self.assertEqual(executar("ortools_solver", g, 1).termino, "indisponivel")
            self.assertEqual(executar("held_karp", g, 1).custo, 15)

    def test_escala_exata_e_overflow(self):
        inteiros, escala = _custos_inteiros({(1, 2): 0.125, (2, 3): 0.2}, 3)
        self.assertEqual((inteiros[1, 2], inteiros[2, 3], escala), (5, 8, 40))
        with self.assertRaisesRegex(ErroGrafo, "int64"):
            _custos_inteiros({(1, 2): 10**30}, 3)


@unittest.skipIf(dependencia_ortools(), "OR-Tools opcional não instalado")
class OrtoolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from ortools.constraint_solver import pywrapcp

    def test_mapa_5_e_18_ambas_variantes_sem_falsa_prova(self):
        for arquivo in ("mapa_05.json", "mapa_18.json"):
            g = carregar_mapa(ROOT / "data" / arquivo)
            for variante in (ORIGINAL, FECHO):
                r = executar("ortools_solver", g, 1, variante=variante,
                             busca_local="GREEDY_DESCENT", orcamento=Orcamento(segundos=1))
                self.assertTrue(r.ordem)
                self.assertFalse(r.otimo)
                if len(g.ids) == 5:
                    self.assertEqual(r.custo, executar("held_karp", g, 1, variante=variante).custo)
                self.assertIn("versao_ortools", dict(r.parametros))
                self.assertIn("status_ortools", dict(r.parametros))
                adj = g.adjacencia()
                self.assertEqual(r.custo, sum(adj[a][b] for a, b in zip(r.caminho, r.caminho[1:])))

    def test_decimais_origem_e_arcos_proibidos(self):
        g = exemplo([2, 7, 9], [(2, 7, 0.125), (7, 9, 0.2), (2, 9, 0.25)])
        r = executar("ortools_solver", g, 7, variante=ORIGINAL, busca_local="GREEDY_DESCENT")
        self.assertAlmostEqual(r.custo, 0.575)
        self.assertEqual((r.ordem[0], r.ordem[-1]), (7, 7))
        estrela = exemplo([1, 2, 3, 4], [(1, 2, 1), (1, 3, 1), (1, 4, 1)])
        r = executar("ortools_solver", estrela, 1, variante=ORIGINAL,
                     orcamento=Orcamento(segundos=0.1))
        self.assertFalse(r.ordem)
        self.assertFalse(r.otimo)
        self.assertGreater(next(c.valor for c in r.contadores if c.nome == "arcos proibidos"), 0)

    def test_timeout_sem_solucao_e_cancelamento_cooperativo(self):
        from ortools.constraint_solver import pywrapcp
        g = carregar_mapa(ROOT / "data/mapa_18.json")
        with patch.object(pywrapcp.RoutingModel, "SolveWithParameters", return_value=None), \
             patch.object(pywrapcp.RoutingModel, "status", return_value=4):
            r = executar("ortools_solver", g, 1)
            self.assertEqual(r.termino, "limite_tempo")
            self.assertFalse(r.caminho)
        sinal = Event()
        timer = Timer(0.03, sinal.set)
        timer.start()
        try:
            r = executar("ortools_solver", g, 1, cancelar=sinal, orcamento=Orcamento(segundos=2))
            self.assertEqual(r.termino, "cancelado")
            self.assertFalse(r.otimo)
            self.assertLess(dict(r.tempos_ms)["total"], 1000)
        finally:
            timer.cancel()

    def test_uma_cidade(self):
        r = executar("ortools_solver", exemplo([5], []), 5, busca_local="GREEDY_DESCENT")
        self.assertEqual((r.ordem, r.custo), ((5,), 0))
