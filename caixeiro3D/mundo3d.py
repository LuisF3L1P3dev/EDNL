"""Relogio do veiculo, sem dependencia do renderizador."""
from dataclasses import dataclass, field
from math import atan2, copysign, cos, degrees, hypot, isfinite, radians, sin

from geometria3d import interpolar, medir_rua, posicoes_mundo, ruas_mundo


def normalizar_angulo(angulo):
    """Retorna um heading equivalente no intervalo (-180, 180]."""
    valor = (angulo + 180.) % 360. - 180.
    return 180. if valor == -180. else valor


def diferenca_angular(atual, alvo):
    """Menor giro assinado necessário para ir de ``atual`` até ``alvo``."""
    return normalizar_angulo(alvo - atual)


def suavizar_heading(atual, alvo, dt, graus_por_segundo=300.):
    if not isfinite(dt) or dt < 0 or graus_por_segundo <= 0:
        raise ValueError("A rotação exige tempo não negativo e velocidade positiva.")
    delta = diferenca_angular(atual, alvo)
    passo = min(abs(delta), graus_por_segundo * dt)
    return normalizar_angulo(atual + copysign(passo, delta) if passo else atual)


def heading_da_direcao(direcao):
    """Heading Panda do pai do veículo, que considera frente local +Y."""
    if hypot(direcao[0], direcao[1]) <= 1e-9:
        return 0.
    return normalizar_angulo(-degrees(atan2(direcao[0], direcao[1])))


def pitch_da_direcao(direcao):
    return degrees(atan2(direcao[2], hypot(*direcao[:2])))


def limitar_heading(tangente, heading):
    desvio = diferenca_angular(tangente, heading)
    return normalizar_angulo(tangente + max(-45., min(45., desvio)))


def heading_antecipado(amostra, distancia=2.25):
    """Prepara a próxima curva da rua, mantendo a direção de chegada ao nó."""
    if distancia <= 0:
        raise ValueError("A antecipação precisa de distância positiva.")
    atual = heading_da_direcao(amostra.tangente)
    if amostra.proxima_tangente is None or amostra.restante_segmento >= distancia:
        return atual
    proximo = heading_da_direcao(amostra.proxima_tangente)
    if abs(diferenca_angular(atual, proximo)) == 180.:
        return atual
    alvo = limitar_heading(atual, proximo)
    aproximacao = 1. - amostra.restante_segmento / distancia
    return normalizar_angulo(atual + diferenca_angular(atual, alvo) * aproximacao)


def direcao_antecipada(ruas, caminho, indice, fracao, distancia=2.25):
    """Direção horizontal antecipada com a inclinação do segmento atual."""
    if distancia <= 0:
        raise ValueError("A antecipação precisa de distância positiva.")
    caminho = tuple(caminho)
    if not 0 <= indice < len(caminho) - 1:
        return 0., 1., 0.
    rua = medir_rua(ruas[caminho[indice], caminho[indice + 1]])
    amostra = rua.amostrar(fracao)
    heading = heading_antecipado(amostra, distancia)
    if heading == heading_da_direcao(amostra.tangente):
        return amostra.tangente
    x, y, z = amostra.tangente
    horizontal = hypot(x, y)
    angulo = radians(heading)
    return -sin(angulo) * horizontal, cos(angulo) * horizontal, z


