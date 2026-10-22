"""Comportamentos comuns de comandos, telemetria e paginação da HUD."""

from ursina import Entity, Text, camera, color, mouse

from ..algorithms.registro import ALGORITMOS
from ..core.game_state import economia_percentual
from ..graphics.estilo import (CIANO, LARANJA, ROXO, SUAVE, SUPERFICIE,
                               TEXTO, VERDE)
from .componentes import botao, km, painel, texto


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
        raise NotImplementedError("A subclasse deve criar a composição visual da HUD.")

    @property
    def editando(self):
        return bool(getattr(self.quantidade, "active", False) or
                    getattr(self.semente, "active", False))

    def trocar_modo(self):
        atual = self.MODOS.index(self.jogo.estado.modo)
        self.jogo.estado.modo = self.MODOS[(atual + 1) % len(self.MODOS)]
        self.modo.text = self.jogo.estado.modo
        self.jogo.notificar("MODO ALTERADO", self.jogo.estado.modo)

    def trocar_dificuldade(self):
        quantidade = int(self.quantidade.text or 15)
        indice = next((i for i, (_, n) in enumerate(self.DIFICULDADES) if n >= quantidade), 1)
        nome, quantidade = self.DIFICULDADES[(indice + 1) % len(self.DIFICULDADES)]
        self.quantidade.text = str(quantidade)
        self.dificuldade.text = f"Dificuldade · {nome}"

    def trocar_algoritmo(self):
        jogo = self.jogo
        indice = ALGORITMOS.index(jogo.estado.algoritmo)
        jogo.estado.algoritmo = ALGORITMOS[(indice + 1) % len(ALGORITMOS)]
        self.algoritmo.text = jogo.estado.algoritmo
        jogo.notificar("ESTRATÉGIA", jogo.estado.algoritmo)

    def trocar_tempo(self):
        tempos = [2.0, 3.0, 5.0]
        atual = self.jogo.config["tempo_otimizacao_segundos"]
        self.jogo.config["tempo_otimizacao_segundos"] = (
            tempos[(tempos.index(atual) + 1) % len(tempos)] if atual in tempos else 3.0)
        self.tempo.text = f"Limite de busca · {self.jogo.config['tempo_otimizacao_segundos']:g} s"

    def trocar_velocidade(self):
        velocidades = [.5, 1.0, 2.0, 4.0, 8.0]
        atual = self.jogo.estado.velocidade
        self.jogo.estado.velocidade = velocidades[(velocidades.index(atual) + 1) % len(velocidades)]
        self.velocidade.text = f"{self.jogo.estado.velocidade:g}×"

    def paginar(self, direcao):
        total = max(1, (len(self.jogo.cenario.cidades) + 6) // 7)
        estado = self.jogo.estado
        estado.pagina_destinos = (estado.pagina_destinos + direcao) % total
        self.atualizar_lista()

    def atualizar_lista(self):
        jogo, estado, cenario = self.jogo, self.jogo.estado, self.jogo.cenario
        rota = estado.ativa
        ordem = rota.ordem[:-1] if rota else list(estado.ordem_manual)
        selecionadas = set(ordem)
        lista = list(ordem) + [no for no in cenario.cidades if no not in selecionadas]
        simulacao = jogo.simulacao
        entregues = simulacao.entregues if simulacao else set()
        proxima = None
        if not (simulacao and simulacao.concluida):
            proxima = next((no for no in ordem if no != cenario.deposito and no not in entregues), None)

        tons = {
            "base": color.hex("#9B72FF"),
            "concluida": color.hex("#40E39B"),
            "proxima": color.hex("#FFD34E"),
            "pendente": color.hex("#FFB020"),
        }
        for i, botao_destino in enumerate(self.destinos):
            indice = estado.pagina_destinos * 7 + i
            botao_destino.enabled = indice < len(lista)
            if indice >= len(lista):
                continue
            no = lista[indice]
            prefixo = ("BASE" if no == cenario.deposito else
                       f"{ordem.index(no):02d}" if no in selecionadas else "··")
            botao_destino.text = f"{prefixo}  {cenario.nome(no)[:19]}"
            if no == cenario.deposito:
                tom = tons["base"]
            elif no in entregues:
                tom = tons["concluida"]
            elif no == proxima:
                tom = tons["proxima"]
            else:
                tom = tons["pendente"]
            botao_destino.color = tom
            botao_destino.highlight_color = tom.tint(.12)
            botao_destino.pressed_color = tom.tint(-.12)
            botao_destino.text_entity.color = color.hex("#172033")
            botao_destino.on_click = lambda no=no: jogo.selecionar_cidade(no)

        total = max(1, (len(lista) + 6) // 7)
        self.pagina.text = f"{estado.pagina_destinos + 1} / {total}"
        self.anterior.disabled = total <= 1
        self.proxima.disabled = total <= 1

    def atualizar(self):
        jogo, estado = self.jogo, self.jogo.estado
        if not jogo.cenario:
            return
        rota = estado.ativa
        if hasattr(self, "topo"):
            texto_topo = f"OPERAÇÃO {jogo.cenario.semente:03d}"
            if self.topo.text != texto_topo:
                self.topo.text = texto_topo
        if hasattr(self, "cidades"):
            texto_cidades = f"{len(jogo.cenario.cidades)} CIDADES"
            if self.cidades.text != texto_cidades:
                self.cidades.text = texto_cidades

        self.distancia.text = km(rota.distancia) if rota else km(jogo.distancia_manual())
        self.nome_algoritmo.text = rota.algoritmo if rota else "Planejamento manual"
        if rota and rota.otima_comprovada:
            self.prova.text = "ÓTIMO COMPROVADO"
        elif rota and rota.reotimizacao:
            self.prova.text = "REOTIMIZAÇÃO DINÂMICA"
        elif rota and rota.algoritmo != "Rota do jogador":
            melhor = estado.referencia and abs(rota.custo - estado.referencia.custo) < 1e-6
            self.prova.text = ("MELHOR CONHECIDA · APROXIMADA" if melhor else
                               "APROXIMADA · SEM PROVA DE ÓTIMO")
        else:
            self.prova.text = "ROTA DO JOGADOR"
        self.prova.color = VERDE if rota and rota.otima_comprovada else SUAVE

        simulacao = jogo.simulacao
        entregas = simulacao.entregas_realizadas if simulacao else 0
        self.metricas["Entregas realizadas"].text = f"{entregas} / {len(jogo.cenario.cidades) - 1}"
        self.metricas["Tempo de cálculo"].text = f"{rota.tempo_segundos * 1000:.1f} ms" if rota else "—"
        referencia = estado.referencia
        self.metricas["Melhor conhecida"].text = km(referencia.distancia) if referencia else "—"
        self.metricas["Percorrido"].text = km(simulacao.distancia if simulacao else 0)
        distancia = rota.distancia if rota else jogo.distancia_manual()
        custo_combustivel = (distancia / 1000 * jogo.config["consumo_litros_por_km"] *
                             jogo.config["preco_litro"])
        self.metricas["Combustível estimado"].text = f"R$ {custo_combustivel:.2f}".replace(".", ",")
        base = estado.manual.custo if estado.manual else jogo.custo_inicial
        economia = economia_percentual(base, rota.custo) if rota and not rota.reotimizacao else None
        self.metricas["Economia de custo"].text = f"{economia:+.1f}%" if economia is not None else "—"
        self.metricas["Custo da rota (u.c.)"].text = f"{rota.custo:,.0f}" if rota else "—"
        if jogo.preferencias["unidade"] == "m":
            self.distancia.text = f"{(rota.distancia if rota else jogo.distancia_manual()):,.0f} m".replace(",", ".")
            if referencia:
                self.metricas["Melhor conhecida"].text = f"{referencia.distancia:.0f} m"
            self.metricas["Percorrido"].text = f"{simulacao.distancia if simulacao else 0:.0f} m"

        self.otimizar.disabled = estado.ocupada
        self.simular.disabled = estado.ocupada or rota is None
        self.pontuacao.text = (f"PONTUAÇÃO  {jogo.pontos:04d} / 1000" if jogo.pontos
                               else "MISSÃO EM PLANEJAMENTO")
        if hasattr(self, "velocidade"):
            velocidade = f"{estado.velocidade:g}×"
            if self.velocidade.text != velocidade:
                self.velocidade.text = velocidade
        if hasattr(self, "camera"):
            modo_camera = jogo.controle_camera.modo
            if self.camera.text != modo_camera:
                self.camera.text = modo_camera
        if hasattr(self, "pausa"):
            pausada = bool((jogo.simulacao and jogo.simulacao.pausada) or
                           (jogo.etapas and jogo.etapas_pausadas))
            texto_pausa = "Retomar" if pausada else "Pausar"
            if self.pausa.text != texto_pausa:
                self.pausa.text = texto_pausa

    def sobre_interface(self):
        entidade = mouse.hovered_entity
        while entidade is not None:
            if entidade in (self.raiz, camera.ui):
                return True
            entidade = getattr(entidade, "parent", None)
        return False

    def redimensionar(self):
        if abs(camera.aspect_ratio - self.aspecto) >= .01:
            self.aspecto = camera.aspect_ratio
