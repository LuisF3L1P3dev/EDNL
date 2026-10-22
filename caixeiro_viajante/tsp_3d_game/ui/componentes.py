"""Peças de interface leves, compartilhadas pela HUD e pelos modais."""

from ursina import BoxCollider, Button, Entity, Text, color
from ursina.shaders import unlit_shader

from .tema import (ALTURA_REFERENCIA, BORDA_CLARA, PALETA, SOMBRA,
                   carregar_fontes)
from ..graphics.estilo import CIANO, PAINEL, SUPERFICIE, TEXTO


def px(valor):
    """Converte pixels de referência para as unidades da câmera de UI."""
    return valor / ALTURA_REFERENCIA


def texto(parent, conteudo, x, y, escala=.65, cor=TEXTO, titulo=False, **kwargs):
    fontes = carregar_fontes()
    node = Text(parent=parent, text=conteudo, x=x, y=y, scale=escala,
                color=cor, origin=(-.5, .5), z=-.06, **kwargs)
    if titulo:
        node.font = fontes[0]
    return node


def _nove_fatias(parent, cor, z, borda_x, borda_y):
    """Painel 3 × 3 com bordas finas que mantêm o tamanho no redimensionamento."""
    face = color.hex(str(cor)) if isinstance(cor, str) else cor
    borda = color.hex(BORDA_CLARA)
    escura = color.hex("#152034")
    topo = color.hex("#354663")
    lateral = color.hex("#223149")
    bx, by = min(.12, max(.004, borda_x)), min(.35, max(.004, borda_y))
    larguras = (bx, 1 - 2 * bx, bx)
    alturas = (by, 1 - 2 * by, by)
    xs = (-.5 + bx / 2, 0, .5 - bx / 2)
    ys = (.5 - by / 2, 0, -.5 + by / 2)
    centro = Entity(parent=parent, position=(0, 0, z))
    for linha in range(3):
        for coluna in range(3):
            if linha == 1 and coluna == 1:
                tom = face
            elif linha == 0:
                tom = topo if coluna == 1 else borda
            elif linha == 2:
                tom = escura
            else:
                tom = lateral
            Entity(parent=centro, model="quad",
                   position=(xs[coluna], ys[linha], -.001),
                   scale=(larguras[coluna], alturas[linha]),
                   color=tom, shader=unlit_shader)
    return centro


def painel(parent, x, y, largura, altura, cor=PAINEL, z=.04, bloquear=False):
    """Cria painel com sombra curta e moldura em nove partes."""
    grupo = Entity(parent=parent, position=(x, y, z), scale=(largura, altura))
    if bloquear:
        # Mantém a área vazia do painel sobre a cena sem encobrir os controles.
        grupo.collider = BoxCollider(grupo, size=(1, 1, .001))
    if altura <= px(8) or largura <= px(8):
        Entity(parent=grupo, model="quad", position=(0, 0, 0), scale=(1, 1),
               color=cor, shader=unlit_shader)
    else:
        bx = px(5) / max(largura, px(5))
        by = px(5) / max(altura, px(5))
        sombra = Entity(parent=grupo, model="quad",
                        position=(px(2) / largura, -px(3) / altura, .012),
                        scale=(1.012, 1.012), color=color.hex(SOMBRA), shader=unlit_shader)
        _nove_fatias(grupo, cor, 0, bx, by)
        grupo.sombra = sombra
    return grupo


def botao(parent, rotulo, x, y, largura, altura, acao,
          cor=SUPERFICIE, cor_texto=TEXTO, titulo=True, raio=.12):
    """Botão arredondado com sombra, relevo e feedback nativo do Ursina."""
    contorno = painel(parent, x, y - altura * .065, largura, altura,
                      color.hex("#24334D"), z=-.082)
    b = Button(parent=parent, text=rotulo or " ", position=(x, y, -.1),
               scale=(largura - .003, altura - .003), color=cor,
               text_color=cor_texto, highlight_color=cor.tint(.14),
               pressed_color=cor.tint(-.16), radius=raio, on_click=acao)
    b.text_entity.scale *= .68
    b.text_entity.font = carregar_fontes()[0] if titulo else carregar_fontes()[1]
    b.moldura = contorno
    return b


def km(valor):
    return f"{valor / 1000:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".") + " km"
