"""Interface Pygame para Dijkstra e força bruta."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from queue import SimpleQueue, Empty
from time import perf_counter
from threading import Event
import pygame
from tsp_core import carregar_mapa, ErroGrafo, LimiteTSPError
from reprodutor import Reprodutor
from identidade_algoritmos import METODOS, garantia_resultado
from solvers import executar, disponibilidade, MODELOS, REGISTRO, ORIGINAL, CAMINHO, Orcamento


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
CORES_METODOS = {chave: metodo.cor for chave, metodo in METODOS.items()}


class Aplicacao:
    def __init__(self, tamanho=(1360, 940)):
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
        self.metodo_selecionado = "dijkstra"
        self.metodo_em_execucao = None
        self.estado_execucao = "pronto"
        self.fase_execucao = "Selecione Dijkstra ou força bruta."
        self.resultado_focado = None
        self.progresso = SimpleQueue()
        self.cancelar = Event()
        self.variante = ORIGINAL
        self.limite_segundos = 5.0
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
        self.resultado_focado = None
        self.estado_execucao = "pronto"
        self.metodo_em_execucao = None
        self.fase_execucao = "Pronto para executar o método selecionado."
        motivo = self.motivo_indisponivel(self.metodo_selecionado)
        if motivo:
            self.estado_execucao = "bloqueado"
            self.fase_execucao = motivo

    def variante_metodo(self, nome):
        return {"dijkstra": CAMINHO, "forca": ORIGINAL}.get(nome, ORIGINAL)

    def motivo_indisponivel(self, nome):
        return disponibilidade(nome, self.mapa, self.variante_metodo(nome))

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
        if metodo not in METODOS:
            self.status = f"Método indisponível: {metodo}"
            return
        self.metodo_selecionado = metodo
        self.limpar()
        try:
            self.mapa.exigir_validado()
            motivo = self.motivo_indisponivel(metodo)
            if motivo:
                raise LimiteTSPError(motivo)
        except ErroGrafo as erro:
            self.status = str(erro)
            self.estado_execucao = "bloqueado"
            self.fase_execucao = self.status
            return
        mapa, origem, destino = self.mapa, self.origem, self.destino
        self.estado_execucao = "executando"
        self.metodo_em_execucao = metodo
        self.fase_execucao = "Preparando a execução."
        self.status = f"Executando {METODOS[metodo].titulo}. A janela continua respondendo."
        self.progresso = SimpleQueue()
        progresso = self.progresso
        self.cancelar = Event()
        cancelar = self.cancelar
        variante = self.variante_metodo(metodo)
        orcamento = Orcamento(segundos=self.limite_segundos)

        def calcular():
            eventos, resultados, tempos = [], {}, {}
            progresso.put((metodo, "Calculando o percurso"))
            informar = lambda fase: progresso.put((metodo, fase))
            r = executar(metodo, mapa, origem, destino=destino, variante=variante, orcamento=orcamento,
                         cancelar=cancelar, progresso=informar)
            tempos[metodo] = dict(r.tempos_ms)["total"]
            eventos.extend(r.eventos)
            resultados[metodo] = r
            return resultados, tempos, eventos

        self.futuro = self.executor.submit(calcular)

    def layout(self):
        w, h = self.tela.get_size()
        self.lateral = pygame.Rect(24, 100, 280, h - 124)
        self.mapa_rect = pygame.Rect(322, 100, w - 346, h - 360)
        self.resultados_rect = pygame.Rect(322, h - 244, w - 346, 220)
        self.faixa_algoritmo = pygame.Rect(self.mapa_rect.x + 16, 180, self.mapa_rect.w - 32,
                                          94 if h >= 860 else 78)
        self.viewport = pygame.Rect(self.mapa_rect.x + 16, self.faixa_algoritmo.bottom + 12,
                                    self.mapa_rect.w - 32, self.mapa_rect.bottom - self.faixa_algoritmo.bottom - 77)
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

    def texto_ajustado(self, texto, pos, largura, tamanho=16, cor=INK, bold=False):
        texto = str(texto)
        while tamanho > 11 and self.fonte(tamanho, bold).size(texto)[0] > largura:
            tamanho -= 1
        if self.fonte(tamanho, bold).size(texto)[0] > largura:
            while texto and self.fonte(tamanho, bold).size(texto + "…")[0] > largura:
                texto = texto[:-1]
            texto += "…"
        return self.texto(texto, pos, tamanho, cor, bold)

    def identidade_visual(self):
        """Estado sem dependência de cores; preserva a origem de cada etapa."""
        chave = self.metodo_selecionado
        estado = {"pronto": "Pronto", "concluido": "Concluído", "bloqueado": "Indisponível", "erro": "Erro", "cancelado": "Cancelado", "limitado": "Limite atingido"}.get(self.estado_execucao, "Pronto")
        fase = self.fase_execucao
        if self.futuro is not None:
            estado = "Em execução"
            atual = self.metodo_em_execucao or chave
            fase = f"{METODOS[atual].curto} · {self.fase_execucao}"
        elif self.player.passo is not None:
            passo = self.player.passo
            chave = passo.metodo_origem or {"forca_bruta": "forca", "dijkstra": "dijkstra"}.get(passo.algoritmo, chave)
            estado = "Reproduzindo" if self.player.reproduzindo else "Pausado"
            etapa = "Dijkstra" if passo.algoritmo == "dijkstra" else METODOS[chave].curto
            tipos = {"inicio": "inicialização", "visita": "visitando cidade", "relaxamento": "atualizando distância",
                     "candidato": "avaliando ordem de visitas", "fim": "resultado", "sem_caminho": "destino inalcançável"}
            fase = f"{etapa}: {tipos.get(passo.tipo, passo.tipo)} · etapa {self.player.indice + 1}/{len(self.historico)}"
        elif self.resultado_focado in self.resultados:
            chave = self.resultado_focado
            fase = "Percurso selecionado no painel de resultados."
            termino = getattr(self.resultados[chave], "termino", "")
            estado = "Cancelado" if termino == "cancelado" else "Limite atingido" if termino.startswith("limite_") else "Indisponível" if termino == "indisponivel" else "Concluído"
        elif self.resultados:
            fase = "Clique em um resultado para destacar o percurso." if len(self.resultados) > 1 else "Resultado e percurso exibidos abaixo."
        metodo = METODOS[chave]
        resultado = self.resultados.get(chave)
        modo = getattr(resultado, "variante", self.variante_metodo(chave))
        problema = MODELOS.get(modo, metodo.problema)
        garantia = garantia_resultado(chave, resultado) if resultado is not None else metodo.garantia
        return {"metodo": chave, "titulo": metodo.titulo, "estado": estado,
                "fase": fase, "problema": problema, "garantia": garantia, "cor": metodo.cor}

    def desenhar_identidade(self):
        identidade = self.identidade_visual()
        r = self.faixa_algoritmo
        cor = identidade["cor"]
        fundo = tuple(round(255 * .93 + c * .07) for c in cor)
        pygame.draw.rect(self.tela, fundo, r, border_radius=10)
        pygame.draw.rect(self.tela, cor, (r.x, r.y + 10, 4, r.h - 20), border_radius=2)
        compacto = r.h < 90
        self.texto("ALGORITMO EM FOCO", (r.x + 15, r.y + (6 if compacto else 9)), 10, MUTED, True)
        pill = pygame.Rect(r.right - 142, r.y + 6, 128, 21)
        pygame.draw.rect(self.tela, cor, pill, border_radius=7)
        label = self.fonte(10, True).render(identidade["estado"].upper(), True, WHITE)
        self.tela.blit(label, label.get_rect(center=pill.center))
        self.texto_ajustado(identidade["titulo"], (r.x + 15, r.y + (23 if compacto else 29)), r.w - 30, 19, cor, True)
        self.texto_ajustado(identidade["fase"], (r.x + 15, r.y + (46 if compacto else 55)), r.w - 30, 13, INK)
        self.texto_ajustado(f"{identidade['problema']} · {identidade['garantia']}",
                            (r.x + 15, r.y + (63 if compacto else 76)), r.w - 30, 11, MUTED)

    def painel(self, rect):
        pygame.draw.rect(self.tela, WHITE, rect, border_radius=14)
        pygame.draw.rect(self.tela, LINE, rect, width=1, border_radius=14)

    def botao(self, chave, titulo, rect, cor=GREEN, ativo=True, selecionado=False):
        self.botoes[chave] = (pygame.Rect(rect), ativo)
        r = pygame.Rect(rect)
        hover = ativo and r.collidepoint(pygame.mouse.get_pos())
        fundo = cor if ativo else (194, 204, 197)
        if hover:
            fundo = tuple(min(255, c + 15) for c in fundo)
            if pygame.mouse.get_pressed()[0]:
                fundo = tuple(max(0, c - 25) for c in fundo)
        pygame.draw.rect(self.tela, fundo, r, border_radius=8)
        if selecionado:
            pygame.draw.rect(self.tela, INK, r.inflate(4, 4), 2, border_radius=10)
        imagem = self.fonte(15, True).render(titulo, True, WHITE)
        self.tela.blit(imagem, imagem.get_rect(center=r.center))

    def cartao_metodo(self, chave, rect):
        metodo = METODOS[chave]
        rect = pygame.Rect(rect)
        ativo = self.futuro is None
        self.botoes[chave] = (rect, ativo)
        destaque = self.identidade_visual()["metodo"] == chave or (self.futuro is not None and self.metodo_em_execucao == chave)
        fundo = tuple(round(255 * .9 + c * .1) for c in metodo.cor) if destaque else (247, 249, 247)
        if ativo and rect.collidepoint(pygame.mouse.get_pos()):
            fundo = tuple(max(0, c - 7) for c in fundo)
        pygame.draw.rect(self.tela, fundo, rect, border_radius=8)
        pygame.draw.rect(self.tela, metodo.cor if destaque else LINE, rect, 2 if destaque else 1, border_radius=8)
        if destaque:
            pygame.draw.rect(self.tela, metodo.cor, (rect.x, rect.y + 9, 4, rect.h - 18), border_radius=2)
        self.texto_ajustado(metodo.curto, (rect.x + 12, rect.y + 2), rect.w - 48, 14, metodo.cor, True)
        motivo = self.motivo_indisponivel(chave)
        estado = "Em execução" if self.futuro is not None and self.metodo_em_execucao == chave else f"Indisponível: {motivo}" if motivo else "Em destaque" if self.resultado_focado == chave else "Selecionado" if self.metodo_selecionado == chave else metodo.garantia
        if self.player.passo is not None and destaque:
            estado = "Reproduzindo etapa" if self.player.reproduzindo else "Reprodução pausada"
        self.texto_ajustado(estado, (rect.x + 12, rect.y + 20), rect.w - 48, 10, INK)
        tecla = self.fonte(12, True).render(metodo.atalho, True, metodo.cor)
        self.tela.blit(tecla, tecla.get_rect(center=(rect.right - 22, rect.centery)))

    def desenhar_lateral(self):
        self.painel(self.lateral)
        self.texto("01  CONFIGURAÇÃO", (42, 119), 12, GREEN, True)
        self.texto("Escolha o percurso", (42, 145), 21, INK, True)
        self.botao("mapa1", "1 · 5 nós", (42, 184, 116, 33), selecionado=self.indice_mapa == 0)
        self.botao("mapa2", "2 · 18 nós", (170, 184, 116, 33), BLUE, selecionado=self.indice_mapa == 1)
        self.texto(f"Origem: {self.origem}    Destino: {self.destino}", (42, 239), 16, INK, True)
        livre = self.futuro is None
        self.texto("ALGORITMOS", (42, 270), 11, MUTED, True)
        for i, chave in enumerate(("dijkstra", "forca")):
            self.cartao_metodo(chave, (42, 294 + i * 42, 244, 38))
        self.botao("original", "O  Referência", (42, 390, 116, 28), MUTED)
        titulo_pesos = ("todos", "do nó", "ocultos")[self.modo_pesos]
        self.botao("pesos", f"P  {titulo_pesos}", (170, 390, 116, 28), MUTED)
        self.botao("limpar", "L  Limpar resultados", (42, 427, 244, 28), MUTED, livre)
        passo = self.player.passo
        if passo is None:
            metodo = METODOS[self.identidade_visual()["metodo"]]
            self.linhas(f"{metodo.descricao}. {metodo.garantia}.",
                        (42, 470), 244, tamanho=12, max_linhas=max(1, (self.lateral.bottom - 477) // 18))
        else:
            self.texto_ajustado(f"Etapa: {passo.algoritmo} · {passo.tipo}", (42, 470), 244, 12, INK)
            dist = ", ".join(f"{i}:{d:g}" for i, d in passo.distancias)
            if passo.adicionadas:
                dist = "Novas arestas: " + str(passo.adicionadas)
            self.texto_ajustado(f"Distâncias: {dist}" if dist else f"Candidato: {passo.candidato}", (42, 496), 244, 11, MUTED)
            self.linhas(f"Fila: {passo.fila}" if passo.fila else f"Melhor custo: {passo.melhor_custo}", (42, 522), 244, 12, max_linhas=3)

    def rotas_exibidas(self):
        passo = self.player.passo
        if passo is not None:
            cor = CORES_METODOS[self.identidade_visual()["metodo"]]
            return [(passo.caminho or passo.candidato, cor, 4)]
        return [(r.caminho, CORES_METODOS[nome], 7 if nome == "forca" else 3)
                for nome, r in self.resultados.items() if self.resultado_focado in (None, nome)]

    def desenhar_mapa(self):
        self.painel(self.mapa_rect)
        self.texto("VISUALIZAÇÃO DO GRAFO", (self.mapa_rect.x + 22, 119), 12, MUTED, True)
        self.texto(f"Mapa {self.indice_mapa + 1} · {len(self.mapa.nos)} cidades", (self.mapa_rect.x + 22, 145), 22, INK, True)
        for i, (chave, titulo) in enumerate((("zoom_menos", "−"), ("zoom_mais", "+"), ("reset", "Z"))):
            self.botao(chave, titulo, (self.mapa_rect.right - 198 + i * 59, 142, 53, 30), MUTED)
        self.desenhar_identidade()
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
                if passo and (aresta.origem, aresta.destino) in passo.adicionadas:
                    pygame.draw.line(self.tela, GREEN, a, b, 5)
                if passo and (aresta.origem, aresta.destino) in passo.removidas:
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
        if self.resultados or self.player.passo is not None:
            legenda = f"Percurso: {self.identidade_visual()['titulo']}"
        else:
            legenda = "Aguardando o resultado do cálculo." if self.futuro is not None else "Nenhum percurso calculado neste mapa."
        self.texto_ajustado(inspecao or legenda, (self.mapa_rect.x + 22, self.mapa_rect.bottom - 49), self.mapa_rect.w - 44, 12, MUTED)

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
        visiveis = list(self.resultados.items())
        largura = (self.resultados_rect.w - 56) // max(1, len(visiveis))
        for indice, (nome, resultado) in enumerate(visiveis):
            cx = x + 22 + indice * (largura + 12)
            cor = CORES_METODOS[nome]
            card = pygame.Rect(cx, y + 46, largura, 163)
            focado = self.resultado_focado == nome
            self.botoes[f"rota_{nome}"] = (card, True)
            pygame.draw.rect(self.tela, (247, 249, 247), card, border_radius=8)
            pygame.draw.rect(self.tela, cor if focado else LINE, card, 2 if focado else 1, border_radius=8)
            self.texto_ajustado(METODOS[nome].curto, (cx + 12, y + 52), largura - 24, 15, cor, True)
            self.texto_ajustado(MODELOS.get(getattr(resultado, "variante", ""), METODOS[nome].problema), (cx + 12, y + 76), largura - 24, 10, MUTED)
            custo = resultado.custo if resultado.caminho else "—"
            self.texto(f"Custo: {custo}", (cx + 12, y + 92), 21, INK, True)
            t = dict(getattr(resultado, "tempos_ms", ()))
            tempo = f"P {t.get('preparacao', 0):.1f} · O {t.get('otimizacao', 0):.1f} · R {t.get('reconstrucao', 0):.1f} ms | total {self.tempos.get(nome, 0):.1f}"
            self.texto_ajustado(tempo, (cx + 12, y + 120), largura - 24, 10, MUTED)
            rota = " → ".join(map(str, resultado.caminho)) or ("Nenhuma rota no orçamento." if not getattr(resultado, "otimo", True) else "Sem percurso viável.")
            self.linhas(rota, (cx + 12, y + 136), largura - 24, 12, cor, max_linhas=2)
            if hasattr(resultado, "contadores"):
                c = resultado.contadores[-1]
                memoria = next((c.valor for c in resultado.contadores if c.unidade == "bytes"), None)
                label = f"{c.nome}: {c.valor} {c.unidade}"
                if memoria is not None:
                    label += f" · DP {memoria / 1024**2:.1f} MiB" if memoria >= 1024**2 else f" · DP {memoria / 1024:.1f} KiB"
                self.texto_ajustado(label, (cx + 12, y + 173), largura - 24, 11, MUTED)
            elif hasattr(resultado, "estados_testados"):
                self.texto(f"{resultado.estados_testados} ordens examinadas", (cx + 12, y + 167), 11, MUTED)
            elif hasattr(resultado, "estado"):
                self.texto(f"{resultado.nos_expandidos} estados expandidos", (cx + 12, y + 167), 11, MUTED)
            self.texto_ajustado(garantia_resultado(nome, resultado), (cx + 12, y + 188), largura - 24, 11, cor, True)

    def desenhar(self):
        self.botoes.clear()
        self.tela.fill(BG)
        self.texto("NEXUS / ESTRUTURA DE DADOS NÃO LINEARES", (26, 16), 11, GREEN, True)
        self.texto("Caixeiro viajante", (24, 35), 32, INK, True)
        self.texto("Dijkstra e força bruta · etapas e percursos", (320, 54), 15, MUTED)
        if self.futuro is not None:
            self.botao("cancelar", "X  Cancelar", (self.tela.get_width() - 154, 38, 130, 34), ORANGE)
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
                       pygame.K_f: "forca", pygame.K_d: "dijkstra", pygame.K_l: "limpar", pygame.K_z: "reset", pygame.K_x: "cancelar"}
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
        if chave == "cancelar":
            self.cancelar.set()
            self.fase_execucao = "Cancelamento solicitado."
            return
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
        elif chave in REGISTRO:
            self.iniciar(chave)
        elif chave == "limpar":
            self.limpar()
            self.status = "Resultados limpos."
        elif chave in ("reproduzir", "pausar", "proximo", "voltar", "velocidade", "fim"):
            self.player.comando(chave)
        elif chave.startswith("rota_") and chave[5:] in self.resultados:
            nome = chave[5:]
            self.resultado_focado = None if self.resultado_focado == nome else nome
            self.player.comando("fim")

    def atualizar(self, dt):
        self.player.atualizar(dt)
        while True:
            try:
                self.metodo_em_execucao, self.fase_execucao = self.progresso.get_nowait()
            except Empty:
                break
        if self.futuro is not None and self.futuro.done():
            try:
                self.resultados, self.tempos, self.historico = self.futuro.result()
                self.player.carregar(self.historico)
                self.status = "Cálculo concluído."
                self.estado_execucao = "concluido"
                self.fase_execucao = "Resultado concluído."
                finais = {getattr(r, "termino", "") for r in self.resultados.values()}
                if "cancelado" in finais or self.cancelar.is_set():
                    self.estado_execucao = "cancelado"
                    self.fase_execucao = "Execução cancelada · sem prova de ótimo."
                elif any(f.startswith("limite_") for f in finais):
                    self.estado_execucao = "limitado"
                    self.fase_execucao = "Orçamento atingido · consulte a garantia do resultado."
                elif finais == {"indisponivel"}:
                    self.estado_execucao = "bloqueado"
                    self.fase_execucao = "Dependência ou método indisponível."
            except Exception as erro:
                self.status = f"Falha no cálculo: {erro}"
                self.estado_execucao = "erro"
                self.fase_execucao = self.status
            self.futuro = None
            self.metodo_em_execucao = None

    def executar(self):
        while self.rodando:
            dt = self.clock.tick(60) / 1000
            for evento in pygame.event.get():
                self.processar_evento(evento)
            self.atualizar(dt)
            self.desenhar()

    def fechar(self):
        self.cancelar.set()
        self.executor.shutdown(wait=True, cancel_futures=True)
        pygame.quit()
