"""Geometria compartilhada pelo pavimento e pelos percursos nas rotatórias."""
from dataclasses import dataclass
from math import asin, atan2, ceil, cos, hypot, pi, sin, tau
from types import MappingProxyType

from roteamento3d import LARGURA_VIA


RAIO_PISTA = 1.75
RAIO_INTERNO = RAIO_PISTA - LARGURA_VIA / 2
RAIO_EXTERNO = RAIO_PISTA + LARGURA_VIA / 2
BOCA = 2.8
_PASSO_ARCO = pi / 36
_ENTRONCAMENTO = pi / 5


@dataclass(frozen=True)
class Rotatoria:
    no: int
    centro: tuple
    bracos: tuple  # pares (vizinho, ângulo da direção para fora)
    angulo_chegada: float

    @property
    def chegada(self):
        return self.ponto(self.angulo_chegada, RAIO_PISTA)

    @property
    def limites_xy(self):
        x, y, _ = self.centro
        return x - BOCA, y - BOCA, x + BOCA, y + BOCA

    def ponto(self, angulo, raio):
        x, y, z = self.centro
        return x + raio * cos(angulo), y + raio * sin(angulo), z

    def arco(self, inicio, fim):
        """Sequência anti-horária incluindo extremos e sem corda pela ilha."""
        variacao = (fim - inicio) % tau
        passos = max(1, ceil(variacao / _PASSO_ARCO))
        return (self.ponto(inicio, RAIO_PISTA),
                *(self.ponto(inicio + variacao * i / passos, RAIO_PISTA) for i in range(1, passos)),
                self.ponto(fim, RAIO_PISTA))

    def acesso(self, vizinho, boca, *, entrando):
        angulo = dict(self.bracos)[vizinho]
        encontro = angulo + (_ENTRONCAMENTO if entrando else -_ENTRONCAMENTO)
        ponto = self.ponto(encontro, RAIO_PISTA)
        x, y, z = boca
        perto_boca = x - .68 * cos(angulo), y - .68 * sin(angulo), z
        sentido = 1 if entrando else -1
        perto_anel = (ponto[0] + sentido * .63 * sin(encontro),
                      ponto[1] - sentido * .63 * cos(encontro), z)
        curva = _bezier(boca, perto_boca, perto_anel, ponto)
        if entrando:
            return curva + self.arco(encontro, self.angulo_chegada)[1:]
        return self.arco(self.angulo_chegada, encontro) + curva[-2::-1]

    def perfis_pavimento(self):
        """Cortes radiais do anel e dos encaixes de largura regular."""
        meia = LARGURA_VIA / 2
        chanfro = atan2(meia, BOCA)
        abertura = asin(meia / RAIO_EXTERNO)
        direcoes = tuple(angulo for _, angulo in self.bracos)
        angulos = {round(i * _PASSO_ARCO, 10) for i in range(round(tau / _PASSO_ARCO))}
        for direcao in direcoes:
            angulos.update(round((direcao + delta) % tau, 10)
                           for delta in (-abertura, -chanfro, chanfro, abertura))
        angulos.add(round(tau, 10))
        for angulo in sorted(angulos):
            raio = RAIO_EXTERNO
            for direcao in direcoes:
                delta = abs((angulo - direcao + pi) % tau - pi)
                if delta <= abertura + 1e-9:
                    raio = max(raio, min(BOCA / cos(delta), meia / sin(delta) if delta else BOCA))
            yield self.ponto(angulo, RAIO_INTERNO), self.ponto(angulo, raio)


def _bezier(a, b, c, d):
    pontos = [a]
    for i in range(1, 12):
        t = i / 12
        u = 1 - t
        pontos.append(tuple(u**3 * p + 3*u*u*t * q + 3*u*t*t * r + t**3 * s
                            for p, q, r, s in zip(a, b, c, d)))
    return (*pontos, d)


def planejar_rotatoria(no, centro, vizinhos, eixos, angulo_chegada):
    bracos = []
    for vizinho in vizinhos:
        _, b, *_ = eixos[no, vizinho]
        dx, dy = b[0] - centro[0], b[1] - centro[1]
        if (dx and dy) or hypot(dx, dy) <= BOCA or b[2] != centro[2]:
            raise ValueError(f'Acesso sem reta livre na rotatória {no}–{vizinho}.')
        bracos.append((vizinho, atan2(dy, dx)))
    if len({a for _, a in bracos}) != len(bracos):
        raise ValueError(f'Acessos sobrepostos na rotatória {no}.')
    return Rotatoria(no, centro, tuple(bracos), angulo_chegada)


def separar_pavimento(ruas, rotatorias):
    """Recorta as bocas e cria a versão direcionada dos waypoints."""
    por_no = {r.no: r for r in rotatorias}
    eixos, trajetos, zonas = {}, {}, {}
    for (u, v), pontos in ruas.items():
        saida, chegada = por_no.get(u), por_no.get(v)
        if saida:
            pontos = (_boca(*pontos[:2]), *pontos[1:])
        if chegada:
            pontos = (*pontos[:-1], _boca(pontos[-1], pontos[-2]))
        eixos[u, v] = pontos
        inicio = saida.acesso(v, pontos[0], entrando=False) if saida else ()
        fim = chegada.acesso(u, pontos[-1], entrando=True) if chegada else ()
        trajetos[u, v] = (*inicio[:-1], *pontos, *fim[1:])
        if inicio or fim:
            zonas[u, v] = (len(inicio) - 1 if inicio else 0, len(fim) - 1 if fim else 0)
    return tuple(MappingProxyType(m) for m in (eixos, trajetos, zonas))


def _boca(a, b):
    comprimento = hypot(b[0] - a[0], b[1] - a[1])
    frac = BOCA / comprimento
    return tuple(x + (y - x) * frac for x, y in zip(a, b))
