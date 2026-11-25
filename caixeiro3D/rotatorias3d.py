"""Pavimento e trajetos das rotatórias, independentes do grafo matemático."""
from dataclasses import dataclass
from math import asin, atan2, ceil, cos, hypot, pi, sin, tau
from types import MappingProxyType

from roteamento3d import LARGURA_VIA, RAIO_PRACA


MEIA_VIA = LARGURA_VIA / 2
_PASSO_ARCO = pi / 36
_ABERTURA_TRANSICAO = .60
_ALARGAMENTO_MAXIMO = .31


@dataclass(frozen=True)
class Braco:
    vizinho: int
    angulo: float
    boca: tuple
    recorte: int
    estacao: float
    lateral: float

    def deslocar(self, longitudinal, lateral, dz=0.):
        """Ponto relativo à boca, no eixo da rua e à sua esquerda."""
        x, y, z = self.boca
        c, s = cos(self.angulo), sin(self.angulo)
        return x + c * longitudinal - s * lateral, y + s * longitudinal + c * lateral, z + dz

    def limite_raio(self, angulo):
        """Faixa com abertura no interior e largura padrão na boca."""
        c, s = cos(angulo - self.angulo), sin(angulo - self.angulo)
        if c <= 0.:
            return 0.
        minimo, maximo = 0., self.estacao / c
        for inclinacao, borda in (
            (lado * s + abertura * c, lado * self.lateral + MEIA_VIA + largura)
            for lado in (-1, 1)
            for abertura, largura in ((_ABERTURA_TRANSICAO, _ABERTURA_TRANSICAO * self.estacao),
                                      (0., _ALARGAMENTO_MAXIMO))
        ):
            if inclinacao > 1e-9:
                maximo = min(maximo, borda / inclinacao)
            elif inclinacao < -1e-9:
                minimo = max(minimo, borda / inclinacao)
            elif borda < 0.:
                return 0.
        return maximo if maximo >= minimo - 1e-9 else 0.


@dataclass(frozen=True)
class Rotatoria:
    no: int
    centro: tuple
    bracos: tuple[Braco, ...]
    angulo_chegada: float
    raio_pista: float

    @property
    def raio_interno(self):
        return self.raio_pista - MEIA_VIA

    @property
    def raio_externo(self):
        return self.raio_pista + MEIA_VIA

    @property
    def chegada(self):
        return self.ponto(self.angulo_chegada, self.raio_pista)

    @property
    def limites_xy(self):
        x, y, _ = self.centro
        alcance = max(self.raio_externo, *(b.estacao for b in self.bracos))
        return x - alcance, y - alcance, x + alcance, y + alcance

    def ponto(self, angulo, raio):
        x, y, z = self.centro
        return x + raio * cos(angulo), y + raio * sin(angulo), z

    def arco(self, inicio, fim):
        """Sequência anti-horária, incluindo os dois extremos."""
        variacao = (fim - inicio) % tau
        if variacao < 1e-10:
            return (self.ponto(fim, self.raio_pista),)
        passos = ceil(variacao / _PASSO_ARCO)
        return (*(self.ponto(inicio + variacao * i / passos, self.raio_pista) for i in range(passos)),
                self.ponto(fim, self.raio_pista))

    def acesso(self, braco, *, entrando):
        sentido = 1 if entrando else -1
        encontro = braco.angulo + atan2(braco.lateral, braco.estacao) + sentido * pi / 5
        ponto = self.ponto(encontro, self.raio_pista)
        perto_boca = braco.deslocar(-.74, 0.)
        perto_anel = (ponto[0] + sentido * .63 * sin(encontro),
                      ponto[1] - sentido * .63 * cos(encontro), ponto[2])
        curva = _bezier(braco.boca, perto_boca, perto_anel, ponto)
        if entrando:
            return curva + self.arco(encontro, self.angulo_chegada)[1:]
        return self.arco(self.angulo_chegada, encontro) + curva[-2::-1]

    def limite_externo(self, angulo):
        """Interseção do raio com o anel unido às faixas dos braços."""
        return max(self.raio_externo, *(b.limite_raio(angulo) for b in self.bracos))

    def perfis_pavimento(self):
        """Inclui as quinas das bocas para casar com as retas."""
        angulos = {round(i * _PASSO_ARCO, 10) for i in range(round(tau / _PASSO_ARCO))}
        for braco in self.bracos:
            for lado in (-1, 1):
                borda = braco.lateral + lado * MEIA_VIA
                corte = braco.estacao - _ALARGAMENTO_MAXIMO / _ABERTURA_TRANSICAO
                cantos = (atan2(borda, braco.estacao),
                          atan2(borda + lado * _ALARGAMENTO_MAXIMO, corte))
                angulos.update(round((braco.angulo + canto) % tau, 10) for canto in cantos)
                topo = (borda + lado * _ALARGAMENTO_MAXIMO) / self.raio_externo
                if abs(topo) <= 1.:
                    angulos.add(round((braco.angulo + asin(topo)) % tau, 10))
                faixa = lado * braco.lateral + MEIA_VIA + _ABERTURA_TRANSICAO * braco.estacao
                proporcao = faixa / (self.raio_externo * hypot(1., _ABERTURA_TRANSICAO))
                if -1. <= proporcao <= 1.:
                    arco = asin(proporcao)
                    inclinacao = atan2(_ABERTURA_TRANSICAO, 1.)
                    for delta in (arco - inclinacao, pi - arco - inclinacao):
                        if abs(delta) < pi / 2:
                            angulos.add(round((braco.angulo + lado * delta) % tau, 10))
        angulos.add(round(tau, 10))
        for angulo in sorted(angulos):
            yield self.ponto(angulo, self.raio_interno), self.ponto(angulo, self.limite_externo(angulo))


