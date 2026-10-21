"""Caminhão construído com primitivas, com direção interpolada."""

import math
from panda3d.core import GeomNode

from ursina import Entity, Vec3, color, lerp_angle, destroy
from ursina.shaders import unlit_shader
from .materiais import shader_cidade as lit_with_shadows_shader

from .estilo import CIANO, LARANJA
from .catalogo_assets import CATALOGO
from .ciclo_vida import destruir_arvore as destroy


class Veiculo3D:
    def __init__(self, posicao):
        self.raiz = Entity(position=posicao)
        self.carroceria = Entity(parent=self.raiz, y=.12)
        def p(posicao, escala, cor, shader=lit_with_shadows_shader):
            return Entity(parent=self.carroceria, model="cube", position=posicao,
                          scale=escala, color=cor, shader=shader)
        p((0, .32, 0), (.64, .18, 1.5), color.hex("#1C293C"))
        p((0, .72, -.25), (.72, .7, .98), color.hex("#EDF2ED"))
        p((0, .72, .58), (.67, .59, .48), CIANO.tint(-.18))
        p((0, .89, .831), (.52, .21, .015), color.hex("#183549"))
        p((.368, .73, -.25), (.02, .19, .69), CIANO, unlit_shader)
        p((-.368, .73, -.25), (.02, .19, .69), CIANO, unlit_shader)
        p((0, 1.105, -.25), (.69, .04, .93), color.hex("#B8C9CE"))
        for x in (-.34, .34):
            for z in (-.57, .51):
                Entity(parent=self.carroceria, model="sphere", position=(x, .28, z),
                       scale=(.17, .34, .34), color=color.hex("#101826"), shader=lit_with_shadows_shader)
        for x in (-.22, .22):
            p((x, .6, .84), (.12, .08, .025), color.hex("#FFFFC0"), unlit_shader)
        p((0, 1.04, .58), (.3, .07, .16), LARANJA, unlit_shader)
        self.brisa = Entity(parent=self.raiz, model="sphere", scale=(1.1, .025, 1.8),
                             y=.1, color=color.rgba32(0, 209, 255, 70), shader=unlit_shader)
        self.drone = Entity(parent=self.raiz, enabled=False)
        Entity(parent=self.drone, model="cube", scale=(.7, .35, .75), color=CIANO,
               shader=lit_with_shadows_shader)
        Entity(parent=self.drone, model="cube", y=-.35, scale=.4, color=LARANJA,
               shader=lit_with_shadows_shader)
        for x in (-.52, .52):
            for z in (-.52, .52):
                Entity(parent=self.drone, model="cube", position=(x / 2, .05, z / 2),
                       scale=(.1, .1, 1.3), rotation_y=45 if x * z > 0 else -45,
                       color=color.hex("#CDDDE4"), shader=lit_with_shadows_shader)
                Entity(parent=self.drone, model="sphere", position=(x, .15, z),
                       scale=(.65, .025, .65), color=color.rgba32(0, 209, 255, 130), shader=unlit_shader)
        self.deslocamento_altura = 0
        self.rodas = []
        self.identidade = Entity(parent=self.raiz)
        # glTF usa mão direita; a conversão para o Ursina inverte o eixo Z.
        # A cabine deve apontar para +Z, direção usada pelo motor do percurso.
        self.modelo_entrega = CATALOGO.criar("cars", "delivery", self.raiz, (0, .10, 0), 1.8, 180)
        if self.modelo_entrega is not None:
            destroy(self.carroceria)
            self.carroceria = self.modelo_entrega
            self.rodas = [no for no in self.carroceria.model.find_all_matches("**/wheel-*")
                          if not isinstance(no.node(), GeomNode)]
            # Identidade NEXUS no baú, em ambas as laterais.
            for lado in (-1, 1):
                Entity(parent=self.identidade, model="cube", position=(lado * .34, .64, -.28),
                       scale=(.012, .12, .56), color=CIANO, shader=unlit_shader)
        self.posicao_anterior = Vec3(*posicao)
        self.giro_rodas = 0.

    def definir_modalidade(self, modo):
        abstrato = modo == "euclidiano"
        self.carroceria.enabled = not abstrato
        self.brisa.enabled = not abstrato
        self.identidade.enabled = not abstrato
        self.drone.enabled = abstrato
        self.deslocamento_altura = 6 if abstrato else 0

    def atualizar(self, posicao, direcao, dt):
        nova_posicao = Vec3(*posicao)
        deslocamento = (nova_posicao - self.posicao_anterior).length()
        self.posicao_anterior = nova_posicao
        if dt > 0:
            self.giro_rodas = (self.giro_rodas + deslocamento / .18 * 180 / math.pi) % 360
            for roda in self.rodas:
                roda.set_p(self.giro_rodas)
        self.raiz.position = Vec3(*posicao) + Vec3(0, self.deslocamento_altura, 0)
        if direcao[0] ** 2 + direcao[2] ** 2 > .00001:
            angulo = math.degrees(math.atan2(direcao[0], direcao[2]))
            self.raiz.rotation_y = lerp_angle(self.raiz.rotation_y, angulo, min(1, dt * 12))
            inclinacao = -math.degrees(math.atan2(direcao[1], math.hypot(direcao[0], direcao[2])))
            self.raiz.rotation_x += (inclinacao - self.raiz.rotation_x) * min(1, dt * 12)

    def destruir(self):
        destroy(self.raiz)

