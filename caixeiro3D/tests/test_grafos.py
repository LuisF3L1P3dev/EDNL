import math
from pathlib import Path
import unittest

from tsp_core import Aresta, Grafo, No, carregar_mapa

ROOT = Path(__file__).resolve().parents[1]
EDGES_5 = {(1, 2, 2), (1, 4, 3), (1, 5, 6), (2, 3, 4),
           (2, 4, 3), (3, 4, 7), (3, 5, 3), (4, 5, 3)}
# Oráculo independente da leitura JSON: transcrição visual + correções do usuário.
EDGES_18 = {
    (1,2,20),(1,3,37),(1,8,29),(1,12,29),(2,3,25),(2,8,28),(2,12,39),
    (3,4,25),(3,8,30),(3,13,54),(4,5,39),(4,6,32),(4,7,42),(4,9,23),
    (4,10,33),(4,14,56),(5,6,12),(5,7,26),(5,10,19),(6,7,17),(6,10,35),
    (6,11,30),(7,11,38),(8,12,25),(8,13,22),(9,10,1),(9,13,34),(9,14,1),
    (9,16,43),(10,11,24),(10,14,1),(10,15,19),(11,15,26),(11,18,36),
    (12,13,1),(12,16,43),(13,14,1),(13,16,19),(14,15,20),(14,16,19),
    (14,17,17),(15,17,18),(15,18,21),(16,17,26),(17,18,15),
}


class GrafosTests(unittest.TestCase):
    def test_dados_exatos_e_adjacencia_simetrica(self):
        for n, expected in ((5, EDGES_5), (18, EDGES_18)):
            g = carregar_mapa(ROOT / 'data' / f'mapa_{n:02}.json')
            self.assertEqual(g.ids, tuple(range(1, n + 1)))
            self.assertEqual({(a.origem,a.destino,a.peso) for a in g.arestas}, expected)
            self.assertFalse(g.pendencias)
            adj = g.adjacencia()
            for a, b, w in expected:
                self.assertEqual(adj[a][b], w)
                self.assertEqual(adj[b][a], w)
            vistos, fila = {1}, [1]
            while fila:
                for b in adj[fila.pop()]:
                    if b not in vistos:
                        vistos.add(b)
                        fila.append(b)
            self.assertEqual(vistos, set(g.ids))

    def test_correcoes_usuario_e_custo(self):
        g = carregar_mapa(ROOT / 'data/mapa_18.json')
        self.assertEqual(g.adjacencia()[9][14], 1)
        self.assertEqual(g.adjacencia()[9][13], 34)
        self.assertEqual(g.adjacencia()[1][3], 37)
        self.assertNotIn(13, g.adjacencia()[1])
        self.assertEqual(g.custo((9, 14, 13, 12)), 3)
        self.assertEqual(g.custo((9, 14, 9)), 2)
        with self.assertRaises(ValueError):
            g.custo((1, 13))

    def test_rejeita_dados_invalidos(self):
        nos = (No(1, .2, .3), No(2, .7, .8))
        for arestas in ((Aresta(1, 1, 1),), (Aresta(1, 3, 2),),
                        (Aresta(1, 2, 0),), (Aresta(1, 2, math.inf),),
                        (Aresta(1, 2, 1), Aresta(2, 1, 2))):
            with self.assertRaises(ValueError):
                Grafo('teste', 'Inválido', nos, arestas)


if __name__ == '__main__':
    unittest.main()
