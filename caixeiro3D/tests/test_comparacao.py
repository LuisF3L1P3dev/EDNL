from itertools import permutations
from pathlib import Path
from threading import Event
import unittest

from comparacao import calcular_comparacao, diferenca_custos, metodos_comparaveis
from tsp_core import carregar_mapa


DATA = Path(__file__).resolve().parents[1] / 'data'


class ComparacaoTest(unittest.TestCase):
    def test_circuitos_do_bairro_usam_a_mesma_origem_e_pesos(self):
        grafo = carregar_mapa(DATA / 'mapa_05.json')
        adj = grafo.adjacencia()
        for origem in (1, 3):
            with self.subTest(origem=origem):
                resultados = calcular_comparacao(grafo, metodos_comparaveis(0, 'forca'), origem, None, Event())
                exato, heuristica = resultados.values()
                self.assertEqual(exato.custo, 15)
                if origem == 1:
                    self.assertEqual(exato.caminho, (1, 2, 3, 5, 4, 1))
                circuitos = ((origem, *ordem, origem) for ordem in permutations(set(grafo.ids) - {origem}))
                validos = sum(all(b in adj[a] for a, b in zip(rota, rota[1:])) for rota in circuitos)
                self.assertEqual(exato.circuitos_validos, validos)
                for resultado in (exato, heuristica):
                    self.assertEqual(resultado.termino, 'concluido')
                    self.assertEqual((resultado.caminho[0], resultado.caminho[-1]), (origem, origem))
                    self.assertEqual(set(resultado.ordem_visita[:-1]), set(grafo.ids))
                    self.assertEqual(grafo.custo(resultado.caminho), resultado.custo)
                    self.assertGreater(resultado.tempo_ms, 0.)
                self.assertEqual(diferenca_custos(exato.custo, heuristica.custo), (0, 0))

    def test_percentual_usa_o_custo_otimo_como_base(self):
        self.assertEqual(diferenca_custos(20, 25), (5, 25))
        self.assertEqual(diferenca_custos(20, 15), (5, -25))
        self.assertEqual(diferenca_custos(0, 3), (3, None))

    def test_regiao_compara_caminho_minimo_e_passeio(self):
        grafo = carregar_mapa(DATA / 'mapa_18.json')
        for selecionado in ('circuito', 'dijkstra', 'heuristica'):
            self.assertEqual(metodos_comparaveis(1, selecionado), ('dijkstra', 'heuristica'))
        self.assertEqual(metodos_comparaveis(0, 'dijkstra'), ())
        resultados = calcular_comparacao(grafo, metodos_comparaveis(1, 'circuito'), 1, 18, Event())
        caminho, passeio = resultados.values()
        self.assertEqual((caminho.caminho[0], caminho.caminho[-1]), (1, 18))
        self.assertEqual((passeio.caminho[0], passeio.caminho[-1]), (1, 1))
        self.assertEqual(set(passeio.ordem_visita), set(grafo.ids))
        self.assertIn('sem garantia', passeio.garantia)
        for resultado in resultados.values():
            self.assertEqual(grafo.custo(resultado.caminho), resultado.custo)
