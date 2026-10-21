"""Cache de GLB com chave por pacote; preserva materiais, texturas e normais."""
from pathlib import Path
import gltf
from panda3d.core import NodePath, MaterialAttrib, ColorAttrib
from ursina import Entity, color
from .materiais import shader_cidade as lit_with_shadows_shader

RAIZ_ASSETS = Path(__file__).resolve().parents[2] / "assets" / "kenney"


class CatalogoAssets:
    def __init__(self):
        self.modelos = {}
        self.dimensoes = {}
        self.suporte = NodePath("cache_instancias")
        self.carregamentos = 0

    def carregar(self, pacote, nome):
        chave = (pacote, nome)
        if chave not in self.modelos:
            caminho = RAIZ_ASSETS / pacote / f"{nome}.glb"
            if not caminho.is_file():
                return None
            opcoes = gltf.GltfSettings()
            opcoes.no_srgb = True
            original = NodePath(gltf.load_model(str(caminho), gltf_settings=opcoes))
            # O shader estilizado usa cores de vértice/estado. Transfere a cor
            # base dos materiais sem textura (Nature Kit) para esse canal.
            for caminho_no in original.find_all_matches("**/+GeomNode"):
                no = caminho_no.node()
                for i in range(no.get_num_geoms()):
                    estado = no.get_geom_state(i)
                    atributo = estado.get_attrib(MaterialAttrib)
                    if atributo and atributo.get_material().has_base_color():
                        cor = atributo.get_material().get_base_color()
                        material = atributo.get_material().get_name().lower()
                        if pacote == "nature" and "leaf" in material:
                            cor = color.rgba(.23, .44, .12, 1) if "dark" in nome else color.rgba(.30, .57, .16, 1)
                        elif pacote == "nature" and "bark" in material:
                            cor = color.rgba(.43, .30, .18, 1)
                        no.set_geom_state(i, estado.add_attrib(ColorAttrib.make_flat(cor)))
            minimo, maximo = original.get_tight_bounds()
            largura = max(maximo.x - minimo.x, maximo.z - minimo.z, .001)
            raiz = NodePath(f"{pacote}_{nome}")
            original.reparent_to(raiz)
            original.set_scale(1 / largura)
            original.set_pos(-(minimo.x + maximo.x) / (2 * largura), -minimo.y / largura,
                             -(minimo.z + maximo.z) / (2 * largura))
            self.modelos[chave] = raiz
            self.dimensoes[chave] = ((maximo.x - minimo.x) / largura,
                                    (maximo.y - minimo.y) / largura,
                                    (maximo.z - minimo.z) / largura)
            self.carregamentos += 1
        return self.modelos[chave]

    def criar(self, pacote, nome, parent, posicao=(0, 0, 0), tamanho=1, rotacao=0):
        modelo = self.carregar(pacote, nome)
        if modelo is None:
            return None
        copia = modelo.copy_to(self.suporte)
        entidade = Entity(parent=parent, model=copia, position=posicao, scale=tamanho,
                          rotation_y=rotacao, color=color.white, shader=lit_with_shadows_shader,
                          name=f"{pacote}_{nome}", add_to_scene_entities=False)
        return entidade


CATALOGO = CatalogoAssets()
