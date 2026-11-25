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
                    if not {a, b} & {r.no for r in cena.rotatorias}:
                        self.assertEqual(cena.ruas[a, b], tuple(reversed(cena.ruas[b, a])))
                    for u, v in ((a, b), (b, a)):
                        self.assertEqual(cena.ruas[u, v][0], cena.posicoes[u])
                        self.assertEqual(cena.ruas[u, v][-1], cena.posicoes[v])

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
                self.assertIn(("rua", "road-roundabout"), cena.modelos_usados)
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
                segmentos = tuple((a, b) for (u, v), eixo in mapa.eixos_pavimento.items() if u < v
                                  for a, b in zip(eixo, eixo[1:]))
                ancoras = set(mapa.posicoes.values()) - {r.centro for r in mapa.rotatorias}
                trechos, juncoes = _pavimento(segmentos, ancoras)
                self.assertTrue(ancoras <= {p for p, _, _ in juncoes})
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

    def test_edificios_ocupam_quarteiroes_com_distribuicao_deterministica(self):
        for grafo in self.grafos[:1]:
            with self.subTest(mapa=grafo.id):
                _, cena = self.construir(grafo)
                _, repetida = self.construir(grafo)
                edificios = [d for d in cena.decoracoes if d.tipo == 'edificio' and d.no is None]
                outros = [d for d in repetida.decoracoes if d.tipo == 'edificio' and d.no is None]
                self.assertEqual(edificios, outros)
                self.assertEqual(len(edificios), 52)
                self.assertGreaterEqual(len({(d.kit, d.modelo) for d in edificios}), 8)
                quadras = {cena._quadra(d.x, d.y) for d in edificios}
                self.assertGreaterEqual(len(quadras), 10)
                self.assertTrue(all(d.altura <= 2.8 + 1e-9 for d in edificios))
                for a, b in combinations(edificios, 2):
                    self.assertGreaterEqual(dist((a.x, a.y), (b.x, b.y)) + 1e-9, a.raio + b.raio)
                # A segunda fileira permite conjuntos de construções no interior.
                self.assertTrue(all(cena.distancia_rua(d.x, d.y) <= 5.51 for d in edificios))

    def test_decoracoes_nao_invadem_ruas_nem_nos(self):
        for grafo in self.grafos:
            with self.subTest(grafo=grafo.id):
                _, cena = self.construir(grafo)
                edificios = [d for d in cena.decoracoes if d.tipo == "edificio"]
                arvores = [d for d in cena.decoracoes if d.tipo == "arvore"]
                self.assertGreaterEqual(len(edificios), 20)
                self.assertGreaterEqual(len(arvores), 60)
                for d in cena.decoracoes:
                    margem = .15 if d.tipo in ('poste', 'placa') else .4
                    self.assertGreaterEqual(cena.distancia_rua(d.x, d.y) + 1e-9,
                                            d.raio + LARGURA_RUA / 2 + margem)
                    for x, y, _ in cena.posicoes.values():
                        afastamento = .85 if d.tipo == 'placa' else 1.2
                        self.assertGreater((d.x - x) ** 2 + (d.y - y) ** 2, (d.raio + afastamento) ** 2)

    def test_vegetacao_diversificada_respeita_altura_e_jardins(self):
        for grafo in self.grafos:
            with self.subTest(mapa=grafo.id):
                _, cena = self.construir(grafo)
                arvores = [d for d in cena.decoracoes if d.tipo == 'arvore']
                jardins = [d for d in cena.decoracoes if d.tipo == 'jardim']
                edificios = [d for d in cena.decoracoes if d.tipo == 'edificio']
                arvores_do_entorno = [d for d in arvores if d.no is None]
                self.assertEqual(len(arvores_do_entorno), 45 if cena.cidades else 100)
                self.assertEqual(len(jardins), 0 if cena.cidades else 12)
                self.assertEqual({d.modelo for d in arvores_do_entorno}, {'tree-small', 'tree-large'})
                self.assertTrue(all(1.04 <= d.altura <= 1.56 for d in arvores_do_entorno))
                self.assertTrue(all(any(dist((j.x, j.y), (e.x, e.y)) <= e.raio + .86
                                        for e in edificios) for j in jardins))
                self.assertGreater(cena._vegetacao_tipos['calcadas'], 0)
                self.assertGreater(cena._vegetacao_tipos['bosques'], 0)

    def test_mobiliario_urbano_e_poste_proximo_de_ponte(self):
        for grafo in self.grafos:
            with self.subTest(mapa=grafo.id):
                _, cena = self.construir(grafo)
                itens = {tipo: [d for d in cena.decoracoes if d.tipo == tipo]
                         for tipo in ('poste', 'banco', 'passeio')}
                self.assertGreaterEqual(len(itens['poste']), 20)
                self.assertEqual(tuple(len(itens[t]) for t in ('banco', 'passeio')), (6, 8))
                self.assertEqual({d.modelo for d in itens['poste']}, {'light-curved', 'light-square'})
                tipos = [tipo for tipo, _, _ in cena.sinalizacao]
                self.assertGreaterEqual(tipos.count('preferencia'), len(cena.rotatorias))
                self.assertTrue({'velocidade', 'direcao', 'curva', 'rotatoria'} <= set(tipos))
                if cena.cidades:
                    self.assertIn('cidade', tipos)
                self.assertTrue(all(abs(d.altura - 1.55) < .01 for d in itens['poste']))
                self.assertTrue(all(d.modelo == 'banco' and d.altura == .69 for d in itens['banco']))
                if cena.pontes:
                    self.assertTrue(cena._postes_ponte)
                    for centro, x, y in cena._postes_ponte:
                        self.assertLess(dist((x, y), centro[:2]), 3.1)
                        self.assertTrue(any(abs(d.x-x) < 1e-7 and abs(d.y-y) < 1e-7
                                            for d in itens['poste']))

    def test_cada_no_tem_construcao_fixa_e_acesso_da_ancora_da_rua(self):
        for grafo in self.grafos[:1]:
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
                    entrada = acessos[f"acesso-no-{no_visual.id}"]
                    self.assertEqual(entrada[1], no_visual.entrada)
                    rotatoria = next((r for r in cena.rotatorias if r.no == no_visual.id), None)
                    if rotatoria:
                        self.assertEqual(cena.marcadores_no[no_visual.id], rotatoria.chegada)
                        self.assertGreater(dist(entrada[0], rotatoria.centro), dist(rotatoria.chegada, rotatoria.centro))
                    else:
                        self.assertEqual(cena.marcadores_no[no_visual.id], no_visual.ancora_rua)
                        self.assertEqual(entrada, no_visual.acesso)
                    metade = endereco.tamanho / 2 + endereco.margem_lote
                    # O círculo que contém o lote não alcança o eixo de uma via.
                    self.assertGreaterEqual(cena.distancia_rua(edificio.x, edificio.y),
                                            (2 * metade ** 2) ** .5 + LARGURA_RUA / 2)

    def test_cidades_tem_lotes_exclusivos_e_acessos_as_suas_ruas(self):
        grafo = self.grafos[1]
        _, cena = self.construir(grafo)
        _, segunda = self.construir(grafo)
        self.assertEqual(set(cena.cidades), set(grafo.ids))
        self.assertEqual(cena.cidades, segunda.cidades)
        self.assertEqual(cena.decoracoes, segunda.decoracoes)
        self.assertEqual({c.perfil for c in cena.cidades.values()},
                         {'residencial', 'misto', 'comercial'})
        for cidade in cena.cidades.values():
            with self.subTest(cidade=cidade.no):
                self.assertEqual(cidade.ancora_rua, cena.marcadores_no[cidade.no])
                self.assertIn(cidade.no, cidade.via_acesso)
                rua = cena.ruas[cidade.via_acesso]
                x, y, _ = cidade.ponto_na_via
                self.assertTrue(any(_distancia_segmento(x, y, a, b) < 1e-8
                                    and a[2] == b[2] == cidade.ancora_rua[2]
                                    for a, b in zip(rua, rua[1:])))
                self.assertAlmostEqual(cena.distancia_rua(*cidade.meio_fio[:2]), LARGURA_RUA / 2 + .002)
                self.assertEqual(len(cidade.grupos), 2)
                self.assertTrue(all(any(lote.tipo == 'edificio' for lote in grupo) for grupo in cidade.grupos))
                lotes = [d for d in cena.decoracoes if d.no == cidade.no]
                casas = [d for d in lotes if d.tipo == 'edificio' and d.kit == 'suburbio']
                predios = [d for d in lotes if d.tipo == 'edificio' and d.kit == 'cidade']
                self.assertGreaterEqual(len(casas), 4)
                self.assertGreaterEqual(len(predios), 1)
                self.assertTrue(any(d.tipo == 'arvore' for d in lotes))
                x0, y0, x1, y1 = cidade.limites_xy
                for d in lotes:
                    hx, hy = d.semieixos
                    self.assertTrue(x0 < d.x - hx < d.x + hx < x1)
                    self.assertTrue(y0 < d.y - hy < d.y + hy < y1)
                    self.assertLessEqual(d.altura, 1.65 + .025 + 1e-8)
                for a, b in combinations(lotes, 2):
                    self.assertTrue(abs(a.x - b.x) > a.semieixos[0] + b.semieixos[0] or
                                    abs(a.y - b.y) > a.semieixos[1] + b.semieixos[1])
        for a, b in combinations(cena.cidades.values(), 2):
            x0, y0, x1, y1 = a.limites_xy
            u0, v0, u1, v1 = b.limites_xy
            self.assertTrue(x1 < u0 or x0 > u1 or y1 < v0 or y0 > v1)

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
                self.assertEqual(cena.rota.getNumChildren(), 1)
                malha = cena.rota.getChild(0).node()
                self.assertEqual(malha.getNumGeoms(), len(set(zip(resultado.caminho, resultado.caminho[1:]))))
                cena.mostrar_trecho(*resultado.caminho[:2])
                self.assertEqual(cena.rota.getChild(0).node().getGeom(0), malha.getGeom(0))
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
