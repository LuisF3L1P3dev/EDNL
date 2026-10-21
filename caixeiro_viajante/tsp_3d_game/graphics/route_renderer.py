"""Rotas sobre as ruas, com expansão das arestas do fecho métrico."""

import math

from ursina import Entity, Mesh, color, destroy
from ursina.shaders import unlit_shader

from ..core.graph_manager import pontos_estrada
from .estilo import CIANO, LARANJA, ROSA, VERDE
from .ciclo_vida import destruir_arvore as destroy


class RenderizadorRota:
    def __init__(self, cenario):
        self.cenario = cenario
        self.raiz = Entity()
        self.camadas = {}
        self.animacao = None
        self.brilho = True
        self.mostrar_computador = True
        self.reconstrucoes = 0

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
            entidade = self._criar_camada(chave, vertices, cor, espessura)
            self.camadas[chave] = entidade

    def _criar_camada(self, chave, vertices, cor, espessura=4):
        entidade = Entity(parent=self.raiz)
        entidade.halo = Entity(parent=entidade, model=Mesh(vertices=vertices, mode="line", thickness=espessura + 7),
                                color=color.rgba(cor.r, cor.g, cor.b, .20), shader=unlit_shader)
        entidade.linha = Entity(parent=entidade, model=Mesh(vertices=vertices, mode="line", thickness=espessura),
                                 color=cor, shader=unlit_shader)
        entidade.halo.set_depth_write(False)
        entidade.computador = chave in ("etapa", "removidas", "adicionadas") or chave == "ativa" and cor != LARANJA
        entidade.halo.enabled = self.brilho
        entidade.enabled = self.mostrar_computador or not entidade.computador
        self.reconstrucoes += 1
        return entidade

    def aplicar_aparencia(self):
        for entidade in self.camadas.values():
            entidade.halo.enabled = self.brilho
            entidade.enabled = self.mostrar_computador or not entidade.computador

    def desenhar(self, chave, matriz, ordem, cor=CIANO, progressiva=False, altura=.26):
        arestas = list(zip(ordem, ordem[1:]))
        if progressiva:
            self.limpar(chave)
            deslocamento = .14 if chave == "manual" else -.14 if chave == "ativa" else 0
            vertices = self._pares(matriz, arestas, altura, deslocamento)
            if not vertices:
                return
            self.camadas[chave] = self._criar_camada(chave, vertices[:2], cor)
            self.animacao = {"chave": chave, "vertices": vertices, "tempo": 0., "quantidade": 2}
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
        animacao = self.animacao
        animacao["tempo"] += dt
        vertices = animacao["vertices"]
        quantidade = min(len(vertices), (int(animacao["tempo"] / 2.2 * len(vertices) / 2) + 1) * 2)
        if quantidade != animacao["quantidade"]:
            entidade = self.camadas.get(animacao["chave"])
            if entidade:
                for parte in (entidade.linha, entidade.halo):
                    parte.model.vertices = vertices[:quantidade]
                    parte.model.generate()
            animacao["quantidade"] = quantidade
        if quantidade == len(vertices):
            self.animacao = None

    def limpar(self, chave=None):
        if chave is None:
            for entidade in list(self.camadas.values()):
                destroy(entidade)
            self.camadas.clear()
            self.animacao = None
        elif chave in self.camadas:
            destroy(self.camadas.pop(chave))
        if chave is not None and self.animacao and self.animacao["chave"] == chave:
            self.animacao = None

    def destruir(self):
        self.animacao = None
        destroy(self.raiz)

