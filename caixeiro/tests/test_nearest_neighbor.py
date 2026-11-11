import unittest
from solvers import executar, ORIGINAL, FECHO
from tsp_core import ErroGrafo
from test_tsp import exemplo
from test_solvers import ROOT
from tsp_core import carregar_mapa


class NearestNeighborTests(unittest.TestCase):
    def test_mapas_conectados_e_custos_fisicos(self):
        for arquivo in ("mapa_05.json", "mapa_18.json"):
            g = carregar_mapa(ROOT / "data" / arquivo)
            r = executar("nearest_neighbor", g, 1)
            self.assertEqual(r.variante, FECHO)
            self.assertEqual(set(r.ordem[:-1]), set(g.ids))
            self.assertEqual((r.ordem[0], r.ordem[-1]), (1, 1))
            adj = g.adjacencia()
            self.assertEqual(r.custo, sum(adj[a][b] for a, b in zip(r.caminho, r.caminho[1:])))
            self.assertFalse(r.otimo)
            self.assertTrue(any(e.tipo == "escolha" for e in r.eventos))

    def test_empates_por_id_e_origem_arbitraria(self):
        g = exemplo([2, 7, 9], [(9, 7, 1), (9, 2, 1), (2, 7, 1)])
        self.assertEqual(executar("nearest_neighbor", g, 9).ordem, (9, 2, 7, 9))
        unico = executar("nearest_neighbor", exemplo([7], []), 7)
        self.assertEqual((unico.ordem, unico.custo), ((7,), 0))

    def test_desconectado_e_bloqueio_guloso_nao_sao_mesma_coisa(self):
        with self.assertRaisesRegex(ErroGrafo, "conectado"):
            executar("nearest_neighbor", exemplo([1, 2, 3], [(1, 2, 1)]), 1)
        # Há ciclo 1-3-2-4-1, mas 1-2-3 trava sem 3-4.
        g = exemplo(range(1, 5), [(1, 2, 1), (2, 3, 1), (1, 3, 2), (2, 4, 2), (4, 1, 2)])
        r = executar("nearest_neighbor", g, 1, variante=ORIGINAL)
        self.assertEqual(r.termino, "construcao_bloqueada")
        self.assertFalse(r.otimo)
        self.assertTrue(executar("forca", g, 1).ordem)
        self.assertTrue(executar("nearest_neighbor", g, 1).ordem)

    def test_compara_apenas_mesmo_modelo(self):
        g = exemplo([1, 2, 3], [(1, 2, 1), (2, 3, 1), (1, 3, 10)])
        for variante in (ORIGINAL, FECHO):
            r = executar("nearest_neighbor", g, 1, variante=variante)
            exato = executar("forca", g, 1, variante=variante)
            self.assertGreaterEqual(r.custo, exato.custo)