@dataclass
class Viagem:
    """Relógio de percurso com durações visuais independentes dos pesos.

    A cada chegada intermediaria ha 0,3 s de sinalizacao, escalados pela
    velocidade. `trecho` e (indice da aresta, fracao); no percurso unitario
    e (0, 1). `em_chegada` sinaliza a pausa visual ao chamador.
    """
    caminho: tuple = ()
    pesos: tuple = ()
    duracoes: tuple = field(default=(), init=False)
    custo_atual: float = 0.
    reproduzindo: bool = False
    velocidade: float = 1.
    _acumulados: tuple = field(default=(), repr=False)
    _indice: int = field(default=0, repr=False)
    _espera: float = field(default=0., repr=False)
    PAUSA_CHEGADA = .3

    @property
    def total(self):
        return sum(self.pesos)

    @property
    def concluida(self):
        return bool(self.caminho) and self._indice >= len(self.pesos)

    @property
    def em_chegada(self):
        return self._espera > 0

    @property
    def progresso_chegada(self):
        return 1. - self._espera / self.PAUSA_CHEGADA if self.em_chegada else 0.

    @property
    def trecho(self):
        if self.concluida:
            return max(0, len(self.pesos) - 1), 1.
        if not self.pesos:
            return 0, 0.
        return self._indice, (self.custo_atual - self._acumulados[self._indice]) / self.pesos[self._indice]

    @property
    def visitadas(self):
        return set(self.caminho[:self._indice + 1])

    def carregar(self, grafo, caminho, *, ciclo=True, duracoes=None):
        caminho = tuple(caminho)
        if not caminho:
            raise ValueError("Percurso vazio.")
        if not set(caminho) <= set(grafo.ids):
            raise ValueError("Percurso contem nos desconhecidos.")
        if ciclo and (caminho[0] != caminho[-1] or set(caminho) != set(grafo.ids)):
            raise ValueError("O ciclo deve visitar todas as cidades e retornar a origem.")
        adj = grafo.adjacencia()
        try:
            pesos = tuple(adj[a][b] for a, b in zip(caminho, caminho[1:]))
        except KeyError as erro:
            raise ValueError("Percurso contem uma rua inexistente.") from erro
        if any(not isfinite(p) or p <= 0 for p in pesos):
            raise ValueError("A animacao exige pesos positivos.")
        if duracoes is None:
            total = sum(pesos)
            duracoes = tuple(30. * peso / total for peso in pesos)
        else:
            duracoes = tuple(duracoes)
            if len(duracoes) != len(pesos) or any(not isfinite(t) or t <= 0 for t in duracoes):
                raise ValueError("Cada trecho exige uma duração visual positiva.")
        acumulados = [0.]
        for peso in pesos:
            acumulados.append(acumulados[-1] + peso)
        self.caminho, self.pesos = caminho, pesos
        self.duracoes = duracoes
        self._acumulados = tuple(acumulados)
        self.reiniciar()
        self.reproduzindo = bool(pesos)

    def atualizar(self, dt):
        if not isfinite(dt) or dt < 0:
            raise ValueError("O delta de tempo deve ser finito e nao negativo.")
        if self.velocidade not in (1, 2, 4):
            raise ValueError("A velocidade deve ser 1, 2 ou 4.")
        if not self.reproduzindo or not dt:
            return
        restante = dt * self.velocidade
        while restante > 0 and not self.concluida:
            if self._espera:
                consumido = min(restante, self._espera)
                self._espera -= consumido
                restante -= consumido
                if self._espera > 1e-10:
                    break
                self._espera = 0.
            taxa = self.pesos[self._indice] / self.duracoes[self._indice]
            tempo = (self._acumulados[self._indice + 1] - self.custo_atual) / taxa
            if restante < tempo:
                self.custo_atual += restante * taxa
                break
            restante -= tempo
            self._indice += 1
            self.custo_atual = self._acumulados[self._indice]
            if not self.concluida:
                self._espera = self.PAUSA_CHEGADA
        if self.concluida:
            self.reproduzindo = False

    def reproduzir(self):
        if self.concluida and self.pesos:
            self.reiniciar()
        self.reproduzindo = bool(self.pesos)

    def reiniciar(self):
        self._indice = 0
        self._espera = 0.
        self.custo_atual = 0.
        self.reproduzindo = False

    def saltar(self, direcao):
        self.reproduzindo = False
        self._espera = 0.
        if not self.caminho or not direcao:
            return
        if direcao > 0:
            alvo = next((i for i, p in enumerate(self._acumulados) if p > self.custo_atual + 1e-8), len(self.pesos))
        else:
            alvo = next((i for i in range(len(self._acumulados) - 1, -1, -1)
                         if self._acumulados[i] < self.custo_atual - 1e-8), 0)
        self._indice = alvo
        self.custo_atual = self._acumulados[alvo]
