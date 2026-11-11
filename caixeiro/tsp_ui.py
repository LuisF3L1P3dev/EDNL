"""Apresentação Pygame; os algoritmos permanecem em tsp_core."""
from pathlib import Path
import pygame
from tsp_core import carregar_mapa


ROOT = Path(__file__).resolve().parent
BG = (240, 243, 240)
WHITE = (255, 255, 255)
INK = (27, 43, 35)
MUTED = (103, 122, 111)
LINE = (219, 228, 221)
GREEN = (26, 107, 75)
BLUE = (57, 108, 178)
ORANGE = (200, 117, 76)


class Aplicacao:
    def __init__(self, tamanho=(1280, 860)):
        pygame.init()
        pygame.display.set_caption("NEXUS TSP | Grafos ponderados")
        self.tela = pygame.display.set_mode(tamanho, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.fontes = {}
        self.botoes = {}
        self.rodando = True
        self.status = "Pronto para explorar os grafos da aula."
        self.mapas = tuple(carregar_mapa(ROOT / "data" / nome) for nome in ("mapa_05.json", "mapa_18.json"))
        self.indice_mapa = 0
        self.original = False
        self.pesos = True
        self.imagens = {}
        self.layout()

    @property
    def mapa(self):
        return self.mapas[self.indice_mapa]

    def trocar_mapa(self, indice):
        self.indice_mapa = indice
        self.original = False
        self.status = "Mapa selecionado." if self.mapa.validado else "Mapa 18: peso 9–14 ausente; cálculos bloqueados."

    def layout(self):
        w, h = self.tela.get_size()
        self.lateral = pygame.Rect(24, 100, 252, h - 124)
        self.mapa_rect = pygame.Rect(294, 100, w - 318, h - 360)
        self.resultados_rect = pygame.Rect(294, h - 244, w - 318, 220)
        self.plot = self.mapa_rect.inflate(-80, -130)
        self.plot.y += 20

    def posicoes(self):
        return {no.id: pygame.Vector2(self.plot.x + no.x * self.plot.w,
                                     self.plot.y + no.y * self.plot.h) for no in self.mapa.nos}

    def fonte(self, tamanho=16, bold=False):
        chave = (tamanho, bold)
        if chave not in self.fontes:
            self.fontes[chave] = pygame.font.SysFont("segoeui", tamanho, bold=bold)
        return self.fontes[chave]

    def texto(self, texto, pos, tamanho=16, cor=INK, bold=False):
        imagem = self.fonte(tamanho, bold).render(str(texto), True, cor)
        self.tela.blit(imagem, pos)
        return imagem.get_rect(topleft=pos)

    def linhas(self, texto, pos, largura, tamanho=15, cor=MUTED, max_linhas=6):
        x, y = pos
        linhas = []
        atual = ""
        for palavra in str(texto).split():
            tentativa = f"{atual} {palavra}".strip()
            if atual and self.fonte(tamanho).size(tentativa)[0] > largura:
                linhas.append(atual)
                atual = palavra
            else:
                atual = tentativa
        if atual:
            linhas.append(atual)
        for linha in linhas[:max_linhas]:
            self.texto(linha, (x, y), tamanho, cor)
            y += tamanho + 6
        return y

    def painel(self, rect):
        pygame.draw.rect(self.tela, WHITE, rect, border_radius=14)
        pygame.draw.rect(self.tela, LINE, rect, width=1, border_radius=14)

    def botao(self, chave, titulo, rect, cor=GREEN, ativo=True):
        self.botoes[chave] = (pygame.Rect(rect), ativo)
        r = pygame.Rect(rect)
        hover = ativo and r.collidepoint(pygame.mouse.get_pos())
        fundo = cor if ativo else (194, 204, 197)
        if hover:
            fundo = tuple(min(255, c + 15) for c in fundo)
        pygame.draw.rect(self.tela, fundo, r, border_radius=8)
        imagem = self.fonte(15, True).render(titulo, True, WHITE)
        self.tela.blit(imagem, imagem.get_rect(center=r.center))

    def desenhar_lateral(self):
        self.painel(self.lateral)
        self.texto("01  CONFIGURAÇÃO", (42, 119), 12, GREEN, True)
        self.texto("Percurso da aula", (42, 147), 21, INK, True)
        self.botao("mapa1", "1  Mapa de 5 nós", (42, 185, 216, 38))
        self.botao("mapa2", "2  Mapa de 18 nós", (42, 231, 216, 38), BLUE)
        self.botao("original", "O  Referência original", (42, 295, 216, 38), MUTED)
        self.botao("pesos", "P  Mostrar / ocultar pesos", (42, 341, 216, 38), MUTED)
        self.linhas("As posições servem ao desenho. Os pesos são os valores fixos da aula.",
                    (42, 410), 210)

    def desenhar_mapa(self):
        self.painel(self.mapa_rect)
        self.texto("VISUALIZAÇÃO DO GRAFO", (self.mapa_rect.x + 22, 119), 12, MUTED, True)
        self.texto(f"Mapa {self.indice_mapa + 1} · {len(self.mapa.nos)} cidades", (self.mapa_rect.x + 22, 145), 22, INK, True)
        if self.original:
            if self.mapa.id not in self.imagens:
                self.imagens[self.mapa.id] = pygame.image.load(str(ROOT / self.mapa.referencia)).convert_alpha()
            imagem = self.imagens[self.mapa.id]
            destino = imagem.get_rect().fit(self.plot)
            self.tela.blit(pygame.transform.smoothscale(imagem, destino.size), destino)
        else:
            pos = self.posicoes()
            labels = []
            for aresta in self.mapa.arestas:
                a, b = pos[aresta.origem], pos[aresta.destino]
                cor = LINE if aresta.peso is not None else ORANGE
                pygame.draw.line(self.tela, cor, a, b, 2)
                delta = b - a
                normal = pygame.Vector2(-delta.y, delta.x)
                if normal.length():
                    normal.scale_to_length(12)
                labels.append(("?" if aresta.peso is None else str(aresta.peso), (a + b) / 2 + normal))
            if self.pesos:
                for titulo, centro in labels:
                    label = self.fonte(13, True).render(titulo, True, MUTED if titulo != "?" else ORANGE)
                    rect = label.get_rect(center=centro)
                    pygame.draw.rect(self.tela, WHITE, rect.inflate(9, 5), border_radius=4)
                    self.tela.blit(label, rect)
            for node_id, centro in pos.items():
                pygame.draw.circle(self.tela, WHITE, centro, 17)
                pygame.draw.circle(self.tela, GREEN, centro, 17, width=2)
                label = self.fonte(15, True).render(str(node_id), True, INK)
                self.tela.blit(label, label.get_rect(center=centro))
        self.texto(f"{len(self.mapa.arestas)} ligações · pesos fixos · não direcionado",
                   (self.mapa_rect.x + 22, self.mapa_rect.bottom - 28), 12, MUTED)

    def desenhar_resultados(self):
        self.painel(self.resultados_rect)
        x, y = self.resultados_rect.topleft
        self.texto("02  RESULTADOS", (x + 22, y + 17), 12, GREEN, True)
        self.linhas(self.status, (x + 22, y + 55), self.resultados_rect.w - 44, 16)

    def desenhar(self):
        self.botoes.clear()
        self.tela.fill(BG)
        self.texto("NEXUS / ESTRUTURA DE DADOS NÃO LINEARES", (26, 16), 11, GREEN, True)
        self.texto("Caixeiro viajante", (24, 35), 32, INK, True)
        self.texto("Grafos ponderados · Dijkstra · Força bruta", (320, 54), 15, MUTED)
        self.desenhar_lateral()
        self.desenhar_mapa()
        self.desenhar_resultados()
        pygame.display.flip()

    def processar_evento(self, evento):
        if evento.type == pygame.QUIT or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE):
            self.rodando = False
        elif evento.type == pygame.VIDEORESIZE:
            self.tela = pygame.display.set_mode((max(1000, evento.w), max(760, evento.h)), pygame.RESIZABLE)
            self.layout()
        elif evento.type == pygame.KEYDOWN:
            atalhos = {pygame.K_1: "mapa1", pygame.K_2: "mapa2", pygame.K_o: "original", pygame.K_p: "pesos"}
            if evento.key in atalhos:
                self.acao(atalhos[evento.key])
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for chave, (rect, ativo) in self.botoes.items():
                if ativo and rect.collidepoint(evento.pos):
                    self.acao(chave)
                    break

    def acao(self, chave):
        if chave in ("mapa1", "mapa2"):
            self.trocar_mapa(0 if chave == "mapa1" else 1)
        elif chave == "original":
            self.original = not self.original
        elif chave == "pesos":
            self.pesos = not self.pesos

    def atualizar(self, dt):
        pass

    def executar(self):
        while self.rodando:
            dt = self.clock.tick(60) / 1000
            for evento in pygame.event.get():
                self.processar_evento(evento)
            self.atualizar(dt)
            self.desenhar()

    def fechar(self):
        pygame.quit()