def _bezier(a, b, c, d):
    pontos = [a]
    for i in range(1, 16):
        t = i / 16
        u = 1 - t
        xy = tuple(u**3 * p + 3*u*u*t * q + 3*u*t*t * r + t**3 * s
                   for p, q, r, s in zip(a[:2], b[:2], c[:2], d[:2]))
        pontos.append((*xy, a[2]))
    return (*pontos, d)


def _braco(vizinho, centro, caminho, estacao):
    for indice, (a, b) in enumerate(zip(caminho, caminho[1:]), 1):
        if a[2] != centro[2] or a[2] != b[2]:
            continue
        eixo = int(a[0] == b[0])
        delta = b[eixo] - a[eixo]
        if not delta:
            continue
        sentido = 1 if delta > 0 else -1
        corte = centro[eixo] + sentido * estacao
        if not (a[eixo] - corte) * sentido <= 0. < (b[eixo] - corte) * sentido:
            continue
        if abs(a[1 - eixo] - centro[1 - eixo]) > RAIO_PRACA / 2 + 1e-8:
            break
        boca = list(a)
        boca[eixo] = corte
        angulo = atan2(b[1] - a[1], b[0] - a[0])
        lateral = (boca[1] - centro[1]) * cos(angulo) - (boca[0] - centro[0]) * sin(angulo)
        return Braco(vizinho, angulo, tuple(boca), indice, estacao, round(lateral, 8))
    raise ValueError(f'Acesso sem reta livre para o vizinho {vizinho} em {centro}.')


def planejar_rotatoria(no, centro, vizinhos, eixos, angulo_chegada):
    bracos = tuple(_braco(v, centro, eixos[no, v], RAIO_PRACA) for v in vizinhos)
    externo = 2.225
    if any(b.lateral for b in bracos):
        # Cobre o canto comum às faixas ortogonais descentradas.
        externo = 2.92 if len(bracos) >= 5 else 2.82
    if len({b.boca for b in bracos}) != len(bracos):
        raise ValueError(f'Acessos sobrepostos na rotatória {no}.')
    return Rotatoria(no, centro, bracos, angulo_chegada, externo - MEIA_VIA)


def separar_pavimento(ruas, rotatorias):
    """Recorta os eixos ortogonais e conecta os waypoints direcionados."""
    bracos = {(r.no, b.vizinho): (r, b) for r in rotatorias for b in r.bracos}
    eixos, trajetos, zonas = {}, {}, {}
    for (u, v), originais in ruas.items():
        saida = bracos.get((u, v))
        chegada = bracos.get((v, u))
        inicio = saida[0].acesso(saida[1], entrando=False) if saida else ()
        fim = chegada[0].acesso(chegada[1], entrando=True) if chegada else ()
        a = saida[1].recorte if saida else 0
        b = len(originais) - chegada[1].recorte if chegada else len(originais)
        pontos = (*inicio[-1:], *originais[a:b], *fim[:1])
        eixos[u, v] = pontos
        trajetos[u, v] = (*inicio[:-1], *pontos, *fim[1:])
        if inicio or fim:
            zonas[u, v] = (max(0, len(inicio) - 1), max(0, len(fim) - 1))
    return tuple(MappingProxyType(m) for m in (eixos, trajetos, zonas))
