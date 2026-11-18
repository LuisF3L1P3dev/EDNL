"""Verificação sem janela da cena real, texturas e separação da topologia."""

from itertools import combinations
from math import dist
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from panda3d.core import Camera, NodePath, Vec3

from assets3d import Biblioteca
from camera3d import CameraIsometrica
from geometria3d import criar_mapa_visual, posicoes_mundo, ruas_mundo
from render3d import (Cena3D, LARGURA_RUA, _distancia_segmento, _faixa,
                      _pavimento, _projetar_no_segmento)
from solvers import executar
from tsp_core import carregar_mapa


ROOT = Path(__file__).resolve().parents[1]


class _RegiaoCamera:
    def setDimensions(self, *args):
        self.dimensoes = args


class _CameraPanda:
    def __init__(self, no):
        self.no = no
        self.regiao = _RegiaoCamera()

    def node(self):
        return self

    def setLens(self, lente):
        self.no.node().setLens(lente)

    def getDisplayRegion(self, indice):
        return self.regiao

    def getRelativePoint(self, *args):
        return self.no.getRelativePoint(*args)


def base_camera():
    render = NodePath('render-camera')
    camera = render.attachNewNode('camera')
    cam = _CameraPanda(camera.attachNewNode(Camera('cam')))
    return SimpleNamespace(render=render, camera=camera, cam=cam,
                           win=SimpleNamespace(getXSize=lambda: 1440,
                                               getYSize=lambda: 960))


