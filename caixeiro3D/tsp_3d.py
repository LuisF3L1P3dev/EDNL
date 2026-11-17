"""Integracao da cena Panda3D, HUD Pygame, busca e animacao."""
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from math import hypot
from pathlib import Path
from queue import Empty, Queue, Full
from threading import Event

import pygame
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec3, loadPrcFileData

from assets3d import Biblioteca, instancia_normalizada
from camera3d import CameraIsometrica
from geometria3d import medir_rua
from mundo3d import (Viagem, diferenca_angular, heading_antecipado, heading_da_direcao,
                     limitar_heading, normalizar_angulo, pitch_da_direcao, suavizar_heading)
from solvers import Progresso, executar
from tsp_core import carregar_cenarios

ROOT = Path(__file__).resolve().parent
FASES = {'enumeracao': 'Comparando circuitos', 'dijkstra': 'Explorando caminhos',
         'matriz': 'Calculando distâncias entre pontos',
         'vizinho_proximo': 'Escolhendo o próximo destino',
         '2-opt': 'Melhorando o circuito', 'expansao': 'Expandindo pelas ruas reais',
         'concluido': 'Busca concluída'}


class Aplicacao3D(ShowBase):
    def __init__(self, tamanho=(1440, 960), *, offscreen=False):
        tamanho = max(1100, tamanho[0]), max(760, tamanho[1])
        loadPrcFileData('tsp', f'win-size {tamanho[0]} {tamanho[1]}\nwindow-title Caixeiro 3D\n'
                        'audio-library-name null\nsync-video false\nclock-mode limited\nclock-frame-rate 60\nnotify-level warning\n')
        super().__init__(windowType='offscreen' if offscreen else None)
        if self.win is None:
            raise RuntimeError('Nao foi possivel abrir uma janela Panda3D')
        self.disableMouse()
        self.setBackgroundColor(.83, .89, .81, 1)
        pygame.font.init()
        self.biblioteca = Biblioteca()
        self.mapas = carregar_cenarios(ROOT / 'data')
        self.indice_mapa = 0
        self.origem, self.destino = self.mapa.ids[0], self.mapa.ids[2]
        self.metodo, self.selecao = 'forca', 'origem'
        self.viagem = Viagem()
        self.resultado = self.etapa = None
        self.fase, self.status = 'Pronto para partir', 'Selecione um algoritmo e inicie.'
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.futuro = None
        self._cancelar = Event()
        self._fila = Queue(maxsize=96)
        self._etapas = deque(maxlen=64)
        self._resultado_pendente = None
        self._relogio = 0.
        self._replay_pausado = False
        self._fechada = False
        self._hud_relogio = 0.
        self._trecho_visual = None
        self._heading_carro = None
        self.arraste = None
        self._luzes()
        from render3d import Cena3D
        self.cena = Cena3D(self, self.mapa, self.biblioteca)
        self.camera_iso = CameraIsometrica(self, self._pontos_enquadramento())
        self.carro = self.render.attachNewNode('veiculo')
        modelo = instancia_normalizada(self.biblioteca.modelo('carro', 'delivery'), 1.6)
        modelo.reparentTo(self.carro)
        # delivery.obj tem a frente em +Z; após a conversão OBJ→Panda ela
        # aponta para -Y. O pai continua usando o heading matemático +Y.
        modelo.setH(180)
        self.modelo_carro = modelo
        limites = modelo.getTightBounds()
        if limites and limites[0] is not None:
            modelo.setZ(-limites[0].z + .04)
        self._posicionar_carro()
        from hud import HUD
        self.ui = HUD(self)
        self._eventos()
        self.taskMgr.add(self._frame, 'atualizar-jogo')
        self.ui.desenhar()

    @property
    def mapa(self):
        return self.mapas[self.indice_mapa]

    @property
    def ocupado(self):
        return self.futuro is not None or bool(self._etapas) or self._resultado_pendente is not None

    @property
    def distancia_percorrida(self):
        return self._distancias_da_viagem()[0]

    @property
    def progresso_visual(self):
        percorrida, total = self._distancias_da_viagem()
        return percorrida / total if total else float(self.viagem.concluida)

    def _distancias_da_viagem(self):
        if not self.viagem.pesos:
            return 0., 0.
        indice, fracao = self.viagem.trecho
        caminho = self.viagem.caminho
        ruas = tuple(medir_rua(self.cena.ruas[a, b]) for a, b in zip(caminho, caminho[1:]))
        total = sum(rua.comprimento for rua in ruas)
        if self.viagem.concluida:
            return total, total
        percorrida = sum(rua.comprimento for rua in ruas[:indice]) + ruas[indice].distancia(fracao)
        return percorrida, total

    def _luzes(self):
        ambiente = AmbientLight('ambiente')
        ambiente.setColor((.65, .68, .72, 1))
        self.render.setLight(self.render.attachNewNode(ambiente))
        sol = DirectionalLight('sol')
        sol.setColor((.43, .40, .36, 1))
        no = self.render.attachNewNode(sol)
        no.setHpr(-35, -55, 0)
        self.render.setLight(no)

    def _eventos(self):
        self.accept('mouse1', self.clicar)
        self.accept('mouse3', self._iniciar_arraste)
        self.accept('mouse3-up', self._terminar_arraste)
        self.accept('wheel_up', self.acao, ['zoom+'])
        self.accept('wheel_down', self.acao, ['zoom-'])
        for tecla, acao in {'1': 'mapa0', '2': 'mapa1', 'd': 'selecionar_dijkstra',
                            'f': 'selecionar_forca', 'h': 'selecionar_heuristica',
                            'z': 'reset', 'p': 'pesos', 'c': 'config',
                            'arrow_left': 'anterior', 'arrow_right': 'proximo'}.items():
            self.accept(tecla, self.acao, [acao])
        self.accept('space', self._espaco)
        self.accept('escape', self._escape)
        self.accept('window-event', self._redimensionar)

    def mouse_pixel(self):
        if self.mouseWatcherNode and self.mouseWatcherNode.hasMouse():
            p = self.mouseWatcherNode.getMouse()
            return ((p.x + 1) * self.win.getXSize() / 2, (1 - p.y) * self.win.getYSize() / 2)
        return None

    def _iniciar_arraste(self):
        p = self.mouse_pixel()
        if not self.ui.config_aberta and p and self.camera_iso.viewport.collidepoint(p):
            self.arraste = p

    def _terminar_arraste(self):
        self.arraste = None

    def _redimensionar(self, janela):
        if self._fechada or janela != self.win:
            return
        if hasattr(janela, 'getProperties') and not janela.getProperties().getOpen():
            self.fechar()
            return
        # Preservar ajuste pixel2d/aspecto e eventos nativos da base Panda3D.
        super().windowEvent(janela)
        if hasattr(self, 'camera_iso') and not janela.getProperties().getMinimized():
            self.camera_iso.ajustar()

    def _escape(self):
        if self.ui.config_aberta:
            self.ui.tratar_acao('config')
        else:
            self.fechar()

    def _espaco(self):
        if self.ui.config_aberta:
            return
        self.acao('pausa' if self.ocupado or self.viagem.caminho else 'iniciar')

    def clicar(self):
        p = self.mouse_pixel()
        if not p:
            return
        for acao, (rect, ativo) in self.ui.botoes.items():
            if rect.collidepoint(p):
                if ativo:
                    self.acao(acao)
                return
        if self.ui.config_aberta or self.ocupado or not self.camera_iso.viewport.collidepoint(p):
            return
        candidatos = [(hypot(p[0] - q[0], p[1] - q[1]), n) for n, q in self.ui.posicoes_tela.items()]
        if candidatos:
            distancia, no = min(candidatos)
            if distancia < 35:
                setattr(self, self.selecao, no)
                self._limpar()

    def _invalidar(self):
        self._cancelar.set()
        if self.futuro:
            self.futuro.cancel()
        self.futuro = None
        self._fila = Queue(maxsize=96)
        self._etapas.clear()
        self._resultado_pendente = None
        self._replay_pausado = False
        self._relogio = 0.
        self.etapa = None

    def _limpar(self):
        self._invalidar()
        velocidade = self.viagem.velocidade
        self.viagem = Viagem(velocidade=velocidade)
        self.resultado = None
        self.cena.limpar_rota()
        self._trecho_visual = None
        self._heading_carro = None
        self._posicionar_carro()
        self.fase, self.status = 'Pronto para partir', 'Selecione um algoritmo e inicie.'

    def _pontos_enquadramento(self):
        """Compatibilidade para cenas de teste e envelope da cena real."""
        pontos = getattr(self.cena, 'pontos_enquadramento', None)
        return pontos() if callable(pontos) else self.cena.posicoes

    def _trocar_mapa(self, indice):
        from render3d import Cena3D
        self._invalidar()
        self.cena.destruir()
        self.indice_mapa = indice
        self.origem, self.destino = self.mapa.ids[0], self.mapa.ids[2]
        self.metodo = 'forca' if indice == 0 else 'heuristica'
        self.selecao = 'origem'
        self.cena = Cena3D(self, self.mapa, self.biblioteca)
        self.camera_iso.centralizar(self._pontos_enquadramento())
        self._limpar()

    def _iniciar(self):
        if self.ocupado:
            return
        if (self.metodo == 'forca' and self.indice_mapa != 0) or (self.metodo == 'heuristica' and self.indice_mapa != 1):
            self.fase, self.status = 'Metodo indisponivel', 'Escolha um algoritmo disponivel neste mapa.'
            return
        self._limpar()
        self._cancelar = Event()
        fila, cancelar = self._fila, self._cancelar
        contador = [0]
        def progresso(etapa):
            if cancelar.is_set():
                return
            if etapa.fase == 'matriz':
                contador[0] += 1
                if contador[0] % 18:
                    return
            try:
                fila.put_nowait(etapa)
            except Full:
                pass
        self.fase, self.status = 'Calculando', 'A busca roda em segundo plano.'
        self.futuro = self.executor.submit(executar, self.metodo, self.mapa, self.origem,
                                            destino=self.destino, cancelar=cancelar, progresso=progresso)

    def acao(self, acao):
        if self.ui.config_aberta and acao not in ('config', 'fechar_config', 'pesos', 'legendas', 'animacao'):
            return
        if self.ui.tratar_acao(acao):
            if self.ui.config_aberta:
                self.arraste = None
            return
        if acao in ('mapa0', 'mapa1'):
            self._trocar_mapa(int(acao[-1]))
        elif acao.startswith('selecionar_'):
            metodo = acao.removeprefix('selecionar_')
            if metodo in ('forca', 'dijkstra', 'heuristica') and not self.ocupado:
                if (metodo == 'forca' and self.indice_mapa != 0) or (metodo == 'heuristica' and self.indice_mapa != 1):
                    self.status = 'Metodo indisponivel neste mapa.'
                else:
                    self.metodo = metodo
                    self._limpar()
        elif acao in ('origem', 'destino') and not self.ocupado:
            self.selecao = acao
        elif acao in ('origem-', 'origem+', 'destino-', 'destino+') and not self.ocupado:
            campo, passo = acao[:-1], 1 if acao[-1] == '+' else -1
            ids = self.mapa.ids
            setattr(self, campo, ids[(ids.index(getattr(self, campo)) + passo) % len(ids)])
            self._limpar()
        elif acao == 'iniciar':
            self._iniciar()
        elif acao == 'cancelar':
            self._limpar()
            self.fase, self.status = 'Cancelado', 'Calculo e reproducao cancelados.'
        elif acao == 'limpar':
            self._limpar()
        elif acao == 'pausa':
            if self.ocupado:
                self._replay_pausado = not self._replay_pausado
            elif self.viagem.reproduzindo:
                self.viagem.reproduzindo = False
            else:
                self.viagem.reproduzir()
        elif acao == 'reiniciar':
            if self.ocupado:
                self._limpar()
            else:
                self.viagem.reiniciar()
                # Reiniciar e uma mudanca deliberada de posicao: alinha de
                # imediato a van com o primeiro trecho, sem herdar um giro.
                self._heading_carro = None
                self._posicionar_carro()
        elif acao in ('anterior', 'proximo') and not self.ocupado:
            self.viagem.saltar(1 if acao == 'proximo' else -1)
            self._heading_carro = None
            self._posicionar_carro()
        elif acao == 'velocidade':
            velocidades = (1, 2, 4)
            self.viagem.velocidade = velocidades[(velocidades.index(self.viagem.velocidade) + 1) % 3]
        elif acao == 'reset':
            self.camera_iso.centralizar()
        elif acao in ('zoom+', 'zoom-'):
            self.camera_iso.mudar_zoom(1.12 if acao == 'zoom+' else 1 / 1.12)

    def _finalizar_busca(self):
        r = self._resultado_pendente
        self._resultado_pendente = None
        self.resultado = r
        if r:
            self.etapa = Progresso('concluido', r.caminho, r.custo,
                                   r.explorados, r.distancias, r.candidatas)
        if r and r.caminho and r.termino == 'concluido':
            self.viagem.carregar(self.mapa, r.caminho, ciclo=self.metodo != 'dijkstra')
            self.cena.mostrar_rota(r.caminho)
            self._trecho_visual = None
            self._heading_carro = None
            self._posicionar_carro()
            self.fase, self.status = 'Percurso calculado', r.garantia
        elif r:
            self.fase, self.status = 'Busca encerrada', r.termino

    def _posicionar_carro(self, dt=0.):
        caminho = self.viagem.caminho
        if not self.viagem.pesos:
            no = caminho[0] if caminho else self.origem
            self.carro.setPos(*self.cena.posicoes[no])
            self.carro.setHpr(0, 0, 0)
            self._heading_carro = 0.
            return

        indice, fracao = self.viagem.trecho
        amostra = medir_rua(self.cena.ruas[caminho[indice:indice + 2]]).amostrar(fracao)
        local = heading_da_direcao(amostra.tangente)
        pitch = pitch_da_direcao(amostra.tangente)
        if self.viagem.em_chegada:
            chegada = medir_rua(self.cena.ruas[caminho[indice - 1:indice + 1]]).amostrar(1.)
            entrada = heading_da_direcao(chegada.tangente)
            progresso = self.viagem.progresso_chegada
            curva = progresso * progresso * (3. - 2. * progresso)
            self._heading_carro = normalizar_angulo(entrada + curva * diferenca_angular(entrada, local))
            pitch_entrada = pitch_da_direcao(chegada.tangente)
            pitch = pitch_entrada + curva * (pitch - pitch_entrada)
        elif self._heading_carro is None or self.viagem.concluida:
            self._heading_carro = local
        elif dt > 0:
            alvo = heading_antecipado(amostra)
            heading = suavizar_heading(self._heading_carro, alvo, dt * self.viagem.velocidade)
            self._heading_carro = limitar_heading(local, heading)
        self.carro.setPos(*amostra.ponto)
        self.carro.setHpr(self._heading_carro, pitch, 0)

    def _destacar_trecho_atual(self):
        if not self.viagem.pesos:
            return
        if self.viagem.concluida:
            # Após a entrega, HUD e cena voltam a mostrar o percurso inteiro
            # uma única vez; durante execução/pausa permanece só o trecho.
            if self._trecho_visual != ():
                self.cena.mostrar_rota(self.viagem.caminho)
                self._trecho_visual = ()
            return
        indice, _ = self.viagem.trecho
        trecho = tuple(self.viagem.caminho[indice:indice + 2])
        if len(trecho) != 2 or trecho == self._trecho_visual:
            return
        desenhar = getattr(self.cena, 'mostrar_trecho', None)
        if desenhar:
            desenhar(*trecho)
        else:  # Dobles de teste e cenas externas preservam o mesmo contrato.
            self.cena.mostrar_rota(trecho)
        self._trecho_visual = trecho

    def atualizar(self, dt):
        if self.futuro:
            while True:
                try:
                    self._etapas.append(self._fila.get_nowait())
                except Empty:
                    break
            if self.futuro.done():
                futuro, self.futuro = self.futuro, None
                try:
                    self._resultado_pendente = futuro.result()
                except Exception as erro:
                    self._etapas.clear()
                    self._resultado_pendente = None
                    self.fase, self.status = 'Erro no calculo', str(erro)
        if self._resultado_pendente is not None and not self._replay_pausado:
            if not self.ui.animar_busca:
                self._etapas.clear()
            self._relogio += max(0, dt) * self.viagem.velocidade
            while self._etapas and self._relogio >= .1:
                self._relogio -= .1
                self.etapa = self._etapas.popleft()
                self.fase = FASES.get(self.etapa.fase, self.etapa.fase)
                self.status = (f'{self.etapa.candidatas} candidatos avaliados'
                               if self.metodo == 'forca' else
                               f'{len(self.etapa.explorados)} pontos explorados')
                if self.etapa.caminho:
                    self.cena.mostrar_rota(self.etapa.caminho)
            if not self._etapas:
                self._finalizar_busca()
        indice_anterior, _ = self.viagem.trecho
        estava_em_chegada = self.viagem.em_chegada
        self.viagem.atualizar(dt)
        if not self.viagem.em_chegada and (estava_em_chegada or self.viagem.trecho[0] != indice_anterior):
            # Um frame pode consumir toda a pausa. A van sai alinhada mesmo
            # se a última orientação desenhada ainda estava no meio do giro.
            self._heading_carro = None
        self._destacar_trecho_atual()
        if self.ocupado and self._replay_pausado:
            self.fase = 'Busca pausada'
        elif self.viagem.caminho:
            if self.viagem.concluida:
                self.fase = 'Concluido'
            elif self.viagem.reproduzindo:
                self.fase = 'Em viagem'
            else:
                self.fase = 'Pausado'
        self._posicionar_carro(dt if self.viagem.reproduzindo else 0.)
        if self.arraste and not self.ui.config_aberta:
            p = self.mouse_pixel()
            if p:
                self.camera_iso.arrastar(p[0] - self.arraste[0], p[1] - self.arraste[1])
                self.arraste = p

    def _frame(self, task):
        from direct.showbase.ShowBaseGlobal import globalClock
        if self._fechada:
            return task.done
        if hasattr(self.win, 'getProperties') and not self.win.getProperties().getOpen():
            self.fechar()
            return task.done
        if (self.win.getXSize() < self.camera_iso.MIN_LARGURA or
                self.win.getYSize() < self.camera_iso.MIN_ALTURA):
            # Aguardar o redimensionamento mínimo sem desenhar painéis em uma
            # superfície temporariamente menor que a interface.
            self.camera_iso.ajustar()
            return task.cont
        # Carregamento/redimensionamento não deve saltar segundos da viagem.
        dt = min(.1, globalClock.getDt())
        self.atualizar(dt)
        self._hud_relogio += dt
        if self._hud_relogio >= 1 / 30:
            self.ui.desenhar()
            self._hud_relogio = 0.
        return task.cont

    def executar(self):
        try:
            self.run()
        finally:
            self.fechar()

    def fechar(self):
        if self._fechada:
            return
        self._fechada = True
        self.taskMgr.remove('atualizar-jogo')
        self.taskMgr.stop()
        self._invalidar()
        self.executor.shutdown(wait=True, cancel_futures=True)
        self.destroy()
