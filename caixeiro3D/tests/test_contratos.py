"""Validação independente das distâncias e dos percursos em todos os mapas."""
from math import inf
from pathlib import Path
import unittest

from solvers import executar
from tsp_core import carregar_mapa

ROOT = Path(__file__).resolve().parents[1]


class ContratosTests(unittest.TestCase):
    def test_dijkstra_concorda_com_floyd_warshall_em_349_pares(self):
        for tamanho in (5, 18):
            g = carregar_mapa(ROOT / f'data/mapa_{tamanho:02}.json')
            d = {(a, b): 0 if a == b else inf for a in g.ids for b in g.ids}
            for e in g.arestas:
                d[e.origem, e.destino] = d[e.destino, e.origem] = e.peso
            for k in g.ids:
                for a in g.ids:
                    for b in g.ids:
                        d[a, b] = min(d[a, b], d[a, k] + d[k, b])
            for a in g.ids:
                for b in g.ids:
                    with self.subTest(mapa=tamanho, origem=a, destino=b):
                        r = executar('dijkstra', g, a, b)
                        self.assertEqual(r.termino, 'concluido')
                        self.assertEqual(r.custo, d[a, b])
                        self.assertEqual(r.custo, g.custo(r.caminho))
                        self.assertEqual((r.caminho[0], r.caminho[-1]), (a, b))

    def test_heuristica_visita_todos_com_ruas_reais_para_todas_as_23_origens(self):
        for tamanho in (5, 18):
            g = carregar_mapa(ROOT / f'data/mapa_{tamanho:02}.json')
            for a in g.ids:
                with self.subTest(mapa=tamanho, origem=a):
                    r = executar('heuristica', g, a)
                    self.assertEqual(r.termino, 'concluido')
                    self.assertEqual(r.caminho[0], a)
                    self.assertEqual(r.caminho[-1], a)
                    self.assertEqual(set(r.caminho), set(g.ids))
                    self.assertEqual(r.custo, g.custo(r.caminho))
                    self.assertIn('sem garantia', r.garantia)

    def test_mapa_18_gera_circuito_real_e_recusa_forca_bruta(self):
        """Aceitação do cenário canônico grande, sem completar arestas fictícias."""
        g = carregar_mapa(ROOT / 'data/mapa_18.json')
        resultado = executar('heuristica', g, 1)
        self.assertEqual(resultado.termino, 'concluido')
        self.assertEqual(resultado.caminho[0], 1)
        self.assertEqual(resultado.caminho[-1], 1)
        self.assertEqual(set(resultado.caminho), set(g.ids))
        adjacencia = g.adjacencia()
        self.assertTrue(all(b in adjacencia[a]
                            for a, b in zip(resultado.caminho, resultado.caminho[1:])))
        self.assertEqual(resultado.custo, g.custo(resultado.caminho))
        with self.assertRaisesRegex(ValueError, '9'):
            executar('forca', g, 1)

    def test_otimo_15_independe_da_origem(self):
        g = carregar_mapa(ROOT / 'data/mapa_05.json')
        for a in g.ids:
            r = executar('forca', g, a)
            self.assertEqual(r.custo, 15)
            self.assertEqual(r.custo, g.custo(r.caminho))
            self.assertEqual(len(set(r.caminho[:-1])), 5)


if __name__ == '__main__':
    unittest.main()
