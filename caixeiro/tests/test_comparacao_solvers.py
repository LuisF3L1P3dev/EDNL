from dataclasses import replace
import unittest
from comparacao_solvers import comparar_solvers, resumir
from solvers import executar, FECHO, ORIGINAL, Orcamento
from test_tsp import exemplo


class ComparacaoSolversTests(unittest.TestCase):
    def setUp(self):
        self.g = exemplo([1, 2, 3], [(1, 2, 1), (2, 3, 1), (1, 3, 10)])

    def test_oraculo_e_gap_do_mesmo_modelo(self):
        for variante, custo in ((ORIGINAL, 12), (FECHO, 4)):
            resultados, resumo = comparar_solvers(self.g, 1, variante, orcamento=Orcamento(segundos=0.05))
            self.assertEqual(resumo["oraculo"], "held_karp")
            self.assertEqual(resumo["otimo"], custo)
            self.assertTrue(all(r.variante == variante for r in resultados.values()))
            self.assertEqual(resumo["gaps"]["held_karp"]["percentual"], 0)

    def test_rejeita_mistura_de_modelos_origens_e_pesos(self):
        a = executar("held_karp", self.g, 1)
        for b in (executar("nearest_neighbor", self.g, 1), executar("held_karp", self.g, 2),
                  executar("held_karp", exemplo([1, 2, 3], [(1, 2, 2), (2, 3, 2), (1, 3, 10)]), 1)):
            with self.assertRaises(ValueError):
                resumir({"a": a, "b": b})
        with self.assertRaises(ValueError):
            resumir({"dijkstra": executar("dijkstra", self.g, 1, destino=2)})

    def test_sem_oraculo_nao_inventa_gap_e_zero_nao_divide(self):
        r = executar("nearest_neighbor", self.g, 1)
        self.assertIsNone(resumir({"nn": r})["gaps"]["nn"]["percentual"])
        g = exemplo([1, 2], [(1, 2, 0)])
        exato = executar("held_karp", g, 1, variante=FECHO)
        nn = executar("nearest_neighbor", g, 1)
        self.assertEqual(resumir({"held_karp": exato, "nn": nn})["gaps"]["nn"]["percentual"], 0)

    def test_oraculo_cortado_nao_e_certificado(self):
        r = executar("held_karp", self.g, 1, orcamento=Orcamento(memoria_bytes=1))
        self.assertIsNone(resumir({"held_karp": r})["otimo"])
