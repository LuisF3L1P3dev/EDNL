"""O layout pode mudar; o cadastro matemático e seus resultados permanecem."""
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import unittest

from geometria3d import (ArestaVisual, ConstrucaoVisual, MapaVisual,
                        criar_mapa_visual, posicoes_mundo, ruas_mundo)
from solvers import executar
from tsp_core import Aresta, carregar_cenarios, carregar_mapa


ROOT = Path(__file__).resolve().parents[1]


class LayoutVisualTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grafos = carregar_cenarios(ROOT / 'data')

    def test_cadastro_referenciado_sem_copiar_nos_arestas_ou_pesos(self):
        for g in self.grafos:
            with self.subTest(mapa=g.id):
                visual = criar_mapa_visual(g)
                self.assertIs(visual.grafo, g)
                self.assertEqual(len(visual.nos), len(g.nos))
                self.assertEqual(len(visual.arestas), len(g.arestas))
                for nv, original in zip(visual.nos, g.nos):
                    self.assertIs(nv.no, original)
                    self.assertEqual(nv.id, original.id)
                    self.assertEqual(nv.posicao_logica, (original.x, original.y))
                    self.assertEqual(set(nv.conexoes), set(g.adjacencia()[nv.id]))
                    self.assertTrue(nv.construcao.kit)
                    self.assertTrue(nv.construcao.nome)
                for av, original in zip(visual.arestas, g.arestas):
                    self.assertIs(av.aresta, original)
                    self.assertEqual((av.origem, av.destino, av.peso),
                                     (original.origem, original.destino, original.peso))
                    self.assertEqual(av.caminho[0], visual.posicoes[av.origem])
                    self.assertEqual(av.caminho[-1], visual.posicoes[av.destino])
                    self.assertEqual(visual.ruas[av.destino, av.origem], tuple(reversed(av.caminho)))

    def test_reorganizar_visualmente_preserva_algoritmos_e_adjacencia(self):
        for g in self.grafos:
            visual = criar_mapa_visual(g)
            adj = g.adjacencia()
            posicoes = {no: (p[0] + no * 3, -p[1], p[2] + .5)
                        for no, p in visual.posicoes.items()}
            antes = executar('forca' if len(g.ids) == 5 else 'heuristica', g, 1)
            outro = criar_mapa_visual(g, posicoes=posicoes)
            depois = executar('forca' if len(g.ids) == 5 else 'heuristica', outro.grafo, 1)
            self.assertNotEqual(visual.posicoes, outro.posicoes)
            self.assertNotEqual(visual.ruas, outro.ruas)
            self.assertEqual(g.adjacencia(), adj)
            self.assertEqual((antes.caminho, antes.custo), (depois.caminho, depois.custo))
            self.assertEqual(executar('dijkstra', g, 1, g.ids[-1]).custo,
                             executar('dijkstra', outro.grafo, 1, g.ids[-1]).custo)
            self.assertIs(outro.grafo, g)

    def test_cache_e_totalmente_imutavel_e_helpers_sao_copias(self):
        for g in self.grafos:
            visual = criar_mapa_visual(g)
            self.assertIs(visual, criar_mapa_visual(g))
            self.assertIs(visual, criar_mapa_visual(g, posicoes=dict(visual.posicoes)))
            with self.assertRaises(FrozenInstanceError):
                visual.nos[0].posicao_3d = (0, 0, 0)
            with self.assertRaises(FrozenInstanceError):
                visual.nos[0].construcao.nome = 'outro'
            with self.assertRaises(TypeError):
                visual.posicoes[1] = (0, 0, 0)
            with self.assertRaises(TypeError):
                visual.ruas[1, 2] = ()
            posicoes, ruas = posicoes_mundo(g), ruas_mundo(g)
            posicoes.clear()
            ruas.clear()
            self.assertEqual(len(visual.posicoes), len(g.ids))
            self.assertEqual(len(visual.ruas), len(g.arestas) * 2)

    def test_cache_preserva_identidade_de_grafos_iguais_recarregados(self):
        g = self.grafos[0]
        recarregado = carregar_mapa(ROOT / 'data' / 'mapa_05.json')
        self.assertEqual(g, recarregado)
        a, b = criar_mapa_visual(g), criar_mapa_visual(recarregado)
        self.assertIsNot(a, b)
        self.assertIs(b.grafo, recarregado)
        self.assertIs(b.arestas[0].aresta, recarregado.arestas[0])

    def test_apresentacao_legada_e_preservada_nesta_etapa(self):
        for g in self.grafos:
            visual = criar_mapa_visual(g)
            self.assertEqual(visual.posicoes,
                             {n.id: ((n.x - .5) * 46, (.5 - n.y) * 38, .12) for n in g.nos})
            for i, av in enumerate(visual.arestas):
                self.assertEqual(len(av.caminho), 4)
                self.assertEqual(av.caminho[1][2], .24 + i * .025)
                self.assertEqual(av.caminho[2][2], .24 + i * .025)

    def test_limites_incluem_lotes_e_desvios_distantes(self):
        g = self.grafos[0]
        endereco = ConstrucaoVisual((80, -60, 0), 'suburbio', 'building-type-a', 4)
        visual = criar_mapa_visual(g, construcoes={1: endereco})
        e = visual.arestas[0]
        desvio = ArestaVisual(e.aresta, (e.caminho[0], (100, 75, 3), e.caminho[-1]))
        outro = MapaVisual(g, visual.nos, (desvio,) + visual.arestas[1:])
        x0, y0, x1, y1 = outro.limites_xy
        self.assertLessEqual(y0, endereco.limites_xy[1])
        self.assertGreaterEqual(x1, 100.55)
        self.assertGreaterEqual(y1, 75.55)
        self.assertLess(x0, min(p[0] for p in visual.posicoes.values()))

    def test_cadastro_incompleto_copiado_ou_falso_e_rejeitado(self):
        g = self.grafos[0]
        visual = criar_mapa_visual(g)
        with self.assertRaises(ValueError):
            MapaVisual(g, visual.nos[:-1], visual.arestas)
        with self.assertRaises(ValueError):
            MapaVisual(g, visual.nos, visual.arestas[:-1])
        e = visual.arestas[0]
        copia = ArestaVisual(Aresta(e.origem, e.destino, e.peso), e.caminho)
        with self.assertRaises(ValueError):
            MapaVisual(g, visual.nos, (copia,) + visual.arestas[1:])
        falso = replace(visual.nos[0], conexoes=())
        with self.assertRaises(ValueError):
            MapaVisual(g, (falso,) + visual.nos[1:], visual.arestas)
        with self.assertRaises(ValueError):
            replace(visual.nos[0], construcao={})

    def test_layout_invalido_nao_contamina_cache(self):
        g = self.grafos[0]
        visual = criar_mapa_visual(g)
        with self.assertRaises(ValueError):
            criar_mapa_visual(g, posicoes={1: (0, 0, 0)})
        posicoes = dict(visual.posicoes)
        posicoes[1] = (float('nan'), 0, 0)
        with self.assertRaises(ValueError):
            criar_mapa_visual(g, posicoes=posicoes)
        with self.assertRaises(ValueError):
            criar_mapa_visual(g, construcoes={99: visual.nos[0].construcao})
        self.assertIs(visual, criar_mapa_visual(g))


if __name__ == '__main__':
    unittest.main()