class TestRender3D(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.biblioteca = Biblioteca()
        cls.grafos = [carregar_mapa(ROOT / "data" / f"mapa_{n:02}.json") for n in (5, 18)]

    def construir(self, grafo):
        base = SimpleNamespace(render=NodePath("render-teste"))
        cena = Cena3D(base, grafo, self.biblioteca)
        self.addCleanup(cena.destruir)
        return base, cena

    def test_topologia_exata_em_ambos_os_grafos(self):
        for grafo in self.grafos:
            with self.subTest(grafo=grafo.id):
                _, cena = self.construir(grafo)
                self.assertEqual(cena.posicoes, posicoes_mundo(grafo))
                self.assertEqual(cena.ruas, ruas_mundo(grafo))
                self.assertEqual(len(cena.ruas), 2 * len(grafo.arestas))
                self.assertGreater(cena.trechos_rua, len(grafo.arestas))
                for aresta in grafo.arestas:
                    a, b = aresta.origem, aresta.destino
                    self.assertEqual(cena.ruas[a, b], tuple(reversed(cena.ruas[b, a])))
                    self.assertEqual(cena.ruas[a, b][0], cena.posicoes[a])
                    self.assertEqual(cena.ruas[a, b][-1], cena.posicoes[b])

    def test_malhas_reais_e_texturas_preservadas(self):
        for grafo in self.grafos:
            with self.subTest(grafo=grafo.id):
                _, cena = self.construir(grafo)
                malhas = cena.raiz.findAllMatches("**/+GeomNode")
                self.assertGreater(malhas.getNumPaths(), 0)
                vertices = sum(no.node().getGeom(i).getVertexData().getNumRows()
                               for no in malhas for i in range(no.node().getNumGeoms()))
                self.assertGreater(vertices, 10000)
                texturas = cena.raiz.findAllTextures()
                self.assertGreaterEqual(texturas.getNumTextures(), 3)
                for textura in texturas:
                    self.assertGreater(textura.getXSize(), 0)
                    self.assertGreater(textura.getYSize(), 0)
                self.assertIn(("rua", "road-straight"), cena.modelos_usados)
                self.assertIn(("rua", "road-crossroad"), cena.modelos_usados)
                self.assertTrue(any(kit == "cidade" for kit, _ in cena.modelos_usados))
                self.assertTrue(any(kit == "suburbio" for kit, _ in cena.modelos_usados))
                if len(grafo.ids) == 5:
                    self.assertEqual(cena.pontes, 0)
                else:
                    self.assertGreater(cena.pontes, 0)
                    self.assertIn(("rua", "bridge-pillar-wide"), cena.modelos_usados)
                    self.assertTrue(cena._pistas_pontes)

    def test_pistas_e_agua_preservam_eixos_e_ruas_inferiores(self):
        _, cena = self.construir(self.grafos[1])
        trechos, _ = _pavimento(cena._segmentos, cena.posicoes.values())
        esperados = {(a, b) for a, b in trechos if a[2] != b[2] or a[2] > .8}
        self.assertEqual(set(cena._pistas_pontes), esperados)
        self.assertEqual(len(cena._agua), 1)
        x0, y0, x1, y1 = cena._agua[0]
        for i in range(7):
            for j in range(13):
                x, y = x0 + (x1-x0)*i/6, y0 + (y1-y0)*j/12
                for a, b in cena._segmentos:
                    if max(a[2], b[2]) < .5:
                        self.assertGreaterEqual(_distancia_segmento(x, y, a, b), LARGURA_RUA/2 + .1)
        self.assertFalse(cena._livre((x0+x1)/2, (y0+y1)/2, .01))

    def test_pista_de_rampa_respeita_extremos_largura_e_normal(self):
        cena = SimpleNamespace(raiz=NodePath('teste'), _pistas_pontes=[], trechos_rua=0)
        superficies = []
        def registrar(parent, nome, pontos, cor, **kw):
            superficies.append((nome, pontos))
        a, b = (0., 0., .12), (3.6, 0., 1.77)
        with patch('render3d.superficie', side_effect=registrar):
            Cena3D._pista_ponte(cena, a, b, None)
        faixas = [p for nome, p in superficies if nome == 'pista-ponte']
        self.assertEqual(len(faixas), 5)
        vertices = [p for faixa in faixas for p in faixa]
        self.assertAlmostEqual(max(p[1] for p in vertices) - min(p[1] for p in vertices), LARGURA_RUA)
        self.assertEqual({(p[0], p[2]) for p in vertices}, {(a[0], a[2]), (b[0], b[2])})
        for pontos in faixas:
            normal = (Vec3(*pontos[1]) - Vec3(*pontos[0])).cross(Vec3(*pontos[2]) - Vec3(*pontos[0]))
            self.assertGreater(normal.z, 0)
        self.assertEqual(cena._pistas_pontes, [(a, b)])

    def test_pavimento_cobre_as_polilinhas_sem_pisos_coplanares_sobrepostos(self):
        meia = LARGURA_RUA / 2
        for grafo in self.grafos:
            with self.subTest(grafo=grafo.id):
                mapa = criar_mapa_visual(grafo)
                segmentos = tuple((a, b) for e in mapa.arestas for a, b in zip(e.caminho, e.caminho[1:]))
                trechos, juncoes = _pavimento(segmentos, mapa.posicoes.values())
                self.assertTrue(set(mapa.posicoes.values()) <= {p for p, _, _ in juncoes})
                pisos = [(p[2], caixa) for p, _, caixa in juncoes]
                for a, b in trechos:
                    if a[2] != b[2]:
                        continue
                    x, y = meia if a[0] == b[0] else 0., meia if a[1] == b[1] else 0.
                    pisos.append((a[2], (min(a[0], b[0]) - x, min(a[1], b[1]) - y,
                                         max(a[0], b[0]) + x, max(a[1], b[1]) + y)))
                for (z1, (a, b, c, d)), (z2, (e, f, g, h)) in combinations(pisos, 2):
                    if z1 == z2:
                        self.assertFalse(min(c, g) - max(a, e) > 1e-7 and min(d, h) - max(b, f) > 1e-7)
                for a, b in segmentos:
                    for t in (0., .025, .5, .975, 1.):
                        p = tuple(x + t * (y - x) for x, y in zip(a, b))
                        coberto = any(dist(p, _projetar_no_segmento(*p[:2], *trecho)) < 1e-7
                                      for trecho in trechos)
                        coberto |= any(abs(p[2] - z) < 1e-7 and
                                       x0 - 1e-7 <= p[0] <= x1 + 1e-7 and y0 - 1e-7 <= p[1] <= y1 + 1e-7
                                       for z, (x0, y0, x1, y1) in pisos)
                        self.assertTrue(coberto, p)

    def test_apoios_ficam_fora_das_faixas_das_outras_ruas(self):
        _, cena = self.construir(self.grafos[1])
        self.assertEqual(cena.pontes, len(cena.mapa_visual.pontes))
        self.assertTrue(cena._apoios_pontes)
        for aresta, x, y, raio in cena._apoios_pontes:
            for outra in cena.mapa_visual.arestas:
                if (outra.origem, outra.destino) != aresta:
                    for a, b in zip(outra.caminho, outra.caminho[1:]):
                        self.assertGreaterEqual(_distancia_segmento(x, y, a, b) + 1e-7, LARGURA_RUA / 2 + raio)

    def test_decoracoes_nao_invadem_ruas_nem_nos(self):
        for grafo in self.grafos:
            with self.subTest(grafo=grafo.id):
                _, cena = self.construir(grafo)
                edificios = [d for d in cena.decoracoes if d.tipo == "edificio"]
                arvores = [d for d in cena.decoracoes if d.tipo == "arvore"]
                self.assertGreaterEqual(len(edificios), 20)
                self.assertGreaterEqual(len(arvores), 60)
                for d in cena.decoracoes:
                    self.assertGreaterEqual(cena.distancia_rua(d.x, d.y) + 1e-9,
                                            d.raio + LARGURA_RUA / 2 + .4)
                    for x, y, _ in cena.posicoes.values():
                        self.assertGreater((d.x - x) ** 2 + (d.y - y) ** 2, (d.raio + 1.2) ** 2)

    def test_cada_no_tem_construcao_fixa_e_acesso_da_ancora_da_rua(self):
        for grafo in self.grafos:
            with self.subTest(grafo=grafo.id):
                acessos = {}

                def desenhar_faixa(parent, nome, a, b, *args, **kwargs):
                    malha = _faixa(parent, nome, a, b, *args, **kwargs)
                    if nome.startswith("acesso-no-"):
                        self.assertFalse(malha.isEmpty())
                        acessos[nome] = (a, b)
                    return malha

                with patch("render3d._faixa", side_effect=desenhar_faixa):
                    _, cena = self.construir(grafo)
                self.assertEqual(set(cena.construcoes_no), set(grafo.ids))
                self.assertEqual(set(cena.marcadores_no), set(grafo.ids))
                for no_visual in cena.mapa_visual.nos:
                    endereco = no_visual.construcao
                    edificio = cena.construcoes_no[no_visual.id]
                    self.assertEqual(edificio.no, no_visual.id)
                    self.assertEqual((edificio.kit, edificio.modelo),
                                     (endereco.kit, endereco.nome))
                    self.assertEqual((edificio.x, edificio.y), endereco.posicao[:2])
                    self.assertEqual(cena.marcadores_no[no_visual.id], no_visual.ancora_rua)
                    self.assertEqual(acessos[f"acesso-no-{no_visual.id}"], no_visual.acesso)
                    metade = endereco.tamanho / 2 + endereco.margem_lote
                    # O círculo que contém o lote não alcança o eixo de uma via.
                    self.assertGreaterEqual(cena.distancia_rua(edificio.x, edificio.y),
                                            (2 * metade ** 2) ** .5 + LARGURA_RUA / 2)

    def test_camera_enquadra_ilha_ruas_predios_e_ancoras_em_ambos_os_mapas(self):
        for grafo in self.grafos:
            with self.subTest(grafo=grafo.id):
                _, cena = self.construir(grafo)
                pontos = cena.pontos_enquadramento()
                self.assertGreater(len(pontos), len(cena.posicoes))
                self.assertTrue(set(cena.marcadores_no.values()).issubset(pontos))
                camera = CameraIsometrica(base_camera(), pontos)

                def assert_tudo_visivel():
                    for ponto in pontos:
                        projetado = camera.projetar(ponto)
                        self.assertIsNotNone(projetado, ponto)
                        self.assertTrue(camera.viewport.inflate(-2, -2).collidepoint(projetado),
                                        (ponto, projetado))

                camera.ajustar((1100, 760))
                assert_tudo_visivel()
                marcadores = [camera.projetar(p) for p in cena.marcadores_no.values()]
                separacao = min(dist(a, b) for a, b in combinations(marcadores, 2))
                self.assertGreaterEqual(separacao, 100 if len(grafo.ids) == 5 else 65)
                camera.ajustar()
                assert_tudo_visivel()
                camera.mudar_zoom(2.)
                camera.arrastar(100000, -100000)
                self.assertNotEqual(camera.pan, Vec3(0))
                camera.centralizar(pontos)
                self.assertEqual(camera.zoom, 1.)
                self.assertEqual(camera.pan, Vec3(0))
                assert_tudo_visivel()

    def test_rota_independente_da_cena_e_validada(self):
        for grafo in self.grafos:
            with self.subTest(grafo=grafo.id):
                base, cena = self.construir(grafo)
                limites = cena.raiz.getTightBounds()
                resultado = executar("heuristica", grafo, 1)
                cena.mostrar_rota(resultado.caminho)
                self.assertEqual(cena.rota.getParent(), base.render)
                self.assertEqual(cena.raiz.getParent(), base.render)
                self.assertNotEqual(cena.raiz, cena.rota)
                self.assertGreater(cena.rota.getNumChildren(), 0)
                self.assertEqual(cena.raiz.getTightBounds(), limites)
                self.assertTrue(cena.raiz.find("**/veículo").isEmpty())
                filhos = cena.rota.getNumChildren()
                with self.assertRaisesRegex(ValueError, "rua"):
                    cena.mostrar_rota((1, 1))
                self.assertEqual(cena.rota.getNumChildren(), filhos)
                cena.limpar_rota()
                self.assertEqual(cena.rota.getNumChildren(), 0)

    def test_cache_reutilizado_ao_reconstruir_e_trocar_mapa(self):
        _, cena = self.construir(self.grafos[0])
        rua = self.biblioteca.modelo("rua", "road-straight")
        limites_originais = rua.getTightBounds()
        textura = rua.findAllTextures()[0]
        quantidade = len(self.biblioteca.modelos)
        cena.destruir()
        _, nova = self.construir(self.grafos[0])
        self.assertEqual(len(self.biblioteca.modelos), quantidade)
        self.assertEqual(self.biblioteca.modelo("rua", "road-straight"), rua)
        self.assertEqual(rua.getTightBounds(), limites_originais)
        self.assertIn(textura, tuple(nova.raiz.findAllTextures()))
        _, outra = self.construir(self.grafos[1])
        self.assertEqual(self.biblioteca.modelo("rua", "road-straight"), rua)
        self.assertEqual(rua.getTightBounds(), limites_originais)
        outra.destruir()
        self.assertTrue(outra.raiz.isEmpty())
        self.assertTrue(outra.rota.isEmpty())

    def test_cores_da_rota_nao_dependem_de_iluminacao(self):
        _, cena = self.construir(self.grafos[0])
        cena.mostrar_rota((1, 2, 3))
        self.assertGreater(cena.rota.findAllMatches("**/+GeomNode").getNumPaths(), 0)
        # Os vértices amarelos ficam acima da rua, sem alterar a polilinha.
        self.assertGreater(cena.rota.getTightBounds()[0].z, .12)

    def test_trecho_ativo_nao_reconstroi_mesh_sem_mudar_aresta(self):
        _, cena = self.construir(self.grafos[0])
        self.assertTrue(cena.mostrar_trecho(1, 2))
        filhos = cena.rota.getNumChildren()
        self.assertFalse(cena.mostrar_trecho(1, 2))
        self.assertEqual(cena.rota.getNumChildren(), filhos)
        self.assertTrue(cena.mostrar_trecho(2, 3))
        self.assertEqual(cena._trecho_destacado, (2, 3))


if __name__ == "__main__":
    unittest.main()
