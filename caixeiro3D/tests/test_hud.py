"""Layout e captura de cliques do HUD com superfícies reais, sem janela."""

from pathlib import Path
from types import SimpleNamespace
import unittest

import pygame
from panda3d.core import NodePath

from geometria3d import posicoes_mundo, ruas_mundo
from hud import HUD, RED
from mundo3d import Viagem
from solvers import executar
from tsp_core import carregar_mapa
from tsp_3d import Aplicacao3D


ROOT = Path(__file__).resolve().parents[1]


class _Camera:
    def __init__(self, tamanho):
        w, h = tamanho
        self.viewport = pygame.Rect(244, 90, w - 494, h - 222)
        self.pontos_forcados = {}

    def projetar(self, ponto):
        if ponto[:2] in self.pontos_forcados:
            return self.pontos_forcados[ponto[:2]]
        r = self.viewport
        return (r.centerx + ponto[0] / 60 * r.w,
                r.centery - ponto[1] / 50 * r.h)


class _App:
    def __init__(self, tamanho, numero_mapa):
        self.win = SimpleNamespace(getXSize=lambda: tamanho[0], getYSize=lambda: tamanho[1])
        self.mapa = carregar_mapa(ROOT / 'data' / f'mapa_{numero_mapa:02}.json')
        self.indice_mapa = 0 if numero_mapa == 5 else 1
        self.metodo = 'forca' if numero_mapa == 5 else 'heuristica'
        self.origem, self.destino = 1, 3
        self.selecao = 'origem'
        self.ocupado = False
        self.viagem = Viagem()
        self.resultado = self.etapa = None
        self.fase, self.status = 'Pronto para partir', 'Selecione um algoritmo e inicie.'
        self.distancia_percorrida = 0
        self.pixel2d, self.render = NodePath('pixel2d'), NodePath('render')
        self.carro = self.render.attachNewNode('veiculo')
        self.cena = SimpleNamespace(posicoes=posicoes_mundo(self.mapa), ruas=ruas_mundo(self.mapa))
        self.camera_iso = _Camera(tamanho)
        self.mouse = None
        self.acoes = []
        self.limpezas = 0

    def mouse_pixel(self):
        return self.mouse

    def acao(self, acao):
        self.acoes.append(acao)
        self.ui.tratar_acao(acao)

    def _limpar(self):
        self.limpezas += 1


class _HUDObservado(HUD):
    """Registra limites efetivamente pintados para detectar texto vazando."""
    def __init__(self, app):
        self.textos = []
        super().__init__(app)

    def texto(self, valor, x, y, tamanho=14, cor=None, bold=False, largura=None):
        from hud import INK
        cor = INK if cor is None else cor
        largura_pintada = super().texto(valor, x, y, tamanho, cor, bold, largura)
        self.textos.append((str(valor), pygame.Rect(x, y, largura_pintada,
                                                 self.fonte(tamanho, bold).get_height()), cor))
        return largura_pintada


