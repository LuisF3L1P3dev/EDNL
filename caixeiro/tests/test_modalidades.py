import unittest
from pathlib import Path
from tsp_core import carregar_mapa
from solvers import executar, ORIGINAL, FECHO, Orcamento
from test_tsp import exemplo

class ModalidadesTests(unittest.TestCase):
    def test_estrela_exige_revisitas(self):
        grafo = exemplo(range(1, 5), [(1, 2, 1), (1, 3, 1), (1, 4, 1)])
        for metodo in ('forca', 'dijkstra'):
            with self.subTest(metodo=metodo):
                self.assertEqual(executar(metodo, grafo, 1, destino=1, variante=ORIGINAL).termino, 'inviavel_comprovado')
                r = executar(metodo, grafo, 1, destino=1, variante=FECHO)
                self.assertEqual(r.custo, 6)
                self.assertEqual((r.caminho[0], r.caminho[-1]), (1, 1))
                self.assertEqual(set(r.caminho), set(grafo.ids))
                self.assertGreater(r.caminho.count(1), 2)

    def test_ciclo_sem_revisitas(self):
        grafo = carregar_mapa(Path(__file__).resolve().parents[1] / 'data/mapa_05.json')
        for metodo in ('forca', 'dijkstra'):
            r = executar(metodo, grafo, 1, destino=1, variante=ORIGINAL)
            self.assertEqual(r.custo, 15)
            self.assertEqual(r.caminho[0], r.caminho[-1])
            self.assertEqual(len(r.caminho[:-1]), len(set(r.caminho[:-1])))
            self.assertEqual(set(r.caminho), set(grafo.ids))

    def test_dijkstra_caminho_e_ciclo(self):
        grafo = carregar_mapa(Path(__file__).resolve().parents[1] / 'data/mapa_05.json')
        self.assertEqual(executar('dijkstra', grafo, 1, destino=3).custo, 6)
        r = executar('dijkstra', grafo, 1, destino=1)
        self.assertEqual(r.custo, 15)
        self.assertEqual(set(r.caminho), set(grafo.ids))
        self.assertEqual((r.caminho[0], r.caminho[-1]), (1, 1))

    def test_limite_ciclo(self):
        grafo = carregar_mapa(Path(__file__).resolve().parents[1] / 'data/mapa_18.json')
        self.assertEqual(executar('dijkstra', grafo, 1, destino=1, orcamento=Orcamento(max_estados=1)).termino, 'limite_estados')
