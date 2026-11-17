"""Relogio do veiculo, sem dependencia do renderizador."""
from dataclasses import dataclass, field
from math import atan2, copysign, degrees, dist, hypot, isfinite

from geometria3d import posicoes_mundo, ruas_mundo, interpolar


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


def direcao_antecipada(ruas, caminho, indice, fracao, distancia=2.25):
    """Vetor até um waypoint futuro, atravessando a próxima rua se preciso."""
    if distancia <= 0:
        raise ValueError("A antecipação precisa de distância positiva.")
    caminho = tuple(caminho)
    if not 0 <= indice < len(caminho) - 1:
        return 0., 1., 0.
    atual, ultima = interpolar(ruas[caminho[indice], caminho[indice + 1]], fracao)
    restante = distancia
    for i in range(indice, len(caminho) - 1):
        pontos = ruas[caminho[i], caminho[i + 1]]
        comprimentos = [dist(a, b) for a, b in zip(pontos, pontos[1:])]
        total = sum(comprimentos)
        inicio = max(0., min(1., fracao)) * total if i == indice else 0.
        disponivel = max(0., total - inicio)
        if restante > disponivel + 1e-9:
            restante -= disponivel
            continue
        alvo = min(total, inicio + restante)
        acumulado = 0.
        for a, b, comprimento in zip(pontos, pontos[1:], comprimentos):
            if alvo <= acumulado + comprimento + 1e-9:
                t = (alvo - acumulado) / comprimento if comprimento else 0.
                ponto = tuple(a[k] + (b[k] - a[k]) * t for k in range(3))
                vetor = tuple(ponto[k] - atual[k] for k in range(3))
                return vetor if hypot(vetor[0], vetor[1]) > 1e-8 else ultima
            acumulado += comprimento
    return ultima


@dataclass
class Viagem:
    """Relogio de percurso: custo avanca por 30 s de movimento a 1x.

    A cada chegada intermediaria ha 0,3 s de sinalizacao, escalados pela
    velocidade. `trecho` e (indice da aresta, fracao); no percurso unitario
    e (0, 1). `em_chegada` sinaliza a pausa visual ao chamador.
    """
    caminho: tuple = ()
    pesos: tuple = ()
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
    def trecho(self):
        if self.concluida:
            return max(0, len(self.pesos) - 1), 1.
        if not self.pesos:
            return 0, 0.
        return self._indice, (self.custo_atual - self._acumulados[self._indice]) / self.pesos[self._indice]

    @property
    def visitadas(self):
        return set(self.caminho[:self._indice + 1])

    def carregar(self, grafo, caminho, *, ciclo=True):
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
        acumulados = [0.]
        for peso in pesos:
            acumulados.append(acumulados[-1] + peso)
        self.caminho, self.pesos = caminho, pesos
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
        taxa = self.total / 30.
        while restante > 0 and not self.concluida:
            if self._espera:
                consumido = min(restante, self._espera)
                self._espera -= consumido
                restante -= consumido
                if self._espera > 1e-10:
                    break
                self._espera = 0.
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
