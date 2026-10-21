"""Dashboard com comandos, estatísticas e lista paginada de entregas."""

from __future__ import annotations

from ursina import Button, Entity, InputField, Text, camera, color, destroy, window
from ursina.shaders import unlit_shader

from ..algorithms.registro import ALGORITMOS
from ..core.game_state import economia_percentual
from ..graphics.estilo import (BORDA, CIANO, FUNDO, LARANJA, PAINEL, ROSA,
                               ROXO, SUAVE, SUPERFICIE, TEXTO, VERDE)


def texto(parent, conteudo, x, y, escala=.65, cor=TEXTO, **kwargs):
    return Text(parent=parent, text=conteudo, x=x, y=y, scale=escala, color=cor,
                origin=(-.5, .5), z=-.06, **kwargs)


def painel(parent, x, y, largura, altura, cor=PAINEL, z=.04, bloquear=False):
    return Entity(parent=parent, model="quad", position=(x, y, z),
                  scale=(largura, altura), color=cor, shader=unlit_shader,
                  collider="box" if bloquear else None)


def botao(parent, rotulo, x, y, largura, altura, acao, cor=SUPERFICIE, cor_texto=TEXTO):
    b = Button(parent=parent, text=rotulo or " ", position=(x, y, -.1), scale=(largura, altura),
               color=cor, text_color=cor_texto, highlight_color=cor.tint(.12),
               pressed_color=cor.tint(-.12), radius=.045, on_click=acao)
    b.text_entity.scale *= .68
    return b


def km(valor):
    return f"{valor / 1000:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".") + " km"


