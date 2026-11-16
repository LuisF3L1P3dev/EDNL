"""Cena urbana estática sobre a geometria do grafo, com assets Kenney locais.

As ruas são exclusivamente as arestas fornecidas. A decoração nunca participa
da adjacência e tem seu espaço reservado fora de todas as polilinhas de ruas.
O veículo, as luzes e as etiquetas projetadas pertencem à aplicação.
"""

from dataclasses import dataclass
from math import atan2, cos, degrees, dist, hypot, pi, sin
from random import Random

from panda3d.core import (Geom, GeomNode, GeomTriangles, GeomVertexData,
                         GeomVertexFormat, GeomVertexWriter,
                         TransparencyAttrib, Vec3)

from geometria3d import criar_mapa_visual


LARGURA_RUA = .95
NIVEL_GRAMA = -.35
AMARELO = (1., .76, .13, 1.)


def superficie(parent, nome, pontos, cor):
    """Triangule uma superfície convexa, inclusive as laterais da ilha."""
    pontos = tuple(pontos)
    if len(pontos) < 3:
        raise ValueError("Uma superfície precisa de pelo menos três vértices.")
    normal = (Vec3(*pontos[1]) - Vec3(*pontos[0])).cross(
        Vec3(*pontos[2]) - Vec3(*pontos[0]))
    normal.normalize()
    dados = GeomVertexData(nome, GeomVertexFormat.getV3n3(), Geom.UH_static)
    v, n = GeomVertexWriter(dados, "vertex"), GeomVertexWriter(dados, "normal")
    for ponto in pontos:
        v.addData3(*ponto)
        n.addData3(normal)
    triangulos = GeomTriangles(Geom.UH_static)
    for i in range(1, len(pontos) - 1):
        triangulos.addVertices(0, i, i + 1)
    geometria = Geom(dados)
    geometria.addPrimitive(triangulos)
    no = GeomNode(nome)
    no.addGeom(geometria)
    malha = parent.attachNewNode(no)
    malha.setColor(*cor)
    malha.setTwoSided(True)
    return malha


def _disco(parent, nome, x, y, z, raio, cor, *, proporcao=1., lados=20):
    return superficie(parent, nome, [
        (x + cos(i * 2 * pi / lados) * raio,
         y + sin(i * 2 * pi / lados) * raio * proporcao, z)
        for i in range(lados)
    ], cor)


def _faixa(parent, nome, a, b, largura, cor, elevacao=0.):
    dx, dy = b[0] - a[0], b[1] - a[1]
    comprimento = hypot(dx, dy)
    if comprimento <= 1e-8:
        return
    px, py = -dy / comprimento * largura / 2, dx / comprimento * largura / 2
    return superficie(parent, nome, [
        (a[0] + px, a[1] + py, a[2] + elevacao),
        (a[0] - px, a[1] - py, a[2] + elevacao),
        (b[0] - px, b[1] - py, b[2] + elevacao),
        (b[0] + px, b[1] + py, b[2] + elevacao),
    ], cor)


