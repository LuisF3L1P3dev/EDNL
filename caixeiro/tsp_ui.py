"""Apresentação Pygame; os algoritmos permanecem em tsp_core."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
import pygame
from tsp_core import carregar_mapa, dijkstra, tsp_forca_bruta, tsp_dijkstra, ErroGrafo, LimiteTSPError
from reprodutor import Reprodutor


ROOT = Path(__file__).resolve().parent
BG = (240, 243, 240)
WHITE = (255, 255, 255)
INK = (27, 43, 35)
MUTED = (103, 122, 111)
LINE = (219, 228, 221)
GREEN = (26, 107, 75)
BLUE = (57, 108, 178)
ORANGE = (200, 117, 76)
PURPLE = (128, 86, 166)
CORES_METODOS = {"forca": GREEN, "dijkstra": BLUE, "fecho": PURPLE}


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
        self.modo_pesos = 0
        self.zoom = 1.0
        self.pan = pygame.Vector2()
        self.arrastando = False
        self.imagens = {}
        self.origem, self.destino = 1, 3
        self.selecao = "origem"
        self.resultados = {}
        self.tempos = {}
        self.historico = []
        self.player = Reprodutor()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.futuro = None
        self.layout()

    @property
    def mapa(self):
        return self.mapas[self.indice_mapa]

    def trocar_mapa(self, indice):
        self.indice_mapa = indice
        self.original = False
        self.zoom = 1.0
        self.pan.update(0, 0)
        self.origem, self.destino = self.mapa.ids[0], self.mapa.ids[2]
        self.selecao = "origem"
        self.limpar()
        self.status = "Mapa selecionado." if self.mapa.validado else "Mapa 18: peso 9–14 ausente; cálculos bloqueados."

    def limpar(self):
        self.resultados = {}
        self.tempos = {}
        self.historico = []
        self.player.carregar(())

    def selecionar_no(self, node_id):
        if self.futuro is not None:
            return
        if self.selecao == "origem":
            self.origem = node_id
            self.selecao = "destino"
        else:
            self.destino = node_id
            self.selecao = "origem"
        self.limpar()
        self.status = f"Origem {self.origem}; destino {self.destino}. Próximo clique define {self.selecao}."

    def iniciar(self, metodo):
        if self.futuro is not None:
            return
        try:
            self.mapa.exigir_validado()
            if metodo != "dijkstra" and len(self.mapa.nos) > 9:
                raise LimiteTSPError("Busca didática limitada a 9 nós.")
        except ErroGrafo as erro:
            self.status = str(erro)
            return
        mapa, origem, destino = self.mapa, self.origem, self.destino
        self.limpar()
        self.status = "Calculando em segundo plano… a janela continua respondendo."

        def calcular():
            eventos, resultados, tempos = [], {}, {}
            metodos = ("forca", "fecho") if metodo == "comparar" else (metodo,)
            for nome in metodos:
                inicio = perf_counter()
                if nome == "dijkstra":
                    r = dijkstra(mapa, origem, destino, eventos=eventos)
                elif nome == "forca":
                    r = tsp_forca_bruta(mapa, origem, eventos=eventos)
                else:
                    r = tsp_dijkstra(mapa, origem, eventos=eventos)
                tempos[nome] = (perf_counter() - inicio) * 1000
                resultados[nome] = r
            return resultados, tempos, eventos

        self.futuro = self.executor.submit(calcular)

    def layout(self):
        w, h = self.tela.get_size()
        self.lateral = pygame.Rect(24, 100, 252, h - 124)
        self.mapa_rect = pygame.Rect(294, 100, w - 318, h - 360)
        self.resultados_rect = pygame.Rect(294, h - 244, w - 318, 220)
        self.viewport = pygame.Rect(self.mapa_rect.x + 16, self.mapa_rect.y + 90,
                                    self.mapa_rect.w - 32, self.mapa_rect.h - 155)
        self.plot = self.viewport.inflate(-26, -12)

    def posicoes(self):
        centro = pygame.Vector2(self.plot.center)
        return {no.id: centro + (pygame.Vector2(self.plot.x + no.x * self.plot.w,
                                     self.plot.y + no.y * self.plot.h) - centro) * self.zoom + self.pan
                for no in self.mapa.nos}

    def mudar_zoom(self, fator, ancora=None):
        ancora = pygame.Vector2(ancora or self.plot.center)
        novo = max(.5, min(4, self.zoom * fator))
        relativo = ancora - pygame.Vector2(self.plot.center)
        self.pan = relativo - (relativo - self.pan) * (novo / self.zoom)
        self.zoom = novo

    @staticmethod
    def distancia_aresta(ponto, a, b):
        delta = b - a
        t = max(0, min(1, (ponto - a).dot(delta) / delta.length_squared())) if delta.length_squared() else 0
        return ponto.distance_to(a + t * delta)

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
        self.texto(f"Origem: {self.origem}    Destino: {self.destino}", (42, 286), 16, INK, True)
        self.texto(f"Clique para definir {self.selecao}", (42, 313), 12, MUTED)
        livre = self.futuro is None
        self.botao("forca", "F  Força bruta exata", (42, 350, 216, 38), ativo=livre)
        self.botao("dijkstra", "D  Dijkstra: origem → destino", (42, 396, 216, 38), BLUE, livre)
        self.botao("comparar", "C  Comparar os dois TSP", (42, 442, 216, 38), ativo=livre)
        self.botao("original", "O  Referência original", (42, 504, 216, 38), MUTED)
        titulo_pesos = ("todos", "do nó", "ocultos")[self.modo_pesos]
        self.botao("pesos", f"P  Pesos: {titulo_pesos}", (42, 550, 216, 38), MUTED)
        self.botao("limpar", "L  Limpar resultados", (42, 596, 216, 38), MUTED, livre)
        passo = self.player.passo
        if passo is None:
            self.linhas("Dijkstra calcula A → B. O caixeiro visita todas as cidades e retorna à origem.",
                        (42, 660), 210, tamanho=13)
        else:
            self.linhas(f"{passo.algoritmo}: {passo.tipo}", (42, 650), 210, 13, INK, 1)
            dist = ", ".join(f"{i}:{d:g}" for i, d in passo.distancias)
            self.linhas(f"Distâncias: {dist}" if dist else f"Candidato: {passo.candidato}", (42, 677), 210, 12, max_linhas=1)
            self.linhas(f"Fila: {passo.fila}" if passo.fila else f"Melhor custo: {passo.melhor_custo}", (42, 704), 210, 12, max_linhas=1)

    def rotas_exibidas(self):
        passo = self.player.passo
        if passo is not None:
            cor = BLUE if passo.algoritmo == "dijkstra" else PURPLE if passo.algoritmo == "tsp_fecho" else GREEN
            return [(passo.caminho or passo.candidato, cor, 4)]
        return [(r.caminho, CORES_METODOS[nome], 7 if nome == "forca" else 3)
                for nome, r in self.resultados.items()]

    def desenhar_mapa(self):
        self.painel(self.mapa_rect)
        self.texto("VISUALIZAÇÃO DO GRAFO", (self.mapa_rect.x + 22, 119), 12, MUTED, True)
        self.texto(f"Mapa {self.indice_mapa + 1} · {len(self.mapa.nos)} cidades", (self.mapa_rect.x + 22, 145), 22, INK, True)
        for i, (chave, titulo) in enumerate((("zoom_menos", "−"), ("zoom_mais", "+"), ("reset", "Z"))):
            self.botao(chave, titulo, (self.mapa_rect.right - 198 + i * 59, 142, 53, 30), MUTED)
        clip_anterior = self.tela.get_clip()
        self.tela.set_clip(self.viewport)
        inspecao = ""
        if self.original:
            if self.mapa.id not in self.imagens:
                self.imagens[self.mapa.id] = pygame.image.load(str(ROOT / self.mapa.referencia)).convert_alpha()
            imagem = self.imagens[self.mapa.id]
            destino = imagem.get_rect().fit(self.plot)
            self.tela.blit(pygame.transform.smoothscale(imagem, destino.size), destino)
        else:
            pos = self.posicoes()
            mouse = pygame.Vector2(pygame.mouse.get_pos())
            hover = next((i for i, p in pos.items() if p.distance_to(mouse) < 22), None) if self.viewport.collidepoint(mouse) else None
            ocupados = [pygame.Rect(p.x - 22, p.y - 22, 44, 44) for p in pos.values()]
            inspecionadas = []
            labels = []
            for aresta in self.mapa.arestas:
                a, b = pos[aresta.origem], pos[aresta.destino]
                cor = LINE if aresta.peso is not None else ORANGE
                pygame.draw.line(self.tela, cor, a, b, 2)
                for caminho, cor_rota, espessura in self.rotas_exibidas():
                    pares = {frozenset((i, j)) for i, j in zip(caminho, caminho[1:])}
                    if frozenset((aresta.origem, aresta.destino)) in pares:
                        pygame.draw.line(self.tela, cor_rota, a, b, espessura)
                passo = self.player.passo
                if passo and passo.relaxamento and frozenset(passo.relaxamento) == frozenset((aresta.origem, aresta.destino)):
                    pygame.draw.line(self.tela, ORANGE, a, b, 5)
                delta = b - a
                normal = pygame.Vector2(-delta.y, delta.x)
                if normal.length():
                    normal.scale_to_length(12)
                titulo = "?" if aresta.peso is None else str(aresta.peso)
                if self.viewport.collidepoint(mouse) and self.distancia_aresta(mouse, a, b) < 6:
                    inspecionadas.append(f"{aresta.origem}–{aresta.destino}: {titulo}")
                if self.modo_pesos != 1 or (hover or self.origem) in (aresta.origem, aresta.destino):
                    labels.append((titulo, (a + b) / 2, normal))
            if self.pesos:
                for titulo, meio, normal in labels:
                    label = self.fonte(13, True).render(titulo, True, MUTED if titulo != "?" else ORANGE)
                    rect = label.get_rect(center=meio + normal)
                    for multiplicador in (1, -1, 2, -2, 3, -3, 0, 4, -4):
                        candidato = label.get_rect(center=meio + normal * multiplicador).inflate(9, 5)
                        if self.viewport.contains(candidato) and not any(candidato.colliderect(r) for r in ocupados):
                            rect = label.get_rect(center=candidato.center)
                            break
                    ocupados.append(rect.inflate(12, 8))
                    if pygame.Vector2(rect.center).distance_to(meio) > 18:
                        pygame.draw.line(self.tela, LINE, meio, rect.center, 1)
                    pygame.draw.rect(self.tela, WHITE, rect.inflate(9, 5), border_radius=4)
                    self.tela.blit(label, rect)
            for node_id, centro in pos.items():
                cor = ORANGE if node_id == self.origem else BLUE if node_id == self.destino else GREEN
                fundo = (220, 233, 248) if self.player.passo and node_id in self.player.passo.visitados else WHITE
                pygame.draw.circle(self.tela, fundo, centro, 17)
                pygame.draw.circle(self.tela, cor, centro, 17, width=3)
                label = self.fonte(15, True).render(str(node_id), True, INK)
                self.tela.blit(label, label.get_rect(center=centro))
            if hover:
                inspecao = f"Nó {hover} · clique para definir {self.selecao}"
            elif inspecionadas:
                inspecao = "Arestas sob o cursor: " + " | ".join(inspecionadas)
        self.tela.set_clip(clip_anterior)
        self.texto(f"{len(self.mapa.arestas)} ligações · pesos fixos · não direcionado",
                   (self.mapa_rect.x + 22, self.mapa_rect.bottom - 28), 12, MUTED)
        legenda = f"Etapa {self.player.indice + 1}/{len(self.historico)} · {self.player.passo.tipo}" if self.player.passo else "Origem: laranja   Destino: azul   TSP direto: verde   Fecho: roxo"
        self.texto(inspecao or legenda,
                   (self.mapa_rect.x + 22, self.mapa_rect.bottom - 49), 12, MUTED)

    def desenhar_resultados(self):
        self.painel(self.resultados_rect)
        x, y = self.resultados_rect.topleft
        self.texto("02  RESULTADOS", (x + 22, y + 17), 12, GREEN, True)
        if self.historico:
            comandos = (("reproduzir", "Play"), ("pausar", "Pausar"), ("voltar", "<"),
                        ("proximo", ">"), ("velocidade", f"{self.player.velocidade:g}x"), ("fim", "Final"))
            for i, (chave, titulo) in enumerate(comandos):
                self.botao(chave, titulo, (x + 190 + i * 73, y + 10, 66, 29), MUTED)
        if not self.resultados:
            self.linhas(self.status, (x + 22, y + 55), self.resultados_rect.w - 44, 15, max_linhas=6)
            return
        largura = (self.resultados_rect.w - 56) // max(1, len(self.resultados))
        titulos = {"forca": "Força bruta · ciclo Hamiltoniano", "dijkstra": "Dijkstra · caminho A → B",
                   "fecho": "Dijkstra + TSP · passeio fechado"}
        for indice, (nome, resultado) in enumerate(self.resultados.items()):
            cx = x + 22 + indice * (largura + 12)
            cor = CORES_METODOS[nome]
            self.texto(titulos[nome], (cx, y + 49), 15, cor, True)
            custo = resultado.custo if resultado.caminho else "sem percurso"
            self.texto(f"Custo: {custo}", (cx, y + 75), 21, INK, True)
            self.texto(f"{self.tempos.get(nome, 0):.3f} ms · com histórico", (cx, y + 106), 12, MUTED)
            rota = " → ".join(map(str, resultado.caminho)) or "Não existe percurso viável."
            self.linhas(rota, (cx, y + 130), largura, 14, cor, max_linhas=2)
            if hasattr(resultado, "estados_testados"):
                self.texto(f"{resultado.estados_testados} ordens testadas · ótimo comprovado", (cx, y + 184), 12, MUTED)

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
            atalhos = {pygame.K_1: "mapa1", pygame.K_2: "mapa2", pygame.K_o: "original", pygame.K_p: "pesos",
                       pygame.K_f: "forca", pygame.K_d: "dijkstra", pygame.K_c: "comparar", pygame.K_l: "limpar", pygame.K_z: "reset"}
            if evento.key in atalhos:
                self.acao(atalhos[evento.key])
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for chave, (rect, ativo) in self.botoes.items():
                if ativo and rect.collidepoint(evento.pos):
                    self.acao(chave)
                    break
            else:
                if self.viewport.collidepoint(evento.pos) and not self.original:
                    for node_id, pos in self.posicoes().items():
                        if pos.distance_to(evento.pos) <= 22:
                            self.selecionar_no(node_id)
                            break
        elif evento.type == pygame.MOUSEWHEEL and self.viewport.collidepoint(pygame.mouse.get_pos()):
            self.mudar_zoom(1.15 ** evento.y, pygame.mouse.get_pos())
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button in (2, 3) and self.viewport.collidepoint(evento.pos):
            self.arrastando = True
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button in (2, 3):
            self.arrastando = False
        elif evento.type == pygame.MOUSEMOTION and self.arrastando:
            self.pan += pygame.Vector2(evento.rel)

    def acao(self, chave):
        if self.futuro is not None and chave not in ("original", "pesos"):
            return
        if chave in ("mapa1", "mapa2"):
            self.trocar_mapa(0 if chave == "mapa1" else 1)
        elif chave == "original":
            self.original = not self.original
        elif chave == "pesos":
            self.modo_pesos = (self.modo_pesos + 1) % 3
            self.pesos = self.modo_pesos != 2
        elif chave == "zoom_mais":
            self.mudar_zoom(1.25)
        elif chave == "zoom_menos":
            self.mudar_zoom(.8)
        elif chave == "reset":
            self.zoom = 1
            self.pan.update(0, 0)
        elif chave in ("forca", "dijkstra", "comparar"):
            self.iniciar(chave)
        elif chave == "limpar":
            self.limpar()
            self.status = "Resultados limpos."
        elif chave in ("reproduzir", "pausar", "proximo", "voltar", "velocidade", "fim"):
            self.player.comando(chave)

    def atualizar(self, dt):
        self.player.atualizar(dt)
        if self.futuro is not None and self.futuro.done():
            try:
                self.resultados, self.tempos, self.historico = self.futuro.result()
                self.player.carregar(self.historico)
                self.status = "Cálculo concluído."
            except Exception as erro:
                self.status = f"Falha no cálculo: {erro}"
            self.futuro = None

    def executar(self):
        while self.rodando:
            dt = self.clock.tick(60) / 1000
            for evento in pygame.event.get():
                self.processar_evento(evento)
            self.atualizar(dt)
            self.desenhar()

    def fechar(self):
        self.executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()