class Dashboard:
    MODOS = ["Desafio Humano", "Inteligência Artificial", "Batalha de Algoritmos"]
    DIFICULDADES = [("Fácil", 7), ("Médio", 15), ("Difícil", 25), ("Especialista", 50)]

    def __init__(self, jogo):
        self.jogo = jogo
        self.raiz = Entity(parent=camera.ui)
        self.esquerda = Entity(parent=self.raiz)
        self.direita = Entity(parent=self.raiz)
        self.aspecto = camera.aspect_ratio
        self.mensagens = []
        self._montar()

    def _montar(self):
        j, r = self.jogo, self.raiz
        margem = camera.aspect_ratio / 2 - .18
        self.esquerda.x, self.direita.x = -margem, margem
        painel(r, 0, .451, camera.aspect_ratio, .098, FUNDO)
        texto(r, "NEXUS", -camera.aspect_ratio / 2 + .03, .482, 1.1, CIANO)
        texto(r, "L O G I S T I C S", -camera.aspect_ratio / 2 + .031, .447, .43, SUAVE)
        texto(r, "TSP 3D", -.34, .478, .94)
        texto(r, "O DESAFIO DA ROTA PERFEITA", -.34, .447, .49, SUAVE)
        self.topo = texto(r, "OPERAÇÃO 042    /    SISTEMA ONLINE", .26, .464, .53, VERDE)
        painel(self.esquerda, 0, -.023, .322, .80)
        painel(self.direita, 0, -.023, .322, .80)
        e, d = self.esquerda, self.direita
        texto(e, "01 / CONTROLE DA MISSÃO", -.141, .357, .51, CIANO)
        texto(e, "Planeje. Explore. Entregue.", -.141, .327, .65)
        self.modo = botao(e, "Modo · Desafio Humano", 0, .267, .284, .038, self.trocar_modo)
        self.dificuldade = botao(e, "Dificuldade · Médio", 0, .220, .284, .035, self.trocar_dificuldade)
        texto(e, "CIDADES (COM BASE)", -.14, .187, .43, SUAVE)
        texto(e, "SEMENTE", .021, .187, .43, SUAVE)
        self.quantidade = InputField(parent=e, default_value=str(j.config["quantidade_cidades"]),
            position=(-.075, .147, -.15), scale=(.13, .035), limit_content_to="0123456789",
            character_limit=3, color=SUPERFICIE, text_color=TEXTO)
        self.semente = InputField(parent=e, default_value=str(j.config["semente"]),
            position=(.08, .147, -.15), scale=(.124, .035), limit_content_to="0123456789",
            character_limit=9, color=SUPERFICIE, text_color=TEXTO)
        botao(e, "GERAR MAPA", 0, .099, .284, .039, j.gerar_mapa, BORDA)
        self.deposito = botao(e, "Base · Central NEXUS", 0, .053, .284, .035, j.trocar_deposito)
        texto(e, "ESTRATÉGIA DE OTIMIZAÇÃO", -.14, .020, .44, SUAVE)
        self.algoritmo = botao(e, j.estado.algoritmo, 0, -.021, .284, .038, self.trocar_algoritmo)
        self.tempo = botao(e, f"Limite de busca · {j.config['tempo_otimizacao_segundos']:g} s", 0, -.065, .284, .032, self.trocar_tempo)
        self.modalidade = botao(e, "Malha rodoviária · Dijkstra", 0, -.105, .284, .032, j.trocar_modalidade)
        self.otimizar = botao(e, "OTIMIZAR ROTA", 0, -.155, .284, .047,
                              j.otimizar, CIANO.tint(-.08), FUNDO)
        self.simular = botao(e, "INICIAR SIMULAÇÃO", 0, -.208, .284, .041, j.iniciar_simulacao, VERDE.tint(-.15), FUNDO)
        botao(e, "COMPARAR ALGORITMOS", 0, -.256, .284, .039, j.comparar)
        botao(e, "Reiniciar missão", -.073, -.301, .137, .031, j.reiniciar)
        botao(e, "Desfazer", .075, -.301, .134, .031, j.desfazer)
        botao(e, "Bloquear rua", -.073, -.342, .137, .031, lambda: j.evento_dinamico("bloqueio"), ROSA.tint(-.62))
        botao(e, "Obras: custo ×2", .075, -.342, .134, .031, lambda: j.evento_dinamico("obras"), LARANJA.tint(-.70))
        botao(e, "Salvar missão / JSON", 0, -.386, .284, .031, j.exportar)

        texto(d, "02 / TELEMETRIA DA ROTA", -.14, .357, .51, CIANO)
        self.distancia = texto(d, "— km", -.14, .323, 1.55)
        self.nome_algoritmo = texto(d, "Selecione os destinos no mapa", -.14, .268, .51, SUAVE)
        self.prova = texto(d, "PLANEJAMENTO MANUAL", -.14, .237, .48, LARANJA)
        self.metricas = {}
        rotulos = ["Entregas realizadas", "Tempo de cálculo", "Melhor conhecida", "Percorrido", "Combustível estimado", "Economia de custo", "Custo da rota (u.c.)"]
        for i, rotulo in enumerate(rotulos):
            y = .191 - i * .029
            texto(d, rotulo, -.14, y, .49, SUAVE)
            self.metricas[rotulo] = Text(parent=d, text="—", x=.138, y=y, scale=.52,
                                       color=TEXTO, origin=(.5, .5), z=-.07)
        texto(d, "SEQUÊNCIA DE ENTREGAS", -.14, -.047, .48, CIANO)
        self.destinos = []
        for i in range(7):
            y = -.084 - i * .028
            b = botao(d, "", 0, y, .286, .026, lambda: None)
            self.destinos.append(b)
        self.anterior = botao(d, "‹", -.12, -.291, .042, .028, lambda: self.paginar(-1))
        self.pagina = texto(d, "1 / 1", -.04, -.284, .48, SUAVE)
        self.proxima = botao(d, "›", .12, -.291, .042, .028, lambda: self.paginar(1))
        self.pontuacao = texto(d, "MISSÃO EM PLANEJAMENTO", -.14, -.327, .5, VERDE)
        texto(d, "Trânsito por uma cidade não conta\ncomo entrega fora da sequência.", -.14, -.360, .46, SUAVE)

        self.grafo = botao(r, "Grafo · G", -.365, .368, .18, .03, j.alternar_grafo)
        self.camera = botao(r, "Vista isométrica · C", -.10, .368, .30, .03, j.trocar_camera)
        botao(r, "Ranking", .316, .368, .18, .03, j.abrir_resultados)
        for x, cor, rotulo in ((-.385, LARANJA, "SUA ROTA"), (-.095, VERDE, "COMPUTADOR"), (.25, ROXO, "DEPÓSITO")):
            painel(r, x, .323, .012, .012, cor)
            texto(r, rotulo, x + .018, .332, .45, SUAVE)
        self.dica_cidade = Text(parent=r, text="", origin=(0, 0), y=.277,
                               color=TEXTO, scale=.62, background=True, z=-.12)
        botao(r, "Pausar / continuar", -.27, -.298, .245, .034, j.pausar)
        self.velocidade = botao(r, "Velocidade · 1×", .01, -.298, .23, .034, self.trocar_velocidade)
        self.etapas = botao(r, "Rever etapas", .285, -.298, .23, .034, j.reproduzir_etapas)
        painel(r, 0, -.379, .94, .105, PAINEL)
        self.status = texto(r, "PREPARANDO MISSÃO", -.445, -.342, .53, CIANO)
        self.explicacao = texto(r, "Clique nos marcadores ou na lista para planejar as entregas.", -.445, -.375, .53, SUAVE)
        self.detalhe = texto(r, "O caminhão percorrerá as ruas e voltará ao depósito.", -.445, -.400, .45, SUAVE)
        texto(r, "WASD  mover    /    botão direito  girar    /    roda  zoom    /    espaço  pausar", -.46, -.463, .47, SUAVE)
        self.atalhos = texto(r, "N  novo mapa    O  otimizar    B  comparar    H  ajuda", -.46, -.484, .43, SUAVE)

    @property
    def editando(self):
        return self.quantidade.active or self.semente.active

    def trocar_modo(self):
        atual = self.MODOS.index(self.jogo.estado.modo)
        self.jogo.estado.modo = self.MODOS[(atual + 1) % len(self.MODOS)]
        self.modo.text = self.jogo.estado.modo
        self.jogo.notificar("MODO ALTERADO", self.jogo.estado.modo)

    def trocar_dificuldade(self):
        quantidade = int(self.quantidade.text or 15)
        indice = next((i for i, (_, n) in enumerate(self.DIFICULDADES) if n >= quantidade), 1)
        nome, n = self.DIFICULDADES[(indice + 1) % len(self.DIFICULDADES)]
        self.quantidade.text = str(n)
        self.dificuldade.text = f"Dificuldade · {nome}"

    def trocar_algoritmo(self):
        j = self.jogo
        indice = ALGORITMOS.index(j.estado.algoritmo)
        j.estado.algoritmo = ALGORITMOS[(indice + 1) % len(ALGORITMOS)]
        self.algoritmo.text = j.estado.algoritmo
        j.notificar("ESTRATÉGIA", j.estado.algoritmo)

    def trocar_tempo(self):
        tempos = [2.0, 3.0, 5.0]
        atual = self.jogo.config["tempo_otimizacao_segundos"]
        self.jogo.config["tempo_otimizacao_segundos"] = tempos[(tempos.index(atual) + 1) % 3] if atual in tempos else 3.0
        self.tempo.text = f"Limite de busca · {self.jogo.config['tempo_otimizacao_segundos']:g} s"

    def trocar_velocidade(self):
        velocidades = [.5, 1.0, 2.0, 4.0, 8.0]
        atual = self.jogo.estado.velocidade
        self.jogo.estado.velocidade = velocidades[(velocidades.index(atual) + 1) % len(velocidades)]
        self.velocidade.text = f"Velocidade · {self.jogo.estado.velocidade:g}×"

    def paginar(self, direcao):
        j = self.jogo
        total = max(1, (len(j.cenario.cidades) + 6) // 7)
        j.estado.pagina_destinos = (j.estado.pagina_destinos + direcao) % total
        self.atualizar_lista()

    def atualizar_lista(self):
        j, estado, c = self.jogo, self.jogo.estado, self.jogo.cenario
        ordem = estado.ativa.ordem[:-1] if estado.ativa else estado.ordem_manual
        selecionadas = set(ordem)
        restantes = [no for no in c.cidades if no not in selecionadas]
        lista = list(ordem) + restantes
        entregues = j.simulacao.entregues if j.simulacao else set()
        for i, b in enumerate(self.destinos):
            indice = estado.pagina_destinos * 7 + i
            b.enabled = indice < len(lista)
            if indice >= len(lista):
                continue
            no = lista[indice]
            prefixo = "BASE" if no == c.deposito else f"{ordem.index(no):02d}" if no in ordem else "··"
            nome = c.nome(no)
            b.text = f"{prefixo}  {nome[:20]}"
            b.color = color.hex("#193D38") if no in entregues else color.hex("#3C3224") if no in selecionadas else SUPERFICIE
            b.on_click = lambda no=no: j.selecionar_cidade(no)
        total = max(1, (len(lista) + 6) // 7)
        self.pagina.text = f"{estado.pagina_destinos + 1} / {total}"

    def atualizar(self):
        j, e = self.jogo, self.jogo.estado
        if not j.cenario:
            return
        self.topo.text = f"OPERAÇÃO {j.cenario.semente:03d}    /    {len(j.cenario.cidades):02d} CIDADES"
        rota = e.ativa
        self.distancia.text = km(rota.distancia) if rota else km(j.distancia_manual())
        self.nome_algoritmo.text = rota.algoritmo if rota else "Planejamento manual"
        if rota and rota.otima_comprovada:
            self.prova.text = "ÓTIMO COMPROVADO"
        elif rota and rota.reotimizacao:
            self.prova.text = "REOTIMIZAÇÃO DINÂMICA"
        elif rota and rota.algoritmo != "Rota do jogador":
            melhor = e.referencia and abs(rota.custo - e.referencia.custo) < 1e-6
            self.prova.text = "MELHOR CONHECIDA · APROXIMADA" if melhor else "APROXIMADA · SEM PROVA DE ÓTIMO"
        else:
            self.prova.text = "ROTA DO JOGADOR"
        self.prova.color = VERDE if rota and rota.otima_comprovada else SUAVE
        sim = j.simulacao
        entregas = sim.entregas_realizadas if sim else 0
        self.metricas["Entregas realizadas"].text = f"{entregas} / {len(j.cenario.cidades) - 1}"
        self.metricas["Tempo de cálculo"].text = f"{rota.tempo_segundos * 1000:.1f} ms" if rota else "—"
        referencia = e.referencia
        self.metricas["Melhor conhecida"].text = km(referencia.distancia) if referencia else "—"
        self.metricas["Percorrido"].text = km(sim.distancia if sim else 0)
        distancia = rota.distancia if rota else j.distancia_manual()
        custo_combustivel = distancia / 1000 * j.config["consumo_litros_por_km"] * j.config["preco_litro"]
        self.metricas["Combustível estimado"].text = f"R$ {custo_combustivel:.2f}".replace(".", ",")
        economia = economia_percentual(e.manual.custo if e.manual else j.custo_inicial, rota.custo) if rota and not rota.reotimizacao else None
        self.metricas["Economia de custo"].text = f"{economia:+.1f}%" if economia is not None else "—"
        self.metricas["Custo da rota (u.c.)"].text = f"{rota.custo:,.0f}" if rota else "—"
        self.deposito.text = "Base · " + j.cenario.nome(j.cenario.deposito)[:21]
        self.otimizar.disabled = e.ocupada
        self.simular.disabled = e.ocupada or rota is None
        self.pontuacao.text = f"PONTUAÇÃO    {j.pontos:04d} / 1000" if j.pontos else "MISSÃO EM PLANEJAMENTO"

    def redimensionar(self):
        if abs(camera.aspect_ratio - self.aspecto) < .01:
            return
        # A janela conserva a proporção 16:9; maximizar reposiciona os painéis laterais.
        self.aspecto = camera.aspect_ratio
        margem = camera.aspect_ratio / 2 - .18
        self.esquerda.x, self.direita.x = -margem, margem

