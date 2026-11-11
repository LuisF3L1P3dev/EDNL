import random
import unittest
from solvers import executar, Orcamento, ORIGINAL, FECHO
from tsp_core import carregar_mapa
from test_solvers import ROOT
from test_tsp import exemplo


class HeldKarpTests(unittest.TestCase):
    def test_coincide_forca_bruta_ambos_modelos(self):
        rng = random.Random(29)
        for n in range(2, 8):
            g = exemplo(range(1, n + 1), [(a, b, rng.randrange(0, 20))
                         for a in range(1, n + 1) for b in range(a + 1, n + 1)])
            for variante in (ORIGINAL, FECHO):
                r = executar("held_karp", g, n, variante=variante)
                self.assertEqual(r.custo, executar("forca", g, n, variante=variante).custo)
                self.assertTrue(r.otimo)
                self.assertEqual((r.ordem[0], r.ordem[-1]), (n, n))

    def test_mapa_18_ciclo_391_memoria_e_camadas(self):
        r = executar("held_karp", carregar_mapa(ROOT / "data/mapa_18.json"), 1)
        self.assertEqual((r.custo, r.termino), (391, "otimo_comprovado"))
        self.assertEqual(len(r.ordem), 19)
        memoria = next(c.valor for c in r.contadores if c.unidade == "bytes")
        self.assertGreater(memoria, 0)
        self.assertLess(memoria, Orcamento().memoria_bytes)
        self.assertEqual(sum(e.tipo == "camada_dp" for e in r.eventos), 17)

    def test_inviavel_singleton_e_limites_sem_prova(self):
        estrela = exemplo([1, 2, 3, 4], [(1, 2, 1), (1, 3, 1), (1, 4, 1)])
        self.assertEqual(executar("held_karp", estrela, 1).termino, "inviavel_comprovado")
        self.assertEqual(executar("held_karp", exemplo([3], []), 3).custo, 0)
        g = carregar_mapa(ROOT / "data/mapa_05.json")
        for orcamento, motivo in ((Orcamento(memoria_bytes=1), "limite_memoria"),
                                  (Orcamento(max_estados=1), "limite_estados"),
                                  (Orcamento(segundos=1e-12), "limite_tempo")):
            r = executar("held_karp", g, 1, orcamento=orcamento)
            self.assertEqual(r.termino, motivo)
            self.assertFalse(r.otimo)
