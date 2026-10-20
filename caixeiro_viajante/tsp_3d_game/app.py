"""Coordenação da missão: renderização na thread principal e cálculo em processo."""

from __future__ import annotations

import atexit
import copy
import math
import random
from time import perf_counter

import networkx as nx
from ursina import (AmbientLight, DirectionalLight, Entity, Text, Vec3, application,
                    camera, color, mouse, time, window)

from .algorithms.registro import ALGORITMOS
from .core.game_state import EstadoJogo, SimulacaoPercurso, pontuar
from .core.graph_manager import alterar_estrada, grafo_transitavel
from .core.modelos import ResultadoRota, custo_rota
from .core.persistencia import salvar_sessao
from .core.route_validator import validar_resultado
from .core.scenario_generator import gerar_cenario
from .core.servico_otimizacao import ServicoOtimizacao
from .graphics.camera_controller import CameraMissao
from .graphics.estilo import CIANO, FUNDO, LARANJA, ROSA, SUAVE, VERDE
from .graphics.route_renderer import RenderizadorRota
from .graphics.vehicle import Veiculo3D
from .graphics.world import Mundo3D
from .ui.dashboard import Dashboard, km
from .ui.results import JanelaResultados


class JogoTSP(Entity):
    def __init__(self, config, cenario=None):
        super().__init__()
        self.config = config
        self.estado = EstadoJogo()
        self.servico = ServicoOtimizacao()
        self.fechado = False
        atexit.register(self.fechar)
        self.cenario = None
        self.matriz = None
        self.matriz_ativa = None
        self.mundo = self.veiculo = self.rotas = None
        self.simulacao = None
        self.custo_inicial = None
        self.pontos = 0
        self.janela_resultados = None
        self.evento_pendente = None
        self.contexto_dinamico = None
        self.etapas = []
        self.indice_etapa = 0
        self.tempo_etapa = 0.0
        self.etapas_pausadas = False
        self.iniciar_apos_etapas = False
        self.tempo_atualizacao = 0.0
        self.horario_calculo = 0.0
        self.finalidade = "preparar"
        self.erro_trabalhador = None
        window.color = FUNDO
        AmbientLight(color=color.rgba32(155, 173, 192, 255))
        self.sol = DirectionalLight(shadows=True, shadow_map_resolution=(2048, 2048),
                                    rotation=(55, -35, 0), color=color.rgba32(245, 237, 211, 255))
        self.ui = Dashboard(self)
        self._carregar_missao(cenario or gerar_cenario(config["quantidade_cidades"],
                              config["semente"], config["metros_por_unidade"]))

    def _carregar_missao(self, cenario):
        if self.janela_resultados:
            self.janela_resultados.fechar()
        for objeto in (self.mundo, self.rotas, self.veiculo):
            if objeto:
                objeto.destruir()
        self.cenario = cenario
        modo, algoritmo = self.estado.modo, self.estado.algoritmo
        self.estado = EstadoJogo(modo=modo, algoritmo=algoritmo, modalidade=self.estado.modalidade)
        self.estado.ordem_manual = [cenario.deposito]
        self.matriz = self.matriz_ativa = None
        self.simulacao = None
        self.custo_inicial = None
        self.pontos = 0
        self.etapas = []
        self.evento_pendente = self.contexto_dinamico = None
        self.mundo = Mundo3D(cenario, self.selecionar_cidade)
        if self.config["mostrar_grafo"]:
            self.mundo.alternar_grafo()
        self.rotas = RenderizadorRota(cenario)
        self.veiculo = Veiculo3D(cenario.posicao(cenario.deposito))
        self.veiculo.definir_modalidade(self.estado.modalidade)
        self.veiculo.atualizar(cenario.posicao(cenario.deposito), (0, 0, 1), 0)
        self.controle_camera = CameraMissao(cenario.lado * cenario.espacamento)
        self.sol.update_bounds(self.mundo.raiz)
        self.ui.quantidade.text = str(len(cenario.cidades))
        self.ui.semente.text = str(cenario.semente)
        dificuldade = "Fácil" if len(cenario.cidades) <= 8 else "Médio" if len(cenario.cidades) <= 15 else "Difícil" if len(cenario.cidades) <= 30 else "Especialista"
        self.ui.dificuldade.text = f"Dificuldade · {dificuldade}"
        self.ui.atualizar_lista()
        self._solicitar("preparar", "preparar")
        self.notificar("NOVA MISSÃO", "Preparando distâncias e caminhos mínimos em segundo plano…")

    def _solicitar(self, acao, finalidade, **extras):
        self.finalidade = finalidade
        self.estado.ocupada = True
        self.horario_calculo = perf_counter()
        self.erro_trabalhador = None
        dados = dict(cenario=copy.deepcopy(self.cenario), modalidade=self.estado.modalidade,
                     escala=self.config["metros_por_unidade"], algoritmo=self.estado.algoritmo,
                     tempo_limite=self.config["tempo_otimizacao_segundos"],
                     limite_held_karp=self.config["limite_held_karp"])
        dados.update(extras)
        self.servico.enviar(acao, **dados)

    def gerar_mapa(self):
        try:
            quantidade, semente = int(self.ui.quantidade.text), int(self.ui.semente.text)
            if quantidade > self.config["limite_cidades"]:
                raise ValueError(f"O limite configurado é {self.config['limite_cidades']} cidades.")
            self._carregar_missao(gerar_cenario(quantidade, semente, self.config["metros_por_unidade"]))
        except ValueError as erro:
            self.notificar("CONFIGURAÇÃO INVÁLIDA", str(erro), erro=True)

    def reiniciar(self):
        antigo_deposito = self.cenario.deposito
        cenario = gerar_cenario(len(self.cenario.cidades), self.cenario.semente, self.config["metros_por_unidade"])
        cenario.deposito = antigo_deposito
        self._carregar_missao(cenario)

    def trocar_deposito(self):
        if self.estado.ocupada or (self.simulacao and not self.simulacao.concluida):
            self.notificar("BASE", "Reinicie a missão antes de trocar a base durante uma viagem.")
            return
        indice = self.cenario.cidades.index(self.cenario.deposito)
        self.cenario.deposito = self.cenario.cidades[(indice + 1) % len(self.cenario.cidades)]
        self._limpar_rotas()
        self.estado.ordem_manual = [self.cenario.deposito]
        self.veiculo.atualizar(self.cenario.posicao(self.cenario.deposito), (0, 0, 1), 0)
        self.mundo.atualizar_cidades([], set(), self.cenario.deposito)
        self.ui.atualizar_lista()
        self.notificar("NOVO DEPÓSITO", self.cenario.nome(self.cenario.deposito))

    def _limpar_rotas(self):
        self.estado.manual = self.estado.ativa = None
        self.estado.resultados.clear()
        self.simulacao = None
        self.contexto_dinamico = None
        self.etapas = []
        self.pontos = 0
        self.rotas.limpar()

    def trocar_modalidade(self):
        nova = "euclidiano" if self.estado.modalidade == "rodoviario" else "rodoviario"
        self.estado.modalidade = nova
        self.veiculo.definir_modalidade(nova)
        self.ui.modalidade.text = "Euclidiano · drone abstrato" if nova == "euclidiano" else "Malha rodoviária · Dijkstra"
        self._limpar_rotas()
        self.estado.ordem_manual = [self.cenario.deposito]
        self.matriz = self.matriz_ativa = None
        self.veiculo.atualizar(self.cenario.posicao(self.cenario.deposito), (0, 0, 1), 0)
        self._solicitar("preparar", "preparar")
        self.ui.atualizar_lista()
        self.notificar("MODALIDADE", "Distâncias diretas: abstração matemática, não representa ruas." if nova == "euclidiano" else "Caminhos mínimos restritos às ruas transitáveis.")

    def selecionar_cidade(self, no):
        if self.janela_resultados or self.estado.ocupada:
            return
        if self.estado.modo != "Desafio Humano":
            self.notificar("DESTINO", self.cenario.nome(no) + " · altere para Desafio Humano para montar uma rota.")
            return
        if self.simulacao and not self.simulacao.concluida:
            self.notificar("VIAGEM EM ANDAMENTO", "Reinicie a missão para planejar outra sequência.")
            return
        if self.matriz is None or self.matriz.revisao != self.cenario.revisao:
            self.notificar("ROTA DESATUALIZADA", "Reinicie ou recalcule as distâncias antes de selecionar destinos.", erro=True)
            return
        if no in self.estado.ordem_manual:
            self.notificar("DESTINO JÁ SELECIONADO", self.cenario.nome(no))
            return
        self.etapas = []
        self.simulacao = None
        self.estado.ativa = None
        self.rotas.limpar("ativa")
        self.estado.ordem_manual.append(no)
        if len(self.estado.ordem_manual) == len(self.cenario.cidades):
            self.estado.ordem_manual.append(self.cenario.deposito)
            indices = [self.matriz.indice(n) for n in self.estado.ordem_manual]
            resultado = ResultadoRota("Rota do jogador", self.estado.ordem_manual.copy(),
                custo_rota(self.matriz.custos, indices), custo_rota(self.matriz.distancias, indices), 0,
                observacao="Sequência de entregas escolhida pelo jogador.")
            validar_resultado(resultado, self.matriz, self.cenario)
            self.estado.manual = self.estado.ativa = resultado
            self.matriz_ativa = self.matriz
            self.notificar("ROTA MANUAL CONCLUÍDA", "Retorno à base incluído. Inicie a viagem ou compare com o computador.")
            if self.estado.referencia is None:
                self._solicitar("resolver", "referencia", algoritmo="OR-Tools + GLS")
        else:
            self.notificar("ENTREGA ADICIONADA", f"{len(self.estado.ordem_manual) - 1} de {len(self.cenario.cidades) - 1} destinos planejados.")
        self.rotas.desenhar("manual", self.matriz, self.estado.ordem_manual, LARANJA, altura=.32)
        self.mundo.atualizar_cidades(self.estado.ordem_manual, set(), self.cenario.deposito)
        self.ui.atualizar_lista()

    def desfazer(self):
        if self.estado.ocupada:
            return
        if self.simulacao and not self.simulacao.concluida:
            self.notificar("VIAGEM EM ANDAMENTO", "Reinicie a missão para editar as entregas.")
            return
        ordem = self.estado.ordem_manual
        if len(ordem) > 1 and ordem[-1] == self.cenario.deposito:
            ordem.pop()
        if len(ordem) > 1:
            ordem.pop()
        self.estado.manual = self.estado.ativa = None
        self.simulacao = None
        self.etapas = []
        self.rotas.limpar("ativa")
        if self.matriz:
            self.rotas.desenhar("manual", self.matriz, ordem, LARANJA, altura=.32)
        self.mundo.atualizar_cidades(ordem, set(), self.cenario.deposito)
        self.ui.atualizar_lista()
        self.notificar("EDIÇÃO DA ROTA", "Última entrega removida.")

    def distancia_manual(self):
        if not self.matriz:
            return 0.0
        indices = [self.matriz.indice(no) for no in self.estado.ordem_manual]
        return custo_rota(self.matriz.distancias, indices)

    def otimizar(self):
        if self.estado.ocupada:
            return
        if self.simulacao and self.simulacao.distancia > 0 and not self.simulacao.concluida:
            self._reotimizar_atual()
            return
        self.etapas = []
        self.simulacao = None
        self._solicitar("resolver", "automatico")
        self.notificar("OTIMIZAÇÃO", "Cálculo em processo separado; a câmera continua disponível.")

    def comparar(self):
        if self.estado.ocupada:
            return
        if self.simulacao and not self.simulacao.concluida and self.simulacao.distancia > 0:
            self.notificar("VIAGEM EM ANDAMENTO", "Conclua ou reinicie a missão para comparar ciclos completos.")
            return
        self.estado.modo = "Batalha de Algoritmos"
        self.ui.modo.text = self.estado.modo
        self.etapas = []
        self.simulacao = None
        self.estado.resultados.clear()
        self._solicitar("comparar", "batalha")
        self.notificar("BATALHA INICIADA", "Todos os métodos recebem a mesma matriz. Held–Karp respeita o limite configurado.")

    def _receber_resultados(self):
        for tipo, conteudo in self.servico.receber():
            if tipo == "matriz":
                self.matriz_ativa = conteudo
                if self.finalidade != "dinamico":
                    self.matriz = conteudo
                    ordem = [conteudo.indice(no) for no in self.cenario.cidades] + [conteudo.indice(self.cenario.cidades[0])]
                    self.custo_inicial = custo_rota(conteudo.custos, ordem)
            elif tipo == "status":
                self.estado.status = conteudo
            elif tipo == "resultado":
                if self.finalidade == "dinamico":
                    conteudo.reotimizacao = True
                if not conteudo.reotimizacao and self.finalidade != "dinamico":
                    self.estado.resultados[conteudo.algoritmo] = conteudo
                if self.finalidade == "automatico":
                    self.exibir_resultado(conteudo, animar=True)
                elif self.finalidade == "dinamico":
                    self.exibir_resultado(conteudo, animar=False)
                    self._iniciar_viagem_dinamica()
            elif tipo == "aviso":
                self.ui.detalhe.text = conteudo[:105]
            elif tipo == "erro":
                self.estado.ocupada = False
                self.erro_trabalhador = conteudo
                self.notificar("NÃO FOI POSSÍVEL CALCULAR", conteudo, erro=True)
            elif tipo in ("concluido", "cancelado"):
                self.estado.ocupada = False
                if self.finalidade == "preparar":
                    self.notificar("MISSÃO PRONTA", "Clique nas cidades para planejar ou peça uma rota ao computador.")
                elif self.finalidade == "batalha":
                    if self.estado.referencia:
                        self.exibir_resultado(self.estado.referencia, animar=False)
                    self.abrir_resultados()
                    self.notificar("COMPARAÇÃO CONCLUÍDA", "Ranking calculado sobre a mesma malha viária.")
                elif self.finalidade == "referencia":
                    self.notificar("REFERÊNCIA CALCULADA", "Sua rota está preservada. O computador já tem uma solução para comparação.")
                elif self.finalidade == "automatico" and not self.etapas:
                    self.notificar("ROTA CALCULADA", self.estado.ativa.observacao if self.estado.ativa else "")
                self.ui.atualizar_lista()

    def exibir_resultado(self, resultado, animar=False):
        self.etapas = []
        if self.simulacao:
            self.simulacao.pausada = True
        self.estado.ativa = resultado
        cor = LARANJA if resultado.algoritmo == "Rota do jogador" else VERDE
        matriz = self.matriz_ativa if resultado.reotimizacao else self.matriz
        if matriz is None:
            return
        self.rotas.limpar("etapa")
        self.rotas.limpar("removidas")
        self.rotas.limpar("adicionadas")
        self.rotas.desenhar("ativa", matriz, resultado.ordem, cor, progressiva=animar)
        entregues = self.simulacao.entregues if self.simulacao else set()
        self.mundo.atualizar_cidades(resultado.ordem, entregues, self.cenario.deposito)
        self.ui.atualizar_lista()
        if animar and self.estado.modo == "Inteligência Artificial":
            self.reproduzir_etapas(iniciar_depois=True)
        elif animar:
            self.notificar("ROTA CALCULADA", resultado.observacao)

    def iniciar_simulacao(self):
        if self.estado.ocupada:
            return
        resultado = self.estado.ativa
        if resultado is None:
            self.notificar("ROTA NECESSÁRIA", "Complete a seleção manual ou calcule uma rota.")
            return
        self.etapas = []
        self.rotas.limpar("etapa")
        self.rotas.limpar("removidas")
        self.rotas.limpar("adicionadas")
        if resultado.reotimizacao:
            self._iniciar_viagem_dinamica()
            return
        try:
            validar_resultado(resultado, self.matriz, self.cenario)
            self.simulacao = SimulacaoPercurso(self.cenario, self.matriz, resultado.ordem,
                                               self.config["metros_por_unidade"])
            self.pontos = 0
            self.mundo.atualizar_cidades(resultado.ordem, set(), self.cenario.deposito)
            self.notificar("VEÍCULO EM ROTA", "As entregas são confirmadas somente na ordem planejada.")
        except ValueError as erro:
            self.notificar("ROTA INVÁLIDA", str(erro), erro=True)

    def pausar(self):
        if self.estado.ocupada:
            return
        if self.etapas:
            self.etapas_pausadas = not self.etapas_pausadas
        elif self.simulacao:
            self.simulacao.pausada = not self.simulacao.pausada
            self.notificar("PAUSADO" if self.simulacao.pausada else "VEÍCULO EM ROTA", "Espaço ou o botão pausa/continua a viagem.")

    def reproduzir_etapas(self, iniciar_depois=False):
        resultado = self.estado.ativa
        if not resultado or not resultado.etapas:
            self.notificar("ETAPAS", "Esta rota não possui etapas intermediárias registradas.")
            return
        if self.simulacao:
            self.simulacao.pausada = True
        self.etapas = resultado.etapas
        self.indice_etapa = 0
        self.tempo_etapa = 1
        self.etapas_pausadas = False
        self.iniciar_apos_etapas = iniciar_depois
        self.notificar("REPRODUÇÃO EDUCATIVA", "Decisões reais registradas no cálculo; use a velocidade para acelerar.")

    def _animar_etapas(self, dt):
        if not self.etapas or self.etapas_pausadas:
            return
        self.tempo_etapa += dt * self.estado.velocidade
        if self.tempo_etapa < .9:
            return
        self.tempo_etapa = 0
        if self.indice_etapa >= len(self.etapas):
            iniciar = self.iniciar_apos_etapas
            self.etapas = []
            self.exibir_resultado(self.estado.ativa)
            if iniciar:
                self.iniciar_simulacao()
            return
        etapa = self.etapas[self.indice_etapa]
        if etapa.rota:
            self.rotas.desenhar("etapa", self.matriz_ativa, etapa.rota, CIANO, altura=.39)
        self.rotas.destacar_etapa(self.matriz_ativa, etapa)
        antes = f"Antes: {etapa.antes:,.1f}  →  Depois: {etapa.custo:,.1f}" if etapa.antes is not None else f"Custo acumulado: {etapa.custo:,.1f}" if etapa.custo is not None else "Estrutura combinatória calculada sobre a matriz de custos."
        self.notificar(f"ETAPA {self.indice_etapa + 1} / {len(self.etapas)}", etapa.descricao, detalhe=antes)
        self.indice_etapa += 1

    def evento_dinamico(self, tipo):
        if self.estado.ocupada or self.evento_pendente:
            return
        if self.estado.modalidade != "rodoviario":
            self.notificar("EVENTOS RODOVIÁRIOS", "Troque para o modo rodoviário para bloquear ou encarecer uma rua.")
            return
        self.etapas = []
        self.evento_pendente = tipo
        if self.simulacao and not self.simulacao.concluida and self.simulacao.distancia > 0:
            self.simulacao.parar_no_proximo_no = True
            # Um evento solicitado durante a pausa pode ser aplicado após continuar.
            self.simulacao.pausada = False
            self.notificar("EVENTO AGENDADO", "O veículo avançará até o próximo cruzamento antes de recalcular.")
        else:
            self._aplicar_evento()

    def _aplicar_evento(self):
        tipo = self.evento_pendente
        self.evento_pendente = None
        rede = grafo_transitavel(self.cenario)
        pontes_grafo = {tuple(sorted(aresta)) for aresta in nx.bridges(rede)} if tipo == "bloqueio" else set()
        candidatas = [(a, b) for a, b in rede.edges if tuple(sorted((a, b))) not in pontes_grafo
                      and (tipo == "bloqueio" or self.cenario.grafo[a][b]["fator"] == 1)]
        if not candidatas:
            self.notificar("EVENTO INDISPONÍVEL", "Não há outro trecho seguro para modificar.")
            if self.simulacao:
                self.simulacao.aguardando_evento = False
                self.simulacao.parar_no_proximo_no = False
            return
        sorteio = random.Random(self.cenario.semente + self.cenario.revisao * 79)
        a, b = sorteio.choice(candidatas)
        alterar_estrada(self.cenario, a, b, bloquear=tipo == "bloqueio", fator=2 if tipo == "obras" else 1)
        self.mundo.atualizar_bloqueios()
        self.estado.resultados.clear()
        self.estado.manual = None
        self.rotas.limpar()
        self.matriz = None
        if self.simulacao and not self.simulacao.concluida:
            self._reotimizar_atual()
        else:
            self._limpar_rotas()
            self.estado.ordem_manual = [self.cenario.deposito]
            self._solicitar("preparar", "preparar")
        self.notificar("ESTRADA BLOQUEADA" if tipo == "bloqueio" else "OBRAS NA VIA",
                       f"Trecho {a}–{b}: " + ("acesso interditado. Recalculando caminhos." if tipo == "bloqueio" else "custo duplicado, distância física preservada."))

    def _reotimizar_atual(self):
        sim = self.simulacao
        if sim is None:
            return
        if sim.progresso > 1e-7 and not sim.aguardando_evento:
            # Também permite clicar em Otimizar no meio de uma viagem.
            self.evento_pendente = "reotimizar"
            sim.parar_no_proximo_no = True
            sim.pausada = False
            return
        sim.pausada = True
        inicio = sim.ultimo_no
        restantes = [no for no in self.cenario.cidades if no != self.cenario.deposito and no not in sim.entregues]
        destinos = list(dict.fromkeys([inicio] + restantes + [self.cenario.deposito]))
        self.contexto_dinamico = {"distancia": sim.distancia, "entregues": sim.entregues.copy()}
        self.contexto_dinamico["entrega_origem"] = inicio in restantes
        self.rotas.limpar()
        self._solicitar("resolver", "dinamico", inicio=inicio, destinos=destinos, algoritmo="OR-Tools + GLS")
        self.notificar("REOTIMIZAÇÃO DINÂMICA", "OR-Tools: posição atual → entregas restantes → depósito. Não é o ciclo TSP inicial.")

    def _iniciar_viagem_dinamica(self):
        try:
            rota = self.estado.ativa
            validar_resultado(rota, self.matriz_ativa, self.cenario, rota.ordem[0], self.cenario.deposito)
            simulacao = SimulacaoPercurso(self.cenario, self.matriz_ativa, rota.ordem,
                                           self.config["metros_por_unidade"],
                                           entregar_origem=bool(self.contexto_dinamico and self.contexto_dinamico.get("entrega_origem")))
            if self.contexto_dinamico:
                simulacao.distancia = self.contexto_dinamico["distancia"]
                simulacao.entregues.update(self.contexto_dinamico["entregues"])
            self.simulacao = simulacao
            self.mundo.atualizar_cidades(rota.ordem, simulacao.entregues, self.cenario.deposito)
            self.ui.atualizar_lista()
            self.notificar("VIAGEM RECALCULADA", "Entregas anteriores preservadas; o veículo segue pelas ruas liberadas.")
        except ValueError as erro:
            self.notificar("REOTIMIZAÇÃO INVÁLIDA", str(erro), erro=True)

    def alternar_grafo(self):
        self.mundo.alternar_grafo()
        self.ui.grafo.text = "Grafo · ligado" if self.mundo.grafo_visivel else "Grafo · G"

    def trocar_camera(self):
        modos = ["Isométrica", "Aérea", "Seguir veículo"]
        modo = modos[(modos.index(self.controle_camera.modo) + 1) % len(modos)]
        self.controle_camera.escolher(modo)
        self.ui.camera.text = modo + " · C"

    def abrir_resultados(self, ajuda=False):
        if self.janela_resultados:
            self.janela_resultados.fechar()
        if self.simulacao:
            self.simulacao.pausada = True
        self.janela_resultados = JanelaResultados(self, ajuda)

    def exportar(self):
        resultados = list(self.estado.resultados.values())
        if self.estado.ativa and self.estado.ativa.reotimizacao:
            resultados.append(self.estado.ativa)
        caminho = salvar_sessao(self.cenario, resultados,
                                self.estado.manual, configuracoes=self.config | {"modalidade": self.estado.modalidade})
        self.notificar("MISSÃO SALVA", caminho.name)

    def notificar(self, status, mensagem, erro=False, detalhe=None):
        self.estado.status = status
        self.ui.status.text = status[:94]
        self.ui.status.color = ROSA if erro else CIANO
        # Quebra controlada evita que explicações longas saiam do painel central.
        mensagem = mensagem.replace("\n", " ")
        if len(mensagem) > 106:
            corte = mensagem.rfind(" ", 0, 106)
            self.ui.explicacao.text = mensagem[:corte]
            self.ui.detalhe.text = mensagem[corte:].strip()[:115]
        else:
            self.ui.explicacao.text = mensagem
            self.ui.detalhe.text = detalhe or ""

    def input(self, key):
        if not hasattr(self, "ui"):
            return
        if key == "escape":
            if self.janela_resultados:
                self.janela_resultados.fechar()
            else:
                application.quit()
            return
        if self.ui.editando or self.janela_resultados:
            return
        atalhos = {"g": self.alternar_grafo, "c": self.trocar_camera, "o": self.otimizar,
                   "b": self.comparar, "space": self.pausar, "r": self.reiniciar,
                   "h": lambda: self.abrir_resultados(ajuda=True), "backspace": self.desfazer}
        if key == "n":
            self.ui.semente.text = str(self.cenario.semente + 1)
            self.gerar_mapa()
        elif key in atalhos:
            atalhos[key]()
        self.controle_camera.entrada(key, abs(mouse.x) < .51)

    def update(self):
        dt = min(time.dt, .1)
        self._receber_resultados()
        if not self.servico.processo.is_alive() and self.estado.ocupada:
            self.estado.ocupada = False
            self.notificar("PROCESSO INTERROMPIDO", "O trabalhador de otimização foi encerrado. Feche e abra o jogo novamente.", erro=True)
        self.controle_camera.atualizar(dt, self.simulacao.posicao if self.simulacao else None,
                                      not self.ui.editando and not self.janela_resultados)
        self.rotas.atualizar(dt * self.estado.velocidade)
        if not self.janela_resultados:
            self._animar_etapas(dt)
        sim = self.simulacao
        if sim and not self.etapas and not self.janela_resultados and not self.estado.ocupada:
            concluida_antes = sim.concluida
            novas = sim.avancar(dt, self.config["velocidade_veiculo"] * self.estado.velocidade)
            self.veiculo.atualizar(sim.posicao, sim.direcao, dt)
            if novas:
                self.mundo.atualizar_cidades(self.estado.ativa.ordem, sim.entregues, self.cenario.deposito)
                self.ui.atualizar_lista()
            if sim.aguardando_evento and self.evento_pendente:
                if self.evento_pendente == "reotimizar":
                    self.evento_pendente = None
                    self._reotimizar_atual()
                else:
                    self._aplicar_evento()
            if sim is self.simulacao and sim.concluida and not concluida_antes and self.estado.ativa:
                referencia = self.estado.referencia
                rota = self.estado.ativa
                if not rota.reotimizacao:
                    self.pontos = pontuar(rota.custo, referencia.custo if referencia else rota.custo,
                                           sim.entregas_realizadas, len(self.cenario.cidades) - 1, True)
                self.notificar("MISSÃO CONCLUÍDA", f"{sim.entregas_realizadas} entregas realizadas e retorno ao depósito. Percorrido: {km(sim.distancia)}.",
                               detalhe="Reotimização dinâmica: pontuação comparativa suspensa." if rota.reotimizacao else f"Pontuação: {self.pontos} / 1000.")
        self.tempo_atualizacao += dt
        if self.tempo_atualizacao >= .15:
            self.tempo_atualizacao = 0
            self.ui.atualizar()
            self.ui.redimensionar()
            if self.estado.ocupada:
                self.ui.status.text = self.estado.status[:74] + f"  ·  {perf_counter() - self.horario_calculo:.1f}s"
            no_hover = next((no for no, marcador in self.mundo.marcadores.items() if marcador.hovered), None)
            self.ui.dica_cidade.text = self.cenario.nome(no_hover) if no_hover is not None else ""

    def fechar(self):
        if self.fechado:
            return
        self.fechado = True
        self.servico.fechar()

