"""Importação dos OBJ Kenney com materiais e texturas originais.

Leitura via Python também funciona no ambiente restrito de desenvolvimento.
As malhas e texturas são compartilhadas por todas as instâncias.
"""
from math import hypot
from pathlib import Path
from panda3d.core import (Geom, GeomNode, GeomTriangles, GeomVertexData,
                         GeomVertexFormat, GeomVertexWriter, NodePath,
                         PNMImage, StringStream, Texture, SamplerState)

ROOT = Path(__file__).resolve().parent / "assets"
KITS = {"cidade": "kenney_city-kit-commercial_2.1", "rua": "kenney_city-kit-roads", "carro": "kenney_car-kit", "suburbio": "kenney_city-kit-suburban_20"}


class Biblioteca:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.modelos = {}
        self.texturas = {}

    def modelo(self, kit, nome, *, cota_minima=None, raio_maximo=None):
        if kit not in KITS:
            raise ValueError(f"Kit desconhecido: {kit!r}. Disponiveis: {', '.join(KITS)}")
        if not nome or Path(nome).name != nome or nome in (".", ".."):
            raise ValueError(f"Nome de modelo invalido: {nome!r}")
        chave = (kit, nome) if cota_minima is None else (kit, nome, cota_minima)
        if raio_maximo is not None:
            chave = (kit, nome, cota_minima, raio_maximo)
        if chave not in self.modelos:
            caminho = self.root / KITS[kit] / "Models" / "OBJ format" / f"{nome}.obj"
            if not caminho.is_file():
                raise FileNotFoundError(f"Asset ausente: {caminho}. Preserve a pasta Models dos kits Kenney.")
            self.modelos[chave] = self._ler_obj(caminho, cota_minima, raio_maximo)
        return self.modelos[chave]

    def paleta(self, kit, variante):
        """Carrega uma variação de cor do próprio kit, com os mesmos UVs."""
        caminho = self.root / KITS[kit] / "Models" / "Textures" / f"variation-{variante}.png"
        return self._textura(caminho)

    def _textura(self, caminho):
        if caminho not in self.texturas:
            if not caminho.is_file():
                raise FileNotFoundError(f"Textura ausente: {caminho}")
            imagem = PNMImage()
            if not imagem.read(StringStream(caminho.read_bytes()), "imagem.png"):
                raise ValueError(f"Textura inválida: {caminho}")
            textura = Texture(str(caminho))
            textura.load(imagem)
            textura.setMagfilter(SamplerState.FT_nearest)
            textura.setMinfilter(SamplerState.FT_linear_mipmap_linear)
            self.texturas[caminho] = textura
        return self.texturas[caminho]

    def _ler_obj(self, caminho, cota_minima, raio_maximo):
        vertices, normais, uvs, faces = [], [], [], {}
        material = ""
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            partes = linha.split()
            if not partes:
                continue
            tipo, valores = partes[0], partes[1:]
            if tipo == "v":
                x, y, z = map(float, valores[:3])
                vertices.append((x, -z, y))  # Kenney Y-up → Panda Z-up.
            elif tipo == "vn":
                x, y, z = map(float, valores)
                normais.append((x, -z, y))
            elif tipo == "vt":
                uvs.append(tuple(map(float, valores[:2])))
            elif tipo == "usemtl":
                material = valores[0]
            elif tipo == "f":
                indices = [tuple(int(v) if v else 0 for v in valor.split("/")) for valor in valores]
                for i in range(1, len(indices) - 1):
                    faces.setdefault(material, []).append((indices[0], indices[i], indices[i + 1]))
        materiais, atual = {}, ""
        arquivo_mtl = caminho.with_suffix(".mtl")
        if not arquivo_mtl.is_file():
            raise FileNotFoundError(f"Material ausente: {arquivo_mtl}")
        for linha in arquivo_mtl.read_text(encoding="utf-8").splitlines():
            partes = linha.split()
            if partes and partes[0] == "newmtl":
                atual = partes[1]
            elif partes and partes[0] == "map_Kd":
                materiais[atual] = caminho.parent / " ".join(partes[1:])
        raiz = NodePath(caminho.stem)
        for material, triangulos in faces.items():
            # Alguns OBJ Kenney repetem grupos com os mesmos índices.
            triangulos = list(dict.fromkeys(triangulos))
            if cota_minima is not None:
                triangulos = [t for t in triangulos
                              if all(vertices[i - 1 if i > 0 else i][2] >= cota_minima
                                     for i, *_ in t)]
            if raio_maximo is not None:
                triangulos = [t for t in triangulos
                              if all(hypot(*vertices[i - 1 if i > 0 else i][:2]) <= raio_maximo
                                     for i, *_ in t)]
            if not triangulos:
                continue
            dados = GeomVertexData(material, GeomVertexFormat.getV3n3t2(), Geom.UH_static)
            dados.setNumRows(len(triangulos) * 3)
            v, n, uv = (GeomVertexWriter(dados, campo) for campo in ("vertex", "normal", "texcoord"))
            primitiva = GeomTriangles(Geom.UH_static)
            for triangulo in triangulos:
                for indices in triangulo:
                    vi, ti, ni = (*indices, 0, 0)[:3]
                    v.addData3(*vertices[vi - 1 if vi > 0 else vi])
                    n.addData3(*(normais[ni - 1 if ni > 0 else ni] if ni else (0, 0, 1)))
                    uv.addData2(*(uvs[ti - 1 if ti > 0 else ti] if ti else (0, 0)))
            for i in range(len(triangulos)):
                primitiva.addVertices(i * 3, i * 3 + 1, i * 3 + 2)
            geometria = Geom(dados)
            geometria.addPrimitive(primitiva)
            no = GeomNode(material)
            no.addGeom(geometria)
            malha = raiz.attachNewNode(no)
            if material in materiais:
                malha.setTexture(self._textura(materiais[material]), 1)
        return raiz


def instancia_normalizada(modelo, tamanho=1.0):
    """Copia o modelo e ajusta sua maior dimensao, sem alterar o cache.

    A origem e a proporcao do asset sao preservadas; nao o centraliza.
    """
    if tamanho <= 0:
        raise ValueError("O tamanho deve ser positivo")
    limites = modelo.getTightBounds()
    if not limites or limites[0] is None:
        raise ValueError("Modelo sem geometria para normalizar")
    minimo, maximo = limites
    dimensao = max(maximo[i] - minimo[i] for i in range(3))
    if dimensao <= 0:
        raise ValueError("Modelo com dimensoes nulas")
    suporte = NodePath("instancia")
    copia = modelo.copyTo(suporte)
    copia.setScale(copia.getScale() * (tamanho / dimensao))
    copia.detachNode()
    return copia
