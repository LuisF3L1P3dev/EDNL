import math
from pathlib import Path
from threading import Event
import unittest
from tsp_core import carregar_mapa, ErroGrafo
from solvers import executar, disponibilidade, Orcamento, ORIGINAL, FECHO
from test_tsp import exemplo

ROOT = Path(__file__).resolve().parents[1]


class ContratoTests(unittest.TestCase):
    def setUp(self):
        self.mapa = carregar_mapa(ROOT / "data/mapa_05.json")

    def test_adaptadores_preservam_custos_e_tempos(self):
        for nome, custo in (("dijkstra", 6), ("forca", 15), ("fecho", 15), ("limitada", 15)):
            r = executar(nome, self.mapa, 1, destino=3)
            self.assertEqual(r.custo, custo)
            self.assertTrue(r.otimo)
            t = dict(r.tempos_ms)
            self.assertAlmostEqual(t["total"], t["preparacao"] + t["otimizacao"] + t["reconstrucao"])
            self.assertTrue(all(c.unidade for c in r.contadores))
            self.assertTrue(all(e.metodo_origem == nome for e in r.eventos))

    def test_original_18_preserva_391(self):
        r = executar("limitada", carregar_mapa(ROOT / "data/mapa_18.json"), 1)
        self.assertEqual((r.custo, r.termino), (391, "otimo_comprovado"))

    def test_estados_distintos(self):
        cancelado = Event()
        cancelado.set()
        self.assertEqual(executar("forca", self.mapa, 1, cancelar=cancelado).termino, "cancelado")
        r = executar("forca", self.mapa, 1, orcamento=Orcamento(max_estados=1))
        self.assertEqual(r.termino, "limite_estados")
        self.assertFalse(r.otimo)
        self.assertEqual(executar("inexistente", self.mapa, 1).termino, "indisponivel")
        estrela = exemplo(range(1, 5), [(1, 2, 1), (1, 3, 1), (1, 4, 1)])
        r = executar("forca", estrela, 1)
        self.assertEqual(r.termino, "inviavel_comprovado")
        self.assertEqual(r.custo, math.inf)
        self.assertEqual(executar("forca", estrela, 1, variante=FECHO).custo, 6)

    def test_limite_eventos_e_progresso_cancelavel(self):
        sinal, fases = Event(), []
        def progresso(fase):
            fases.append(fase)
            sinal.set()
        r = executar("fecho", self.mapa, 1, cancelar=sinal, progresso=progresso)
        self.assertEqual(r.termino, "cancelado")
        self.assertTrue(fases)
        r = executar("forca", self.mapa, 1, orcamento=Orcamento(max_eventos=2))
        self.assertLessEqual(len(r.eventos), 2)

    def test_guardas(self):
        with self.assertRaises(ErroGrafo):
            executar("forca", self.mapa, 99)
        with self.assertRaises(ValueError):
            Orcamento(segundos=0)
        self.assertTrue(disponibilidade("forca", carregar_mapa(ROOT / "data/mapa_18.json")))
