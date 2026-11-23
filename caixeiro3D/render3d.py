"""Cena urbana estática sobre a geometria do grafo, com assets Kenney locais.

As ruas são exclusivamente as arestas fornecidas. A decoração nunca participa
da adjacência e tem seu espaço reservado fora de todas as polilinhas de ruas.
O veículo, as luzes e as etiquetas projetadas pertencem à aplicação.
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from math import atan2, cos, degrees, dist, hypot, pi, sin
from random import Random

from panda3d.core import (Geom, GeomNode, GeomTriangles, GeomVertexData,
                         GeomVertexFormat, GeomVertexWriter,
                         TransparencyAttrib, Vec3)

from geometria3d import COTA_LOTE, NIVEL_GRAMA, criar_mapa_visual, medir_rua
from roteamento3d import LARGURA_VIA


LARGURA_RUA = LARGURA_VIA
LARGURA_ACESSO = .52
AMARELO = (1., .76, .13, 1.)
ESCALA_VERTICAL_RUA = .55
COR_GRAMA = (.60, .79, .52, 1)
COR_CALCADA = (.88, .84, .73, 1)
COR_CONTORNO_PONTE = (.56, .60, .65, 1)
COR_GUARDA_CORPO = (.94, .74, .52, 1)
TINTA_RUA = (1.08, 1.08, 1.04, 1)


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
        self.construcoes_no = {}
        self._acessos = tuple(no.acesso for no in self.mapa_visual.nos)
        self.modelos_usados = set()
        self._limites_modelos = {}
        self.trechos_rua = 0
        self.pontes = len(self.mapa_visual.pontes)
        self._apoios_pontes = ()
        self._agua = ()
        self._trecho_destacado = None
        self._segmentos = tuple(
            trecho for aresta in grafo.arestas
            for trecho in medir_rua(self.ruas[aresta.origem, aresta.destino]).segmentos
        )
        self._rng = Random(410 + len(grafo.ids))
        x0, y0, x1, y1 = self.mapa_visual.limites_xy
        self.meia_largura = max(26., abs(x0) + 2., abs(x1) + 2.)
        self.meia_altura = max(23., abs(y0) + 2., abs(y1) + 2.)
        try:
            self._terreno()
            self._criar_agua_local()
            self._construir_ruas()
            self._decorar()
            self.raiz.flattenStrong()
        except Exception:
            self.destruir()
            raise

    @property
    def marcadores_no(self):
        return self.mapa_visual.posicoes

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
            pontos.extend((no.posicao_marcador, no.entrada))
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
        trechos, juncoes = _pavimento(self._segmentos, self.posicoes.values())
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
        for no, (x, y, z) in self.posicoes.items():
            _disco(self.raiz, f"aro-ponto-{no}", x, y, z + .014, .40, (.91, .95, .96, 1))
            _disco(self.raiz, f"ponto-{no}", x, y, z + .015, .29, (.25, .60, .86, 1))
        if self.pontes:
            self._construir_apoios()

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
        return min((_distancia_segmento(x, y, a, b) for a, b in self._segmentos), default=float("inf"))

    def _livre(self, x, y, raio, *, afastamento_no=1.2):
        if abs(x) + raio > self.meia_largura - 1 or abs(y) + raio > self.meia_altura - 1:
            return False
        for x0, y0, x1, y1 in self._agua:
            if hypot(x - max(x0, min(x1, x)), y - max(y0, min(y1, y))) < raio + .1:
                return False
        if self.distancia_rua(x, y) < raio + LARGURA_RUA / 2 + .4:
            return False
        if any(hypot(x - p[0], y - p[1]) < raio + afastamento_no for p in self.posicoes.values()):
            return False
        if any(_distancia_segmento(x, y, a, b) < raio + LARGURA_ACESSO / 2
               for a, b in self._acessos):
            return False
        return not any(hypot(x - d.x, y - d.y) < raio + d.raio + .3 for d in self.decoracoes)

    def _sombra(self, x, y, raio):
        for i, (fator, alfa) in enumerate(((1.30, .026), (1.17, .05), (1.04, .085), (.87, .10))):
            _disco(self._sombras, "sombra-suave", x + .14, y + .12,
                   NIVEL_GRAMA + .006 + i * .001, raio * fator,
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
        ancora, entrada = no_visual.acesso
        _faixa(self.raiz, f"acesso-no-{no_visual.id}", ancora, entrada,
               LARGURA_ACESSO, COR_CALCADA)
        _faixa(self.raiz, f"porta-no-{no_visual.id}", entrada, no_visual.porta,
               LARGURA_ACESSO, COR_CALCADA)
        self._sombra(x, y, raio)
        construcao = Decoracao("edificio", endereco.kit, endereco.nome, x, y,
                               raio, altura, no_visual.id)
        self.decoracoes.append(construcao)
        self.construcoes_no[no_visual.id] = construcao

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
        # O endereço cadastrado é a cidade de cada nó, sempre na mesma posição.
        for no_visual in self.mapa_visual.nos:
            self._adicionar_construcao_no(no_visual)
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

    def _criar_mobiliario(self, vagas):
        """Posiciona mobiliario nas vagas livres e nas proximidades das pontes."""
        self._postes_ponte = []
        postes = bancos = caminhos = 0
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
        for i, (x, y, orientacao) in enumerate(vagas):
            if postes < 14:
                nome = 'light-curved' if i % 2 else 'light-square'
                if self._adicionar_decoracao('poste', 'rua', nome, x, y, 1.55, orientacao):
                    postes += 1
                    continue
            if bancos < 6 and self._banco(x, y, orientacao):
                bancos += 1
                continue
            if caminhos < 8 and self._adicionar_decoracao('passeio', 'suburbio', 'path-stones-short',
                                                          x, y, .9, orientacao):
                caminhos += 1
            if postes >= 14 and bancos >= 6 and caminhos >= 8:
                break
        self._mobiliario = {'postes': postes, 'bancos': bancos, 'passeios': caminhos}

    def _plantar_vegetacao(self, vagas):
        """Jardins, alinhamentos e pequenos bosques sem bloquear circulacao."""
        edificios = [d for d in self.decoracoes if d.tipo == 'edificio']
        jardins = 0
        for edificio in edificios:
            for angulo in (0, 90, 180, 270):
                a = (angulo + 45) * pi / 180
                distancia = edificio.raio + .85
                if self._adicionar_decoracao('jardim', 'suburbio', 'planter',
                                             edificio.x + cos(a)*distancia,
                                             edificio.y + sin(a)*distancia, .65, angulo):
                    jardins += 1
                    break
            if jardins >= 12:
                break

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

    def mostrar_rota(self, caminho, cor=AMARELO):
        caminho = tuple(caminho)
        if not set(caminho) <= set(self.posicoes):
            raise ValueError("A rota contém um nó inexistente.")
        try:
            ruas = [medir_rua(self.ruas[a, b]) for a, b in zip(caminho, caminho[1:])]
        except KeyError as erro:
            raise ValueError("A rota contém uma rua inexistente.") from erro
        # Validar primeiro preserva a rota atual se o novo percurso for inválido.
        self.limpar_rota()
        self._trecho_destacado = None
        for rua in ruas:
            for a, b in rua.segmentos:
                _faixa(self.rota, "contorno-rota", a, b, .34, (.60, .40, .08, 1), .031)
                _faixa(self.rota, "rota-amarela", a, b, .24, cor, .035)
            for x, y, z in rua.pontos:
                _disco(self.rota, "junta-rota", x, y, z + .036, .12, cor, lados=12)
        self.rota.flattenStrong()

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
