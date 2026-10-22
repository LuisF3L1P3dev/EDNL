"""HUD cartunesca e responsiva para a operação NEXUS Logistics."""

from time import perf_counter

from ursina import Entity, InputField, Text, camera, color, mouse, window

from .dashboard import Dashboard
from .componentes import botao, painel, px, texto
from .tema import (ALTURA_REFERENCIA, ALTURA_RODAPE, ALTURA_TOPO,
                   LARGURA_DIREITA, LARGURA_ESQUERDA, MARGEM)
from ..graphics.estilo import (CIANO, FUNDO, LARANJA, PAINEL, ROSA, ROXO,
                               SUAVE, SUPERFICIE, TEXTO, VERDE)


class HUDCompacta(Dashboard):
    def _montar(self):
        jogo, raiz = self.jogo, self.raiz
        self.oculta = False

        # Faixa superior e marca vetorial.
        altura = window.size[1]
        largura = window.size[0]
        def posicao_topo(y):
            return px(ALTURA_REFERENCIA / 2 - y)
        topo_y = px(ALTURA_REFERENCIA / 2 - ALTURA_TOPO / 2)
        self.faixa = painel(raiz, 0, topo_y, window.aspect_ratio, px(ALTURA_TOPO), FUNDO, bloquear=True)
        self.marca = Entity(parent=raiz)
        self._montar_icone_caminhao(self.marca)
        self.marca_texto = texto(self.marca, "NEXUS", px(28), px(8), 1.0, CIANO, titulo=True)
        self.submarca = texto(self.marca, "LOGISTICS", px(29), px(-13), .36, SUAVE)
        self.titulo = texto(raiz, "TSP 3D", 0, 0, .82, TEXTO, titulo=True)
        self.subtitulo = texto(raiz, "ROTA PERFEITA", 0, 0, .34, SUAVE)

        self.operacao_bg = painel(raiz, 0, topo_y, px(145), px(42), color.hex("#17263C"), z=.04)
        self.cidades_bg = painel(raiz, 0, topo_y, px(112), px(42), color.hex("#17263C"), z=.04)
        self.topo = texto(raiz, "OPERAÇÃO 042", 0, topo_y + px(5), .48, VERDE, titulo=True)
        self.cidades = texto(raiz, "15 CIDADES", 0, topo_y + px(5), .48, TEXTO, titulo=True)
        self.legenda = Entity(parent=raiz)
        self._montar_legenda()
        self.modo = botao(raiz, jogo.estado.modo, 0, topo_y, px(164), px(42), self.trocar_modo)
        self.configuracoes = botao(raiz, "Config.", 0, topo_y, px(82), px(42), jogo.abrir_configuracoes)
        self.ajuda = botao(raiz, "?", 0, topo_y, px(42), px(42), lambda: jogo.abrir_resultados(ajuda=True))
        self._montar_icone_config()

        # Colunas laterais ocupam a mesma faixa entre o topo e o rodapé.
        altura_coluna = ALTURA_REFERENCIA - ALTURA_TOPO - ALTURA_RODAPE - 2 * MARGEM
        self.esquerda.scale = (1, 1, 1)
        self.direita.scale = (1, 1, 1)
        self.fundo_esquerda = painel(self.esquerda, 0, 0, px(LARGURA_ESQUERDA), px(altura_coluna), color.rgba32(19, 29, 47, 249), bloquear=True)
        self.fundo_direita = painel(self.direita, 0, 0, px(LARGURA_DIREITA), px(altura_coluna), color.rgba32(19, 29, 47, 249), bloquear=True)

        e, d = self.esquerda, self.direita
        texto(e, "CONTROLE DA MISSÃO", px(-124), px(altura_coluna / 2 - 36), .56, CIANO, titulo=True)
        texto(e, "Planeje · otimize · entregue", px(-124), px(altura_coluna / 2 - 60), .43, SUAVE)
        self.nova = botao(e, "+  Nova missão", 0, posicao_topo(194), px(248), px(42), self.abrir_missao)
        self.algoritmo = botao(e, jogo.estado.algoritmo, 0, posicao_topo(247), px(248), px(42), self.trocar_algoritmo)
        self.otimizar = botao(e, "OTIMIZAR ROTA", 0, posicao_topo(301), px(248), px(46), jogo.otimizar, CIANO, FUNDO)
        self.simular = botao(e, "INICIAR VIAGEM", 0, posicao_topo(354), px(248), px(44), jogo.iniciar_simulacao, VERDE, FUNDO)
        botao(e, "Comparar algoritmos", 0, posicao_topo(405), px(248), px(40), jogo.comparar)
        self.mais = botao(e, "Mais ações  +", 0, posicao_topo(468), px(248), px(36), self.alternar_acoes)

        self.acoes = Entity(parent=e, position=(0, px(-.245 * ALTURA_REFERENCIA), 0), enabled=False)
        self.acoes.scale_y = 1
        self.acoes_abertas = False
        self._acoes_fechar_ate = None
        self.fundo_acoes = painel(self.acoes, 0, 0, px(260), px(270), color.hex("#18243A"), bloquear=True)
        acoes = [
            ("Desfazer última entrega", jogo.desfazer),
            ("Reiniciar missão", jogo.reiniciar),
            ("Trocar depósito", jogo.trocar_deposito),
            ("Bloquear uma rua", lambda: jogo.evento_dinamico("bloqueio")),
            ("Obras: custo ×2", lambda: jogo.evento_dinamico("obras")),
            ("Salvar missão / JSON", jogo.exportar),
            ("Ranking de resultados", jogo.abrir_resultados),
        ]
        self.botoes_acoes = []
        for i, (rotulo, acao) in enumerate(acoes):
            self.botoes_acoes.append(botao(self.acoes, rotulo, 0,
                                           px(108 - i * 34), px(236), px(30), acao))

        # Telemetria e sequência de sete destinos permanecem simultâneas.
        texto(d, "TELEMETRIA", px(-130), px(altura_coluna / 2 - 36), .56, CIANO, titulo=True)
        self.distancia = texto(d, "0,00 km", px(-130), px(altura_coluna / 2 - 82), 1.24, TEXTO, titulo=True)
        self.nome_algoritmo = texto(d, "Planejamento manual", px(-130), px(altura_coluna / 2 - 112), .44, SUAVE)
        self.prova = texto(d, "ROTA DO JOGADOR", px(-130), px(altura_coluna / 2 - 137), .38, SUAVE)
        self.metricas = {}
        rotulos = ["Entregas realizadas", "Tempo de cálculo", "Economia de custo",
                   "Melhor conhecida", "Percorrido", "Combustível estimado",
                   "Custo da rota (u.c.)"]
        y_inicio_metricas = altura_coluna / 2 - 183
        for i, rotulo in enumerate(rotulos):
            y = px(y_inicio_metricas - i * 28)
            texto(d, rotulo, px(-130), y, .44, SUAVE)
            valor = Text(parent=d, text="—", x=px(130), y=y, scale=.45,
                         color=TEXTO, origin=(.5, .5), z=-.06)
            self.metricas[rotulo] = valor

        self.lista = Entity(parent=d)
        self.detalhes = Entity(parent=d, enabled=False)
        linha_y = px(y_inicio_metricas - len(rotulos) * 28 + 3)
        painel(d, 0, linha_y, px(248), px(2), color.hex("#34445F"), z=.02)
        texto(self.lista, "SEQUÊNCIA DE ENTREGAS", px(-130), linha_y - px(14), .47, CIANO, titulo=True)
        self.destinos = [botao(self.lista, "", 0,
                               linha_y - px(45 + i * 34), px(248), px(30), lambda: None,
                               LARANJA, FUNDO) for i in range(7)]
        self.anterior = botao(self.lista, "‹", px(-100), linha_y - px(288), px(34), px(28), lambda: self.paginar(-1))
        self.pagina = texto(self.lista, "1 / 1", px(-22), linha_y - px(285), .37, SUAVE)
        self.proxima = botao(self.lista, "›", px(100), linha_y - px(288), px(34), px(28), lambda: self.paginar(1))
        self.pontuacao = texto(self.lista, "MISSÃO EM PLANEJAMENTO", px(-130), linha_y - px(322), .38, VERDE)

        # Dica contextual, barra de transporte e notificação compacta.
        self.dica_cidade = Text(parent=raiz, text="", origin=(0, 0),
                                color=TEXTO, scale=.55, background=True, z=-.15)
        self.transporte = Entity(parent=raiz)
        largura_controles = 714
        altura_coluna = ALTURA_REFERENCIA - ALTURA_TOPO - ALTURA_RODAPE - 2 * MARGEM
        self.barra_transporte = painel(self.transporte, 0, 0, px(largura_controles), px(ALTURA_RODAPE),
                                       color.rgba32(19, 29, 47, 250), bloquear=True)
        controles = [
            (124, "Isométrica", jogo.trocar_camera),
            (32, "−", lambda: jogo.controle_camera.zoom(1.15)),
            (32, "+", lambda: jogo.controle_camera.zoom(.87)),
            (92, "Pausar", jogo.pausar),
            (52, "1×", self.trocar_velocidade),
            (70, "Reiniciar", jogo.reiniciar_viagem),
            (74, "Etapas", jogo.reproduzir_etapas),
            (74, "Centralizar", jogo.centralizar_camera),
            (62, "Grafo", jogo.alternar_grafo),
            (50, "HUD", self.alternar_hud),
        ]
        espaco, cursor = 4, -largura_controles / 2 + 8
        botoes_controle = []
        for indice, (largura_px, rotulo, acao) in enumerate(controles):
            centro = cursor + largura_px / 2
            botao_controle = botao(self.transporte, rotulo, px(centro), 0,
                                   px(largura_px), px(40), acao)
            botoes_controle.append(botao_controle)
            cursor += largura_px + espaco
        (self.camera, self.zoom_menos, self.zoom_mais, self.pausa, self.velocidade,
         self.reiniciar_viagem, self.etapas, self.centralizar, self.grafo, self.botao_hud) = botoes_controle

        largura_status = min(740, max(500, largura - 2 * (MARGEM + 5) - LARGURA_ESQUERDA - LARGURA_DIREITA))
        self.notificacao = Entity(parent=raiz)
        self.painel_notificacao = painel(self.notificacao, 0, 0, px(largura_status), px(52),
                                         color.rgba32(19, 29, 47, 242), bloquear=True)
        self.status = texto(self.notificacao, "PREPARANDO MISSÃO", px(-largura_status / 2 + 16), px(15), .42, CIANO, titulo=True)
        self.explicacao = texto(self.notificacao, "Clique nos destinos para planejar as entregas.", px(-largura_status / 2 + 16), px(-1), .40, TEXTO)
        self.detalhe = texto(self.notificacao, "", px(-largura_status / 2 + 16), px(-15), .36, SUAVE)
        self.atalhos = texto(raiz, "WASD mover  ·  botão direito girar  ·  roda zoom",
                             0, px(altura_coluna / 2 - 24), .37, FUNDO)

        self._montar_missao()
        self._posicionar()

    def _montar_icone_caminhao(self, parent):
        def quad(x, y, w, h, tom):
            return Entity(parent=parent, model="quad", position=(px(x), px(y), -.08),
                          scale=(px(w), px(h)), color=tom)
        quad(0, 0, 27, 16, CIANO)
        quad(18, 4, 14, 12, VERDE)
        quad(22, 5, 8, 7, color.hex("#DFF8FF"))
        Entity(parent=parent, model="circle", position=(px(6), px(-9), -.09), scale=px(8), color=FUNDO)
        Entity(parent=parent, model="circle", position=(px(25), px(-9), -.09), scale=px(8), color=FUNDO)

    def _montar_icone_config(self):
        # Pequena engrenagem geométrica, sem depender de glifos externos.
        self.icone_config = Entity(parent=self.raiz)
        for angulo in (0, 45, 90, 135):
            Entity(parent=self.icone_config, model="quad", scale=(px(4), px(16)),
                   rotation_z=angulo, color=CIANO)
        Entity(parent=self.icone_config, model="circle", scale=px(17), color=CIANO, z=-.01)
        Entity(parent=self.icone_config, model="circle", scale=px(7), color=PAINEL, z=-.02)

    def _montar_legenda(self):
        for x, cor, nome, largura in ((-116, LARANJA, "SUA ROTA", 73),
                                      (-35, VERDE, "COMPUTADOR", 105),
                                      (78, ROXO, "BASE", 56)):
            Entity(parent=self.legenda, model="quad", position=(px(x), px(1), -.04),
                   scale=(px(10), px(10)), color=cor)
            texto(self.legenda, nome, px(x + 9), px(6), .38, TEXTO, titulo=True)

    def _montar_missao(self):
        jogo = self.jogo
        self.janela_missao = Entity(parent=self.raiz, z=-2, enabled=False)
        janela = self.janela_missao
        w, _ = window.size
        fundo = botao(janela, "", 0, 0, window.aspect_ratio, 1, lambda: None,
                      color.rgba32(3, 9, 19, 205), raio=0)
        fundo.moldura.enabled = False
        fundo.z = .3
        fundo.highlight_color = fundo.pressed_color = fundo.color
        painel(janela, 0, 0, .72, .65, PAINEL, bloquear=True)
        texto(janela, "NOVA MISSÃO", -.315, .28, .85, CIANO, titulo=True)
        texto(janela, "A semente permite repetir a mesma região.", -.315, .235, .48, SUAVE)
        botao(janela, "×", .306, .286, .045, .04, self.fechar_missao)
        self.dificuldade = botao(janela, "Dificuldade · Médio", 0, .162, .62, .044, self.trocar_dificuldade)
        texto(janela, "CIDADES (INCLUI A BASE)", -.31, .112, .43, SUAVE)
        texto(janela, "SEMENTE", .02, .112, .43, SUAVE)
        self.quantidade = InputField(parent=janela, default_value=str(jogo.config["quantidade_cidades"]),
            position=(-.16, .060, -.15), scale=(.30, .045), limit_content_to="0123456789",
            character_limit=3, color=SUPERFICIE, text_color=TEXTO)
        self.semente = InputField(parent=janela, default_value=str(jogo.config["semente"]),
            position=(.165, .060, -.15), scale=(.29, .045), limit_content_to="0123456789",
            character_limit=9, color=SUPERFICIE, text_color=TEXTO)
        self.modalidade = botao(janela, "Malha rodoviária · Dijkstra", 0, -.014, .62, .04, self.alternar_modalidade_pendente)
        self.tempo = botao(janela, "Limite de busca · 3 s", 0, -.064, .62, .04, self.alternar_tempo_pendente)
        self.deposito = botao(janela, "Base · Central NEXUS", 0, -.114, .62, .04, self.alternar_base_pendente)
        self.erro_missao = texto(janela, "", -.31, -.157, .43, ROSA)
        botao(janela, "Cancelar", -.16, -.254, .29, .045, self.fechar_missao)
        botao(janela, "GERAR MAPA", .165, -.254, .29, .045, self.confirmar_missao, CIANO, FUNDO)

    def _posicionar(self):
        largura, altura = window.size
        aspecto = window.aspect_ratio
        self.raiz.scale = (1, 1, 1)
        self.aspecto = aspecto
        self.tamanho_janela = (largura, altura)
        topo_y = px(ALTURA_REFERENCIA / 2 - ALTURA_TOPO / 2)
        self.marca.position = (-aspecto / 2 + px(22), topo_y, 0)
        self.titulo.position = (-aspecto / 2 + px(166), topo_y + px(6), -.06)
        self.subtitulo.position = (-aspecto / 2 + px(166), topo_y - px(13), -.06)

        operacao_x = -aspecto / 2 + px(365)
        cidade_x = -aspecto / 2 + px(492)
        self.faixa.position = (0, topo_y, .04)
        self.faixa.scale = (aspecto, px(ALTURA_TOPO), 1)
        self.operacao_bg.position = (operacao_x, topo_y, .04)
        self.operacao_bg.scale = (px(145), px(42), 1)
        self.cidades_bg.position = (cidade_x, topo_y, .04)
        self.cidades_bg.scale = (px(112), px(42), 1)
        self.topo.position = (operacao_x, topo_y + px(5), -.06)
        self.cidades.position = (cidade_x, topo_y + px(5), -.06)

        self.legenda.position = (px(80), topo_y, 0)
        self.modo.position = (aspecto / 2 - px(298), topo_y, -.1)
        self.configuracoes.position = (aspecto / 2 - px(100), topo_y, -.1)
        self.ajuda.position = (aspecto / 2 - px(32), topo_y, -.1)
        for botao_topo in (self.modo, self.configuracoes, self.ajuda):
            botao_topo.moldura.position = (
                botao_topo.x, botao_topo.y - botao_topo.scale_y * .065, -.082)
        self.icone_config.position = (aspecto / 2 - px(126), topo_y, -.12)
        self.configuracoes.text_entity.x = px(7)

        faixa_vertical = ALTURA_REFERENCIA - ALTURA_TOPO - ALTURA_RODAPE - 2 * MARGEM
        self.esquerda.position = (-aspecto / 2 + px(MARGEM + LARGURA_ESQUERDA / 2), 0, 0)
        self.direita.position = (aspecto / 2 - px(MARGEM + LARGURA_DIREITA / 2), 0, 0)
        self.fundo_esquerda.scale = (px(LARGURA_ESQUERDA), px(faixa_vertical), 1)
        self.fundo_direita.scale = (px(LARGURA_DIREITA), px(faixa_vertical), 1)
        self.dica_cidade.y = px(faixa_vertical / 2 - 24)
        altura_acoes = 270
        passo_acoes = (altura_acoes - 16) / 7
        altura_botao_acao = max(17, passo_acoes - 2)
        centro_acoes = -faixa_vertical / 2 + 5 + altura_acoes / 2
        self.acoes_y = px(centro_acoes)
        self.acoes.position = (0, self.acoes_y, 0)
        self.fundo_acoes.scale = (px(260), px(altura_acoes), 1)
        for i, acao in enumerate(self.botoes_acoes):
            acao.y = px(altura_acoes / 2 - 8 - passo_acoes * (i + .5))
            acao.scale = (px(236), px(altura_botao_acao), 1)
            acao.moldura.position = (acao.x, acao.y - px(altura_botao_acao) * .065, -.082)
            acao.moldura.scale = (px(236), px(altura_botao_acao), 1)

        self.transporte.position = (px((LARGURA_ESQUERDA - LARGURA_DIREITA) / 2),
                                    px(ALTURA_RODAPE / 2 + MARGEM - ALTURA_REFERENCIA / 2), 0)
        largura_disponivel = max(500, (aspecto - 2 * px(MARGEM + 5) -
                                        px(LARGURA_ESQUERDA + LARGURA_DIREITA)) * ALTURA_REFERENCIA)
        self.transporte.scale_x = min(1, largura_disponivel / 714)
        largura_status = min(740, max(500, largura_disponivel))
        y_status = px(102 - ALTURA_REFERENCIA / 2)
        self.notificacao.position = (px((LARGURA_ESQUERDA - LARGURA_DIREITA) / 2), y_status, 0)
        self.notificacao.scale_x = min(1, largura_disponivel / largura_status)
        controle_camera = getattr(self.jogo, "controle_camera", None)
        if controle_camera:
            controle_camera.ajustar_enquadramento(aspecto)

    def abrir_missao(self):
        if self.jogo.modal_aberto:
            return
        self.acoes.enabled = False
        self.acoes_abertas = False
        self._acoes_fechar_ate = None
        self._repor_campos_missao()
        self.modalidade_pendente = self.jogo.estado.modalidade
        self.tempo_pendente = self.jogo.config["tempo_otimizacao_segundos"]
        self.base_pendente = self.jogo.cenario.cidades.index(self.jogo.cenario.deposito)
        self.erro_missao.text = ""
        self.atualizar_opcoes_missao()
        self.janela_missao.enabled = True

    def atualizar_opcoes_missao(self):
        self.modalidade.text = ("Malha rodoviária · Dijkstra" if self.modalidade_pendente == "rodoviario"
                                else "Euclidiano · drone abstrato")
        self.tempo.text = f"Limite de busca · {self.tempo_pendente:g} s"
        self.deposito.text = "Depósito inicial · destino " + str(self.base_pendente)

    def alternar_modalidade_pendente(self):
        self.modalidade_pendente = "euclidiano" if self.modalidade_pendente == "rodoviario" else "rodoviario"
        self.atualizar_opcoes_missao()

    def alternar_tempo_pendente(self):
        opcoes = [2., 3., 5.]
        self.tempo_pendente = opcoes[(opcoes.index(self.tempo_pendente) + 1) % 3] if self.tempo_pendente in opcoes else 3.
        self.atualizar_opcoes_missao()

    def alternar_base_pendente(self):
        total = max(3, min(self.jogo.config["limite_cidades"], int(self.quantidade.text or 15)))
        self.base_pendente = (self.base_pendente + 1) % total
        self.atualizar_opcoes_missao()

    def confirmar_missao(self):
        from ..core.scenario_generator import gerar_cenario
        jogo = self.jogo
        try:
            quantidade, semente = int(self.quantidade.text), int(self.semente.text)
            if not 3 <= quantidade <= jogo.config["limite_cidades"]:
                raise ValueError(f"Escolha de 3 a {jogo.config['limite_cidades']} cidades.")
            cenario = gerar_cenario(quantidade, semente, jogo.config["metros_por_unidade"])
            cenario.deposito = cenario.cidades[self.base_pendente % quantidade]
        except ValueError as erro:
            self.erro_missao.text = str(erro)[:85]
            return
        jogo.estado.modalidade = self.modalidade_pendente
        jogo.config["tempo_otimizacao_segundos"] = self.tempo_pendente
        self.fechar_missao()
        jogo._carregar_missao(cenario)

    def fechar_missao(self):
        self.quantidade.active = self.semente.active = False
        self.janela_missao.enabled = False
        self._repor_campos_missao()

    def _repor_campos_missao(self):
        cenario = self.jogo.cenario
        self.quantidade.text = str(len(cenario.cidades))
        self.semente.text = str(cenario.semente)
        quantidade = len(cenario.cidades)
        nome = "Fácil" if quantidade <= 8 else "Médio" if quantidade <= 15 else "Difícil" if quantidade <= 30 else "Especialista"
        self.dificuldade.text = "Dificuldade · " + nome

    @property
    def editando(self):
        return self.janela_missao.enabled

    def alternar_acoes(self):
        abrir = not self.acoes_abertas
        self.acoes_abertas = abrir
        self.mais.text = "Mais ações  −" if abrir else "Mais ações  +"
        if abrir:
            self._acoes_fechar_ate = None
            self.acoes.enabled = True
            self.acoes.y = self.acoes_y - px(18)
            self.acoes.animate_y(self.acoes_y, duration=.18)
        else:
            self.acoes.animate_y(self.acoes_y - px(18), duration=.15)
            self._acoes_fechar_ate = perf_counter() + .16

    def alternar_painel(self, nome):
        if nome == "lista":
            self.lista.enabled = True
        elif nome == "detalhes":
            self.detalhes.enabled = not self.detalhes.enabled

    def alternar_hud(self):
        self.oculta = not self.oculta
        self.raiz.enabled = not self.oculta

    def sobre_interface(self):
        entidade = mouse.hovered_entity
        while entidade is not None:
            if entidade in (self.raiz, camera.ui):
                return True
            entidade = getattr(entidade, "parent", None)
        return False

    def atualizar(self):
        super().atualizar()
        jogo = self.jogo
        if self._acoes_fechar_ate and perf_counter() >= self._acoes_fechar_ate:
            self.acoes.enabled = False
            self.acoes.position = (0, self.acoes_y, 0)
            self._acoes_fechar_ate = None
        if self.janela_missao.enabled:
            self.atualizar_opcoes_missao()
        self.atalhos.enabled = jogo.preferencias["dicas"] and not self.oculta

    def redimensionar(self):
        tamanho = tuple(window.size)
        if tamanho != getattr(self, "tamanho_janela", None):
            self._posicionar()
