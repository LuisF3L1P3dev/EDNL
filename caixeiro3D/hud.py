"""HUD Pygame sobre a cena Panda3D, adaptado da base ../caixeiro/tsp_3d.py.

Painéis e eventos da interface não alteram o grafo nem o relógio da viagem.
"""
from math import hypot, isfinite
from functools import lru_cache
from itertools import chain

import pygame
from panda3d.core import CardMaker, Texture, TransparencyAttrib

from geometria3d import NIVEL_GRAMA, medir_rua

INK = (32, 47, 64)
MUTED = (72, 91, 105)
BLUE = (47, 126, 221)
GREEN = (35, 161, 115)
GREEN_TEXT = (22, 113, 80)
YELLOW = (247, 188, 56)
CURRENT = (137, 79, 190)
PASSAGEM = (78, 120, 133)
RED = (184, 45, 57)
WHITE = (253, 254, 251)
LINE = (224, 232, 229)
METHODS = {'forca': 'Força bruta · TSP exato', 'dijkstra': 'Dijkstra · caminho mínimo',
           'circuito': 'Circuito exato · TSP', 'heuristica': 'Passeio heurístico com Dijkstra'}


@lru_cache(maxsize=8)
def _offsets_pins(largura, altura):
    limite = ((max(largura, altura) + 31) // 32) * 32
    offsets = [(x, y) for x in range(-limite, limite + 1, 32)
               for y in range(-limite, limite + 1, 32)]
    return tuple(sorted(offsets, key=lambda d: (d[0]**2 + d[1]**2, d[1], d[0])))


_OFFSETS_PESOS = tuple(sorted(((x, y) for x in range(-144, 145, 16)
                               for y in range(-144, 145, 16)),
                              key=lambda d: (d[0]**2 + d[1]**2, d[1], d[0])))
_OFFSETS_CIDADES = tuple(sorted(((x, y) for x in range(-156, 157, 12)
                                 for y in range(-156, 157, 12) if x*x + y*y <= 156**2),
                                key=lambda d: (d[0]**2 + d[1]**2, d[1], d[0])))


@lru_cache(maxsize=128)
def _amostras_pesos(pontos):
    rua = medir_rua(pontos)
    return tuple(rua.amostrar(f).ponto for f in (.5, .34, .66, .2, .8, .42, .58,
                                                 .12, .88, .27, .73, .05, .95))


class HUD:
    def __init__(self, app):
        self.app = app
        pygame.font.init()
        self.fontes = {}
        self.botoes = {}
        self.posicoes_tela = {}
        self.ancoras_tela = {}
        self.etiquetas_tela = {}
        self.pesos_tela = {}
        self.pesos_ativos = set()
        self._projecao_anterior = None
        self._chave_pesos = None
        self.config_aberta = False
        self.mostrar_pesos = True
        self.mostrar_legendas = True
        self.animar_busca = True
        self.mostrar_percurso = False
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
        elif acao == 'alternar_percurso':
            self.mostrar_percurso = not self.mostrar_percurso
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
        if a.viagem.pesos and not a.viagem.concluida:
            indice, _ = a.viagem.trecho
            selecionadas = {frozenset(a.viagem.caminho[indice:indice + 2])}
        else:
            selecionadas = {frozenset((u, v)) for u, v in zip(caminho, caminho[1:])}
        self.posicoes_tela = {}
        self.ancoras_tela = {}
        self.etiquetas_tela = {}
        self.pesos_tela = {}
        self.pesos_ativos = set()
        explorados = set(a.etapa.explorados if a.etapa else ())
        entregas = a.viagem.visitadas
        passagens = a.viagem.passagens
        controles = self._area_controles()
        if not a.viagem.caminho:
            atual = a.origem
        elif a.viagem.concluida:
            atual = a.viagem.caminho[-1]
        else:
            indice_atual, fracao = a.viagem.trecho
            atual = a.viagem.caminho[indice_atual] if fracao <= 1e-9 else None
        ocupadas_pins = [pygame.Rect(258, 100, 230, 50), controles]
        projecao = getattr(a.camera_iso, 'chave_projecao', None)
        chave = (a.cena, projecao)
        if projecao is None or chave != self._projecao_anterior:
            self._edificios_tela = self._construcoes_tela(viewport)
            self._projecao_anterior = chave
            self._chave_pesos = None
        cidades = getattr(a.cena, 'cidades', {})
        nos = sorted(a.cena.mapa_visual.nos, key=lambda n: (n.id != a.origem, n.id))
        marcadores = getattr(a.cena, 'marcadores_no', {})
        offsets = _offsets_pins(viewport.w, viewport.h)
        tem_rotatorias = bool(getattr(a.cena, 'rotatorias', ()))
        proximos = _OFFSETS_CIDADES if cidades or tem_rotatorias else tuple(
            d for d in offsets if d[0]**2 + d[1]**2 <= 64**2)
        for no_visual in nos:
            no = no_visual.id
            p = a.camera_iso.projetar(marcadores.get(no, no_visual.posicao_marcador))
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
            dx, dy = no_visual.deslocamento_etiqueta
            centro_x = round(max(viewport.left + margem_x + 2,
                                 min(viewport.right - margem_x - 2, p[0] + dx)))
            deslocamento_y = abs(dy)
            margem_y = 44 if label else 23
            abaixo = dy > 0 or p[1] - deslocamento_y - margem_y < viewport.top + 2
            if abaixo and p[1] + deslocamento_y + margem_y > viewport.bottom - 2:
                abaixo = False
            # O título da cena também fica dentro do viewport. Quando a
            # origem está no canto superior esquerdo, a etiqueta acima do pin
            # invadiria “Cidade das rotas”; neste caso a haste a leva abaixo.
            titulo_cena = pygame.Rect(258, 100, 230, 50)
            etiqueta_acima = pygame.Rect(round(centro_x - largura_label / 2),
                                         round(p[1] - deslocamento_y - 43), largura_label, 18)
            if label and etiqueta_acima.colliderect(titulo_cena):
                abaixo = True
            cima, baixo = (23, 44) if abaixo and label else (44, 23) if label else (23, 23)
            centro = (
                centro_x,
                round(max(viewport.top + cima + 2, min(viewport.bottom - baixo - 2,
                      p[1] + deslocamento_y if abaixo else p[1] - deslocamento_y))),
            )
            # Primeiro tenta a posicao preferida, depois aneis progressivos.
            preferido = centro
            escolhido = None
            candidatos = chain(((x, y, True) for x, y in proximos),
                               ((x, y, True) for x, y in offsets) if tem_rotatorias else (),
                               ((x, y, False) for x, y in offsets))
            for ox, oy, evitar_edificios in candidatos:
                cx = round(max(viewport.left + margem_x + 2,
                               min(viewport.right - margem_x - 2, preferido[0] + ox)))
                cy = round(max(viewport.top + cima + 2,
                               min(viewport.bottom - baixo - 2, preferido[1] + oy)))
                caixa = pygame.Rect(cx - 23, cy - 23, 46, 46)
                if label:
                    legenda = pygame.Rect(cx - largura_label // 2,
                                          cy + 25 if abaixo else cy - 43, largura_label, 18)
                    caixa.union_ip(legenda)
                if (not caixa.collidepoint(p) and caixa.collidelist(ocupadas_pins) < 0
                        and (not evitar_edificios or caixa.collidelist(self._edificios_tela) < 0)):
                    escolhido = (cx, cy)
                    break
            if escolhido is not None:
                centro = escolhido
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
            if no in passagens:
                cor = PASSAGEM
            elif no == atual:
                cor = CURRENT
            elif no in entregas:
                cor = GREEN
            else:
                cor = YELLOW if no in explorados and a.ocupado else BLUE
            pygame.draw.circle(self.canvas, (35, 63, 66, 65), (centro[0], centro[1] + 3), 18)
            pygame.draw.circle(self.canvas, WHITE, centro, 18)
            pygame.draw.circle(self.canvas, cor, centro, 15)
            tinta = INK if cor == YELLOW else WHITE
            if no in cidades:
                sigla = self.fonte(8, True).render('NÓ', True, tinta)
                self.canvas.blit(sigla, sigla.get_rect(center=(centro[0], centro[1] - 6)))
                img = self.fonte(13, True).render(f'{no:02}', True, tinta)
                self.canvas.blit(img, img.get_rect(center=(centro[0], centro[1] + 4)))
            else:
                img = self.fonte(14, True).render(str(no), True, tinta)
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
            ocupadas_pins.append(box)
        if self.mostrar_pesos:
            self._desenhar_pesos(viewport, selecionadas)
        if a.viagem.em_chegada:
            p = a.camera_iso.projetar(tuple(a.carro.getPos(a.render)))
            if p:
                pygame.draw.circle(self.canvas, GREEN, tuple(map(int, p)), 27, 3)
        self.canvas.set_clip(None)

    def _construcoes_tela(self, viewport):
        """Retangulos conservadores das construcoes reais projetadas."""
        caixas = []
        for d in getattr(self.app.cena, 'decoracoes', ()):
            if d.tipo not in ('edificio', 'placa'):
                continue
            hx, hy = getattr(d, 'semieixos', None) or (d.raio, d.raio)
            base_z = NIVEL_GRAMA + (.59 if d.tipo == 'placa' else 0.)
            pontos = [self.app.camera_iso.projetar((d.x + x, d.y + y, z))
                      for x in (-hx, hx) for y in (-hy, hy)
                      for z in (base_z, NIVEL_GRAMA + d.altura)]
            pontos = [p for p in pontos if p is not None]
            if pontos:
                x0, x1 = min(p[0] for p in pontos), max(p[0] for p in pontos)
                y0, y1 = min(p[1] for p in pontos), max(p[1] for p in pontos)
                caixa = pygame.Rect(int(x0), int(y0), max(1, int(x1-x0)+2), max(1, int(y1-y0)+2))
                if caixa.colliderect(viewport):
                    caixas.append(caixa)
        return caixas

    def _desenhar_pesos(self, viewport, selecionadas):
        """Posiciona pesos próximos à sua rua sem encobrir pins ou outros pesos."""
        chave = (frozenset(selecionadas), tuple(tuple(r) for r in self.etiquetas_tela.values()))
        if chave != self._chave_pesos:
            self._layout_pesos = self._posicionar_pesos(viewport, selecionadas)
            self._chave_pesos = chave
        self.pesos_ativos = set(selecionadas)
        for par, texto, caixa, ligacao in self._layout_pesos:
            if ligacao:
                pygame.draw.line(self.canvas, (80, 96, 100, 150), *ligacao, 1)
            ativa = frozenset(par) in selecionadas
            pygame.draw.rect(self.canvas, (255, 244, 197) if ativa else (252, 253, 248, 235),
                             caixa, border_radius=6)
            pygame.draw.rect(self.canvas, YELLOW if ativa else LINE, caixa, 1, border_radius=6)
            self.texto(texto, caixa.x + 7, caixa.y + 2, 12, INK, True)
            self.pesos_tela[par] = caixa

    def _posicionar_pesos(self, viewport, selecionadas):
        a = self.app
        ocupadas = list(self.etiquetas_tela.values()) + [pygame.Rect(258, 100, 230, 50),
                                                        self._area_controles()]
        ocupadas.extend(self._edificios_tela)
        fonte = self.fonte(12, True)
        arestas = sorted(a.mapa.arestas, key=lambda e: frozenset((e.origem, e.destino)) not in selecionadas)
        layout = []
        eixos = a.cena.mapa_visual.eixos_pavimento
        for e in arestas:
            texto = f'{e.peso:g}'
            tamanho = fonte.size(texto)
            escolhido = None
            amostras = _amostras_pesos(eixos[e.origem, e.destino])
            projetados = [a.camera_iso.projetar(ponto) for ponto in amostras]
            projetados = [p for p in projetados if p is not None]
            if not projetados:
                continue
            box = pygame.Rect(0, 0, tamanho[0] + 14, 22)
            for dx, dy in _OFFSETS_PESOS:
                for projetado in projetados:
                    box.center = round(projetado[0] + dx), round(projetado[1] + dy)
                    if viewport.contains(box) and box.collidelist(ocupadas) < 0:
                        escolhido = box.copy()
                        ancora_peso = projetado
                        break
                if escolhido:
                    break
            if escolhido is None:
                # Ultimo recurso: procurar espaco livre em toda a area visivel.
                pontos_visiveis = [p for p in projetados if p and viewport.collidepoint(p)]
                melhor = float('inf')
                if pontos_visiveis:
                    for y in range(viewport.top, viewport.bottom - box.h + 1, 8):
                        for x in range(viewport.left, viewport.right - box.w + 1, 8):
                            box.topleft = x, y
                            if box.collidelist(ocupadas) >= 0:
                                continue
                            referencia = min(pontos_visiveis, key=lambda p: (p[0]-box.centerx)**2 + (p[1]-box.centery)**2)
                            distancia = (referencia[0]-box.centerx)**2 + (referencia[1]-box.centery)**2
                            if distancia < melhor:
                                melhor, escolhido, ancora_peso = distancia, box.copy(), referencia
                    if escolhido:
                        dx, dy = escolhido.centerx - ancora_peso[0], escolhido.centery - ancora_peso[1]
            if escolhido is None:
                continue
            ligacao = None
            if hypot(dx, dy) > 22:
                ponta = (max(escolhido.left, min(escolhido.right, round(ancora_peso[0]))),
                         max(escolhido.top, min(escolhido.bottom, round(ancora_peso[1]))))
                inicio = tuple(map(round, ancora_peso))
                if viewport.collidepoint(inicio) and not any(r.clipline(inicio, ponta) for r in ocupadas):
                    ligacao = inicio, ponta
            layout.append(((e.origem, e.destino), texto, escolhido, ligacao))
            ocupadas.append(escolhido)
        return layout

    def _esquerda(self):
        a = self.app
        self.card((16, 94, 212, 540))
        self.texto('PLANEJAR ENTREGA', 32, 112, 10, MUTED, True)
        self.texto('Sua próxima rota', 32, 135, 19, INK, True)
        self.texto('ALGORITMO', 32, 173, 10, MUTED, True)
        circuito = ('forca', 'Força bruta · exato') if a.indice_mapa == 0 else ('circuito', 'Circuito exato · TSP')
        opcoes = (circuito, ('dijkstra', 'Dijkstra · A → B'), ('heuristica', 'Passeio · aceita revisitas'))
        for i, (chave, titulo) in enumerate(opcoes):
            disponivel = a.indice_mapa == 1 or chave != 'heuristica'
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
            self.card((16, y, 212, 128))
            self.texto('LEGENDA DO MAPA', 32, y + 14, 10, MUTED, True)
            for i, (cor, label) in enumerate(((BLUE, 'Ponto de entrega'), (YELLOW, 'Rota / exploração'),
                                              (GREEN, 'Entrega concluída'), (PASSAGEM, 'Passagem intermediária'),
                                              (CURRENT, 'Ponto atual'))):
                pygame.draw.circle(self.canvas, cor, (39, y + 41 + i * 17), 5)
                self.texto(label, 52, y + 32 + i * 17, 13, MUTED)
        else:
            for x, y_item, cor, label in ((37, 603, BLUE, 'Ponto'),
                                           (98, 603, YELLOW, 'Rota'),
                                           (157, 603, CURRENT, 'Atual'),
                                           (37, 625, GREEN, 'Entregue'),
                                           (125, 625, PASSAGEM, 'Passagem')):
                pygame.draw.circle(self.canvas, cor, (x, y_item), 4)
                self.texto(label, x + 8, y_item - 9, 12, MUTED)


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
        total_entregas = len(set(a.viagem.ordem_visita)) or len(a.mapa.ids)
        self.texto(f'Entregas: {len(a.viagem.visitadas)} / {total_entregas}', x + 16, 342, 13, MUTED)
        self.texto(f'Distância: {a.distancia_percorrida:.1f} u.', x + 16, 365, 13, MUTED)
        tempo = a.resultado.tempo_ms if a.resultado else None
        self.texto('Cálculo: —' if tempo is None else f'Cálculo: {tempo:.2f} ms', x + 16, 388, 13, MUTED)
        caminho, entregas = a.viagem.caminho, a.viagem.ordem_visita
        expandido = bool(caminho and caminho != entregas)
        fisico = expandido and self.mostrar_percurso
        titulo = 'PERCURSO FÍSICO' if fisico else 'ORDEM DE ENTREGA' if caminho else 'PRÉVIA DA ROTA'
        self.texto(titulo, x + 16, 424, 10, MUTED, True)
        sequencia = caminho if fisico else entregas
        if not caminho and a.etapa:
            sequencia = a.etapa.caminho
        linhas = self.linhas(' → '.join(map(str, sequencia)) if sequencia else 'Aguardando sua partida.',
                             x + 16, 447, 186, 13, INK, 6)
        if expandido:
            self.botao('alternar_percurso', 'Ver ordem de entrega' if fisico else 'Ver percurso físico',
                       (x + 16, 447 + linhas + 3, 186, 26))
        elif caminho:
            self.texto('Percurso físico segue a ordem acima', x + 16, 447 + linhas + 5, 11, MUTED,
                       largura=186)
        garantia = a.resultado.garantia if a.resultado else (
            'Heurística: sem garantia de ótimo global.' if a.metodo == 'heuristica' else
            'Caminho mínimo entre dois pontos.' if a.metodo == 'dijkstra' else
            'Busca exata de circuito Hamiltoniano.')
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

    def _texto_trecho(self):
        """Resumo curto e estável da posição da van na rota exibida."""
        viagem = self.app.viagem
        if not viagem.caminho:
            return f'No ponto {self.app.origem} · aguardando rota'
        if not viagem.pesos:
            return f'Concluído no ponto {viagem.caminho[0]}'
        indice, _ = viagem.trecho
        origem, destino = viagem.caminho[indice:indice + 2]
        if viagem.concluida:
            return f'Concluído no ponto {destino} · último: {origem} → {destino}'
        if viagem.em_chegada:
            return f'Aguardando no ponto {origem} · próximo: {origem} → {destino}'
        if viagem.reproduzindo:
            return f'Em rota: {origem} → {destino}'
        return f'Pausada: {origem} → {destino}'

    def _inferior(self, w, h):
        a = self.app
        y = h - 116
        self.card((16, y, w - 32, 100))
        erro = a.fase.casefold().startswith('erro') or 'indispon' in a.fase.casefold()
        self.texto(a.fase, 34, y + 12, 16, RED if erro else INK, True, largura=w - 600)
        self.texto(a.status, 34, y + 38, 13, RED if erro else MUTED, largura=w - 600)
        self.texto(self._texto_trecho(), 34, y + 57, 12, GREEN_TEXT if a.viagem.caminho else MUTED,
                   largura=w - 600)
        self.botao('iniciar', 'Iniciar entrega', (w - 526, y + 17, 131, 35), ativo=not a.ocupado, destaque=True)
        pausado = getattr(a, '_replay_pausado', False) if a.ocupado else not a.viagem.reproduzindo
        self.botao('pausa', 'Continuar' if pausado else 'Pausar', (w - 386, y + 17, 91, 35), ativo=a.ocupado or bool(a.viagem.pesos))
        self.botao('reiniciar', 'Reiniciar', (w - 286, y + 17, 88, 35), ativo=bool(a.viagem.caminho) and not a.ocupado)
        self.botao('velocidade', f'{a.viagem.velocidade:g}×', (w - 189, y + 17, 55, 35))
        barra = pygame.Rect(34, y + 74, w - 68, 7)
        pygame.draw.rect(self.canvas, LINE, barra, border_radius=4)
        fracao = a.progresso_visual
        if fracao:
            preenchido = barra.copy()
            preenchido.w = max(1, int(barra.w * fracao))
            pygame.draw.rect(self.canvas, GREEN if a.viagem.concluida else YELLOW, preenchido, border_radius=4)

    def _area_controles(self):
        viewport = self.app.camera_iso.viewport
        return pygame.Rect(viewport.right - 216, viewport.top + 10, 206, 84)

    def _controles_mapa(self):
        r = self._area_controles()
        camera = self.app.camera_iso
        self.card(r)
        self.botao('zoom-', '−', (r.x + 5, r.y + 5, 32, 34), ativo=camera.zoom > camera.ZOOM_MIN)
        percentual = self.fonte(12, True).render(f'{round(camera.zoom * 100)}%', True, INK)
        self.canvas.blit(percentual, percentual.get_rect(center=(r.x + 64, r.y + 22)))
        self.botao('zoom+', '+', (r.x + 91, r.y + 5, 32, 34), ativo=camera.zoom < camera.ZOOM_MAX)
        self.botao('reset', 'Centrar', (r.x + 128, r.y + 5, 73, 34))
        self.botao('acompanhar', 'Acompanhar veículo', (r.x + 5, r.y + 44, 196, 34),
                   selecionado=getattr(self.app, 'acompanhando', False))

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
        self.botao('mapa1', '02  /  Região · 18 cidades', (w - 215, 28, 183, 34), selecionado=a.indice_mapa == 1)
        self._esquerda()
        self._direita(w, h)
        self._inferior(w, h)
        self.texto('VISTA ISOMÉTRICA', 260, 102, 10, MUTED, True)
        self.texto(a.mapa.nome, 260, 123, 16, INK, True)
        self._controles_mapa()
        if self.config_aberta:
            self._config(w, h)
        if self.textura.getXSize() != w or self.textura.getYSize() != h:
            self.textura.setup2dTexture(w, h, Texture.T_unsigned_byte, Texture.F_rgba)
        # Panda armazena esta textura em BGRA; evitar conversão de cada pixel.
        self.textura.setRamImageAs(pygame.image.tobytes(self.canvas, 'BGRA', True), 'BGRA')
        self.raiz.setScale(w, 1, h)

    def destruir(self):
        self.raiz.removeNode()