class TestHUD(unittest.TestCase):
    def construir(self, tamanho=(1440, 960), numero_mapa=18):
        app = _App(tamanho, numero_mapa)
        app.ui = _HUDObservado(app)
        self.addCleanup(app.ui.destruir)
        app.ui.desenhar()
        return app

    def test_acoes_visiveis_e_sem_sobreposicao_nas_resolucoes(self):
        for tamanho in [(1100, 760), (1100, 880), (1440, 960)]:
            for mapa in [5, 18]:
                with self.subTest(tamanho=tamanho, mapa=mapa):
                    app = self.construir(tamanho, mapa)
                    app.metodo = 'dijkstra'
                    app.ui.desenhar()
                    janela = pygame.Rect((0, 0), tamanho)
                    for acao, (rect, _) in app.ui.botoes.items():
                        self.assertTrue(janela.contains(rect), acao)
                    botoes = list(app.ui.botoes.items())
                    for i, (acao, (rect, _)) in enumerate(botoes):
                        for outra, (outro, _) in botoes[i + 1:]:
                            self.assertFalse(rect.colliderect(outro), f'{acao} sobrepõe {outra}')
                    self.assertIn('distancias', app.ui.botoes)
                    self.assertTrue(any(t == 'Visitado' or t == 'Ponto visitado'
                                        for t, _, _ in app.ui.textos))

    def test_etiquetas_liberam_veiculo_e_ficam_dentro_do_viewport(self):
        for tamanho in [(1100, 760), (1440, 960)]:
            app = self.construir(tamanho, 5)
            app.metodo = 'dijkstra'
            app.ui.desenhar()
            viewport = app.camera_iso.viewport
            for no, box in app.ui.etiquetas_tela.items():
                self.assertTrue(viewport.contains(box), no)
                ancora = app.ui.ancoras_tela[no]
                self.assertFalse(box.collidepoint(ancora), no)
                self.assertGreaterEqual(abs(app.ui.posicoes_tela[no][1] - ancora[1]), 30)
            # Simular pan até três cantos: as etiquetas não podem ser cortadas.
            for no, ancora in [(1, (viewport.left + 1, viewport.top + 1)),
                               (2, (viewport.right - 1, viewport.bottom - 1)),
                               (3, (viewport.right - 1, viewport.top + 1))]:
                ponto = app.cena.posicoes[no]
                app.camera_iso.pontos_forcados[ponto[:2]] = ancora
            app.ui.desenhar()
            for no in (1, 2, 3):
                self.assertTrue(viewport.contains(app.ui.etiquetas_tela[no]), no)
                self.assertFalse(app.ui.etiquetas_tela[no].collidepoint(app.ui.ancoras_tela[no]), no)

    def test_badge_deslocado_continua_selecionavel(self):
        app = self.construir(numero_mapa=5)
        app.mouse = app.ui.posicoes_tela[3]
        Aplicacao3D.clicar(app)
        self.assertEqual(app.origem, 3)
        self.assertEqual(app.limpezas, 1)

    def test_modal_config_captura_cliques_e_volta_ao_mapa(self):
        for tamanho in [(1100, 760), (1440, 960)]:
            app = self.construir(tamanho)
            app.ui.tratar_acao('config')
            app.ui.desenhar()
            self.assertEqual(set(app.ui.botoes), {'pesos', 'legendas', 'animacao', 'fechar_config'})
            for _, (rect, _) in app.ui.botoes.items():
                self.assertTrue(app.ui.canvas.get_rect().contains(rect))
            origem = app.origem
            app.mouse = app.ui.posicoes_tela[3]
            Aplicacao3D.clicar(app)
            self.assertEqual(app.origem, origem)
            self.assertEqual(app.limpezas, 0)
            self.assertEqual(app.acoes, [])
            app.mouse = app.ui.botoes['pesos'][0].center
            Aplicacao3D.clicar(app)
            self.assertFalse(app.ui.mostrar_pesos)
            self.assertTrue(app.ui.config_aberta)
            app.mouse = app.ui.botoes['fechar_config'][0].center
            Aplicacao3D.clicar(app)
            self.assertFalse(app.ui.config_aberta)

    def test_modal_dijkstra_exibe_todos_os_dezoito_nos(self):
        for tamanho in [(1100, 760), (1440, 960)]:
            app = self.construir(tamanho)
            app.metodo = 'dijkstra'
            app.resultado = executar('dijkstra', app.mapa, 1, 18)
            app.ui.tratar_acao('distancias')
            app.ui.textos.clear()
            app.ui.desenhar()
            self.assertEqual(set(app.ui.botoes), {'fechar_config'})
            entradas = [(t, r) for t, r, _ in app.ui.textos
                        if t[:2].isdigit() and t[2:].startswith('  ·  ')]
            self.assertEqual(len(entradas), 18)
            modal = pygame.Rect((tamanho[0] - 440) // 2, (tamanho[1] - 362) // 2, 440, 362)
            for _, rect in entradas:
                self.assertTrue(modal.contains(rect))
                self.assertLess(rect.bottom, app.ui.botoes['fechar_config'][0].top)

    def test_rota_longa_indica_omissao_preserva_destino_e_nao_vaza(self):
        app = self.construir((1100, 760))
        rota = tuple([1, 2] * 70 + [1])
        app.viagem.carregar(app.mapa, rota, ciclo=False)
        app.ui.textos.clear()
        app.ui.desenhar()
        linhas = [(t, r) for t, r, _ in app.ui.textos if '→' in t or t.startswith('… ')]
        self.assertGreater(len(linhas), 0)
        self.assertLessEqual(len(linhas), 6)
        self.assertTrue(linhas[-1][0].startswith('… '))
        self.assertTrue(linhas[-1][0].endswith('1'))
        for _, rect in linhas:
            self.assertGreaterEqual(rect.left, 1100 - 234 + 16)
            self.assertLessEqual(rect.right, 1100 - 16)
            self.assertLess(rect.bottom, 760 - 172)

    def test_estado_de_erro_e_contagem_de_busca_aparecem(self):
        app = self.construir(numero_mapa=5)
        app.fase, app.status = 'Erro no cálculo', 'Peso inválido.'
        app.resultado = executar('forca', app.mapa, 1)
        app.ui.textos.clear()
        app.ui.desenhar()
        self.assertIn(('Erro no cálculo', RED), [(t, c) for t, _, c in app.ui.textos])
        self.assertTrue(any('24 candidatas' in t for t, _, _ in app.ui.textos))

    def test_upload_da_textura_preserva_cor_e_transparencia(self):
        app = self.construir((1100, 760), 5)
        pixels = bytes(app.ui.textura.getRamImageAs('RGBA'))
        largura, altura = app.ui.canvas.get_size()
        for x, y in [(35, 35), (245, 91)]:
            indice = ((altura - y - 1) * largura + x) * 4
            self.assertEqual(tuple(pixels[indice:indice + 4]), tuple(app.ui.canvas.get_at((x, y))))
        self.assertEqual(app.ui.canvas.get_at((245, 91)).a, 0)


if __name__ == '__main__':
    unittest.main()
