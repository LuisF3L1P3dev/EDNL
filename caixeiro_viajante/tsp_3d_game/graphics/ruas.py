"""Módulos Kenney ajustados à altura contínua das ruas e pontes da missão."""
import math
from panda3d.core import (GeomVertexReader, InternalName, TextureAttrib, TextureStage, TexMatrixAttrib)
from ursina import Entity, Mesh
from .catalogo_assets import CATALOGO
from .geometria_ruas import (PerfilViario, LARGURA_VIA, ALTURA_PISO,
                             escolher_cruzamento, dividir_triangulo)
from .lotes_estaticos import agrupar_estatico
from .materiais import shader_cidade


class Ruas3D:
    def __init__(self, cenario, parent):
        self.cenario = cenario
        self.raiz = Entity(parent=parent, name="Vias_Kenney")
        self.perfil = PerfilViario(cenario)
        self.cache_modelos = {}
        self.regioes = {}
        self.pontes = []
        for a, b, dados in cenario.grafo.edges(data=True):
            self._estrada(a, b, dados)
        for no in cenario.grafo:
            self._cruzamento(no)
        for regiao in self.regioes.values():
            agrupar_estatico(regiao)

    @staticmethod
    def disponivel():
        return CATALOGO.carregar("vias", "road-bridge") is not None

    def _regiao(self, x, z):
        tamanho = self.cenario.espacamento * 3
        chave = (math.floor(x / tamanho), math.floor(z / tamanho))
        if chave not in self.regioes:
            self.regioes[chave] = self.raiz.attach_new_node(f"Trechos_{chave}")
        return self.regioes[chave]

    def _modelo(self, nome):
        if nome in self.cache_modelos:
            return self.cache_modelos[nome]
        modelo = CATALOGO.carregar("vias", nome)
        if modelo is None:
            raise FileNotFoundError(f"Modelo de rua ausente: {nome}.glb")
        partes = []
        for caminho in modelo.find_all_matches("**/+GeomNode"):
            no = caminho.node()
            matriz = caminho.get_mat(modelo)
            for i in range(no.get_num_geoms()):
                geometria = no.get_geom(i)
                dados = geometria.get_vertex_data()
                posicoes = GeomVertexReader(dados, "vertex")
                normais = GeomVertexReader(dados, "normal")
                coluna_uv = InternalName.get_texcoord_name("0")
                if not dados.get_format().has_column(coluna_uv):
                    coluna_uv = InternalName.get_texcoord()
                uvs = GeomVertexReader(dados, coluna_uv)
                vertices = []
                while not posicoes.is_at_end():
                    p = matriz.xform_point(posicoes.get_data3())
                    n = matriz.xform_vec(normais.get_data3())
                    n.normalize()
                    uv = uvs.get_data2()
                    vertices.append(tuple(round(v, 6) for v in p) + tuple(n) + tuple(uv))
                triangulos = []
                for j in range(geometria.get_num_primitives()):
                    primitiva = geometria.get_primitive(j).decompose()
                    for k in range(primitiva.get_num_primitives()):
                        inicio, fim = primitiva.get_primitive_start(k), primitiva.get_primitive_end(k)
                        ids = [primitiva.get_vertex(indice) for indice in range(inicio, fim)]
                        triangulos.append(tuple(vertices[indice] for indice in ids))
                # A malha Ursina usa UVs padrão; mantém a textura original no
                # mesmo estágio, sem depender do nome texcoord.0 do importador.
                estado = no.get_geom_state(i)
                texturas = estado.get_attrib(TextureAttrib)
                if texturas and texturas.get_num_on_stages():
                    antigo = texturas.get_on_stage(0)
                    comum = TextureStage.get_default()
                    matrizes = estado.get_attrib(TexMatrixAttrib)
                    estado = estado.remove_attrib(TextureAttrib).remove_attrib(TexMatrixAttrib)
                    estado = estado.add_attrib(TextureAttrib.make().add_on_stage(comum, texturas.get_on_texture(antigo)))
                    if matrizes and matrizes.has_stage(antigo):
                        estado = estado.add_attrib(TexMatrixAttrib.make().add_stage(comum, matrizes.get_transform(antigo)))
                partes.append((triangulos, estado))
        self.cache_modelos[nome] = partes
        return partes

    def _modulo(self, nome, x, z, escala_x, escala_z, giro=0, piso=.01, altura_minima=None):
        angulo = math.radians(giro)
        seno, cosseno = math.sin(angulo), math.cos(angulo)
        raio = (abs(cosseno * escala_x) + abs(seno * escala_z)) / 2
        profundidade = (abs(seno * escala_x) + abs(cosseno * escala_z)) / 2
        cortes_x = self.perfil.cortes(0, x - raio, x + raio)
        cortes_z = self.perfil.cortes(2, z - profundidade, z + profundidade)
        for triangulos, estado in self._modelo(nome):
            vertices, normais, uvs = [], [], []
            for triangulo in triangulos:
                if altura_minima is not None and min(v[1] for v in triangulo) < altura_minima:
                    continue
                pontos = []
                for px, py, pz, nx, ny, nz, u, v in triangulo:
                    wx = x + cosseno * px * escala_x + seno * pz * escala_z
                    wz = z - seno * px * escala_x + cosseno * pz * escala_z
                    normal = (cosseno * nx / escala_x + seno * nz / escala_z,
                              ny / LARGURA_VIA, -seno * nx / escala_x + cosseno * nz / escala_z)
                    pontos.append((wx, py, wz, *normal, u, v))
                for parte in dividir_triangulo(pontos, cortes_x, cortes_z):
                    for wx, py, wz, nx, ny, nz, u, v in parte:
                        altura = self.perfil.altura(wx, wz) + ALTURA_PISO + (py - piso) * LARGURA_VIA
                        vertices.append((wx, altura, wz))
                        normais.append(self.perfil.normal(wx, wz, (nx, ny, nz)))
                        uvs.append((u, v))
            malha = Mesh(vertices=vertices, normals=normais, uvs=uvs, mode="triangle", static=True)
            for caminho in malha.find_all_matches("**/+GeomNode"):
                caminho.node().set_geom_state(0, estado)
            Entity(parent=self._regiao(x, z), model=malha, shader=shader_cidade,
                   name=nome, add_to_scene_entities=False)

    def _estrada(self, a, b, dados):
        p, q = self.cenario.posicao(a), self.cenario.posicao(b)
        comprimento = math.hypot(q[0] - p[0], q[2] - p[2])
        comprimento -= LARGURA_VIA
        x, z = (p[0] + q[0]) / 2, (p[2] + q[2]) / 2
        horizontal = abs(q[0] - p[0]) > abs(q[2] - p[2])
        giro = 0 if horizontal else 90
        if dados["ponte"]:
            # road-bridge é um viaduto com uma rua inferior. Mantemos apenas
            # o tabuleiro superior; o pilar abaixo é ajustado à altura do rio.
            self._modulo("road-bridge", x, z, LARGURA_VIA, comprimento,
                         90 if horizontal else 0, piso=.51, altura_minima=.449)
            self._modulo("road-straight-barrier", x, z, LARGURA_VIA, comprimento,
                         90 if horizontal else 0, piso=0)
            topo = self.perfil.altura(x, z) + ALTURA_PISO - .115
            pilar = CATALOGO.criar("vias", "bridge-pillar-wide", self._regiao(x, z), (x, .14, z))
            altura_modelo = CATALOGO.dimensoes[("vias", "bridge-pillar-wide")][1]
            pilar.scale = (.42, max(.05, topo - .14) / altura_modelo, .42)
            self.pontes.append((a, b))
        else:
            self._modulo("road-straight", x, z, comprimento, LARGURA_VIA, giro)

    def _cruzamento(self, no):
        p = self.cenario.posicao(no)
        direcoes = []
        for vizinho in self.cenario.grafo.neighbors(no):
            q = self.cenario.posicao(vizinho)
            direcoes.append((round((q[0] - p[0]) / self.cenario.espacamento),
                             round((q[2] - p[2]) / self.cenario.espacamento)))
        nome, giro = escolher_cruzamento(direcoes)
        self._modulo(nome, p[0], p[2], LARGURA_VIA, LARGURA_VIA, giro)