def _distancia_segmento(x, y, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    comprimento2 = dx * dx + dy * dy
    t = max(0., min(1., ((x - a[0]) * dx + (y - a[1]) * dy) / comprimento2)) if comprimento2 else 0.
    return hypot(x - a[0] - t * dx, y - a[1] - t * dy)


@dataclass(frozen=True)
class Decoracao:
    tipo: str
    kit: str
    modelo: str
    x: float
    y: float
    raio: float
    altura: float


class Cena3D:
    def __init__(self, base, grafo, biblioteca):
        self.grafo = grafo
        self.biblioteca = biblioteca
        self.mapa_visual = criar_mapa_visual(grafo)
        self.posicoes = self.mapa_visual.posicoes
        self.ruas = self.mapa_visual.ruas
        self.raiz = base.render.attachNewNode(f"cidade-{grafo.id}")
        self.rota = base.render.attachNewNode("rota-calculada")
        self.rota.setLightOff()
        self.decoracoes = []
        self.modelos_usados = set()
        self.trechos_rua = 0
        self._segmentos = tuple(
            (a, b) for aresta in grafo.arestas
            for a, b in zip(self.ruas[aresta.origem, aresta.destino],
                            self.ruas[aresta.origem, aresta.destino][1:])
        )
        self._rng = Random(410 + len(grafo.ids))
        x0, y0, x1, y1 = self.mapa_visual.limites_xy
        self.meia_largura = max(26., abs(x0) + 2., abs(x1) + 2.)
        self.meia_altura = max(23., abs(y0) + 2., abs(y1) + 2.)
        try:
            self._terreno()
            self._construir_ruas()
            self._cruzamentos()
            self._decorar()
            self.raiz.flattenStrong()
        except Exception:
            self.destruir()
            raise

    def _modelo(self, kit, nome):
        self.modelos_usados.add((kit, nome))
        return self.biblioteca.modelo(kit, nome)

    def _terreno(self):
        w, h = self.meia_largura, self.meia_altura
        superficie(self.raiz, "gramado", [(-w, -h, NIVEL_GRAMA), (w, -h, NIVEL_GRAMA),
                   (w, h, NIVEL_GRAMA), (-w, h, NIVEL_GRAMA)], (.52, .73, .43, 1))
        cantos = [(-w, -h), (w, -h), (w, h), (-w, h)]
        for a, b in zip(cantos, cantos[1:] + cantos[:1]):
            superficie(self.raiz, "terra-da-ilha", [(*a, NIVEL_GRAMA), (*b, NIVEL_GRAMA),
                       (*b, -1.15), (*a, -1.15)], (.37, .52, .31, 1))
            # Faixa clara na borda destaca a espessura da maquete.
            superficie(self.raiz, "borda-da-ilha", [(*a, NIVEL_GRAMA), (*b, NIVEL_GRAMA),
                       (*b, NIVEL_GRAMA - .12), (*a, NIVEL_GRAMA - .12)], (.66, .77, .52, 1))
        self._sombras = self.raiz.attachNewNode("sombras-de-contato")
        self._sombras.setTransparency(TransparencyAttrib.M_alpha)
        self._sombras.setDepthWrite(False)
        self._sombras.setLightOff()
        # Variações discretas do gramado dão escala sem desenhar novas ruas.
        for _ in range(24):
            x = self._rng.uniform(-w + 3, w - 3)
            y = self._rng.uniform(-h + 3, h - 3)
            _disco(self.raiz, "canteiro-gramado", x, y, NIVEL_GRAMA + .002,
                   self._rng.uniform(1.4, 3.1), (.50, .71, .40, 1),
                   proporcao=self._rng.uniform(.6, 1.2), lados=9)

    def _construir_ruas(self):
        modelo = self._modelo("rua", "road-straight")
        lo, hi = modelo.getTightBounds()
        comprimento_modelo, largura_modelo = hi.x - lo.x, hi.y - lo.y
        for a, b in self._segmentos:
            delta = Vec3(*b) - Vec3(*a)
            comprimento = delta.length()
            # A calçada estrutural acompanha exatamente a mesma aresta.
            _faixa(self.raiz, "base-da-rua", a, b, LARGURA_RUA + .15,
                   (.65, .69, .65, 1), -.025)
            partes = max(1, round(comprimento / 1.6))
            for i in range(partes):
                suporte = self.raiz.attachNewNode("trecho-rua")
                suporte.setPos(Vec3(*a) + delta * ((i + .5) / partes))
                suporte.setHpr(-degrees(atan2(delta.x, delta.y)),
                               degrees(atan2(delta.z, hypot(delta.x, delta.y))), 0)
                malha = modelo.copyTo(suporte)
                malha.setH(90)
                # Kenney usa X longitudinal: preservar a escala das marcações.
                malha.setScale(comprimento / partes / comprimento_modelo * 1.004,
                               LARGURA_RUA / largura_modelo, .55)
                malha.setZ(-hi.z * .55)
                self.trechos_rua += 1

    def _cruzamentos(self):
        modelo = self._modelo("rua", "road-crossroad")
        lo, hi = modelo.getTightBounds()
        escala = 1.18 / max(hi.x - lo.x, hi.y - lo.y)
        for no, (x, y, z) in self.posicoes.items():
            _disco(self.raiz, f"base-cruzamento-{no}", x, y, z - .018, .78,
                   (.70, .74, .69, 1), lados=16)
            malha = modelo.copyTo(self.raiz)
            malha.setScale(escala, escala, .5)
            malha.setPos(x, y, z - hi.z * .5)
            # Um ponto azul identifica o único local em que ruas se conectam.
            _disco(self.raiz, f"ponto-{no}", x, y, z + .017, .33, (.13, .50, .78, 1))
            _disco(self.raiz, f"miolo-{no}", x, y, z + .019, .20, (.36, .73, .93, 1))

    def distancia_rua(self, x, y):
        """Distância XY à rua mais próxima, útil para verificar lotes."""
        return min((_distancia_segmento(x, y, a, b) for a, b in self._segmentos), default=float("inf"))

    def _livre(self, x, y, raio, *, afastamento_no=1.2):
        if abs(x) + raio > self.meia_largura - 1 or abs(y) + raio > self.meia_altura - 1:
            return False
        if self.distancia_rua(x, y) < raio + LARGURA_RUA / 2 + .4:
            return False
        if any(hypot(x - p[0], y - p[1]) < raio + afastamento_no for p in self.posicoes.values()):
            return False
        return not any(hypot(x - d.x, y - d.y) < raio + d.raio + .3 for d in self.decoracoes)

    def _sombra(self, x, y, raio):
        for i, (fator, alfa) in enumerate(((1.25, .035), (1.07, .05), (.88, .065))):
            _disco(self._sombras, "sombra-suave", x + .14, y + .12,
                   NIVEL_GRAMA + .006 + i * .001, raio * fator,
                   (.12, .22, .12, alfa), proporcao=.78, lados=16)

    def _dimensoes(self, kit, nome, tamanho, altura=False):
        modelo = self._modelo(kit, nome)
        lo, hi = modelo.getTightBounds()
        escala = tamanho / ((hi.z - lo.z) if altura else max(hi.x - lo.x, hi.y - lo.y))
        raio = hypot(hi.x - lo.x, hi.y - lo.y) * escala / 2
        return modelo, lo, hi, escala, raio

    def _adicionar_decoracao(self, tipo, kit, nome, x, y, tamanho, orientacao=0.):
        modelo, lo, hi, escala, raio = self._dimensoes(kit, nome, tamanho, tipo == "arvore")
        raio += .20 if tipo == "edificio" else .05
        if not self._livre(x, y, raio, afastamento_no=2. if tipo == "edificio" else 1.5):
            return False
        suporte = self.raiz.attachNewNode(tipo)
        suporte.setPos(x, y, NIVEL_GRAMA + .055)
        suporte.setH(orientacao)
        malha = modelo.copyTo(suporte)
        malha.setScale(escala)
        malha.setPos(-(lo.x + hi.x) * escala / 2,
                     -(lo.y + hi.y) * escala / 2, -lo.z * escala)
        self._sombra(x, y, raio)
        if tipo == "edificio":
            # O lote não toca as ruas: nenhum caminho decorativo vira conexão.
            metade_x = (hi.x - lo.x) * escala / 2 + .14
            metade_y = (hi.y - lo.y) * escala / 2 + .14
            superficie(suporte, "lote-calcado", [(-metade_x, -metade_y, -.025),
                       (metade_x, -metade_y, -.025), (metade_x, metade_y, -.025),
                       (-metade_x, metade_y, -.025)], (.79, .81, .71, 1))
        self.decoracoes.append(Decoracao(tipo, kit, nome, x, y, raio, (hi.z - lo.z) * escala))
        return True

    def _decorar(self):
        # Primeiro garantir um endereço construído perto de cada ponto, recuado.
        for indice, (x, y, _) in enumerate(self.posicoes.values()):
            kit = "cidade" if indice % 3 == 0 else "suburbio"
            nome = f"building-{chr(97 + indice % 8)}" if kit == "cidade" else f"building-type-{chr(97 + indice % 10)}"
            encontrou = False
            for distancia in (3.8, 5.2, 6.6):
                for passo in range(16):
                    # Começar atrás do nó no enquadramento isométrico padrão.
                    angulo = 3 * pi / 4 + passo * 2 * pi / 16
                    if self._adicionar_decoracao("edificio", kit, nome,
                            x + cos(angulo) * distancia, y + sin(angulo) * distancia,
                            2.3 if kit == "suburbio" else 2., orientacao=90 * (indice % 4)):
                        encontrou = True
                        break
                if encontrou:
                    break
        alvo_edificios = 28 + len(self.posicoes)
        for tentativa in range(1600):
            if sum(d.tipo == "edificio" for d in self.decoracoes) >= alvo_edificios:
                break
            kit = "cidade" if tentativa % 4 == 0 else "suburbio"
            nome = f"building-{chr(97 + tentativa % 8)}" if kit == "cidade" else f"building-type-{chr(97 + tentativa % 12)}"
            x = self._rng.uniform(-self.meia_largura + 3, self.meia_largura - 3)
            y = self._rng.uniform(-self.meia_altura + 3, self.meia_altura - 3)
            self._adicionar_decoracao("edificio", kit, nome, x, y,
                                     self._rng.uniform(1.8, 2.7), 90 * (tentativa % 4))
        alvo_arvores = 90 + 2 * len(self.posicoes)
        for tentativa in range(3200):
            if sum(d.tipo == "arvore" for d in self.decoracoes) >= alvo_arvores:
                break
            self._adicionar_decoracao("arvore", "suburbio",
                                     "tree-large" if tentativa % 3 else "tree-small",
                                     self._rng.uniform(-self.meia_largura + 1.5, self.meia_largura - 1.5),
                                     self._rng.uniform(-self.meia_altura + 1.5, self.meia_altura - 1.5),
                                     self._rng.uniform(1.1, 2.1), self._rng.uniform(0, 360))
        self.decoracoes = tuple(self.decoracoes)

    def mostrar_rota(self, caminho, cor=AMARELO):
        caminho = tuple(caminho)
        if not set(caminho) <= set(self.posicoes):
            raise ValueError("A rota contém um nó inexistente.")
        try:
            ruas = [self.ruas[a, b] for a, b in zip(caminho, caminho[1:])]
        except KeyError as erro:
            raise ValueError("A rota contém uma rua inexistente.") from erro
        # Validar primeiro preserva a rota atual se o novo percurso for inválido.
        self.limpar_rota()
        for pontos in ruas:
            for a, b in zip(pontos, pontos[1:]):
                _faixa(self.rota, "contorno-rota", a, b, .34, (.60, .40, .08, 1), .031)
                _faixa(self.rota, "rota-amarela", a, b, .24, cor, .035)
            for x, y, z in pontos:
                _disco(self.rota, "junta-rota", x, y, z + .036, .12, cor, lados=12)
        self.rota.flattenStrong()

    def limpar_rota(self):
        for filho in self.rota.getChildren():
            filho.removeNode()

    def destruir(self):
        self.raiz.removeNode()
        self.rota.removeNode()
