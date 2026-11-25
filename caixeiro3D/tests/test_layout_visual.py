"""O layout pode mudar; o cadastro matemático e seus resultados permanecem."""
from dataclasses import FrozenInstanceError, replace
from itertools import combinations
from math import atan2, cos, dist, hypot, radians, sin
from pathlib import Path
import unittest

from geometria3d import (ArestaVisual, ConstrucaoVisual, MapaVisual,
                        criar_mapa_visual, fracao_com_rotatoria, medir_rua,
                        posicoes_mundo, ruas_mundo)
from roteamento3d import ALTURA_RUA, MEIO_TABULEIRO, RAIO_PRACA, RAMPA, VAO_LIVRE, posicoes_planejadas
from rotatorias3d import MEIA_VIA
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
                    self.assertEqual(nv.posicao_3d, nv.ancora_rua)
                    self.assertEqual(nv.posicao_marcador, nv.ancora_rua)
                    self.assertEqual(nv.acesso, (nv.ancora_rua, nv.entrada))
                    self.assertGreaterEqual(dist(nv.entrada[:2], nv.construcao.posicao[:2]),
                                            nv.construcao.metade_lote - 1e-7)
                    self.assertLess(dist(nv.entrada[:2], nv.porta[:2]), nv.construcao.metade_lote)
                    self.assertTrue(nv.construcao.kit)
                    self.assertTrue(nv.construcao.nome)
                for av, original in zip(visual.arestas, g.arestas):
                    self.assertIs(av.aresta, original)
                    self.assertEqual((av.origem, av.destino, av.peso),
                                     (original.origem, original.destino, original.peso))
                    self.assertEqual(av.caminho[0], visual.posicoes[av.origem])
                    self.assertEqual(av.caminho[-1], visual.posicoes[av.destino])
                    self.assertEqual(visual.ruas[av.destino, av.origem], tuple(reversed(av.caminho)))

    def test_fachadas_e_portas_apontam_para_as_ancoras(self):
        for grafo in self.grafos:
            for no in criar_mapa_visual(grafo).nos:
                lote = no.construcao
                a = radians(lote.rotacao)
                frente = (-sin(a), cos(a))
                para_ancora = (no.ancora_rua[0] - lote.posicao[0],
                                no.ancora_rua[1] - lote.posicao[1])
                self.assertGreater(sum(x*y for x, y in zip(frente, para_ancora)), 0)
                entrada_porta = (no.entrada[0] - no.porta[0], no.entrada[1] - no.porta[1])
                self.assertAlmostEqual(entrada_porta[0]*frente[1] - entrada_porta[1]*frente[0], 0., places=6)
                self.assertGreater(sum(x*y for x, y in zip(frente, entrada_porta)), 0)

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

    def test_mover_no_atualiza_acesso_marcador_e_extremos_das_ruas(self):
        for g in self.grafos:
            with self.subTest(mapa=g.id):
                original = criar_mapa_visual(g)
                antes = original.nos[0]
                posicoes = dict(original.posicoes)
                x, y, z = posicoes[antes.id]
                posicoes[antes.id] = (x - 2., y, z + 1.)
                outro = criar_mapa_visual(g, posicoes=posicoes)
                no = outro.nos[0]
                self.assertEqual(no.posicao_marcador, posicoes[no.id])
                self.assertEqual(no.acesso, (no.posicao_marcador, no.entrada))
                for atual, anterior in ((no.entrada, antes.entrada),
                                        (no.construcao.posicao, antes.construcao.posicao)):
                    self.assertAlmostEqual(dist(atual, (anterior[0] - 2., anterior[1], anterior[2] + 1.)), 0.)
                for vizinho in no.conexoes:
                    self.assertEqual(outro.ruas[no.id, vizinho][0], no.ancora_rua)
                    self.assertEqual(outro.ruas[vizinho, no.id][-1], no.ancora_rua)

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

    def test_malha_planejada_e_ortogonal_na_task04(self):
        for g in self.grafos:
            visual = criar_mapa_visual(g)
            self.assertEqual(visual.posicoes, posicoes_planejadas(g))
            self.assertEqual(len(visual.arestas), len(g.arestas))
            for av in visual.arestas:
                self.assertIs(av.aresta, next(e for e in g.arestas if e is av.aresta))
                for a, b in zip(av.caminho, av.caminho[1:]):
                    # Toda rua segue uma direção cardinal no plano: a altura
                    # pode variar somente na rampa de uma ponte.
                    self.assertTrue(abs(a[0] - b[0]) < 1e-8 or abs(a[1] - b[1]) < 1e-8)
                    self.assertGreaterEqual(min(a[2], b[2]), ALTURA_RUA - 1e-8)
                for no, posicao in visual.posicoes.items():
                    if no not in (av.origem, av.destino):
                        self.assertNotIn(posicao, av.caminho)
            if len(g.ids) == 5:
                self.assertFalse(visual.pontes)
                self.assertFalse(any(p[2] > ALTURA_RUA + .01
                                     for av in visual.arestas for p in av.caminho))
            else:
                self.assertTrue(visual.pontes)
                pares = {tuple(sorted((e.origem, e.destino))) for e in g.arestas}
                for ponte in visual.pontes:
                    self.assertIn(tuple(sorted(ponte.aresta)), pares)
                    self.assertIn(tuple(sorted(ponte.inferior)), pares)
                    self.assertNotEqual(ponte.aresta, ponte.inferior)
                    self.assertGreaterEqual(ponte.altura, VAO_LIVRE)
                    self.assertGreaterEqual(ponte.centro[2] - ALTURA_RUA, VAO_LIVRE)
                    for extremo in (ponte.inicio, ponte.fim):
                        distancia = ((extremo[0] - ponte.centro[0]) ** 2 +
                                     (extremo[1] - ponte.centro[1]) ** 2) ** .5
                        self.assertGreaterEqual(distancia + 1e-8, RAMPA + MEIO_TABULEIRO)
                self.assertTrue(any(p[2] > ALTURA_RUA + .8
                                    for av in visual.arestas for p in av.caminho))

    @staticmethod
    def _altura_no_cruzamento(pontos, x, y):
        """Altura da polilinha na projeção XY de uma passagem elevada."""
        alturas = []
        for a, b in zip(pontos, pontos[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            if abs(dx) > 1e-8:
                t = (x - a[0]) / dx
            elif abs(dy) > 1e-8:
                t = (y - a[1]) / dy
            else:
                continue
            if ( -1e-8 <= t <= 1 + 1e-8 and
                    abs(a[0] + t * dx - x) < 1e-7 and
                    abs(a[1] + t * dy - y) < 1e-7):
                alturas.append(a[2] + t * (b[2] - a[2]))
        if not alturas:
            self.fail("A ponte não está sobre a rua declarada.")
        return tuple(alturas)

    def test_pontes_deixam_vao_em_cruzamentos_reais(self):
        grande = next(g for g in self.grafos if len(g.ids) == 18)
        visual = criar_mapa_visual(grande)
        # Cada item descreve um cruzamento não incidente, nunca uma junção
        # lógica adicionada pelo desenho. O total pode variar ao reservar os
        # lotes persistentes de construções.
        self.assertGreater(len(visual.pontes), 0)
        for ponte in visual.pontes:
            x, y, _ = ponte.centro
            altas = self._altura_no_cruzamento(visual.ruas[ponte.aresta], x, y)
            baixas = self._altura_no_cruzamento(visual.ruas[ponte.inferior], x, y)
            self.assertGreaterEqual(min(altas) - max(baixas) + 1e-8, VAO_LIVRE)
            self.assertNotEqual(ponte.aresta, ponte.inferior)

    def test_cidade_compacta_tem_apenas_cruzamentos_elevados_fora_das_pracas(self):
        grande = next(g for g in self.grafos if len(g.ids) == 18)
        visual = criar_mapa_visual(grande)
        x0, y0, x1, y1 = visual.limites_xy
        self.assertLessEqual(x1 - x0, 94.)
        self.assertLessEqual(y1 - y0, 66.)
        pontes = {(frozenset((p.aresta, p.inferior)), p.centro[:2]) for p in visual.pontes}
        encontrados = set()
        for e, f in combinations(visual.arestas, 2):
            par_e, par_f = (e.origem, e.destino), (f.origem, f.destino)
            pracas = [visual.posicoes[n] for n in set(par_e) & set(par_f)]
            for a, b in zip(e.caminho, e.caminho[1:]):
                for c, d in zip(f.caminho, f.caminho[1:]):
                    if (a[0] == b[0]) == (c[0] == d[0]):
                        continue
                    (h0, h1), (v0, v1) = ((c, d), (a, b)) if a[0] == b[0] else ((a, b), (c, d))
                    x, y = v0[0], h0[1]
                    if (abs(x - h0[0]) + abs(x - h1[0]) > abs(h0[0] - h1[0]) + 1e-8 or
                            abs(y - v0[1]) + abs(y - v1[1]) > abs(v0[1] - v1[1]) + 1e-8):
                        continue
                    if any(max(abs(x - px), abs(y - py)) <= RAIO_PRACA for px, py, _ in pracas):
                        continue
                    encontrados.add((frozenset((par_e, par_f)), (x, y)))
        self.assertEqual(encontrados, pontes)

    def test_trafego_das_rotatorias_preserva_acessos_e_desacelera_no_anel(self):
        for grafo in self.grafos:
            mapa = criar_mapa_visual(grafo)
            adjacencia = grafo.adjacencia()
            self.assertEqual({r.no for r in mapa.rotatorias},
                             {no for no, vizinhos in adjacencia.items() if len(vizinhos) >= 3})
            self.assertEqual(set(mapa.trajetos), set(mapa.ruas))
            for a, b in combinations(mapa.rotatorias, 2):
                self.assertGreater(dist(a.centro, b.centro), a.raio_externo + b.raio_externo)
            for rotatoria in mapa.rotatorias:
                no = rotatoria.no
                self.assertEqual({b.vizinho for b in rotatoria.bracos}, set(adjacencia[no]))
                x, y, z = rotatoria.centro
                perfis = tuple(rotatoria.perfis_pavimento())
                for braco in rotatoria.bracos:
                    for lateral in (-MEIA_VIA, MEIA_VIA):
                        canto = braco.deslocar(0., lateral)
                        self.assertTrue(any(dist(canto, p) < 1e-8 for _, p in perfis), (no, braco))
                    for entrando in (False, True):
                        par = (braco.vizinho, no) if entrando else (no, braco.vizinho)
                        rua = medir_rua(mapa.trajetos[par])
                        self.assertEqual(rua.pontos[0], mapa.chegadas[par[0]])
                        self.assertEqual(rua.pontos[-1], mapa.chegadas[par[1]])
                        inicio, fim = zonas = mapa.zonas_rotatorias[par]
                        curva = rua.segmentos[-fim:] if entrando else rua.segmentos[:inicio]
                        for a, b in curva:
                            px, py, pz = tuple((u + v) / 2 for u, v in zip(a, b))
                            dx, dy = px - x, py - y
                            raio = hypot(dx, dy)
                            self.assertAlmostEqual(pz, z)
                            self.assertGreater(raio, rotatoria.raio_interno)
                            self.assertLessEqual(raio, rotatoria.limite_externo(atan2(dy, dx)) + 1e-8)
                            # Envelope dos centros das rodas da van na escala
                            # do jogo, incluindo o eixo que já alcançou a reta.
                            vx, vy = b[0] - a[0], b[1] - a[1]
                            comprimento = hypot(vx, vy)
                            c, s = cos(braco.angulo), sin(braco.angulo)
                            for eixo in (-.54, .54):
                                for roda in (-.30, .30):
                                    px = dx + (eixo * vx - roda * vy) / comprimento
                                    py = dy + (eixo * vy + roda * vx) / comprimento
                                    raio = hypot(px, py)
                                    longitudinal = px*c + py*s
                                    lateral = -px*s + py*c - braco.lateral
                                    reta = longitudinal >= braco.estacao and abs(lateral) <= MEIA_VIA
                                    self.assertGreater(raio, rotatoria.raio_interno)
                                    self.assertTrue(reta or raio <= rotatoria.limite_externo(atan2(py, px)) + .005,
                                                    (par, px, py))
                        valores = [fracao_com_rotatoria(rua.pontos, zonas, i / 100) for i in range(101)]
                        self.assertEqual((valores[0], valores[-1]), (0., 1.))
                        passos = [b - a for a, b in zip(valores, valores[1:])]
                        self.assertGreater(min(passos), 0.)
                        self.assertGreater(max(passos), 1.5 * min(passos))

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
