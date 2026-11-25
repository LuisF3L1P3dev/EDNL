"""Cena urbana estática sobre a geometria do grafo, com assets Kenney locais.

As ruas são exclusivamente as arestas fornecidas. A decoração nunca participa
da adjacência e tem seu espaço reservado fora de todas as polilinhas de ruas.
O veículo, as luzes e as etiquetas projetadas pertencem à aplicação.
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from functools import lru_cache
from math import atan2, cos, degrees, dist, hypot, pi, sin
from random import Random

from panda3d.core import (Geom, GeomNode, GeomTriangles, GeomVertexData, TextNode,
                         GeomVertexFormat, GeomVertexWriter,
                         TransparencyAttrib, Vec3)

from geometria3d import (COTA_LOTE, NIVEL_GRAMA, comprimento_no_ritmo_da_via,
                         criar_mapa_visual, fracao_com_rotatoria, medir_rua)
from roteamento3d import LARGURA_VIA
from cidades3d import COTA_PRACA, planejar_cidades


LARGURA_RUA = LARGURA_VIA
LARGURA_ACESSO = .52
AMARELO = (1., .76, .13, 1.)
LARANJA = (1., .48, .14, 1.)
ESCALA_VERTICAL_RUA = .55
COR_GRAMA = (.60, .79, .52, 1)
COR_CALCADA = (.88, .84, .73, 1)
COR_CONTORNO_PONTE = (.56, .60, .65, 1)
COR_GUARDA_CORPO = (.94, .74, .52, 1)
TINTA_RUA = (1.08, 1.08, 1.04, 1)
CORES_CIDADES = {
    'residencial': ((.71, .83, .60, 1), (.27, .58, .39, 1)),
    'misto': ((.80, .83, .66, 1), (.22, .63, .66, 1)),
    'comercial': ((.84, .82, .70, 1), (.72, .46, .28, 1)),
}


def superficie(parent, nome, pontos, cor, *, material=None):
    """Triangule uma superfície convexa, inclusive as laterais da ilha."""
    pontos = tuple(pontos)
    if len(pontos) < 3:
        raise ValueError("Uma superfície precisa de pelo menos três vértices.")
    normal = (Vec3(*pontos[1]) - Vec3(*pontos[0])).cross(
        Vec3(*pontos[2]) - Vec3(*pontos[0]))
    normal.normalize()
    formato = GeomVertexFormat.getV3n3t2() if material else GeomVertexFormat.getV3n3()
    dados = GeomVertexData(nome, formato, Geom.UH_static)
    v, n = GeomVertexWriter(dados, "vertex"), GeomVertexWriter(dados, "normal")
    uv = GeomVertexWriter(dados, "texcoord") if material else None
    for ponto in pontos:
        v.addData3(*ponto)
        n.addData3(normal)
        if uv:
            uv.addData2(*material[1])
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
    if material:
        malha.setTexture(material[0], 1)
    return malha


def _disco(parent, nome, x, y, z, raio, cor, *, proporcao=1., lados=20):
    return superficie(parent, nome, _pontos_disco(x, y, z, raio, proporcao, lados), cor)


def _pontos_disco(x, y, z, raio, proporcao, lados):
    return tuple(
        (x + cos(i * 2 * pi / lados) * raio,
         y + sin(i * 2 * pi / lados) * raio * proporcao, z)
        for i in range(lados)
    )


def _faixa(parent, nome, a, b, largura, cor, elevacao=0.):
    pontos = _pontos_faixa(a, b, largura, elevacao)
    if pontos:
        return superficie(parent, nome, pontos, cor)


def _pontos_faixa(a, b, largura, elevacao):
    dx, dy = b[0] - a[0], b[1] - a[1]
    comprimento = hypot(dx, dy)
    if comprimento <= 1e-8:
        return ()
    px, py = -dy / comprimento * largura / 2, dx / comprimento * largura / 2
    return (
        (a[0] + px, a[1] + py, a[2] + elevacao),
        (a[0] - px, a[1] - py, a[2] + elevacao),
        (b[0] - px, b[1] - py, b[2] + elevacao),
        (b[0] + px, b[1] + py, b[2] + elevacao),
    )


@lru_cache(maxsize=128)
def _geometria_destaque(pontos_rua, cor):
    """Compartilha as faixas e juntas de uma rua entre prévia e viagem."""
    rua = medir_rua(pontos_rua)
    poligonos = []
    for a, b in rua.segmentos:
        contorno = _pontos_faixa(a, b, .34, .031)
        if contorno:
            poligonos.append((contorno, (.60, .40, .08, 1)))
            poligonos.append((_pontos_faixa(a, b, .24, .035), cor))
    for x, y, z in rua.pontos:
        poligonos.append((_pontos_disco(x, y, z + .036, .12, 1., 12), cor))

    dados = GeomVertexData("rota", GeomVertexFormat.getV3c4(), Geom.UH_static)
    quantidade = sum(len(pontos) for pontos, _ in poligonos)
    dados.setNumRows(quantidade)
    vertices = GeomVertexWriter(dados, "vertex")
    cores = GeomVertexWriter(dados, "color")
    triangulos = GeomTriangles(Geom.UH_static)
    if quantidade > 65535:
        triangulos.setIndexType(Geom.NT_uint32)
    triangulos.reserveNumVertices(3 * (quantidade - 2 * len(poligonos)))
    indice = 0
    for pontos, tinta in poligonos:
        for ponto in pontos:
            vertices.setData3(*ponto)
            cores.setData4(*tinta)
        for i in range(1, len(pontos) - 1):
            triangulos.addVertices(indice, indice + i, indice + i + 1)
        indice += len(pontos)
    geometria = Geom(dados)
    geometria.addPrimitive(triangulos)
    return geometria


def _projetar_no_segmento(x, y, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    comprimento2 = dx * dx + dy * dy
    t = max(0., min(1., ((x - a[0]) * dx + (y - a[1]) * dy) / comprimento2)) if comprimento2 else 0.
    return a[0] + t * dx, a[1] + t * dy, a[2] + t * (b[2] - a[2])


def _distancia_segmento(x, y, a, b):
    px, py, _ = _projetar_no_segmento(x, y, a, b)
    return hypot(x - px, y - py)


def _unir_intervalos(intervalos):
    unidos = []
    for inicio, fim in sorted(intervalos):
        if unidos and inicio <= unidos[-1][1]:
            anterior, limite = unidos[-1]
            unidos[-1] = (anterior, max(limite, fim))
        else:
            unidos.append((inicio, fim))
    return unidos


def _ponto_eixo(eixo, posicao, lateral, altura):
    return (posicao, lateral, altura) if eixo == 0 else (lateral, posicao, altura)


def _pavimento(segmentos, ancoras):
    """Trechos sem sobreposição e peças que completam suas junções em XY."""
    linhas = defaultdict(list)
    rampas = []
    for a, b in segmentos:
        a, b = (tuple(round(v, 9) for v in p) for p in (a, b))
        eixo = int(a[0] == b[0])
        if a[2] == b[2]:
            linhas[eixo, a[1 - eixo], a[2]].append(tuple(sorted((a[eixo], b[eixo]))))
        else:
            rampas.append((a, b))
    linhas = {chave: _unir_intervalos(intervalos) for chave, intervalos in linhas.items()}

    direcoes = {p: set() for p in ancoras}
    horizontais = [(y, z, intervalos) for (e, y, z), intervalos in linhas.items() if e == 0]
    verticais = [(x, z, intervalos) for (e, x, z), intervalos in linhas.items() if e == 1]
    for y, z, horizontais_y in horizontais:
        for x, altura, verticais_x in verticais:
            if (z == altura and any(a <= x <= b for a, b in horizontais_y)
                    and any(a <= y <= b for a, b in verticais_x)):
                direcoes.setdefault((x, y, z), set())

    metade = LARGURA_RUA / 2
    limites = {}
    for p in direcoes:
        x, y, _ = p
        caixa = [x - metade, y - metade, x + metade, y + metade]
        # Uma rampa pode começar dentro da peça de um cotovelo. A borda
        # deve parar na costura da rampa, sem uma segunda superfície abaixo.
        for a, b in rampas:
            eixo = int(a[0] == b[0])
            for entrada, saida in ((a, b), (b, a)):
                if entrada[2] != p[2] or entrada[1 - eixo] != p[1 - eixo]:
                    continue
                inicio = entrada[eixo]
                if saida[eixo] > inicio >= p[eixo]:
                    caixa[eixo + 2] = min(caixa[eixo + 2], inicio)
                elif saida[eixo] < inicio <= p[eixo]:
                    caixa[eixo] = max(caixa[eixo], inicio)
        limites[p] = tuple(caixa)

    retas = list(rampas)
    for (eixo, lateral, altura), intervalos in linhas.items():
        centros = sorted(p[eixo] for p in direcoes if p[1 - eixo] == lateral and p[2] == altura)
        for inicio, fim in intervalos:
            cursor = inicio
            for centro in centros:
                if not inicio <= centro <= fim:
                    continue
                p = _ponto_eixo(eixo, centro, lateral, altura)
                if inicio < centro:
                    direcoes[p].add((-1, 0) if eixo == 0 else (0, -1))
                if centro < fim:
                    direcoes[p].add((1, 0) if eixo == 0 else (0, 1))
                esquerda, direita = limites[p][eixo], limites[p][eixo + 2]
                if esquerda > cursor:
                    retas.append((_ponto_eixo(eixo, cursor, lateral, altura),
                                  _ponto_eixo(eixo, esquerda, lateral, altura)))
                cursor = max(cursor, direita)
            if fim > cursor:
                retas.append((_ponto_eixo(eixo, cursor, lateral, altura),
                              _ponto_eixo(eixo, fim, lateral, altura)))
    return tuple(retas), tuple((p, direcoes[p], limites[p]) for p in sorted(direcoes))


@dataclass(frozen=True)
class Decoracao:
    tipo: str
    kit: str
    modelo: str
    x: float
    y: float
    raio: float
    altura: float
    no: int | None = None
    semieixos: tuple[float, float] | None = None


class Cena3D:
    def __init__(self, base, grafo, biblioteca):
        self.grafo = grafo
        self.biblioteca = biblioteca
        self.mapa_visual = criar_mapa_visual(grafo)
        self.posicoes = self.mapa_visual.chegadas
        self.ruas = self.mapa_visual.trajetos
        self.rotatorias = self.mapa_visual.rotatorias
        self.raiz = base.render.attachNewNode(f"cidade-{grafo.id}")
        self.rota = base.render.attachNewNode("rota-calculada")
        self.rota.setLightOff()
        self.decoracoes = []
        self.construcoes_no = {}
        self.cidades = {}
        self._espacos_urbanos = ()
        self._acessos = tuple(self._acesso_construcao(no) for no in self.mapa_visual.nos)
        self.modelos_usados = set()
        self._limites_modelos = {}
        self.trechos_rua = 0
        self.pontes = len(self.mapa_visual.pontes)
        self._apoios_pontes = ()
        self._agua = ()
        self._trecho_destacado = None
        self.sinalizacao = []
        self._segmentos = tuple(
            trecho for aresta in grafo.arestas
            for trecho in medir_rua(self.mapa_visual.eixos_pavimento[aresta.origem, aresta.destino]).segmentos
        )
        self._rng = Random(410 + len(grafo.ids))
        x0, y0, x1, y1 = self.mapa_visual.limites_xy
        self.meia_largura = max(26., abs(x0) + 2., abs(x1) + 2.)
        self.meia_altura = max(23., abs(y0) + 2., abs(y1) + 2.)
        try:
            self._terreno()
            self._criar_agua_local()
            if grafo.id == 'mapa_18' and len(grafo.ids) == 18:
                self.cidades = planejar_cidades(
                    self.mapa_visual, self.meia_largura, self.meia_altura, self._agua)
                self._acessos = ()
                self._espacos_urbanos = tuple(limites for c in self.cidades.values()
                                              for limites in (c.limites_xy, c.limites_acesso))
            self._construir_ruas()
            self._decorar()
            self.raiz.flattenStrong()
        except Exception:
            self.destruir()
            raise

    @property
    def marcadores_no(self):
        return self.posicoes

    def fracao_percurso(self, par, fracao):
        return fracao_com_rotatoria(self.ruas[par], self.mapa_visual.zonas_rotatorias.get(par), fracao)

    def duracoes_percurso(self, caminho):
        if not self.rotatorias or len(caminho) < 2:
            return None
        comprimentos = tuple(
            comprimento_no_ritmo_da_via(self.ruas[par], self.mapa_visual.zonas_rotatorias.get(par))
            for par in zip(caminho, caminho[1:])
        )
        # Limita o ritmo nas retas a 18 unidades/s em 1×. O perfil do anel
        # usa o mesmo comprimento ponderado para reduzir o ritmo local.
        ritmo = min(18., sum(comprimentos) / 30.)
        return tuple(comprimento / ritmo for comprimento in comprimentos)

    def pontos_enquadramento(self):
        """Envelope completo que a câmera ortográfica precisa preservar.

        Os nós matemáticos sozinhos não representam o tamanho da maquete: as
        ruas podem desviar e os lotes e a decoração ocupam área adicional.
        Os cantos da ilha ainda mantêm a borda
        visível, sem depender da ordem em que os modelos foram instanciados.
        """
        w, h = self.meia_largura, self.meia_altura
        pontos = [(x, y, z)
                  for x in (-w, w) for y in (-h, h)
                  for z in (NIVEL_GRAMA - .8, NIVEL_GRAMA)]
        for rua in self.ruas.values():
            pontos.extend(rua)
        for decoracao in self.decoracoes:
            # raio já é circunscrito: inclui o lote quadrado e toda a malha.
            raio = decoracao.raio
            for x in (decoracao.x - raio, decoracao.x + raio):
                for y in (decoracao.y - raio, decoracao.y + raio):
                    pontos.append((x, y, NIVEL_GRAMA))
                    pontos.append((x, y, NIVEL_GRAMA + decoracao.altura))
        for no in self.mapa_visual.nos:
            pontos.extend((self.posicoes[no.id], no.entrada))
        return tuple(pontos)

    def _modelo(self, kit, nome, **opcoes):
        self.modelos_usados.add((kit, nome))
        return self.biblioteca.modelo(kit, nome, **opcoes)

    def _terreno(self):
        w, h = self.meia_largura, self.meia_altura
        corte = 1.8
        cantos = [(-w + corte, -h), (w - corte, -h), (w, -h + corte), (w, h - corte),
                  (w - corte, h), (-w + corte, h), (-w, h - corte), (-w, -h + corte)]
        superficie(self.raiz, "gramado", [(*p, NIVEL_GRAMA) for p in cantos], COR_GRAMA)
        for a, b in zip(cantos, cantos[1:] + cantos[:1]):
            meio = NIVEL_GRAMA - .15
            superficie(self.raiz, "terra-da-ilha", [(*a, meio), (*a, -1.15),
                       (*b, -1.15), (*b, meio)], (.65, .61, .49, 1))
            superficie(self.raiz, "borda-da-ilha", [(*a, NIVEL_GRAMA), (*a, meio),
                       (*b, meio), (*b, NIVEL_GRAMA)], (.49, .69, .46, 1))
        self._sombras = self.raiz.attachNewNode("sombras-de-contato")
        self._sombras.setTransparency(TransparencyAttrib.M_alpha)
        self._sombras.setDepthWrite(False)
        self._sombras.setLightOff()
        # Variações discretas do gramado dão escala sem desenhar novas ruas.
        for _ in range(24):
            x = self._rng.uniform(-w + 3, w - 3)
            y = self._rng.uniform(-h + 3, h - 3)
            _disco(self.raiz, "canteiro-gramado", x, y, NIVEL_GRAMA + .002,
                   self._rng.uniform(1.4, 3.1), (.58, .77, .50, 1),
                   proporcao=self._rng.uniform(.6, 1.2))

    def _criar_agua_local(self):
        """Canal curto sob uma ponte, fora das ruas no nivel do solo."""
        baixas = [(a, b) for a, b in self._segmentos if max(a[2], b[2]) < .5]
        for ponte in self.mapa_visual.pontes:
            dx, dy = ponte.fim[0] - ponte.inicio[0], ponte.fim[1] - ponte.inicio[1]
            comprimento = hypot(dx, dy)
            ux, uy = dx / comprimento, dy / comprimento
            for lado in (-1, 1):
                cx, cy = ponte.centro[0] + lado * 1.5 * ux, ponte.centro[1] + lado * 1.5 * uy
                # O canal corre perpendicular ao tabuleiro; a rua inferior
                # permanece seca ao lado, sem inventar conexoes no grafo.
                hx, hy = (.30, 1.4) if abs(ux) > .5 else (1.4, .30)
                x0, x1, y0, y1 = cx - hx, cx + hx, cy - hy, cy + hy
                amostras = [(x0 + (x1-x0)*i/6, y0 + (y1-y0)*j/12)
                            for i in range(7) for j in range(13)]
                if any(_distancia_segmento(x, y, a, b) < LARGURA_RUA/2 + .10
                       for x, y in amostras for a, b in baixas):
                    continue
                if any(not (x1 < n.construcao.limites_xy[0] or x0 > n.construcao.limites_xy[2]
                            or y1 < n.construcao.limites_xy[1] or y0 > n.construcao.limites_xy[3])
                       for n in self.mapa_visual.nos):
                    continue
                superficie(self.raiz, 'agua-local', [(x0, y0, NIVEL_GRAMA + .006),
                           (x1, y0, NIVEL_GRAMA + .006), (x1, y1, NIVEL_GRAMA + .006),
                           (x0, y1, NIVEL_GRAMA + .006)], (.40, .75, .81, 1))
                self._agua = ((x0, y0, x1, y1),)
                return

    def _construir_ruas(self):
        ancoras_retas = (p for n, p in self.posicoes.items() if n not in {r.no for r in self.rotatorias})
        trechos, juncoes = _pavimento(self._segmentos, ancoras_retas)
        self._trechos_pavimento = trechos
        self._juncoes_pavimento = juncoes
        reta = self._modelo("rua", "road-straight")
        textura = reta.find("**/+GeomNode").getTexture()
        limites_reta = reta.getTightBounds()
        self._pistas_pontes = []
        for a, b in trechos:
            elevado = a[2] != b[2] or a[2] > .8
            if elevado:
                self._pista_ponte(a, b, textura)
            else:
                self._encaixar_rua(a, b, reta, limites_reta, .01)
        for ponto, bracos, caixa in juncoes:
            self._piso_juncao(ponto, bracos, caixa, textura)
        for rotatoria in self.rotatorias:
            self._construir_rotatoria(rotatoria, textura)
        for no, (x, y, z) in self.posicoes.items():
            _disco(self.raiz, f"aro-ponto-{no}", x, y, z + .014, .40, (.91, .95, .96, 1))
            cidade = self.cidades.get(no)
            cor = CORES_CIDADES[cidade.perfil][1] if cidade else (.25, .60, .86, 1)
            _disco(self.raiz, f"ponto-{no}", x, y, z + .015, .29, cor)
        if self.pontes:
            self._construir_apoios()

    def _construir_rotatoria(self, rotatoria, textura):
        x, y, z = rotatoria.centro
        meio_fio = self._modelo('rua', 'road-roundabout', raio_maximo=.351).copyTo(self.raiz)
        escala = rotatoria.raio_interno / .35
        meio_fio.setScale(escala, escala, 3.)
        meio_fio.setPos(x, y, z - .03)
        _disco(self.raiz, 'grama-da-ilha', x, y, z + .02, .25 * escala, COR_GRAMA, lados=48)
        arvore = self._modelo('suburbio', 'tree-small').copyTo(self.raiz)
        altura = arvore.getTightBounds()[1].z
        arvore.setScale(.82 / altura)
        arvore.setPos(x - .26, y + .22, z + .02)
        arbusto = self._modelo('suburbio', 'planter').copyTo(self.raiz)
        lo, hi = arbusto.getTightBounds()
        arbusto.setScale(.45 / max(hi.x - lo.x, hi.y - lo.y))
        arbusto.setPos(x + .29, y - .21, z + .02)
        perfis = tuple(rotatoria.perfis_pavimento())
        for (a, b), (c, d) in zip(perfis, perfis[1:]):
            superficie(self.raiz, 'piso-rotatoria', [a, b, d, c], TINTA_RUA,
                       material=(textura, (.03125, .125)))
        self.trechos_rua += len(perfis) - 1
        for braco in rotatoria.bracos:
            for lateral in (.14, .32):
                superficie(self.raiz, 'marca-preferencia',
                           [braco.deslocar(-.25, lateral, .008),
                            braco.deslocar(-.085, lateral + .065, .008),
                            braco.deslocar(-.085, lateral - .065, .008)],
                           (.98, .95, .86, 1))

    def _pista_ponte(self, a, b, textura):
        """Pista e laterais em faixas contiguas, seguindo a polilinha real."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        comprimento = hypot(dx, dy)
        if not comprimento:
            return
        nx, ny = -dy / comprimento, dx / comprimento
        metade = LARGURA_RUA / 2
        secoes = (-metade, -.40, -.38, .38, .40, metade)
        cores = (COR_CALCADA, (.96, .93, .84, 1), TINTA_RUA,
                 (.96, .93, .84, 1), COR_CALCADA)
        for i, (esquerda, direita) in enumerate(zip(secoes, secoes[1:])):
            pontos = [(a[0] + nx * direita, a[1] + ny * direita, a[2]),
                      (a[0] + nx * esquerda, a[1] + ny * esquerda, a[2]),
                      (b[0] + nx * esquerda, b[1] + ny * esquerda, b[2]),
                      (b[0] + nx * direita, b[1] + ny * direita, b[2])]
            superficie(self.raiz, 'pista-ponte', pontos, cores[i],
                       material=(textura, (.03125, .125)) if i == 2 else None)
        espessura = (.06 if a[2] == b[2] else .01) * ESCALA_VERTICAL_RUA
        for lado in (-1, 1):
            x1, y1 = a[0] + nx * lado * metade, a[1] + ny * lado * metade
            x2, y2 = b[0] + nx * lado * metade, b[1] + ny * lado * metade
            superficie(self.raiz, 'borda-tabuleiro', [(x1, y1, a[2] - espessura),
                       (x2, y2, b[2] - espessura), (x2, y2, b[2]),
                       (x1, y1, a[2])], COR_CONTORNO_PONTE)
        superficie(self.raiz, 'fundo-tabuleiro',
                   [(a[0] - nx*metade, a[1] - ny*metade, a[2] - espessura),
                    (b[0] - nx*metade, b[1] - ny*metade, b[2] - espessura),
                    (b[0] + nx*metade, b[1] + ny*metade, b[2] - espessura),
                    (a[0] + nx*metade, a[1] + ny*metade, a[2] - espessura)], COR_CONTORNO_PONTE)
        # Guarda-corpos fora da faixa de rodagem, sem ergue-los no solo.
        if max(a[2], b[2]) > .8:
            for lado in (-1, 1):
                offset = lado * metade
                x1, y1 = a[0] + nx * offset, a[1] + ny * offset
                x2, y2 = b[0] + nx * offset, b[1] + ny * offset
                superficie(self.raiz, 'guarda-corpo', [(x1, y1, a[2]), (x2, y2, b[2]),
                           (x2, y2, b[2] + .19), (x1, y1, a[2] + .19)], COR_GUARDA_CORPO)
        self._pistas_pontes.append((a, b))
        self.trechos_rua += 1

    def _encaixar_rua(self, a, b, modelo, limites, cota):
        delta = Vec3(*b) - Vec3(*a)
        comprimento = delta.length()
        partes = max(1, round(comprimento / 1.6))
        lo, hi = limites
        sx = comprimento / partes / (hi.x - lo.x)
        sy = LARGURA_RUA / (hi.y - lo.y)
        for i in range(partes):
            suporte = self.raiz.attachNewNode("trecho-rua")
            suporte.setPos(Vec3(*a) + delta * ((i + .5) / partes))
            suporte.setHpr(-degrees(atan2(delta.x, delta.y)),
                           degrees(atan2(delta.z, hypot(delta.x, delta.y))), 0)
            malha = modelo.copyTo(suporte)
            malha.setColorScale(*TINTA_RUA)
            malha.setH(90)
            malha.setScale(sx, sy, ESCALA_VERTICAL_RUA)
            malha.setPos((lo.y + hi.y) * sy / 2, -(lo.x + hi.x) * sx / 2,
                         -cota * ESCALA_VERTICAL_RUA)
        self.trechos_rua += partes

    def _piso_juncao(self, ponto, bracos, caixa, textura):
        x, y, z = ponto
        metade = LARGURA_RUA / 2
        x0, y0, x1, y1 = caixa
        if len(bracos) == 4 and caixa == (x - metade, y - metade, x + metade, y + metade):
            cruzamento = self._modelo("rua", "road-crossroad").copyTo(self.raiz)
            cruzamento.setScale(LARGURA_RUA, LARGURA_RUA, ESCALA_VERTICAL_RUA)
            cruzamento.setPos(x, y, z - .01 * ESCALA_VERTICAL_RUA)
            cruzamento.setColorScale(*TINTA_RUA)
            return
        secoes = (-metade, -.8 * metade, .8 * metade, metade)
        for i, (a, b) in enumerate(zip(secoes, secoes[1:]), -1):
            esquerda, direita = max(x0, x + a), min(x1, x + b)
            for j, (c, d) in enumerate(zip(secoes, secoes[1:]), -1):
                baixo, cima = max(y0, y + c), min(y1, y + d)
                if direita <= esquerda or cima <= baixo:
                    continue
                asfalto = (i, j) == (0, 0) or (i, j) in bracos
                altura = z if asfalto else z + .01 * ESCALA_VERTICAL_RUA
                uv = (.03125, .125) if asfalto else (.46875, .475)
                superficie(self.raiz, "piso-juncao",
                           [(esquerda, baixo, altura), (direita, baixo, altura),
                            (direita, cima, altura), (esquerda, cima, altura)],
                           TINTA_RUA, material=(textura, uv))

    def _construir_apoios(self):
        modelo = self._modelo("rua", "bridge-pillar-wide")
        lo, hi = modelo.getTightBounds()
        largura = .65 * LARGURA_RUA
        escala = largura / max(hi.x - lo.x, hi.y - lo.y)
        raio = hypot(hi.x - lo.x, hi.y - lo.y) * escala / 2
        base = NIVEL_GRAMA + .02
        apoios = []
        for ponte in self.mapa_visual.pontes:
            trechos = medir_rua(self.ruas[ponte.aresta]).segmentos
            obstaculos = [t for t in self._segmentos if t not in trechos]
            x0, y0, _ = ponte.centro
            dx, dy = (ponte.fim[i] - ponte.inicio[i] for i in (0, 1))
            comprimento = hypot(dx, dy)
            for lado in (-1, 1):
                for recuo in (1.55, 2.25):
                    x = x0 + lado * recuo * dx / comprimento
                    y = y0 + lado * recuo * dy / comprimento
                    if any(_distancia_segmento(x, y, a, b) < LARGURA_RUA / 2 + raio
                           for a, b in obstaculos):
                        continue
                    if any(hypot(x - px, y - py) < 2 * raio for _, px, py, _ in apoios):
                        break
                    for a, b in trechos:
                        px, py, z = _projetar_no_segmento(x, y, a, b)
                        if hypot(x - px, y - py) > 1e-8:
                            continue
                        declive = abs(b[2] - a[2]) / hypot(b[0] - a[0], b[1] - a[1])
                        espessura = (.06 if declive == 0 else .01) * ESCALA_VERTICAL_RUA
                        topo = z - espessura - declive * largura / 2
                        altura = (topo - base) / (hi.z - lo.z)
                        apoio = modelo.copyTo(self.raiz)
                        apoio.setScale(escala, escala, altura)
                        apoio.setPos(x, y, base - lo.z * altura)
                        apoios.append((ponte.aresta, x, y, raio))
                        break
                    else:
                        continue
                    break
        self._apoios_pontes = tuple(apoios)

    def distancia_rua(self, x, y):
        """Distância XY à rua mais próxima, útil para verificar lotes."""
        retas = min((_distancia_segmento(x, y, a, b) for a, b in self._segmentos), default=float("inf"))
        anel = min((abs(hypot(x - r.centro[0], y - r.centro[1]) - r.raio_pista)
                    for r in self.rotatorias), default=float("inf"))
        return min(retas, anel)

    def _livre(self, x, y, raio, *, afastamento_no=1.2, margem_rua=.4):
        if abs(x) + raio > self.meia_largura - 1 or abs(y) + raio > self.meia_altura - 1:
            return False
        for x0, y0, x1, y1 in self._agua + self._espacos_urbanos:
            if hypot(x - max(x0, min(x1, x)), y - max(y0, min(y1, y))) < raio + .1:
                return False
        if any(hypot(x - r.centro[0], y - r.centro[1]) < r.raio_externo + raio + .32
               for r in self.rotatorias):
            return False
        if self.distancia_rua(x, y) < raio + LARGURA_RUA / 2 + margem_rua:
            return False
        if any(hypot(x - p[0], y - p[1]) < raio + afastamento_no for p in self.posicoes.values()):
            return False
        if any(_distancia_segmento(x, y, a, b) < raio + LARGURA_ACESSO / 2
               for a, b in self._acessos):
            return False
        return not any(hypot(x - d.x, y - d.y) < raio + d.raio + .3 for d in self.decoracoes)

    def _sombra(self, x, y, raio, *, piso=NIVEL_GRAMA):
        for i, (fator, alfa) in enumerate(((1.30, .026), (1.17, .05), (1.04, .085), (.87, .10))):
            _disco(self._sombras, "sombra-suave", x + .14, y + .12,
                   piso + .005 + i * .001, raio * fator,
                   (.22, .37, .31, alfa), proporcao=.78, lados=24)

    def _dimensoes(self, kit, nome, tamanho, altura=False):
        modelo = self._modelo(kit, nome)
        chave = kit, nome
        if chave not in self._limites_modelos:
            self._limites_modelos[chave] = modelo.getTightBounds()
        lo, hi = self._limites_modelos[chave]
        escala = tamanho / ((hi.z - lo.z) if altura else max(hi.x - lo.x, hi.y - lo.y))
        raio = hypot(hi.x - lo.x, hi.y - lo.y) * escala / 2
        return modelo, lo, hi, escala, raio

    def _adicionar_decoracao(self, tipo, kit, nome, x, y, tamanho, orientacao=0., variante=None):
        modelo, lo, hi, escala, raio = self._dimensoes(kit, nome, tamanho, tipo in ("arvore", "poste"))
        if tipo == 'edificio':
            escala = min(escala, 2.8 / (hi.z - lo.z))
            metade_x = (hi.x - lo.x) * escala / 2
            metade_y = (hi.y - lo.y) * escala / 2
            raio = hypot(metade_x + .12, metade_y + .24)
        else:
            raio += .05
        if not self._livre(x, y, raio, afastamento_no=2. if tipo == "edificio" else 1.5,
                           margem_rua=.15 if tipo == 'poste' else .4):
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
            if variante:
                malha.setTexture(self.biblioteca.paleta(kit, variante), 2)
            malha.setColorScale(1.14, 1.12, 1.09, 1)
            if kit == 'suburbio':
                cor_lote = (.70, .80, .58, 1)
                _faixa(suporte, 'passeio-do-lote', (0., metade_y * .5, -.020),
                       (0., metade_y + .24, -.020), .36, COR_CALCADA)
            else:
                cor_lote = COR_CALCADA
            x_lote, fundos, frente = metade_x + .12, -metade_y - .12, metade_y + .24
            superficie(suporte, "lote-calcado", [(-x_lote, fundos, -.025),
                       (x_lote, fundos, -.025), (x_lote, frente, -.025),
                       (-x_lote, frente, -.025)], cor_lote)
        self.decoracoes.append(Decoracao(tipo, kit, nome, x, y, raio, (hi.z - lo.z) * escala))
        return True

    def _adicionar_construcao_no(self, no_visual):
        """Instancia o endereço imutável associado a um nó do grafo."""
        endereco = no_visual.construcao
        modelo, lo, hi, escala, _ = self._dimensoes(endereco.kit, endereco.nome,
                                                     endereco.tamanho)
        x, y, _ = endereco.posicao
        altura = (hi.z - lo.z) * escala
        # O raio circunscreve o lote quadrado, impedindo decoração aleatória
        # de encostar em qualquer canto da construção persistente.
        metade = endereco.metade_lote
        raio = hypot(metade, metade)
        suporte = self.raiz.attachNewNode(f"construcao-no-{no_visual.id}")
        suporte.setPos(*endereco.posicao)
        suporte.setH(endereco.rotacao)
        malha = modelo.copyTo(suporte)
        malha.setScale(escala)
        if endereco.kit == 'suburbio':
            variante = ('a', 'b', None)[no_visual.id % 3]
            if variante:
                malha.setTexture(self.biblioteca.paleta(endereco.kit, variante), 2)
        malha.setColorScale(1.14, 1.12, 1.09, 1)
        malha.setPos(-(lo.x + hi.x) * escala / 2,
                     -(lo.y + hi.y) * escala / 2, -lo.z * escala)
        superficie(suporte, "lote-do-no", [(-metade, -metade, COTA_LOTE),
                   (metade, -metade, COTA_LOTE), (metade, metade, COTA_LOTE),
                   (-metade, metade, COTA_LOTE)], COR_CALCADA)
        ancora, entrada = self._acesso_construcao(no_visual)
        _faixa(self.raiz, f"acesso-no-{no_visual.id}", ancora, entrada,
               LARGURA_ACESSO, COR_CALCADA)
        _faixa(self.raiz, f"porta-no-{no_visual.id}", entrada, no_visual.porta,
               LARGURA_ACESSO, COR_CALCADA)
        self._sombra(x, y, raio)
        construcao = Decoracao("edificio", endereco.kit, endereco.nome, x, y,
                               raio, altura, no_visual.id)
        self.decoracoes.append(construcao)
        self.construcoes_no[no_visual.id] = construcao

    def _acesso_construcao(self, no):
        entrada = no.entrada
        r = next((r for r in self.rotatorias if r.no == no.id), None)
        if r is None:
            return no.acesso
        # O passeio termina na margem do anel voltada para a fachada.
        angulo = atan2(entrada[1] - r.centro[1], entrada[0] - r.centro[0])
        return r.ponto(angulo, r.limite_externo(angulo)), entrada

    def _construir_cidade(self, cidade):
        largura, comprimento = cidade.area
        faixa, destaque = CORES_CIDADES[cidade.perfil]
        x0, y0, x1, y1 = cidade.limites_xy
        z = COTA_PRACA
        superficie(self.raiz, "lote-urbano", [(x0, y0, z), (x1, y0, z),
                   (x1, y1, z), (x0, y1, z)], faixa)
        fundo = (*cidade.ponto_local(0, -comprimento / 2 + .20), z + .002)
        entrada = (*cidade.entrada[:2], z + .002)
        _faixa(self.raiz, "alameda-pedonal", fundo, entrada, .64, COR_CALCADA)
        praca = (*cidade.ponto_local(0, comprimento / 2 - .56), z + .003)
        _faixa(self.raiz, "praca-de-chegada", praca, (*entrada[:2], z + .003), 1.08, COR_CALCADA)
        # A faixa termina no meio-fio da rua incidente, fora da pista da van.
        _faixa(self.raiz, "acesso-pedonal", entrada, cidade.meio_fio, .52, COR_CALCADA)
        a = (*cidade.ponto_local(-.32, comprimento / 2 - .20), z + .004)
        b = (*cidade.ponto_local(.32, comprimento / 2 - .20), z + .004)
        _faixa(self.raiz, "entrada-urbana", a, b, .22, destaque)

        for grupo in cidade.grupos:
            for lote in grupo:
                self._instanciar_lote_urbano(cidade.no, lote, (largura - .74) / 4 + .02)

    def _instanciar_lote_urbano(self, no, lote, distancia_alameda):
        arvore = lote.tipo == 'arvore'
        modelo, lo, hi, escala, _ = self._dimensoes(lote.kit, lote.modelo, lote.tamanho, arvore)
        altura_maxima = 1.65 if lote.kit == 'cidade' else 1.35
        escala = min(escala, altura_maxima / (hi.z - lo.z))
        meia_x, meia_y = (hi.x - lo.x) * escala / 2, (hi.y - lo.y) * escala / 2
        x, y, z = lote.posicao
        suporte = self.raiz.attachNewNode(lote.tipo)
        suporte.setPos(x, y, z)
        suporte.setH(lote.rotacao)
        malha = modelo.copyTo(suporte)
        malha.setScale(escala)
        malha.setPos(-(lo.x + hi.x) * escala / 2,
                     -(lo.y + hi.y) * escala / 2, -lo.z * escala)
        if arvore:
            _disco(suporte, 'jardim-urbano', 0, 0, .002, .34, (.58, .73, .46, 1), lados=12)
        else:
            if lote.paleta:
                malha.setTexture(self.biblioteca.paleta(lote.kit, lote.paleta), 2)
            malha.setColorScale(1.14, 1.12, 1.09, 1)
            inicio = (0., meia_y * .75, .003)
            fim = (0., distancia_alameda, .003)
            _faixa(suporte, 'passeio-entrada', inicio, fim, .30, COR_CALCADA)
        raio = hypot(meia_x, meia_y)
        self._sombra(x, y, raio, piso=z)
        semieixos = (meia_y, meia_x) if lote.rotacao % 180 else (meia_x, meia_y)
        self.decoracoes.append(Decoracao(lote.tipo, lote.kit, lote.modelo, x, y, raio,
                                         (hi.z - lo.z) * escala + z - NIVEL_GRAMA, no, semieixos))

    def _vagas_quarteiroes(self):
        """Vagas dos dois lados das ruas, alternadas por area da cidade."""
        grupos = defaultdict(list)
        vistas = set()
        for a, b in self._segmentos:
            if a[2] != b[2] or a[2] > .5:
                continue
            dx, dy = b[0] - a[0], b[1] - a[1]
            comprimento = hypot(dx, dy)
            if comprimento < 1e-8:
                continue
            ux, uy = dx / comprimento, dy / comprimento
            nx, ny = -uy, ux
            partes = max(1, round(comprimento / 2.75))
            for i in range(partes):
                t = (i + .5) / partes
                for lado in (-1, 1):
                    for recuo in (2.35, 3.35, 4.45, 5.5):
                        x, y = a[0] + dx*t + lado*nx*recuo, a[1] + dy*t + lado*ny*recuo
                        chave = (round(x, 3), round(y, 3))
                        if chave in vistas:
                            continue
                        vistas.add(chave)
                        quadra = self._quadra(x, y)
                        orientacao = degrees(atan2(lado * nx, -lado * ny))
                        grupos[quadra].append((x, y, orientacao))
        filas = [deque(sorted(grupos[chave])) for chave in sorted(grupos)]
        while filas:
            restantes = []
            for fila in filas:
                yield fila.popleft()
                if fila:
                    restantes.append(fila)
            filas = restantes

    def _quadra(self, x, y):
        return (int((x + self.meia_largura) // 10), int((y + self.meia_altura) // 10))

    def _decorar(self):
        if self.cidades:
            for cidade in self.cidades.values():
                self._construir_cidade(cidade)
            self._sinalizar()
            vagas = tuple(self._vagas_quarteiroes())
            self._criar_mobiliario(vagas)
            self._plantar_vegetacao(vagas, alvo=45, limite_jardins=0)
            self.decoracoes = tuple(self.decoracoes)
            return
        # O endereço cadastrado é a cidade de cada nó, sempre na mesma posição.
        for no_visual in self.mapa_visual.nos:
            self._adicionar_construcao_no(no_visual)
        self._sinalizar()
        alvo_edificios = 52 if len(self.posicoes) <= 5 else 80
        residencias = tuple(f'building-type-{letra}' for letra in 'acdfghijklmnopqrstu')
        comercio = tuple(f'building-{letra}' for letra in 'bdefgh') + (
            'low-detail-building-wide-a', 'low-detail-building-wide-b',
            'low-detail-building-c', 'low-detail-building-j',
        )
        vagas = tuple(self._vagas_quarteiroes())
        indice = 0
        ocupacao = defaultdict(int)
        for x, y, orientacao in vagas:
            if indice >= alvo_edificios:
                break
            coluna, linha = quadra = self._quadra(x, y)
            vaga = ocupacao[quadra]
            # Vizinhanças comerciais alternam com fileiras residenciais.
            if (coluna + 2 * linha) % 4 == 0 or vaga % 5 == 3:
                kit, nome = 'cidade', comercio[(2 * coluna + linha + vaga) % len(comercio)]
                minimo, maximo = 1.75, 2.35
                variante = 'b' if vaga % 2 == 0 else None
            else:
                kit = 'suburbio'
                nome = residencias[(3 * coluna + 5 * linha + vaga) % len(residencias)]
                minimo, maximo = 1.45, 2.25
                variante = ('a', 'b', None)[(coluna + linha + vaga) % 3]
            if self._adicionar_decoracao("edificio", kit, nome, x, y,
                                        self._rng.uniform(minimo, maximo), orientacao, variante):
                ocupacao[quadra] += 1
                indice += 1
        self._criar_mobiliario(vagas)
        self._plantar_vegetacao(vagas)
        self.decoracoes = tuple(self.decoracoes)

    def _banco(self, x, y, orientacao):
        raio = .55
        if not self._livre(x, y, raio, afastamento_no=1.5):
            return False
        suporte = self.raiz.attachNewNode('banco')
        suporte.setPos(x, y, NIVEL_GRAMA + .055)
        suporte.setH(orientacao)
        def caixa(nome, x0, x1, y0, y1, z0, z1, cor):
            faces = [((x0,y0,z1), (x1,y0,z1), (x1,y1,z1), (x0,y1,z1)),
                     ((x0,y0,z0), (x1,y0,z0), (x1,y0,z1), (x0,y0,z1)),
                     ((x1,y0,z0), (x1,y1,z0), (x1,y1,z1), (x1,y0,z1)),
                     ((x1,y1,z0), (x0,y1,z0), (x0,y1,z1), (x1,y1,z1)),
                     ((x0,y1,z0), (x0,y0,z0), (x0,y0,z1), (x0,y1,z1))]
            for face in faces:
                superficie(suporte, nome, face, cor)
        madeira, metal = (.52, .34, .19, 1), (.30, .35, .35, 1)
        caixa('assento', -.42, .42, -.16, .16, .31, .39, madeira)
        caixa('encosto', -.42, .42, .10, .17, .39, .69, madeira)
        for x0 in (-.34, .24):
            caixa('apoio-banco', x0, x0+.10, -.12, .12, 0, .31, metal)
        self.decoracoes.append(Decoracao('banco', 'procedural', 'banco', x, y, raio, .69))
        return True

    def _placa(self, tipo, x, y, direcao, texto=''):
        raio = .41 if texto else .25
        if not self._livre(x, y, raio, afastamento_no=.85, margem_rua=.15):
            return False
        dx, dy = direcao
        orientacao = degrees(atan2(dx, -dy))
        modelo = 'road-sign-warning' if tipo == 'curva' else 'road-sign-empty'
        original, lo, hi, escala, _ = self._dimensoes('rua', modelo, .89, altura=True)
        suporte = self.raiz.attachNewNode(f'placa-{tipo}')
        suporte.setPos(x, y, NIVEL_GRAMA + .04)
        suporte.setH(orientacao)
        haste = original.copyTo(suporte)
        haste.setScale(escala)
        haste.setZ(-lo.z * escala)
        if tipo == 'preferencia':
            a, b, c = (-.24, -.045, 1.04), (.24, -.045, 1.04), (0., -.045, .64)
            superficie(suporte, 'acesso-preferencial', [a, b, c], (.88, .25, .31, 1))
            superficie(suporte, 'miolo-preferencial',
                       [(-.158, -.053, 1.), (.158, -.053, 1.), (0., -.053, .727)], (.99, .97, .91, 1))
        elif tipo == 'rotatoria':
            superficie(suporte, 'painel-da-rotatoria',
                       [(.245 * cos(i*pi/10), -.052, .90 + .245 * sin(i*pi/10))
                        for i in range(20)], (.18, .43, .72, 1))
            for i in range(3):
                angulo = i * 2 * pi / 3
                c, s = cos(angulo), sin(angulo)
                for peca in (((.09, -.075), (.135, -.075), (.135, .065), (.09, .065)),
                             ((.058, .045), (.166, .045), (.112, .135))):
                    superficie(suporte, 'seta-da-rotatoria',
                               [(x*c - z*s, -.062, .90 + x*s + z*c) for x, z in peca],
                               (.98, .97, .91, 1))
        elif texto:
            if tipo == 'velocidade':
                # A placa circular tem a face em -Y, na direção da aproximação.
                for raio_face, frente, cor in ((.25, -.047, (.84, .22, .27, 1)),
                                               (.192, -.056, (.99, .97, .91, 1))):
                    superficie(suporte, 'limite-de-velocidade',
                               [(raio_face * cos(i*pi/10), frente, .90 + raio_face*sin(i*pi/10))
                                for i in range(20)], cor)
                cor_texto = (.16, .20, .23, 1)
            else:
                cor = (.20, .53, .52, 1) if tipo == 'cidade' else (.20, .41, .66, 1)
                superficie(suporte, 'painel-direcional', [(-.40, -.05, .74), (.40, -.05, .74),
                           (.40, -.05, 1.06), (-.40, -.05, 1.06)], cor)
                cor_texto = (.99, .98, .91, 1)
            letreiro = TextNode(tipo)
            letreiro.setText(texto)
            letreiro.setAlign(TextNode.ACenter)
            letreiro.setTextColor(*cor_texto)
            legenda = suporte.attachNewNode(letreiro.generate())
            legenda.setPos(-.065 if tipo == 'direcao' else 0, -.066, .836)
            legenda.setScale(.18)
            legenda.setLightOff()
            if tipo == 'direcao':
                superficie(suporte, 'haste-da-seta', [(.20, -.066, .87), (.28, -.066, .87),
                           (.28, -.066, .93), (.20, -.066, .93)], cor_texto)
                superficie(suporte, 'ponta-da-seta',
                           [(.28, -.066, .83), (.37, -.066, .90), (.28, -.066, .97)], cor_texto)
        face = (abs(dy) * raio + abs(dx) * .08, abs(dx) * raio + abs(dy) * .08)
        self.decoracoes.append(Decoracao('placa', 'rua', modelo, x, y, raio, 1.18, semieixos=face))
        self.sinalizacao.append((tipo, (x, y), direcao))
        return True

    def _sinalizar(self):
        for r in self.rotatorias:
            limite_colocado = False
            painel_colocado = False
            acessos = sorted(r.bracos, key=lambda braco: sin(braco.angulo) - cos(braco.angulo))
            for braco in acessos:
                dx, dy = cos(braco.angulo), sin(braco.angulo)
                vagas = (braco.deslocar(recuo, lateral)
                         for lateral in (1.08, 1.32, 1.58, -1.08)
                         for recuo in (.55, .95, 1.35, 1.85, 2.35))
                for x, y, _ in vagas:
                    if self._placa('preferencia', x, y, (dx, dy)):
                        break
                if not painel_colocado:
                    for recuo, lateral in ((1.5, -1.08), (2.2, 1.08), (1.7, -1.55), (2.25, -1.32)):
                        x, y, _ = braco.deslocar(recuo, lateral)
                        if self._placa('rotatoria', x, y, (dx, dy)):
                            painel_colocado = True
                            break
                for recuo in (2.4, 2.9, 3.45):
                    x, y, _ = braco.deslocar(recuo, -1.12)
                    tipo = 'direcao' if limite_colocado else 'velocidade'
                    texto = '30' if tipo == 'velocidade' else f'VIA {braco.vizinho:02}'
                    if self._placa(tipo, x, y, (dx, dy), texto):
                        limite_colocado = True
                        break

        for cidade in self.cidades.values():
            x, y, _ = cidade.ponto_na_via
            dx, dy = cidade.frente
            for lado in (1, -1):
                if self._placa('cidade', x + 1.08*dx - lado*.98*dy, y + 1.08*dy + lado*.98*dx,
                               (-lado*dy, lado*dx), f'NO {cidade.no:02}'):
                    break

        curvas = 0
        for ponto, bracos, _ in self._juncoes_pavimento:
            if len(bracos) != 2 or len({bool(dx) for dx, _ in bracos}) != 2:
                continue
            for dx, dy in sorted(bracos):
                x, y = ponto[0] + 2.0*dx - .98*dy, ponto[1] + 2.0*dy + .98*dx
                if self._placa('curva', x, y, (dx, dy)):
                    curvas += 1
                    break
            if curvas >= (7 if self.cidades else 4):
                break

    def _iluminar_ruas(self):
        postes = 0
        for r in self.rotatorias:
            for braco in r.bracos:
                dx, dy = cos(braco.angulo), sin(braco.angulo)
                for recuo in (.35, .80, 1.15):
                    px, py, _ = braco.deslocar(recuo, -1.)
                    if self._adicionar_decoracao('poste', 'rua', 'light-curved', px, py, 1.55,
                                                degrees(atan2(dy, dx))):
                        postes += 1
                        break
        setores = defaultdict(list)
        for i, (a, b) in enumerate(self._trechos_pavimento):
            dx, dy = b[0] - a[0], b[1] - a[1]
            comprimento = hypot(dx, dy)
            if a[2] != b[2] or a[2] > .5 or comprimento < 5.:
                continue
            ux, uy = dx / comprimento, dy / comprimento
            quantidade = max(1, round(comprimento / (9. if self.cidades else 7.)))
            for j in range(quantidade):
                trecho = comprimento * (j + .5) / quantidade
                lado = -1 if (i + j) % 2 else 1
                x, y = a[0] + trecho * ux, a[1] + trecho * uy
                modelo = 'light-square' if i % 3 else 'light-curved'
                setores[self._quadra(x, y)].append((x, y, ux, uy, lado, modelo))
        vagas = sorted((i, setor, vaga) for setor, pontos in setores.items()
                       for i, vaga in enumerate(pontos))
        for _, _, (x, y, ux, uy, lado, modelo) in vagas:
            for sinal in (lado, -lado):
                if self._adicionar_decoracao('poste', 'rua', modelo,
                                            x - sinal*uy*1.05, y + sinal*ux*1.05, 1.55,
                                            degrees(atan2(-sinal*uy, sinal*ux))):
                    postes += 1
                    break
            if postes >= (48 if self.cidades else 24):
                break
        return postes

    def _criar_mobiliario(self, vagas):
        """Distribui sinalização e luz nas vias, com bancos e passeios livres."""
        postes = self._iluminar_ruas()
        self._postes_ponte = []
        bancos = caminhos = 0
        for ponte in self.mapa_visual.pontes:
            dx, dy = ponte.fim[0] - ponte.inicio[0], ponte.fim[1] - ponte.inicio[1]
            comprimento = hypot(dx, dy)
            ux, uy = dx / comprimento, dy / comprimento
            for sinal in (-1, 1):
                for lado in (-1, 1):
                    x = ponte.centro[0] + sinal*ux*2.2 - lado*uy*2.0
                    y = ponte.centro[1] + sinal*uy*2.2 + lado*ux*2.0
                    if self._adicionar_decoracao('poste', 'rua', 'light-curved', x, y, 1.55):
                        self._postes_ponte.append((ponte.centro, x, y))
                        postes += 1
                        break
                if self._postes_ponte:
                    break
            if self._postes_ponte:
                break
        for x, y, orientacao in vagas:
            if bancos < 6 and self._banco(x, y, orientacao):
                bancos += 1
                continue
            if caminhos < 8 and self._adicionar_decoracao('passeio', 'suburbio', 'path-stones-short',
                                                          x, y, .9, orientacao):
                caminhos += 1
            if bancos >= 6 and caminhos >= 8:
                break
        self._mobiliario = {'postes': postes, 'bancos': bancos, 'passeios': caminhos}

    def _plantar_vegetacao(self, vagas, *, alvo=None, limite_jardins=12):
        """Jardins, alinhamentos e pequenos bosques sem bloquear circulacao."""
        edificios = [d for d in self.decoracoes if d.tipo == 'edificio']
        jardins = 0
        for edificio in edificios:
            if jardins >= limite_jardins:
                break
            for angulo in (0, 90, 180, 270):
                a = (angulo + 45) * pi / 180
                distancia = edificio.raio + .85
                if self._adicionar_decoracao('jardim', 'suburbio', 'planter',
                                             edificio.x + cos(a)*distancia,
                                             edificio.y + sin(a)*distancia, .65, angulo):
                    jardins += 1
                    break

        if alvo is None:
            alvo = 90 + 2 * len(self.posicoes)
        quantidades = {'jardins': jardins, 'calcadas': 0, 'bosques': 0, 'demais': 0}
        def plantar(x, y, grupo, indice):
            if sum(quantidades[k] for k in ('calcadas', 'bosques', 'demais')) >= alvo:
                return False
            sucesso = self._adicionar_decoracao(
                'arvore', 'suburbio', 'tree-small' if indice % 3 == 0 else 'tree-large',
                x, y, self._rng.uniform(1.05, 1.55), self._rng.uniform(0, 360))
            if sucesso:
                quantidades[grupo] += 1
            return sucesso

        for i, (x, y, _) in enumerate(vagas):
            if quantidades['calcadas'] >= alvo // 3:
                break
            plantar(x, y, 'calcadas', i)

        # Centros distintos com pequenos grupos organicos; tentativas passam
        # pela mesma verificacao espacial usada para todos os demais objetos.
        for grupo in range(80):
            if quantidades['bosques'] >= alvo // 3:
                break
            cx = self._rng.uniform(-self.meia_largura + 3, self.meia_largura - 3)
            cy = self._rng.uniform(-self.meia_altura + 3, self.meia_altura - 3)
            for i in range(5):
                if quantidades['bosques'] >= alvo // 3:
                    break
                angulo = self._rng.uniform(0, 2*pi)
                raio = self._rng.uniform(0, 3.)
                plantar(cx + cos(angulo)*raio, cy + sin(angulo)*raio, 'bosques', grupo*5+i)
        for i in range(3200):
            if sum(quantidades[k] for k in ('calcadas', 'bosques', 'demais')) >= alvo:
                break
            plantar(self._rng.uniform(-self.meia_largura + 1.5, self.meia_largura - 1.5),
                    self._rng.uniform(-self.meia_altura + 1.5, self.meia_altura - 1.5), 'demais', i)
        self._vegetacao_tipos = quantidades

    def mostrar_rota(self, caminho, cor=AMARELO, *, ultimo_ativo=False):
        caminho = tuple(caminho)
        if not set(caminho) <= set(self.posicoes):
            raise ValueError("A rota contém um nó inexistente.")
        try:
            ruas = {par: self.ruas[par] for par in zip(caminho, caminho[1:])}
        except KeyError as erro:
            raise ValueError("A rota contém uma rua inexistente.") from erro
        # Validar primeiro preserva a rota atual se o novo percurso for inválido.
        malha = GeomNode("rota-destacada")
        cor = tuple(cor)
        ativa = ruas.pop(caminho[-2:], None) if ultimo_ativo else None
        for rua in ruas.values():
            malha.addGeom(_geometria_destaque(rua, cor))
        self.limpar_rota()
        if ruas:
            self.rota.attachNewNode(malha).setTwoSided(True)
        if ativa is not None:
            malha_ativa = GeomNode("trecho-ativo")
            malha_ativa.addGeom(_geometria_destaque(ativa, LARANJA))
            no = self.rota.attachNewNode(malha_ativa)
            no.setTwoSided(True)
            # A aresta pode ter sido atravessada no sentido inverso.
            no.setZ(.009)

    def mostrar_trecho(self, origem, destino, cor=AMARELO):
        """Atualiza a faixa ativa só quando a van troca de aresta."""
        trecho = origem, destino
        if trecho == self._trecho_destacado:
            return False
        self.mostrar_rota(trecho, cor)
        self._trecho_destacado = trecho
        return True

    def limpar_rota(self):
        for filho in self.rota.getChildren():
            filho.removeNode()
        self._trecho_destacado = None

    def destruir(self):
        self.raiz.removeNode()
        self.rota.removeNode()
