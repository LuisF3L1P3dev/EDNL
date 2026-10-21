"""Cidade low-poly com assets locais e alternativa procedural."""

from __future__ import annotations

import math
import random

from ursina import (AmbientLight, Cone, DirectionalLight, Entity, Mesh, Text,
                    Vec3, color, destroy, camera)
from ursina.shaders import unlit_shader
from .materiais import shader_cidade as lit_with_shadows_shader

from ..core.graph_manager import pontos_estrada
from .estilo import CIANO, VERDE, LARANJA, ROXO, ROSA, SUAVE
from .catalogo_assets import CATALOGO
from .decoracao import DecoracaoCidade
from .efeitos import malha_anel
from .ciclo_vida import destruir_arvore as destroy
from .lotes_estaticos import agrupar_estatico
from .ruas import Ruas3D


def barra(parent, a, b, cor, largura=.12, altura=.06, shader=unlit_shader):
    a, b = Vec3(*a), Vec3(*b)
    entidade = Entity(parent=parent, model="cube", color=cor, position=(a + b) / 2,
                      scale=(largura, altura, max(.001, (b - a).length())), shader=shader)
    entidade.look_at(b)
    return entidade


class Mundo3D:
    def __init__(self, cenario, ao_selecionar, preferencias=None):
        self.cenario = cenario
        self.preferencias = preferencias or {}
        self.proximo_destino = None
        self.tempo_visual = 0.
        self.escala_rotulos = None
        self.raiz = Entity(name="Regiao_NEXUS")
        self.estatica = Entity(parent=self.raiz, shader=lit_with_shadows_shader)
        self.mobiliario = Entity(parent=self.raiz, name="Mobiliario_urbano")
        self.marcadores = {}
        self.rotulos = {}
        self.textos_rotulos = {}
        self.colunas = {}
        self.halos = {}
        self.bloqueios = Entity(parent=self.raiz)
        self.grafo_visivel = False
        self.sorteio = random.Random(cenario.semente + 137)
        self._terreno()
        self._ruas()
        self.decoracao = DecoracaoCidade(self)
        agrupar_estatico(self.mobiliario)
        self._destinos(ao_selecionar)
        self._grafo()
        # Uma malha colorida para todos os objetos estáticos reduz as chamadas de desenho.
        self.estatica.combine(auto_destroy=True, include_normals=True)
        self.estatica.shader = lit_with_shadows_shader
        self.definir_aparencia()
        self.atualizar_cidades([], set(), cenario.deposito)

    def cubo(self, posicao, escala, cor):
        return Entity(parent=self.estatica, model="cube", position=posicao,
                      scale=escala, color=cor, shader=lit_with_shadows_shader)

    def definir_aparencia(self):
        self.raiz.setShaderInput("sombra_ativa", float(self.preferencias.get("sombras", True)), 10)

    def _terreno(self):
        c = self.cenario
        tamanho = c.lado * c.espacamento + 2
        self.cubo((0, -1.0, 0), (tamanho, 1.8, tamanho), color.hex("#516A66"))
        self.cubo((0, -.04, 0), (tamanho - .3, .18, tamanho - .3), color.hex("#83AD62"))
        # Uma faixa de água entre colunas; apenas as pontes ligam as margens.
        coluna = c.lado // 2 - 1
        self.rio_x = (coluna - (c.lado - 1) / 2 + .5) * c.espacamento
        self.cubo((self.rio_x, .07, 0), (2.4, .14, tamanho - .4), color.hex("#3EA6C3"))
        for lado in (-1, 1):
            self.cubo((self.rio_x + lado * 1.28, .12, 0), (.20, .23, tamanho - .4), color.hex("#D6CDB3"))
        for i in range(c.lado * 3):
            z = -tamanho / 2 + i * 2.1
            self.cubo((self.rio_x + .2, .15, z), (1.0, .012, .09), color.hex("#3AA8B8"))
        for eixo in (-1, 1):
            self.cubo((eixo * tamanho / 2, -.4, 0), (.09, .06, tamanho), CIANO.tint(-.45))
            self.cubo((0, -.4, eixo * tamanho / 2), (tamanho, .06, .09), CIANO.tint(-.45))

    def _ruas(self):
        if Ruas3D.disponivel():
            self.vias = Ruas3D(self.cenario, self.raiz)
            for no in self.cenario.grafo:
                if no % 3 == 0:
                    p = self.cenario.posicao(no)
                    CATALOGO.criar("roads", "traffic-light" if no % 2 else "light-curved", self.mobiliario,
                                   (p[0] - 1.15, p[1], p[2] - 1.15), .42, 90)
            return
        self._ruas_procedurais()

    def _ruas_procedurais(self):
        for a, b, dados in self.cenario.grafo.edges(data=True):
            pontos = pontos_estrada(self.cenario, a, b)
            for p, q in zip(pontos, pontos[1:]):
                barra(self.estatica, p, q, color.hex("#414B54"), 1.65, .16, lit_with_shadows_shader)
                dx, dz = q[0] - p[0], q[2] - p[2]
                comprimento = max(.001, math.hypot(dx, dz))
                for lado in (-1, 1):
                    ox, oz = -dz / comprimento * lado, dx / comprimento * lado
                    a = (p[0] + ox, p[1] + .04, p[2] + oz)
                    b = (q[0] + ox, q[1] + .04, q[2] + oz)
                    if comprimento > 2:
                        # Encurta a calçada para deixar as bocas do cruzamento livres.
                        a = (a[0] + dx / comprimento, a[1], a[2] + dz / comprimento)
                        b = (b[0] - dx / comprimento, b[1], b[2] - dz / comprimento)
                        barra(self.estatica, a, b, color.hex("#D9D9CC"), .32, .18, lit_with_shadows_shader)
                # Linha central em pequenos traços, sem ocupar as calçadas.
                for fracao in (.22, .52, .82):
                    inicio = tuple(p[i] + (q[i] - p[i]) * fracao + (.091 if i == 1 else 0) for i in range(3))
                    fim = tuple(p[i] + (q[i] - p[i]) * min(.99, fracao + .09) + (.091 if i == 1 else 0) for i in range(3))
                    barra(self.estatica, inicio, fim, color.hex("#EEEAD7"), .045, .012)
                if dados["ponte"]:
                    for lado in (-1.12, 1.12):
                        inicio = (p[0], p[1] + .26, p[2] + lado)
                        fim = (q[0], q[1] + .26, q[2] + lado)
                        barra(self.estatica, inicio, fim, color.hex("#BDC9C9"), .055, .16, lit_with_shadows_shader)
            if dados["ponte"]:
                p = pontos[len(pontos) // 2]
                self.cubo((p[0], .3, p[2]), (.38, 1.1, .8), color.hex("#637B86"))
        for no in self.cenario.grafo:
            p = self.cenario.posicao(no)
            self.cubo((p[0], p[1] - .02, p[2]), (1.7, .16, 1.7), color.hex("#414B54"))
            if self.cenario.grafo.degree(no) >= 3:
                for vizinho in self.cenario.grafo.neighbors(no):
                    q = pontos_estrada(self.cenario, no, vizinho)[1]
                    dx, dz = q[0] - p[0], q[2] - p[2]
                    comprimento = max(.001, math.hypot(dx, dz))
                    ux, uz = dx / comprimento, dz / comprimento
                    for lateral in (-.59, -.35, -.11, .13, .37, .61):
                        a = (p[0] + ux * 1.02 - uz * lateral, p[1] + .11, p[2] + uz * 1.02 + ux * lateral)
                        b = (a[0] + ux * .42, a[1] + (q[1] - p[1]) / comprimento * .42, a[2] + uz * .42)
                        barra(self.estatica, a, b, color.hex("#F3F1DF"), .13, .014)
            if no % 3 == 0:
                # Postes ficam na calçada, fora das conexões transitáveis.
                CATALOGO.criar("roads", "traffic-light" if no % 2 else "light-curved", self.mobiliario,
                               (p[0] - 1.15, p[1], p[2] - 1.15), .42, 90)

    def _arvore(self, x, y, z, escala=1):
        self.cubo((x, y + .38 * escala, z), (.13 * escala, .76 * escala, .13 * escala), color.hex("#645345"))
        Entity(parent=self.estatica, model=Cone(5), position=(x, y + 1.0 * escala, z),
               scale=(1.0 * escala, 1.6 * escala, 1.0 * escala),
               color=self.sorteio.choice([color.hex("#327B68"), color.hex("#409079"), color.hex("#62AB82")]),
               shader=lit_with_shadows_shader)

    def _predio(self, x, y, z, altura, largura, cor):
        self.cubo((x, y + altura / 2, z), (largura, altura, largura), cor)
        self.cubo((x, y + altura + .08, z), (largura + .12, .16, largura + .12), color.hex("#B3CBD1"))
        for andar in range(max(1, int(altura / .5))):
            janela_y = y + .35 + andar * .49
            self.cubo((x, janela_y, z - largura / 2 - .012), (largura * .72, .15, .024), color.hex("#75C9D3"))
            self.cubo((x + largura / 2 + .012, janela_y, z), (.024, .15, largura * .72), color.hex("#4A9BAD"))
        if altura > 2.7:
            self.cubo((x, y + altura + .35, z), (.25, .5, .25), color.hex("#5B7888"))

    def _quadras(self):
        c, r = self.cenario, self.sorteio
        for linha in range(c.lado - 1):
            for coluna in range(c.lado - 1):
                if coluna == c.lado // 2 - 1:
                    continue
                nos = [linha * c.lado + coluna, linha * c.lado + coluna + 1,
                       (linha + 1) * c.lado + coluna, (linha + 1) * c.lado + coluna + 1]
                x = (coluna - (c.lado - 1) / 2 + .5) * c.espacamento
                z = (linha - (c.lado - 1) / 2 + .5) * c.espacamento
                y = min(c.posicao(no)[1] for no in nos) - .12
                self.cubo((x, y / 2, z), (4.7, max(.12, y), 4.7), color.hex("#3C5C59"))
                escolha = r.random()
                if escolha < .14:
                    Entity(parent=self.estatica, model=Cone(5), position=(x, y + 1.2, z),
                           scale=(3.9, 2.8, 3.9), color=color.hex("#667A7C"), shader=lit_with_shadows_shader)
                    Entity(parent=self.estatica, model=Cone(5), position=(x, y + 2.25, z),
                           scale=(1.0, .75, 1.0), color=color.hex("#A9BCC0"), shader=lit_with_shadows_shader)
                elif escolha < .33:
                    for dx, dz in ((-1.2, -1.2), (1.0, -.8), (-.8, 1), (1.1, 1.1)):
                        self._arvore(x + dx, y, z + dz, r.uniform(.7, 1.1))
                else:
                    for dx, dz in ((-1.25, -1.1), (1.1, -.9), (-1.1, 1.15), (1.15, 1.1)):
                        self._predio(x + dx, y, z + dz, r.uniform(.7, 3.7), r.uniform(.85, 1.4),
                                     r.choice([color.hex("#678695"), color.hex("#86A4AB"),
                                               color.hex("#527685"), color.hex("#C2BCA7")]))
        # Pequenos centros logísticos junto aos destinos, fora do leito da rua.
        for indice, no in enumerate(c.cidades):
            x, y, z = c.posicao(no)
            dx, dz = 1.35, 1.25
            self.cubo((x + dx, y + .38, z + dz), (1.05, .9, 1.05), color.hex("#DFD8BC"))
            self.cubo((x + dx, y + .88, z + dz), (1.22, .12, 1.22), CIANO.tint(-.35))
            self.cubo((x + dx, y + .35, z + dz - .54), (.62, .52, .03), color.hex("#284457"))

    def _destinos(self, ao_selecionar):
        c = self.cenario
        for indice, no in enumerate(c.cidades):
            x, y, z = c.posicao(no)
            raiz = Entity(parent=self.raiz, position=(x, y, z), name=f"Destino_{no}")
            halo = Entity(parent=raiz, model=malha_anel(.64, .045), y=.16, double_sided=True,
                          color=CIANO, shader=unlit_shader)
            coluna = Entity(parent=raiz, model="cube", scale=(.028, 1.1, .028), y=.73,
                            color=CIANO, shader=unlit_shader)
            marcador = Entity(parent=raiz, model="cube", scale=.32, position=(0, 1.32, 0),
                               rotation=(0, 45, 45), color=CIANO, collider="box", shader=unlit_shader)
            marcador.on_click = lambda no=no: ao_selecionar(no)
            placa = Entity(parent=raiz, position=(0, 1.82, 0), billboard=True)
            self.textos_rotulos[no] = Text(parent=placa, text=f"{indice:02d}",
                 origin=(0, 0), scale=22, color=color.white, background=True)
            self.marcadores[no], self.halos[no], self.colunas[no] = marcador, halo, coluna
            self.rotulos[no] = placa

    def _grafo(self):
        vertices = []
        for a, b in self.cenario.grafo.edges:
            pontos = pontos_estrada(self.cenario, a, b)
            for p, q in zip(pontos, pontos[1:]):
                vertices.extend([(p[0], p[1] + .23, p[2]), (q[0], q[1] + .23, q[2])])
        self.sobreposicao_grafo = Entity(parent=self.raiz,
            model=Mesh(vertices=vertices, mode="line", thickness=2), color=ROXO,
            shader=unlit_shader, enabled=False)
        self.pontos_grafo = Entity(parent=self.raiz, enabled=False)
        for no in self.cenario.grafo:
            x, y, z = self.cenario.posicao(no)
            Entity(parent=self.pontos_grafo, model="cube", position=(x, y + .25, z),
                   scale=.18, color=ROXO, shader=unlit_shader)
        self.pontos_grafo.combine(auto_destroy=True)

    def alternar_grafo(self):
        self.grafo_visivel = not self.grafo_visivel
        self.sobreposicao_grafo.enabled = self.grafo_visivel
        self.pontos_grafo.enabled = self.grafo_visivel

    def atualizar_cidades(self, ordem, entregues, deposito):
        for no, marcador in self.marcadores.items():
            cor = ROXO if no == deposito else VERDE if no in entregues else LARANJA if no in ordem else CIANO
            marcador.color = cor
            self.colunas[no].color = cor
            self.halos[no].color = cor.tint(-.25)
            indice = ordem.index(no) if no in ordem else None
            prefixo = "BASE" if no == deposito else f"{indice:02d}" if indice is not None else f"ID{self.cenario.grafo.nodes[no]['numero']:02d}"
            rotulo = self.textos_rotulos[no]
            novo_texto = f"{prefixo} · {self.cenario.nome(no)}" if self.preferencias.get("mostrar_nomes") else prefixo
            if rotulo.text != novo_texto:
                rotulo.text = novo_texto
                if rotulo.background_entity:
                    destroy(rotulo.background_entity)
                    rotulo.background_entity = None
                rotulo.background = True

    def destacar_proxima(self, no):
        if no == self.proximo_destino:
            return
        if self.proximo_destino in self.halos:
            self.halos[self.proximo_destino].scale = 1
        self.proximo_destino = no

    def animar(self, dt):
        self.tempo_visual += dt
        escala = max(.25, min(3., camera.fov / 35))
        if self.escala_rotulos is None or abs(escala - self.escala_rotulos) > .001:
            for rotulo in self.rotulos.values():
                rotulo.scale = escala
            self.escala_rotulos = escala
        if self.proximo_destino in self.halos:
            self.halos[self.proximo_destino].scale = 1.15 + .16 * math.sin(self.tempo_visual * 4)

    def atualizar_bloqueios(self):
        destroy(self.bloqueios)
        self.bloqueios = Entity(parent=self.raiz)
        for a, b, dados in self.cenario.grafo.edges(data=True):
            if not dados["bloqueada"] and dados["fator"] == 1:
                continue
            cor = ROSA if dados["bloqueada"] else LARANJA
            for p, q in zip(dados["pontos"], dados["pontos"][1:]):
                p, q = (p[0], p[1] + .2, p[2]), (q[0], q[1] + .2, q[2])
                barra(self.bloqueios, p, q, cor, .45, .12)
            p, q = dados["pontos"][0], dados["pontos"][-1]
            centro = tuple((a + b) / 2 for a, b in zip(p, q))
            angulo = math.degrees(math.atan2(q[0] - p[0], q[2] - p[2]))
            CATALOGO.criar("roads", "construction-barrier" if dados["bloqueada"] else "construction-cone",
                           self.bloqueios, (centro[0], centro[1] + .12, centro[2]),
                           1.5 if dados["bloqueada"] else .45, angulo)

    def destruir(self):
        destroy(self.raiz)

