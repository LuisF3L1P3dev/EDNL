"""Layout e captura de cliques do HUD com superfícies reais, sem janela."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import unittest

import pygame
from panda3d.core import NodePath

from comparacao import CORES_ROTAS
from geometria3d import criar_mapa_visual
from hud import HUD, RED, BLUE, GREEN, CURRENT, LINE, YELLOW, PASSAGEM
from mundo3d import Viagem
from solvers import executar
from tsp_core import carregar_mapa
from tsp_3d import Aplicacao3D


ROOT = Path(__file__).resolve().parents[1]


class _Camera:
    ZOOM_MIN, ZOOM_MAX = .65, 3.

    def __init__(self, tamanho):
        w, h = tamanho
        self.viewport = pygame.Rect(244, 90, w - 494, h - 222)
        self.pontos_forcados = {}
        self.zoom = 1.

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
        self.comparacao_aberta = self.comparacao_erro = self.rota_comparada = False
        self.comparacao_futuro = None
        self.comparacao_resultados = {}
        self.viagem = Viagem()
        self.resultado = self.etapa = None
        self.fase, self.status = 'Pronto para partir', 'Selecione um algoritmo e inicie.'
        self.distancia_percorrida = 0
        self.progresso_visual = 0.
        self.pixel2d, self.render = NodePath('pixel2d'), NodePath('render')
        self.carro = self.render.attachNewNode('veiculo')
        visual = criar_mapa_visual(self.mapa)
        self.cena = SimpleNamespace(mapa_visual=visual, posicoes=visual.posicoes, ruas=visual.ruas)
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

    def test_controles_de_zoom_reservam_area_e_capturam_cliques(self):
        for tamanho in ((1100, 760), (1440, 960)):
            app = self.construir(tamanho, 5)
            area = app.ui._area_controles()
            ponto = app.cena.posicoes[1]
            app.camera_iso.pontos_forcados[ponto[:2]] = area.center
            app.ui.desenhar()
            self.assertFalse(area.colliderect(app.ui.etiquetas_tela[1]))
            self.assertFalse(any(area.colliderect(box) for box in app.ui.pesos_tela.values()))
            self.assertFalse(area.colliderect(app.ui.botoes['mapa1'][0]))
            for acao in ('zoom-', 'zoom+', 'reset'):
                app.mouse = app.ui.botoes[acao][0].center
                Aplicacao3D.clicar(app)
                self.assertEqual(app.acoes[-1], acao)
            app.camera_iso.zoom = app.camera_iso.ZOOM_MAX
            app.ui.desenhar()
            self.assertFalse(app.ui.botoes['zoom+'][1])
            antes = len(app.acoes)
            app.mouse = app.ui.botoes['zoom+'][0].center
            Aplicacao3D.clicar(app)
            self.assertEqual(len(app.acoes), antes)
            app.camera_iso.zoom = app.camera_iso.ZOOM_MIN
            app.ui.desenhar()
            self.assertFalse(app.ui.botoes['zoom-'][1])

    def test_pins_proximos_ficam_separados_e_sao_estaveis(self):
        for tamanho in ((1100, 760), (1440, 960)):
            app = self.construir(tamanho, 5)
            for no, ponto in app.cena.posicoes.items():
                app.camera_iso.pontos_forcados[ponto[:2]] = (500 + no, 300 + no)
            app.ui.desenhar()
            caixas = list(app.ui.etiquetas_tela.values())
            for i, caixa in enumerate(caixas):
                self.assertFalse(any(caixa.colliderect(outra) for outra in caixas[i + 1:]))
            posicoes = dict(app.ui.posicoes_tela)
            ancoras = dict(app.ui.ancoras_tela)
            app.ui.desenhar()
            self.assertEqual(app.ui.posicoes_tela, posicoes)
            self.assertEqual(app.ui.ancoras_tela, ancoras)
            for no, centro in posicoes.items():
                app.mouse = centro
                Aplicacao3D.clicar(app)
                self.assertEqual(app.origem, no)

    def test_pesos_evitam_projecao_de_construcoes(self):
        app = self.construir(numero_mapa=5)
        app.cena.decoracoes = [SimpleNamespace(tipo='edificio', x=0, y=0, raio=3, altura=5)]
        app.ui.desenhar()
        edificios = app.ui._construcoes_tela(app.camera_iso.viewport)
        self.assertTrue(edificios)
        self.assertTrue(app.ui.pesos_tela)
        for peso in app.ui.pesos_tela.values():
            self.assertLess(peso.collidelist(edificios), 0)

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
                    self.assertTrue(any(t in ('Entrega concluída', 'Entregue') for t, _, _ in app.ui.textos))

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

    def test_cor_do_ponto_atual_em_viagem_pausa_e_final(self):
        app = self.construir(numero_mapa=5)
        def cor(no):
            x, y = app.ui.posicoes_tela[no]
            return tuple(app.ui.canvas.get_at((x + 10, y)))[:3]
        self.assertEqual(cor(1), CURRENT)
        app.viagem.carregar(app.mapa, (1, 2, 3), ciclo=False)
        app.viagem.atualizar(1)
        app.viagem.reproduzindo = False
        app.ui.desenhar()
        self.assertEqual(cor(1), GREEN)
        self.assertEqual(cor(2), BLUE)
        app.viagem.saltar(1)
        app.ui.desenhar()
        self.assertEqual(cor(2), CURRENT)
        app.viagem.saltar(1)
        app.ui.desenhar()
        self.assertEqual(cor(3), CURRENT)
        self.assertEqual(cor(2), GREEN)
        app.viagem.carregar(app.mapa, (1, 2, 3), ciclo=False, ordem_visita=(1, 3), indices_visita=(0, 2))
        app.viagem.saltar(1)
        app.ui.desenhar()
        self.assertEqual(cor(2), PASSAGEM)

    def test_badge_deslocado_continua_selecionavel(self):
        app = self.construir(numero_mapa=5)
        app.mouse = app.ui.posicoes_tela[3]
        Aplicacao3D.clicar(app)
        self.assertEqual(app.origem, 3)
        self.assertEqual(app.limpezas, 1)

    def test_marcadores_usam_ancoras_da_rua_e_identificam_origem(self):
        app = self.construir(numero_mapa=5)
        visual = app.cena.mapa_visual
        primeiro = replace(visual.nos[0], deslocamento_etiqueta=(16., -58.))
        app.cena.mapa_visual = replace(visual, nos=(primeiro,) + visual.nos[1:])
        app.ui.textos.clear()
        app.ui.desenhar()
        for no, ancora in visual.posicoes.items():
            esperado = app.camera_iso.projetar(ancora)
            self.assertEqual(app.ui.ancoras_tela[no], esperado)
            self.assertTrue(app.camera_iso.viewport.contains(app.ui.etiquetas_tela[no]))
        x, y = app.ui.ancoras_tela[primeiro.id]
        self.assertEqual(app.ui.posicoes_tela[primeiro.id], (round(x + 16), round(y - 58)))
        self.assertTrue(any(texto == 'ORIGEM' for texto, _, _ in app.ui.textos))

    def test_pesos_das_ruas_nao_colidem_com_pins_ou_entre_si(self):
        for mapa in (5, 18):
            app = self.construir(numero_mapa=mapa)
            # A câmera de teste não é a câmera isométrica real; enquadrar a
            # malha inteira permite validar as 45 etiquetas, inclusive as
            # ruas no perímetro da cidade.
            def projetar_malha(ponto, camera=app.camera_iso):
                r = camera.viewport
                return r.centerx + ponto[0] / 145 * r.w, r.centery - ponto[1] / 110 * r.h
            app.camera_iso.projetar = projetar_malha
            app.ui.desenhar()
            pesos = app.ui.pesos_tela
            self.assertEqual(len(pesos), len(app.mapa.arestas))
            caixas = list(pesos.values())
            for i, caixa in enumerate(caixas):
                self.assertTrue(app.camera_iso.viewport.contains(caixa))
                self.assertFalse(caixa.colliderect(pygame.Rect(258, 100, 230, 50)))
                self.assertFalse(any(caixa.colliderect(pin)
                                     for pin in app.ui.etiquetas_tela.values()))
                self.assertFalse(any(caixa.colliderect(outra)
                                     for outra in caixas[i + 1:]))

    def test_destaque_de_peso_acompanha_somente_trecho_atual(self):
        app = self.construir(numero_mapa=5)
        app.viagem.carregar(app.mapa, (1, 2, 3), ciclo=False)
        app.ui.desenhar()
        self.assertEqual(app.ui.pesos_ativos, {frozenset((1, 2))})
        app.viagem.reproduzindo = False  # pausa mantém o mesmo trecho
        app.ui.desenhar()
        self.assertEqual(app.ui.pesos_ativos, {frozenset((1, 2))})
        app.viagem.reproduzir()
        app.viagem.atualizar(100)
        app.ui.desenhar()
        self.assertEqual(app.ui.pesos_ativos,
                         {frozenset((1, 2)), frozenset((2, 3))})

    def test_barra_pinta_a_fracao_geometrica(self):
        tamanho = (1100, 760)
        app = self.construir(tamanho, 5)
        app.viagem.carregar(app.mapa, (1, 2, 3), ciclo=False)
        app.viagem.atualizar(15.)
        self.assertGreater(app.viagem.custo_atual / app.viagem.total, .4)
        app.progresso_visual = .25
        app.ui.desenhar()
        y = tamanho[1] - 116 + 77
        self.assertEqual(tuple(app.ui.canvas.get_at((200, y)))[:3], YELLOW[:3])
        self.assertEqual(tuple(app.ui.canvas.get_at((400, y)))[:3], LINE[:3])

    def test_barra_inferior_indica_trecho_em_todos_os_estados(self):
        for tamanho in [(1100, 760), (1440, 960)]:
            with self.subTest(tamanho=tamanho):
                app = self.construir(tamanho, 5)

                def trecho_pintado():
                    return [(texto, rect) for texto, rect, _ in app.ui.textos
                            if texto.startswith(('No ponto ', 'Em rota:', 'Pausada:',
                                                'Aguardando no ponto', 'Concluído no ponto'))]

                self.assertIn(('No ponto 1 · aguardando rota',),
                              [(texto,) for texto, _ in trecho_pintado()])
                app.viagem.carregar(app.mapa, (1, 2, 3), ciclo=False)
                app.ui.textos.clear()
                app.ui.desenhar()
                self.assertIn(('Em rota: 1 → 2',), [(texto,) for texto, _ in trecho_pintado()])
                app.viagem.reproduzindo = False
                app.ui.textos.clear()
                app.ui.desenhar()
                self.assertIn(('Pausada: 1 → 2',), [(texto,) for texto, _ in trecho_pintado()])
                app.viagem._indice, app.viagem._espera = 1, app.viagem.PAUSA_CHEGADA
                app.ui.textos.clear()
                app.ui.desenhar()
                self.assertIn(('Aguardando no ponto 2 · próximo: 2 → 3',),
                              [(texto,) for texto, _ in trecho_pintado()])
                app.viagem._indice = len(app.viagem.pesos)
                app.viagem._espera = 0.
                app.ui.textos.clear()
                app.ui.desenhar()
                atual = trecho_pintado()
                self.assertIn(('Concluído no ponto 3 · último: 2 → 3',),
                              [(texto,) for texto, _ in atual])
                inicio_botoes = app.ui.botoes['iniciar'][0].left
                topo_barra = tamanho[1] - 116 + 74
                for _, rect in atual:
                    self.assertLessEqual(rect.right, inicio_botoes)
                    self.assertLessEqual(rect.bottom, topo_barra)
                self.assertTrue(any(texto == 'NEXUS' for texto, _, _ in app.ui.textos))

    def test_modal_config_captura_cliques_e_volta_ao_mapa(self):
        for tamanho in [(1100, 760), (1440, 960)]:
            app = self.construir(tamanho)
            app.ui.tratar_acao('config')
            app.ui.desenhar()
            self.assertEqual(set(app.ui.botoes), {'pesos', 'legendas', 'animacao', 'fechar_config'})
            for _, (rect, _) in app.ui.botoes.items():
                self.assertTrue(app.ui.canvas.get_rect().contains(rect))
            origem = app.origem
            app.mouse = next(iter(app.ui.posicoes_tela.values()))
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
        # A barra inferior também informa o trecho atual; esta checagem é
        # exclusivamente da sequência longa no painel de resultados.
        linhas = [(t, r) for t, r, _ in app.ui.textos
                  if ('→' in t or t.startswith('… ')) and r.left >= 1100 - 234]
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

    def test_painel_mostra_custo_e_alterna_entre_entregas_e_percurso(self):
        app = self.construir((1100, 760))
        app.resultado = executar('heuristica', app.mapa, 1)
        resultado = app.resultado
        self.assertNotEqual(resultado.caminho, resultado.ordem_visita)
        app.viagem.carregar(app.mapa, resultado.caminho, ordem_visita=resultado.ordem_visita,
                            indices_visita=resultado.indices_visita)
        for titulo, nos in (('ORDEM DE ENTREGA', resultado.ordem_visita),
                            ('PERCURSO FÍSICO', resultado.caminho)):
            app.ui.textos.clear()
            app.ui.desenhar()
            textos = [t for t, r, _ in app.ui.textos if r.left >= 1100 - 218]
            self.assertIn(titulo, textos)
            self.assertIn('388', textos)
            self.assertIn('Entregas: 1 / 18', textos)
            rota = tuple(int(n) for t in textos if '→' in t for n in t.split() if n.isdigit())
            self.assertEqual(rota, nos)
            app.acao('alternar_percurso')

    def test_painel_do_circuito_mostra_custo_e_todas_as_entregas(self):
        app = self.construir((1100, 760))
        app.metodo = 'circuito'
        app.resultado = executar(app.metodo, app.mapa, 1)
        r = app.resultado
        app.viagem.carregar(app.mapa, r.caminho, ordem_visita=r.ordem_visita, indices_visita=r.indices_visita)
        app.viagem.atualizar(120)
        app.ui.textos.clear()
        app.ui.desenhar()
        textos = [t for t, rect, _ in app.ui.textos if rect.left >= 1100 - 218]
        self.assertIn(f'{r.custo:g}', textos)
        self.assertIn('Percorrido: 391.0', textos)
        self.assertIn('Entregas: 18 / 18', textos)
        self.assertIn('Percurso físico segue a ordem acima', textos)
        self.assertEqual(tuple(int(n) for t in textos if '→' in t for n in t.split() if n.isdigit()), r.caminho)

    def test_card_comparacao_em_duas_resolucoes_sem_cobrir_controles(self):
        for tamanho in ((1100, 760), (1440, 960)):
            with self.subTest(tamanho=tamanho):
                app = self.construir(tamanho, 5)
                hud = app.ui
                self.assertIn('comparar', hud.botoes)
                self.assertFalse(hud.area_comparacao)
                app.comparacao_aberta = True
                app.comparacao_resultados = {m: executar(m, app.mapa, app.origem) for m in ('forca', 'heuristica')}
                hud.textos.clear()
                hud.desenhar()
                visiveis = [t for t, r, _ in hud.textos if hud.area_comparacao.contains(r)]
                self.assertIn('Empate no custo', visiveis)
                self.assertEqual(visiveis.count('1 → 2 → 3 → 5 → 4 → 1'), 2)
                self.assertIn('Diferença absoluta  0   ·   Em relação ao ótimo  0.00%', visiveis)
                botoes_rota = [hud.botoes['visualizar_' + metodo] for metodo in ('forca', 'heuristica')]
                self.assertTrue(all(ativo for _, ativo in botoes_rota))
                self.assertLess(botoes_rota[0][0].right, botoes_rota[1][0].left)
                for (rect, _), metodo in zip(botoes_rota, ('forca', 'heuristica')):
                    self.assertEqual(hud.canvas.get_at((rect.x + 12, rect.centery))[:3], CORES_ROTAS[metodo])
                for acao in ('mapa0', 'mapa1', 'iniciar', 'pausa', 'zoom+', 'zoom-', 'acompanhar', 'comparar'):
                    self.assertFalse(hud.area_comparacao.colliderect(hud.botoes[acao][0]), acao)
                app.comparacao_aberta = False
                app.metodo = 'dijkstra'
                hud.desenhar()
                self.assertNotIn('comparar', hud.botoes)
                self.assertNotIn('visualizar_forca', hud.botoes)

    def test_card_regiao_rotula_objetivos_e_rola_percurso_expandido(self):
        app = self.construir((1100, 760))
        hud = app.ui
        app.comparacao_aberta = True
        app.comparacao_resultados = {'dijkstra': executar('dijkstra', app.mapa, 1, 3),
                                    'heuristica': executar('heuristica', app.mapa, 1)}
        hud.textos.clear()
        hud.desenhar()
        textos = [t for t, _, _ in hud.textos]
        self.assertIn('Caminho mínimo A → B', textos)
        self.assertIn('Circuito completo · solução aproximada', textos)
        self.assertIn('Força bruta desabilitada neste mapa.', textos)
        self.assertNotIn('visualizar_forca', hud.botoes)
        self.assertNotIn('Empate no custo', textos)
        self.assertGreater(hud._limite_comparacao, 0)
        app.mouse = hud.area_comparacao.center
        self.assertTrue(hud.rolar_comparacao(100))
        hud.textos.clear()
        hud.desenhar()
        fim = app.comparacao_resultados['heuristica'].caminho[-4:]
        self.assertTrue(any(t.endswith(' → '.join(map(str, fim))) and r.bottom < hud.botoes['visualizar_heuristica'][0].top
                            for t, r, _ in hud.textos))

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
