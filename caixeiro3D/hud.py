"""HUD Pygame sobre a cena Panda3D, adaptado da base ../caixeiro/tsp_3d.py.

Painéis e eventos da interface não alteram o grafo nem o relógio da viagem.
"""
from math import hypot, isfinite

import pygame
from panda3d.core import CardMaker, Texture, TransparencyAttrib

from geometria3d import interpolar

INK = (32, 47, 64)
MUTED = (72, 91, 105)
BLUE = (47, 126, 221)
GREEN = (35, 161, 115)
GREEN_TEXT = (22, 113, 80)
YELLOW = (247, 188, 56)
RED = (184, 45, 57)
WHITE = (253, 254, 251)
LINE = (224, 232, 229)
METHODS = {'forca': 'Força bruta · TSP exato', 'dijkstra': 'Dijkstra · caminho mínimo',
           'heuristica': 'Dijkstra + heurística'}


class HUD:
    def __init__(self, app):
        self.app = app
        pygame.font.init()
        self.fontes = {}
        self.botoes = {}
        self.posicoes_tela = {}
        self.ancoras_tela = {}
        self.etiquetas_tela = {}
        self.config_aberta = False
        self.mostrar_pesos = True
        self.mostrar_legendas = True
        self.animar_busca = True
        self.dist_pagina = 0
        self.dist_aberta = False
        self.textura = Texture('HUD Pygame')
        cm = CardMaker('HUD')
        cm.setFrame(0, 1, -1, 0)
        self.raiz = app.pixel2d.attachNewNode(cm.generate())
        self.raiz.setTransparency(TransparencyAttrib.M_alpha)
        self.raiz.setTexture(self.textura)
        self.raiz.setDepthTest(False)
        self.raiz.setDepthWrite(False)
        self.raiz.setBin('fixed', 100)

    def fonte(self, tamanho=14, bold=False):
        chave = tamanho, bold
        if chave not in self.fontes:
            self.fontes[chave] = pygame.font.SysFont('segoeui', tamanho, bold)
        return self.fontes[chave]

    def texto(self, valor, x, y, tamanho=14, cor=INK, bold=False, largura=None):
        valor = str(valor)
        fonte = self.fonte(tamanho, bold)
        if largura and fonte.size(valor)[0] > largura:
            while valor and fonte.size(valor + '…')[0] > largura:
                valor = valor[:-1]
            valor += '…'
        img = fonte.render(valor, True, cor)
        self.canvas.blit(img, (int(x), int(y)))
        return img.get_width()

    def linhas(self, valor, x, y, largura, tamanho=13, cor=MUTED, max_linhas=5):
        """Quebra em palavras sem cortar a sequência da rota."""
        linhas, atual = [], ''
        for palavra in str(valor).split():
            nova = f'{atual} {palavra}'.strip()
            if atual and self.fonte(tamanho).size(nova)[0] > largura:
                linhas.append(atual)
                atual = palavra
            else:
                atual = nova
        if atual:
            linhas.append(atual)
        visiveis = linhas[:max_linhas]
        if len(linhas) > max_linhas and visiveis:
            # Indicar o trecho omitido e preservar o fim do percurso.
            visiveis[-1] = '… ' + linhas[-1]
        for i, linha in enumerate(visiveis):
            self.texto(linha, x, y + i * (tamanho + 5), tamanho, cor,
                       largura=largura)
        return min(len(linhas), max_linhas) * (tamanho + 5)

    def card(self, rect):
        rect = pygame.Rect(rect)
        pygame.draw.rect(self.canvas, (25, 55, 45, 28), rect.move(0, 4), border_radius=15)
        pygame.draw.rect(self.canvas, WHITE, rect, border_radius=15)
        pygame.draw.rect(self.canvas, LINE, rect, 1, border_radius=15)

    def botao(self, acao, label, rect, *, ativo=True, selecionado=False, destaque=False):
        rect = pygame.Rect(rect)
        mouse = self.app.mouse_pixel()
        hover = ativo and mouse is not None and rect.collidepoint(mouse)
        cor = BLUE if destaque and ativo else (224, 239, 252) if selecionado else (232, 240, 239) if hover else (243, 246, 243)
        pygame.draw.rect(self.canvas, cor, rect, border_radius=8)
        if selecionado:
            pygame.draw.rect(self.canvas, BLUE, rect, 1, border_radius=8)
        tinta = WHITE if destaque and ativo else INK if ativo else (133, 145, 150)
        fonte = self.fonte(13, True)
        img = fonte.render(str(label), True, tinta)
        self.canvas.blit(img, img.get_rect(center=rect.center))
        self.botoes[acao] = rect, ativo

    def tratar_acao(self, acao):
        if acao in ('config', 'fechar_config'):
            self.config_aberta = not self.config_aberta
            self.dist_aberta = False
        elif acao == 'pesos':
            self.mostrar_pesos = not self.mostrar_pesos
        elif acao == 'legendas':
            self.mostrar_legendas = not self.mostrar_legendas
        elif acao == 'animacao':
            self.animar_busca = not self.animar_busca
        elif acao == 'distancias':
            self.dist_aberta = True
            self.config_aberta = True
        else:
            return False
        return True

    def _grafo(self):
        a = self.app
        viewport = a.camera_iso.viewport
        self.canvas.set_clip(viewport)
        caminho = a.viagem.caminho or (a.etapa.caminho if a.etapa else ())
        selecionadas = {frozenset((u, v)) for u, v in zip(caminho, caminho[1:])}
        if self.mostrar_pesos:
            for e in a.mapa.arestas:
                ponto, _ = interpolar(a.cena.ruas[e.origem, e.destino], .5)
                p = a.camera_iso.projetar(ponto)
                if not p or not viewport.collidepoint(p):
                    continue
                label = f'{e.peso:g}'
                fonte = self.fonte(12, True)
                box = pygame.Rect(0, 0, fonte.size(label)[0] + 14, 22)
                box.center = int(p[0]), int(p[1])
                ativa = frozenset((e.origem, e.destino)) in selecionadas
                pygame.draw.rect(self.canvas, (255, 244, 197) if ativa else (252, 253, 248, 235), box, border_radius=6)
                pygame.draw.rect(self.canvas, YELLOW if ativa else LINE, box, 1, border_radius=6)
                self.texto(label, box.x + 7, box.y + 2, 12, INK, True)
        self.posicoes_tela = {}
        self.ancoras_tela = {}
        self.etiquetas_tela = {}
        explorados = set(a.etapa.explorados if a.etapa else ())
        for no, ponto in a.cena.posicoes.items():
            p = a.camera_iso.projetar(ponto)
            if not p or not viewport.collidepoint(p):
                continue
            label = ''
            if self.mostrar_legendas:
                if no == a.origem:
                    label = 'ORIGEM'
                elif no == a.destino and a.metodo == 'dijkstra':
                    label = 'DESTINO'
            largura_label = self.fonte(10, True).size(label)[0] + 12 if label else 0
            margem_x = max(23, largura_label // 2 + 1)
            abaixo = p[1] - 46 - (44 if label else 23) < viewport.top + 2
            cima, baixo = (23, 44) if abaixo and label else (44, 23) if label else (23, 23)
            centro = (
                round(max(viewport.left + margem_x + 2, min(viewport.right - margem_x - 2, p[0]))),
                round(max(viewport.top + cima + 2, min(viewport.bottom - baixo - 2,
                      p[1] + 46 if abaixo else p[1] - 46))),
            )
            self.posicoes_tela[no] = centro
            self.ancoras_tela[no] = p
            box = pygame.Rect(centro[0] - 23, centro[1] - 23, 46, 46)
            # A haste indica o ponto real sem cobrir o veículo na chegada.
            dx, dy = p[0] - centro[0], p[1] - centro[1]
            comprimento = hypot(dx, dy)
            ponta = (round(centro[0] + dx / comprimento * 18),
                     round(centro[1] + dy / comprimento * 18)) if comprimento else centro
            ancora = tuple(map(round, p))
            pygame.draw.line(self.canvas, (26, 50, 54, 80), ancora, ponta, 5)
            pygame.draw.line(self.canvas, WHITE, ancora, ponta, 2)
            pygame.draw.circle(self.canvas, WHITE, ancora, 3)
            cor = GREEN if no in a.viagem.visitadas else YELLOW if no in explorados and a.ocupado else BLUE
            pygame.draw.circle(self.canvas, (35, 63, 66, 65), (centro[0], centro[1] + 3), 18)
            pygame.draw.circle(self.canvas, WHITE, centro, 18)
            pygame.draw.circle(self.canvas, cor, centro, 15)
            img = self.fonte(14, True).render(str(no), True, INK if cor == YELLOW else WHITE)
            self.canvas.blit(img, img.get_rect(center=centro))
            if no == a.origem:
                pygame.draw.circle(self.canvas, GREEN, centro, 21, 2)
            if label:
                r = pygame.Rect(centro[0] - largura_label // 2,
                                centro[1] + 25 if abaixo else centro[1] - 43, largura_label, 18)
                pygame.draw.rect(self.canvas, WHITE, r, border_radius=5)
                self.texto(label, r.x + 6, r.y + 1, 10, GREEN_TEXT if no == a.origem else BLUE, True)
                box.union_ip(r)
            self.etiquetas_tela[no] = box
        if a.viagem.em_chegada:
            p = a.camera_iso.projetar(tuple(a.carro.getPos(a.render)))
            if p:
                pygame.draw.circle(self.canvas, GREEN, tuple(map(int, p)), 27, 3)
        self.canvas.set_clip(None)

    def _esquerda(self):
        a = self.app
        self.card((16, 94, 212, 540))
        self.texto('PLANEJAR ENTREGA', 32, 112, 10, MUTED, True)
        self.texto('Sua próxima rota', 32, 135, 19, INK, True)
        self.texto('ALGORITMO', 32, 173, 10, MUTED, True)
        for i, (chave, titulo) in enumerate((('forca', 'Força bruta · exato'), ('dijkstra', 'Dijkstra · A → B'), ('heuristica', 'Dijkstra + heurística'))):
            disponivel = chave == 'dijkstra' or (chave == 'forca') == (a.indice_mapa == 0)
            self.botao('selecionar_' + chave, titulo, (32, 195 + i * 39, 180, 33),
                       ativo=disponivel and not a.ocupado, selecionado=a.metodo == chave)
        self.texto('ORIGEM', 32, 323, 10, MUTED, True)
        for acao, label, x, largura in [('origem-', '‹', 32, 29), ('origem', f'Ponto {a.origem:02}', 66, 112), ('origem+', '›', 183, 29)]:
            self.botao(acao, label, (x, 344, largura, 33), ativo=not a.ocupado, selecionado=acao == a.selecao)
        self.texto('DESTINO' if a.metodo == 'dijkstra' else 'CIRCUITO COMPLETO', 32, 391, 10, MUTED, True)
        if a.metodo == 'dijkstra':
            for acao, label, x, largura in [('destino-', '‹', 32, 29), ('destino', f'Ponto {a.destino:02}', 66, 112), ('destino+', '›', 183, 29)]:
                self.botao(acao, label, (x, 412, largura, 33), ativo=not a.ocupado, selecionado=acao == a.selecao)
        else:
            self.linhas('Visite todos os pontos e retorne à origem.', 32, 412, 180, 13)
        self.linhas('Clique em um ponto do mapa para escolher a ' + a.selecao + '.', 32, 460, 180, 13)
        self.botao('cancelar' if a.ocupado else 'limpar', 'Cancelar busca' if a.ocupado else 'Limpar percurso', (32, 518, 180, 32))
        self.botao('config', 'Configurações', (32, 562, 180, 32))
        y = 652
        if self.canvas.get_height() >= 880:
            self.texto('Scroll: zoom · Direito: mover', 32, 607, 12, MUTED)
            self.card((16, y, 212, 108))
            self.texto('LEGENDA DO MAPA', 32, y + 14, 10, MUTED, True)
            for i, (cor, label) in enumerate(((BLUE, 'Ponto de entrega'), (YELLOW, 'Rota / exploração'), (GREEN, 'Ponto visitado'))):
                pygame.draw.circle(self.canvas, cor, (39, y + 43 + i * 20), 5)
                self.texto(label, 52, y + 34 + i * 20, 13, MUTED)
        else:
            for x, cor, label in ((37, BLUE, 'Ponto'), (94, YELLOW, 'Rota'), (145, GREEN, 'Visitado')):
                pygame.draw.circle(self.canvas, cor, (x, 613), 4)
                self.texto(label, x + 8, 604, 12, MUTED)

    def _direita(self, w, h):
        a = self.app
        x = w - 234
        self.card((x, 94, 218, h - 226))
        self.texto('PAINEL DE ENTREGA', x + 16, 112, 10, MUTED, True)
        self.texto('Resultados', x + 16, 135, 20, INK, True)
        self.texto(f'{len(a.mapa.ids)} pontos  ·  {len(a.mapa.arestas)} ruas', x + 16, 171, 13, MUTED)
        self.linhas(METHODS[a.metodo], x + 16, 199, 186, 13, INK, 2)
        busca = a.etapa if a.ocupado else a.resultado
        if busca:
            resumo = (f'Explorados: {len(busca.explorados)} / {len(a.mapa.ids)}'
                      if a.metodo == 'dijkstra' else
                      f'{busca.candidatas} candidatas · {len(busca.explorados)} nós')
            self.texto(resumo, x + 16, 228, 12, MUTED, largura=186)
        custo = a.resultado.custo if a.resultado else a.etapa.custo if a.etapa else None
        self.texto('CUSTO DA ROTA', x + 16, 251, 10, MUTED, True)
        self.texto('—' if custo is None else f'{custo:g}', x + 16, 271, 35, INK, True)
        self.texto(f'Percorrido: {a.viagem.custo_atual:.1f}', x + 16, 319, 13, GREEN_TEXT)
        self.texto(f'Visitados: {len(a.viagem.visitadas)} / {len(a.mapa.ids)}', x + 16, 342, 13, MUTED)
        self.texto(f'Distância: {a.distancia_percorrida:.1f} u.', x + 16, 365, 13, MUTED)
        tempo = a.resultado.tempo_ms if a.resultado else None
        self.texto('Cálculo: —' if tempo is None else f'Cálculo: {tempo:.2f} ms', x + 16, 388, 13, MUTED)
        self.texto('SEQUÊNCIA DA ROTA', x + 16, 424, 10, MUTED, True)
        caminho = a.viagem.caminho or (a.etapa.caminho if a.etapa else ())
        self.linhas(' → '.join(map(str, caminho)) if caminho else 'Aguardando sua partida.', x + 16, 447, 186, 13, INK, 6)
        garantia = a.resultado.garantia if a.resultado else 'Heurística: sem garantia de ótimo global.' if a.metodo == 'heuristica' else 'Busca exata de circuito Hamiltoniano.' if a.metodo == 'forca' else 'Caminho mínimo entre dois pontos.'
        if h >= 880:
            self.linhas(garantia, x + 16, 569, 186, 12, GREEN_TEXT if a.metodo != 'heuristica' else MUTED, 3)
            if a.metodo == 'dijkstra':
                distancias = a.etapa.distancias if a.etapa else a.resultado.distancias if a.resultado else {}
                pares = list(sorted(distancias.items()))
                offset = self.dist_pagina * 9 if len(pares) > 9 else 0
                linhas_disponiveis = max(0, min(3, (h - 184 - 661) // 22))
                if linhas_disponiveis:
                    self.texto('DISTÂNCIAS EXPLORADAS', x + 16, 636, 10, MUTED, True)
                for i, (no, d) in enumerate(pares[offset:offset + 3 * linhas_disponiveis]):
                    col, row = i % 3, i // 3
                    self.texto(f'{no}: {d:g}' if isfinite(d) else f'{no}: ∞', x + 16 + col * 64, 661 + row * 22, 12, MUTED)
        if a.metodo == 'dijkstra':
            self.botao('distancias', 'Ver todas as distâncias', (x + 16, h - 172, 186, 28))

    def _inferior(self, w, h):
        a = self.app
        y = h - 116
        self.card((16, y, w - 32, 100))
        erro = a.fase.casefold().startswith('erro') or 'indispon' in a.fase.casefold()
        self.texto(a.fase, 34, y + 12, 16, RED if erro else INK, True, largura=w - 600)
        self.texto(a.status, 34, y + 38, 13, RED if erro else MUTED, largura=w - 600)
        self.botao('iniciar', 'Iniciar entrega', (w - 526, y + 17, 131, 35), ativo=not a.ocupado, destaque=True)
        pausado = getattr(a, '_replay_pausado', False) if a.ocupado else not a.viagem.reproduzindo
        self.botao('pausa', 'Continuar' if pausado else 'Pausar', (w - 386, y + 17, 91, 35), ativo=a.ocupado or bool(a.viagem.pesos))
        self.botao('reiniciar', 'Reiniciar', (w - 286, y + 17, 88, 35), ativo=bool(a.viagem.caminho) and not a.ocupado)
        self.botao('velocidade', f'{a.viagem.velocidade:g}×', (w - 189, y + 17, 55, 35))
        self.botao('reset', 'Centrar', (w - 125, y + 17, 91, 35))
        barra = pygame.Rect(34, y + 74, w - 68, 7)
        pygame.draw.rect(self.canvas, LINE, barra, border_radius=4)
        fracao = a.viagem.custo_atual / a.viagem.total if a.viagem.total else 1 if a.viagem.concluida else 0
        if fracao:
            preenchido = barra.copy()
            preenchido.w = max(1, int(barra.w * fracao))
            pygame.draw.rect(self.canvas, GREEN if a.viagem.concluida else YELLOW, preenchido, border_radius=4)

    def _config(self, w, h):
        pygame.draw.rect(self.canvas, (22, 39, 46, 145), (0, 0, w, h))
        x, y = (w - 440) // 2, (h - 362) // 2
        self.card((x, y, 440, 362))
        self.botoes = {}  # O diálogo captura todos os cliques.
        if self.dist_aberta:
            self._distancias(x, y)
            return
        self.texto('Configurações', x + 25, y + 22, 24, INK, True)
        self.texto('Uma cidade clara, no seu ritmo.', x + 25, y + 61, 13, MUTED)
        for i, (acao, titulo, valor) in enumerate((('pesos', 'Pesos das ruas', self.mostrar_pesos), ('legendas', 'Legendas de origem e destino', self.mostrar_legendas), ('animacao', 'Acompanhar busca passo a passo', self.animar_busca))):
            self.botao(acao, f'{titulo}     {"Ligado" if valor else "Desligado"}', (x + 25, y + 103 + i * 51, 390, 39), selecionado=valor)
        self.texto('Espaço: pausa  ·  Z: centralizar  ·  1 / 2: mapa', x + 25, y + 271, 12, MUTED)
        self.botao('fechar_config', 'Voltar ao mapa', (x + 25, y + 306, 390, 36), destaque=True)

    def _distancias(self, x, y):
        a = self.app
        self.texto('Exploração de Dijkstra', x + 25, y + 22, 22, INK, True)
        self.texto(f'Distâncias a partir do ponto {a.origem}', x + 25, y + 60, 13, MUTED)
        distancias = a.etapa.distancias if a.etapa else a.resultado.distancias if a.resultado else {}
        explorados = set(a.etapa.explorados if a.etapa else a.resultado.explorados if a.resultado else ())
        for i, no in enumerate(a.mapa.ids):
            col, linha = i % 3, i // 3
            d = distancias.get(no, float('inf'))
            xx, yy = x + 25 + col * 132, y + 103 + linha * 29
            pygame.draw.circle(self.canvas, GREEN if no in explorados else BLUE, (xx + 5, yy + 8), 4)
            self.texto(f'{no:02}  ·  {d:g}' if isfinite(d) else f'{no:02}  ·  ∞', xx + 16, yy, 13, INK)
        self.texto('Verde: nó explorado  ·  ∞: ainda sem distância', x + 25, y + 278, 12, MUTED)
        self.botao('fechar_config', 'Voltar ao mapa', (x + 25, y + 306, 390, 36), destaque=True)

    def desenhar(self):
        a = self.app
        w, h = a.win.getXSize(), a.win.getYSize()
        self.canvas = pygame.Surface((w, h), pygame.SRCALPHA)
        self.botoes = {}
        self._grafo()
        self.card((16, 14, w - 32, 62))
        pygame.draw.rect(self.canvas, BLUE, (31, 27, 36, 36), border_radius=10)
        self.texto('N', 39, 25, 25, WHITE, True)
        self.texto('NEXUS', 79, 23, 22, INK, True)
        self.texto('ROTAS & ENTREGAS', 80, 51, 9, MUTED, True)
        self.texto('Cada entrega encontra seu caminho.', 270, 35, 15, MUTED, largura=w - 690)
        self.botao('mapa0', '01  /  Bairro · 5 pontos', (w - 406, 28, 181, 34), selecionado=a.indice_mapa == 0)
        self.botao('mapa1', '02  /  Cidade · 18 pontos', (w - 215, 28, 183, 34), selecionado=a.indice_mapa == 1)
        self._esquerda()
        self._direita(w, h)
        self._inferior(w, h)
        self.texto('VISTA ISOMÉTRICA', 260, 102, 10, MUTED, True)
        self.texto(a.mapa.nome, 260, 123, 16, INK, True)
        if self.config_aberta:
            self._config(w, h)
        if self.textura.getXSize() != w or self.textura.getYSize() != h:
            self.textura.setup2dTexture(w, h, Texture.T_unsigned_byte, Texture.F_rgba)
        # Panda armazena esta textura em BGRA; evitar conversão de cada pixel.
        self.textura.setRamImageAs(pygame.image.tobytes(self.canvas, 'BGRA', True), 'BGRA')
        self.raiz.setScale(w, 1, h)

    def destruir(self):
        self.raiz.removeNode()
