"""Pequena reserva de efeitos de entrega, sem criar entidades por quadro."""
import math
from ursina import Entity, Mesh, Vec3, color, destroy
from ursina.shaders import unlit_shader
from .estilo import VERDE, CIANO
from .ciclo_vida import destruir_arvore as destroy


def malha_anel(raio=1, espessura=.06, segmentos=32):
    vertices, triangulos = [], []
    for i in range(segmentos):
        angulo = i * math.tau / segmentos
        for r in (raio, raio + espessura):
            vertices.append((math.cos(angulo) * r, 0, math.sin(angulo) * r))
        a, b = i * 2, ((i + 1) % segmentos) * 2
        triangulos.extend(((a, b, a + 1), (a + 1, b, b + 1)))
    return Mesh(vertices=vertices, triangles=triangulos, mode="triangle")


class EfeitosEntrega:
    def __init__(self):
        self.raiz = Entity()
        malha = malha_anel(.5, .06)
        self.reserva = [Entity(parent=self.raiz, model=malha, color=VERDE, double_sided=True,
                               shader=unlit_shader, enabled=False) for _ in range(12)]
        self.tempos = [0.] * len(self.reserva)
        self.ativo = True

    def emitir(self, posicao):
        if not self.ativo:
            return
        indice = next((i for i, e in enumerate(self.reserva) if not e.enabled), 0)
        entidade = self.reserva[indice]
        entidade.position = Vec3(*posicao) + Vec3(0, .24, 0)
        entidade.enabled = True
        entidade.scale = 1
        self.tempos[indice] = 0

    def atualizar(self, dt):
        for i, entidade in enumerate(self.reserva):
            if not entidade.enabled:
                continue
            self.tempos[i] += dt
            t = self.tempos[i] / 1.1
            entidade.enabled = t < 1 and self.ativo
            entidade.scale = 1 + t * 4
            entidade.color = color.rgba(VERDE.r, VERDE.g, VERDE.b, max(0, 1 - t))

    def destruir(self):
        destroy(self.raiz)
