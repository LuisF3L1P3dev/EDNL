"""Agrupa decoração opaca por região, preservando cores, UVs e normais."""
from panda3d.core import (MaterialAttrib, ShaderAttrib, TransparencyAttrib,
                         TextureAttrib, TexMatrixAttrib, TextureStagePool, SceneGraphReducer)
from .materiais import shader_cidade


def agrupar_estatico(raiz):
    """Aplicar somente a objetos sem interação, animação, texto ou transparência.

    Cada Entity aplica seus próprios ShaderInputs e transparência dual. Retirar
    esses estados redundantes permite juntar as geometrias com o mesmo material
    visual. As cores-base dos GLB já foram transferidas pelo catálogo.
    """
    for caminho in raiz.find_all_matches("**"):
        caminho.clear_python_tag("Entity")
        for atributo in (MaterialAttrib, ShaderAttrib, TransparencyAttrib):
            caminho.clear_attrib(atributo)
        no = caminho.node()
        if not no.is_geom_node():
            continue
        for i in range(no.get_num_geoms()):
            estado = no.get_geom_state(i)
            for atributo in (MaterialAttrib, ShaderAttrib, TransparencyAttrib):
                estado = estado.remove_attrib(atributo)
            texturas = estado.get_attrib(TextureAttrib)
            if texturas:
                comuns = TextureAttrib.make()
                for indice in range(texturas.get_num_on_stages()):
                    estagio = texturas.get_on_stage(indice)
                    comuns = comuns.add_on_stage(TextureStagePool.get_stage(estagio), texturas.get_on_texture(estagio))
                estado = estado.add_attrib(comuns)
            matrizes = estado.get_attrib(TexMatrixAttrib)
            if matrizes:
                comuns = TexMatrixAttrib.make()
                for indice in range(matrizes.get_num_stages()):
                    estagio = matrizes.get_stage(indice)
                    comuns = comuns.add_stage(TextureStagePool.get_stage(estagio), matrizes.get_transform(estagio))
                estado = estado.add_attrib(comuns)
            no.set_geom_state(i, estado)
    if not shader_cidade.compiled:
        shader_cidade.compile()
    raiz.set_shader(shader_cidade._shader)
    for nome, valor in shader_cidade.default_input.items():
        raiz.set_shader_input(nome, valor)
    raiz.set_transparency(TransparencyAttrib.M_none)
    raiz.clear_model_nodes()
    raiz.flatten_strong()
    redutor = SceneGraphReducer()
    redutor.collect_vertex_data(raiz.node(), 0)
    redutor.unify(raiz.node(), False)
