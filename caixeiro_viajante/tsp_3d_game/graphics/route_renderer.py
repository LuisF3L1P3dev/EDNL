"""Rotas sobre as ruas, com expansão das arestas do fecho métrico."""

import math

from ursina import Entity, Mesh, color, destroy
from ursina.shaders import unlit_shader

from ..core.graph_manager import pontos_estrada
from .estilo import CIANO, LARANJA, ROSA, VERDE


class RenderizadorRota:
    def __init__(self, cenario):
        self.cenario = cenario
        self.raiz = Entity()
        self.camadas = {}
        self.animacao = None

    def _pares(self, matriz, arestas, altura=.26, deslocamento=0):
        if matriz.modo == "euclidiano":
            altura += 6
        vertices = []
        for a, b in arestas:
            if a == b:
                continue
            if matriz.modo == "euclidiano":
                pontos = [self.cenario.posicao(a), self.cenario.posicao(b)]
            else:
                nos = matriz.caminhos.get((a, b), [])
                pontos = [self.cenario.posicao(a)]
                for u, v in zip(nos, nos[1:]):
                    pontos.extend(pontos_estrada(self.cenario, u, v)[1:])
            for p, q in zip(pontos, pontos[1:]):
                dx, dz = q[0] - p[0], q[2] - p[2]
                comprimento = max(1e-9, math.hypot(dx, dz))
                ox, oz = -dz / comprimento * deslocamento, dx / comprimento * deslocamento
                vertices.extend([(p[0] + ox, p[1] + altura, p[2] + oz),
                                 (q[0] + ox, q[1] + altura, q[2] + oz)])
        return vertices

    def desenhar_arestas(self, chave, matriz, arestas, cor=CIANO, altura=.26, espessura=4):
        self.limpar(chave)
        # Cores ligeiramente separadas permitem comparar rotas sobre a mesma rua.
        deslocamento = .14 if chave == "manual" else -.14 if chave == "ativa" else 0
        vertices = self._pares(matriz, arestas, altura, deslocamento)
        if vertices:
            entidade = Entity(parent=self.raiz, model=Mesh(vertices=vertices, mode="line", thickness=espessura),
                               color=cor, shader=unlit_shader)
            self.camadas[chave] = entidade

    def desenhar(self, chave, matriz, ordem, cor=CIANO, progressiva=False, altura=.26):
        arestas = list(zip(ordem, ordem[1:]))
        if progressiva:
            self.animacao = (chave, matriz, arestas, cor, altura, 0.0)
            self.limpar(chave)
        else:
            self.desenhar_arestas(chave, matriz, arestas, cor, altura)

    def destacar_etapa(self, matriz, etapa):
        self.limpar("removidas")
        self.limpar("adicionadas")
        if etapa.removidas:
            self.desenhar_arestas("removidas", matriz, etapa.removidas, ROSA, .38, 7)
        if etapa.adicionadas:
            self.desenhar_arestas("adicionadas", matriz, etapa.adicionadas, VERDE, .44, 5)

    def atualizar(self, dt):
        if not self.animacao:
            return
        chave, matriz, arestas, cor, altura, tempo = self.animacao
        tempo += dt
        quantidade = min(len(arestas), int(tempo * max(5, len(arestas) / 1.5)) + 1)
        self.desenhar_arestas(chave, matriz, arestas[:quantidade], cor, altura)
        self.animacao = None if quantidade == len(arestas) else (chave, matriz, arestas, cor, altura, tempo)

    def limpar(self, chave=None):
        if chave is None:
            for entidade in list(self.camadas.values()):
                destroy(entidade)
            self.camadas.clear()
            self.animacao = None
        elif chave in self.camadas:
            destroy(self.camadas.pop(chave))

    def destruir(self):
        self.animacao = None
        destroy(self.raiz)

