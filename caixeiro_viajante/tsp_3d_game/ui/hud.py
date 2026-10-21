"""HUD compacta. Reutiliza os comandos e a telemetria do dashboard existente."""
from ursina import Entity, InputField, Text, camera, color, mouse
from .dashboard import Dashboard, botao, painel, texto, km
from ..graphics.estilo import CIANO, FUNDO, LARANJA, PAINEL, ROXO, SUAVE, SUPERFICIE, TEXTO, VERDE, ROSA


class HUDCompacta(Dashboard):
    def _montar(self):
        j, r = self.jogo, self.raiz
        self.oculta = False
        self.faixa = painel(r, 0, .461, camera.aspect_ratio, .078, FUNDO, bloquear=True)
        self.marca = Entity(parent=r)
        texto(self.marca, "N E X U S", 0, .483, .95, CIANO)
        texto(self.marca, "L O G I S T I C S  /  T S P  3 D", .002, .449, .36, SUAVE)
        self.topo = texto(r, "OPERAÇÃO 042", -.38, .472, .56)
        self.modo = botao(r, j.estado.modo, .21, .461, .26, .036, self.trocar_modo)
        self.configuracoes = botao(r, "Config.", .67, .461, .14, .036, j.abrir_configuracoes)
        self.ajuda = botao(r, "?", .81, .461, .045, .036, lambda: j.abrir_resultados(ajuda=True))
        # Engrenagem vetorial: não depende de um glifo instalado no computador.
        engrenagem = Entity(parent=self.configuracoes, x=-.37, z=-.02, scale=(.10, .40, 1))
        for angulo in (0, 45, 90, 135):
            Entity(parent=engrenagem, model="quad", scale=(.28, 1), rotation_z=angulo, color=CIANO)
        Entity(parent=engrenagem, model="circle", scale=.65, color=CIANO, z=-.01)
        Entity(parent=engrenagem, model="circle", scale=.28, color=PAINEL, z=-.02)
        self.configuracoes.text_entity.x = .05
        e, d = self.esquerda, self.direita
        e.y, d.y = .18, .23
        painel(e, 0, 0, .285, .375, color.rgba32(15, 24, 39, 242), bloquear=True)
        texto(e, "CONTROLE DA MISSÃO", -.122, .166, .46, CIANO)
        botao(e, "+  Nova missão", 0, .117, .245, .037, self.abrir_missao)
        self.algoritmo = botao(e, j.estado.algoritmo, 0, .068, .245, .037, self.trocar_algoritmo)
        self.otimizar = botao(e, "OTIMIZAR ROTA", 0, .016, .245, .045, j.otimizar, CIANO, FUNDO)
        self.simular = botao(e, "INICIAR VIAGEM", 0, -.036, .245, .042, j.iniciar_simulacao, VERDE, FUNDO)
        botao(e, "Comparar algoritmos", 0, -.087, .245, .036, j.comparar)
        self.mais = botao(e, "Mais ações  +", 0, -.143, .245, .03, self.alternar_acoes)
        self.acoes = Entity(parent=e, y=-.32, enabled=False)
        painel(self.acoes, 0, -.015, .285, .285, bloquear=True)
        for i, (nome, acao) in enumerate([
            ("Desfazer última entrega", j.desfazer), ("Reiniciar missão", j.reiniciar),
            ("Trocar depósito", j.trocar_deposito),
            ("Bloquear uma rua", lambda: j.evento_dinamico("bloqueio")),
            ("Obras: custo ×2", lambda: j.evento_dinamico("obras")),
            ("Salvar missão / JSON", j.exportar), ("Ranking de resultados", j.abrir_resultados)]):
            botao(self.acoes, nome, 0, .096 - i * .038, .245, .031, acao)

        painel(d, 0, .001, .292, .293, color.rgba32(15, 24, 39, 242), bloquear=True)
        texto(d, "TELEMETRIA", -.125, .128, .46, CIANO)
        self.distancia = texto(d, "0,00 km", -.125, .096, 1.22)
        self.nome_algoritmo = texto(d, "Planejamento manual", -.125, .050, .48, SUAVE)
        self.prova = texto(d, "ROTA DO JOGADOR", -.125, .023, .40, SUAVE)
        self.metricas = {}
        self.detalhes = Entity(parent=d, y=-.272, enabled=False)
        painel(self.detalhes, 0, 0, .292, .235, bloquear=True)
        rotulos = ["Entregas realizadas", "Tempo de cálculo", "Economia de custo",
                   "Melhor conhecida", "Percorrido", "Combustível estimado", "Custo da rota (u.c.)"]
        for i, rotulo in enumerate(rotulos):
            pai, y = (d, -.011 - i * .028) if i < 3 else (self.detalhes, .087 - (i - 3) * .035)
            texto(pai, rotulo, -.125, y, .43, SUAVE)
            self.metricas[rotulo] = Text(parent=pai, text="—", x=.125, y=y, scale=.49,
                                         color=TEXTO, origin=(.5, .5), z=-.08)
        self.pontuacao = texto(self.detalhes, "MISSÃO EM PLANEJAMENTO", -.125, -.067, .42, VERDE)
        self.btn_detalhes = botao(d, "Detalhes", -.067, -.113, .12, .029, lambda: self.alternar_painel("detalhes"))
        self.btn_lista = botao(d, "Entregas", .067, -.113, .12, .029, lambda: self.alternar_painel("lista"))
        self.lista = Entity(parent=d, y=-.302, enabled=False)
        painel(self.lista, 0, 0, .292, .294, bloquear=True)
        texto(self.lista, "SEQUÊNCIA DE ENTREGAS", -.125, .13, .42, CIANO)
        self.destinos = [botao(self.lista, "", 0, .09 - i * .029, .26, .026, lambda: None) for i in range(7)]
        self.anterior = botao(self.lista, "‹", -.108, -.123, .04, .026, lambda: self.paginar(-1))
        self.proxima = botao(self.lista, "›", .108, -.123, .04, .026, lambda: self.paginar(1))
        self.pagina = texto(self.lista, "1 / 1", -.027, -.115, .44, SUAVE)

        self.grafo = botao(r, "Grafo · G", -.38, .388, .13, .028, j.alternar_grafo)
        self.legenda = Entity(parent=r, x=-.18, y=.388)
        for x, cor, nome in ((0, LARANJA, "SUA ROTA"), (.17, VERDE, "COMPUTADOR"), (.39, ROXO, "BASE")):
            painel(self.legenda, x, 0, .009, .009, cor)
            texto(self.legenda, nome, x + .014, .008, .35, FUNDO)
        self.dica_cidade = Text(parent=r, text="", origin=(0, 0), y=.332,
                               color=TEXTO, scale=.7, background=True, z=-.15)
        self.transporte = Entity(parent=r, y=-.363)
        painel(self.transporte, 0, 0, 1.03, .061, color.rgba32(15, 24, 39, 242), bloquear=True)
        self.camera = botao(self.transporte, "Isométrica · C", -.38, 0, .235, .035, j.trocar_camera)
        botao(self.transporte, "−", -.22, 0, .04, .035, lambda: j.controle_camera.zoom(1.15))
        botao(self.transporte, "+", -.173, 0, .04, .035, lambda: j.controle_camera.zoom(.87))
        self.pausa = botao(self.transporte, "Pausar / seguir", -.037, 0, .20, .035, j.pausar)
        self.velocidade = botao(self.transporte, "1×", .115, 0, .08, .035, self.trocar_velocidade)
        self.etapas = botao(self.transporte, "Rever etapas", .252, 0, .17, .035, j.reproduzir_etapas)
        botao(self.transporte, "HUD · Tab", .422, 0, .145, .035, self.alternar_hud)
        self.rodape = Entity(parent=r, y=-.451)
        painel(self.rodape, 0, 0, 1.03, .09, color.rgba32(15, 24, 39, 240), bloquear=True)
        self.status = texto(self.rodape, "PREPARANDO MISSÃO", -.49, .032, .44, CIANO)
        self.explicacao = texto(self.rodape, "Clique nos destinos para planejar.", -.49, .007, .43, TEXTO)
        self.detalhe = texto(self.rodape, "", -.49, -.019, .38, SUAVE)
        self.atalhos = texto(r, "WASD  mover   /   botão direito  girar   /   roda  zoom", -.24, .353, .34, FUNDO)
        self._montar_missao()
        self._posicionar()

    def _montar_missao(self):
        j = self.jogo
        self.janela_missao = Entity(parent=self.raiz, z=-2, enabled=False)
        p = self.janela_missao
        fundo = botao(p, "", 0, 0, camera.aspect_ratio, 1, lambda: None, color.rgba32(3, 9, 19, 200))
        fundo.z = .3
        fundo.highlight_color = fundo.pressed_color = fundo.color
        painel(p, 0, 0, .72, .65)
        texto(p, "NOVA MISSÃO", -.315, .28, .85, CIANO)
        texto(p, "A semente permite repetir a mesma região.", -.315, .235, .52, SUAVE)
        self.dificuldade = botao(p, "Dificuldade · Médio", 0, .162, .62, .044, self.trocar_dificuldade)
        texto(p, "CIDADES (INCLUI A BASE)", -.31, .112, .47, SUAVE)
        texto(p, "SEMENTE", .02, .112, .47, SUAVE)
        self.quantidade = InputField(parent=p, default_value=str(j.config["quantidade_cidades"]),
            position=(-.16, .060, -.15), scale=(.30, .045), limit_content_to="0123456789", character_limit=3,
            color=SUPERFICIE, text_color=TEXTO)
        self.semente = InputField(parent=p, default_value=str(j.config["semente"]),
            position=(.165, .060, -.15), scale=(.29, .045), limit_content_to="0123456789", character_limit=9,
            color=SUPERFICIE, text_color=TEXTO)
        self.modalidade = botao(p, "Malha rodoviária · Dijkstra", 0, -.014, .62, .04, self.alternar_modalidade_pendente)
        self.tempo = botao(p, "Limite de busca · 3 s", 0, -.064, .62, .04, self.alternar_tempo_pendente)
        self.deposito = botao(p, "Base · Central NEXUS", 0, -.114, .62, .04, self.alternar_base_pendente)
        self.erro_missao = texto(p, "", -.31, -.157, .46, ROSA)
        botao(p, "Cancelar", -.16, -.254, .29, .045, self.fechar_missao)
        botao(p, "GERAR MAPA", .165, -.254, .29, .045, self.confirmar_missao, CIANO, FUNDO)

    def abrir_missao(self):
        if self.jogo.modal_aberto:
            return
        self.acoes.enabled = False
        self._repor_campos_missao()
        self.modalidade_pendente = self.jogo.estado.modalidade
        self.tempo_pendente = self.jogo.config["tempo_otimizacao_segundos"]
        self.base_pendente = self.jogo.cenario.cidades.index(self.jogo.cenario.deposito)
        self.erro_missao.text = ""
        self.atualizar_opcoes_missao()
        self.janela_missao.enabled = True

    def atualizar_opcoes_missao(self):
        self.modalidade.text = "Malha rodoviária · Dijkstra" if self.modalidade_pendente == "rodoviario" else "Euclidiano · drone abstrato"
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
        j = self.jogo
        try:
            quantidade, semente = int(self.quantidade.text), int(self.semente.text)
            if not 3 <= quantidade <= j.config["limite_cidades"]:
                raise ValueError(f"Escolha de 3 a {j.config['limite_cidades']} cidades.")
            cenario = gerar_cenario(quantidade, semente, j.config["metros_por_unidade"])
            cenario.deposito = cenario.cidades[self.base_pendente % quantidade]
        except ValueError as erro:
            self.erro_missao.text = str(erro)[:85]
            return
        j.estado.modalidade = self.modalidade_pendente
        j.config["tempo_otimizacao_segundos"] = self.tempo_pendente
        self.fechar_missao()
        j._carregar_missao(cenario)

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
        self.acoes.enabled = not self.acoes.enabled
        self.mais.text = "Mais ações  −" if self.acoes.enabled else "Mais ações  +"

    def alternar_painel(self, nome):
        alvo = getattr(self, nome)
        abrir = not alvo.enabled
        self.lista.enabled = self.detalhes.enabled = False
        alvo.enabled = abrir

    def alternar_hud(self):
        self.oculta = not self.oculta
        for entidade in (self.esquerda, self.direita, self.rodape, self.grafo, self.legenda):
            entidade.enabled = not self.oculta

    def sobre_interface(self):
        entidade = mouse.hovered_entity
        while entidade is not None:
            if entidade in (self.raiz, camera.ui):
                return True
            entidade = getattr(entidade, "parent", None)
        return False

    def atualizar(self):
        super().atualizar()
        j = self.jogo
        if j.preferencias["unidade"] == "m":
            distancia = j.estado.ativa.distancia if j.estado.ativa else j.distancia_manual()
            self.distancia.text = f"{distancia:,.0f} m".replace(",", ".")
            if j.estado.referencia:
                self.metricas["Melhor conhecida"].text = f"{j.estado.referencia.distancia:.0f} m"
            self.metricas["Percorrido"].text = f"{j.simulacao.distancia if j.simulacao else 0:.0f} m"
        if self.janela_missao.enabled:
            self.atualizar_opcoes_missao()
        self.velocidade.text = f"{j.estado.velocidade:g}×"
        self.atalhos.enabled = j.preferencias["dicas"] and not self.oculta

    def _posicionar(self):
        meio = camera.aspect_ratio / 2
        self.esquerda.x, self.direita.x = -meio + .158, meio - .161
        self.marca.x = -meio + .028
        self.configuracoes.x, self.ajuda.x = meio - .165, meio - .055
        self.faixa.scale_x = camera.aspect_ratio

    def redimensionar(self):
        if abs(camera.aspect_ratio - self.aspecto) >= .01:
            self.aspecto = camera.aspect_ratio
            self._posicionar()
