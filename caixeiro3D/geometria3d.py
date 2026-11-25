"""Apresentação imutável do grafo, independente de Panda3D e dos algoritmos.

O cadastro matemático continua em ``tsp_core``. Este módulo associa posições,
endereços e polilinhas aos mesmos objetos No/Aresta, sem copiar seus pesos.
"""
from bisect import bisect_right
from dataclasses import dataclass, field
from functools import lru_cache
from itertools import accumulate
from math import ceil, cos, dist, isfinite, pi, radians, sin, ulp
from types import MappingProxyType
from typing import Mapping

from tsp_core import Aresta, Grafo, No
from roteamento3d import ALTURA_RUA, posicoes_planejadas, rotear
from rotatorias3d import Rotatoria, planejar_rotatoria, separar_pavimento


XYZ = tuple[float, float, float]
NIVEL_GRAMA = -.35
COTA_LOTE = -.025
DESLOCAMENTO_PADRAO_ETIQUETA = (0., -46.)
_LOTES_MAPA_05 = {1: (-4.5, -4.5), 4: (4.5, -4.5), 5: (4.5, 4.5)}
# Coordenadas da porta na malha Panda (+Y aponta para a fachada), antes da normalizacao.
# O ultimo valor e a maior dimensao horizontal original usada pela escala do renderizador.
FACHADAS = {('suburbio', 'building-type-a'): (0., .40, 1.30),
            ('suburbio', 'building-type-b'): (.40, .45, 1.828),
            ('cidade', 'building-a'): (.21, .40, .94)}
_ETIQUETAS_MAPA_18 = {9: (12., -34.), 10: (12., -34.), 13: (12., -34.), 14: (0., 34.)}


def _xyz(valor):
    ponto = tuple(float(v) for v in valor)
    if len(ponto) != 3 or not all(isfinite(v) for v in ponto):
        raise ValueError("Uma posição visual precisa de três coordenadas finitas.")
    return ponto


@dataclass(frozen=True)
class ConstrucaoVisual:
    """Endereço reservado; o tamanho delimita o lote, sem carregar o asset."""
    posicao: XYZ
    kit: str
    nome: str
    tamanho: float = 2.3
    margem_lote: float = .3
    rotacao: float = 0.

    def __post_init__(self):
        object.__setattr__(self, 'posicao', _xyz(self.posicao))
        if not isinstance(self.kit, str) or not isinstance(self.nome, str) or not self.kit or not self.nome:
            raise ValueError("A construção precisa de referências ao kit e ao modelo.")
        if not isfinite(self.tamanho) or self.tamanho <= 0:
            raise ValueError("O tamanho da construção deve ser positivo e finito.")
        if not isfinite(self.margem_lote) or self.margem_lote < 0:
            raise ValueError("A margem do lote deve ser finita e não negativa.")
        if not isfinite(self.rotacao):
            raise ValueError("A rotação da construção deve ser finita.")

    @property
    def metade_lote(self):
        return self.tamanho / 2 + self.margem_lote

    @property
    def limites_xy(self):
        x, y, _ = self.posicao
        angulo = radians(self.rotacao)
        metade = self.metade_lote * (abs(cos(angulo)) + abs(sin(angulo)))
        return x - metade, y - metade, x + metade, y + metade


@dataclass(frozen=True)
class NoVisual:
    """Endereço e ponto de chegada de um nó no mundo 3D."""

    no: No
    posicao_3d: XYZ
    construcao: ConstrucaoVisual
    conexoes: tuple[int, ...]
    deslocamento_etiqueta: tuple[float, float] = DESLOCAMENTO_PADRAO_ETIQUETA

    def __post_init__(self):
        object.__setattr__(self, 'posicao_3d', _xyz(self.posicao_3d))
        object.__setattr__(self, 'conexoes', tuple(self.conexoes))
        offset = tuple(float(v) for v in self.deslocamento_etiqueta)
        if len(offset) != 2 or not all(isfinite(v) for v in offset):
            raise ValueError("O deslocamento da etiqueta deve ter duas coordenadas finitas.")
        object.__setattr__(self, 'deslocamento_etiqueta', offset)
        if not isinstance(self.construcao, ConstrucaoVisual):
            raise ValueError("O endereço deve ser uma ConstrucaoVisual imutável.")

    @property
    def id(self):
        return self.no.id

    @property
    def posicao_logica(self):
        return self.no.x, self.no.y

    @property
    def ancora_rua(self):
        return self.posicao_3d

    @property
    def posicao_marcador(self):
        return self.ancora_rua

    @property
    def entrada(self):
        """Meio da borda do lote que dá acesso à rua."""
        lote = self.construcao
        x, y, z = lote.posicao
        angulo = radians(lote.rotacao)
        c, s = cos(angulo), sin(angulo)
        fachada = FACHADAS.get((lote.kit, lote.nome))
        if fachada is None:
            # Enderecos externos continuam permitindo qualquer modelo.
            dx, dy = self.ancora_rua[0] - x, self.ancora_rua[1] - y
            local_x, local_y = dx * c + dy * s, -dx * s + dy * c
            metade = lote.metade_lote
            if abs(local_x) >= abs(local_y):
                ex, ey = (metade if local_x >= 0 else -metade), 0.
            else:
                ex, ey = 0., (metade if local_y >= 0 else -metade)
        else:
            ex = fachada[0] * lote.tamanho / fachada[2]
            ey = lote.metade_lote
        return x + ex * c - ey * s, y + ex * s + ey * c, z + COTA_LOTE

    @property
    def porta(self):
        """Ponto da fachada no plano do lote, na escala da instancia."""
        lote = self.construcao
        fachada = FACHADAS.get((lote.kit, lote.nome))
        if fachada is None:
            return self.entrada
        ex, ey, dimensao = fachada
        ex, ey = ex * lote.tamanho / dimensao, ey * lote.tamanho / dimensao
        c, s = cos(radians(lote.rotacao)), sin(radians(lote.rotacao))
        x, y, z = lote.posicao
        return x + ex*c - ey*s, y + ex*s + ey*c, z + COTA_LOTE + .004

    @property
    def acesso(self):
        return self.ancora_rua, self.entrada


@dataclass(frozen=True)
class ArestaVisual:
    aresta: Aresta
    caminho: tuple[XYZ, ...]

    def __post_init__(self):
        object.__setattr__(self, 'caminho', tuple(_xyz(p) for p in self.caminho))
        if len(self.caminho) < 2:
            raise ValueError("Uma rua precisa de pelo menos dois pontos.")

    @property
    def origem(self):
        return self.aresta.origem

    @property
    def destino(self):
        return self.aresta.destino

    @property
    def peso(self):
        return self.aresta.peso


@dataclass(frozen=True)
class MapaVisual:
    grafo: Grafo
    nos: tuple[NoVisual, ...]
    arestas: tuple[ArestaVisual, ...]
    pontes: tuple = ()
    rotatorias: tuple[Rotatoria, ...] = ()
    chegadas: Mapping[int, XYZ] = field(init=False, repr=False, compare=False)
    eixos_pavimento: Mapping[tuple[int, int], tuple[XYZ, ...]] = field(init=False, repr=False, compare=False)
    trajetos: Mapping[tuple[int, int], tuple[XYZ, ...]] = field(init=False, repr=False, compare=False)
    zonas_rotatorias: Mapping[tuple[int, int], tuple[int, int]] = field(init=False, repr=False, compare=False)
    _posicoes: Mapping[int, XYZ] = field(init=False, repr=False, compare=False)
    _ruas: Mapping[tuple[int, int], tuple[XYZ, ...]] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, 'nos', tuple(self.nos))
        object.__setattr__(self, 'arestas', tuple(self.arestas))
        object.__setattr__(self, 'pontes', tuple(self.pontes))
        originais = {n.id: n for n in self.grafo.nos}
        if len(self.nos) != len(originais) or {n.id for n in self.nos} != set(originais):
            raise ValueError("O mapa visual deve representar exatamente os nós do grafo.")
        adj = self.grafo.adjacencia()
        for n in self.nos:
            if n.no is not originais[n.id]:
                raise ValueError("O nó visual deve referenciar o nó original do grafo.")
            if len(n.conexoes) != len(adj[n.id]) or set(n.conexoes) != set(adj[n.id]):
                raise ValueError("As conexões visuais devem corresponder à adjacência original.")
        posicoes = {n.id: n.ancora_rua for n in self.nos}
        esperadas = {id(e) for e in self.grafo.arestas}
        if len(self.arestas) != len(esperadas) or {id(e.aresta) for e in self.arestas} != esperadas:
            raise ValueError("As ruas devem referenciar exatamente as arestas originais.")
        ruas = {}
        for e in self.arestas:
            if e.caminho[0] != posicoes[e.origem] or e.caminho[-1] != posicoes[e.destino]:
                raise ValueError("Os extremos da rua devem coincidir com seus nós visuais.")
            ruas[e.origem, e.destino] = e.caminho
            ruas[e.destino, e.origem] = tuple(reversed(e.caminho))
        object.__setattr__(self, '_posicoes', MappingProxyType(posicoes))
        object.__setattr__(self, '_ruas', MappingProxyType(ruas))
        rotatorias = tuple(self.rotatorias)
        object.__setattr__(self, 'rotatorias', rotatorias)
        chegadas = posicoes | {r.no: r.chegada for r in rotatorias}
        eixos, trajetos, zonas = separar_pavimento(ruas, rotatorias)
        object.__setattr__(self, 'chegadas', MappingProxyType(chegadas))
        object.__setattr__(self, 'eixos_pavimento', eixos)
        object.__setattr__(self, 'trajetos', trajetos)
        object.__setattr__(self, 'zonas_rotatorias', zonas)

    @property
    def posicoes(self):
        return self._posicoes

    @property
    def ruas(self):
        """Eixos ortogonais do traçado, antes de aplicar as rotatórias."""
        return self._ruas

    @property
    def limites_xy(self):
        """Envelope de ruas e lotes; inclui desvios além dos nós do grafo."""
        pontos = list(self.posicoes.values())
        for e in self.arestas:
            pontos.extend(e.caminho)
        xs = [p[0] for p in pontos]
        ys = [p[1] for p in pontos]
        # Meio metro cobre a meia largura do asfalto; a cena acrescenta margem.
        xs.extend((min(xs) - .55, max(xs) + .55))
        ys.extend((min(ys) - .55, max(ys) + .55))
        for n in self.nos:
            x0, y0, x1, y1 = n.construcao.limites_xy
            xs.extend((x0, x1))
            ys.extend((y0, y1))
        return min(xs), min(ys), max(xs), max(ys)


@dataclass(frozen=True, eq=False)
class _IdentidadeGrafo:
    grafo: Grafo

    def __hash__(self):
        return id(self.grafo)

    def __eq__(self, outro):
        return isinstance(outro, _IdentidadeGrafo) and self.grafo is outro.grafo


@lru_cache(maxsize=16)
def _criar_em_cache(identidade, posicoes, construcoes, com_rotatorias):
    grafo = identidade.grafo
    posicoes, construcoes = dict(posicoes), dict(construcoes)
    adj = grafo.adjacencia()
    etiquetas = _ETIQUETAS_MAPA_18 if grafo.id == 'mapa_18' else {}
    nos = tuple(NoVisual(n, posicoes[n.id], construcoes[n.id], tuple(sorted(adj[n.id])),
                         etiquetas.get(n.id, DESLOCAMENTO_PADRAO_ETIQUETA)) for n in grafo.nos)
    ancoras = {n.id: n.ancora_rua for n in nos}
    # A malha urbana canônica é exclusivamente visual. Cada caminho continua
    # referenciando a mesma Aresta imutável fornecida pelo grafo. Um layout
    # explicitamente fornecido permanece livre para ferramentas e testes da
    # task anterior; ele recebe uma polilinha ortogonal simples, sem mudar
    # topologia nem exigir que seus pontos caibam na grade planejada.
    layout_padrao = ancoras == posicoes_planejadas(grafo)
    if layout_padrao:
        rotas = rotear(grafo, ancoras, construcoes, w5=len(grafo.ids) == 5)
        por_aresta = dict(rotas.caminhos)
        pontes = rotas.pontes
    else:
        por_aresta = {}
        for aresta in grafo.arestas:
            a, b = ancoras[aresta.origem], ancoras[aresta.destino]
            curva = (b[0], a[1], ALTURA_RUA)
            por_aresta[aresta.origem, aresta.destino] = (a, curva, b) if curva not in (a, b) else (a, b)
        pontes = ()
    rotatorias = ()
    if layout_padrao and com_rotatorias:
        if grafo.id in {'mapa_05', 'mapa_18'}:
            eixos = por_aresta | {(v, u): p[::-1] for (u, v), p in por_aresta.items()}
            rotatorias = tuple(
                planejar_rotatoria(no, centro, sorted(adj[no]), eixos, -pi / 4)
                for no, centro in ancoras.items() if len(adj[no]) >= 3
            )
    arestas = [ArestaVisual(aresta, por_aresta[aresta.origem, aresta.destino])
               for aresta in grafo.arestas]
    return MapaVisual(grafo, nos, tuple(arestas), tuple(pontes), rotatorias)


def criar_mapa_visual(grafo, *, posicoes=None, construcoes=None):
    """Crie ou reutilize uma apresentação para este objeto Grafo e este layout.

    Posições fornecidas devem cobrir todos os nós. Referências a construções
    podem substituir apenas os endereços desejados. Nenhuma opção altera o
    cadastro matemático. O cache mantém identidades distintas mesmo para dois
    grafos com os mesmos valores, preservando referências aos objetos originais.
    """
    if posicoes is None:
        posicoes = posicoes_planejadas(grafo)
    if set(posicoes) != set(grafo.ids):
        raise ValueError("O layout deve fornecer posições para exatamente os nós do grafo.")
    posicoes = {no: _xyz(posicoes[no]) for no in grafo.ids}
    enderecos = {}
    lotes = _LOTES_MAPA_05 if grafo.id == 'mapa_05' else {}
    centro_x = sum(p[0] for p in posicoes.values()) / len(posicoes)
    centro_y = sum(p[1] for p in posicoes.values()) / len(posicoes)
    for i, no in enumerate(grafo.ids):
        x, y, z = posicoes[no]
        kit, nome = (('suburbio', 'building-type-a'), ('cidade', 'building-a'),
                     ('suburbio', 'building-type-b'))[i % 3]
        # Lote persistente no lado voltado ao centro da cidade, fora da praça
        # e das oito portas do nó.
        dx = 4.5 if x < centro_x else -4.5
        dy = 4.5 if y < centro_y else -4.5
        dx, dy = lotes.get(no, (dx, dy))
        base = NIVEL_GRAMA + .055 + (z - ALTURA_RUA)
        # Panda gira +Y para -X com heading positivo.
        rotacao = (90. if dx > 0 else -90.) if abs(dx) >= abs(dy) else (180. if dy > 0 else 0.)
        enderecos[no] = ConstrucaoVisual(
            (x + dx, y + dy, base), kit, nome, rotacao=rotacao)
    com_rotatorias = True
    if construcoes is not None:
        if not set(construcoes) <= set(grafo.ids):
            raise ValueError("Endereço associado a um nó inexistente.")
        if not all(isinstance(c, ConstrucaoVisual) for c in construcoes.values()):
            raise ValueError("Endereços devem ser objetos ConstrucaoVisual imutáveis.")
        # As bocas e o contorno de cada anel foram encaixados no cadastro padrão.
        com_rotatorias = all(enderecos[no] == lote for no, lote in construcoes.items())
        enderecos.update(construcoes)
    return _criar_em_cache(_IdentidadeGrafo(grafo),
                          tuple((no, posicoes[no]) for no in grafo.ids),
                          tuple((no, enderecos[no]) for no in grafo.ids), com_rotatorias)


criar_mapa_visual.cache_info = _criar_em_cache.cache_info
criar_mapa_visual.cache_clear = _criar_em_cache.cache_clear


def posicoes_mundo(grafo):
    """Compatibilidade: cópia mutável das posições da apresentação padrão."""
    return dict(criar_mapa_visual(grafo).chegadas)


def ruas_mundo(grafo):
    """Compatibilidade: ruas bidirecionais da mesma apresentação em cache."""
    return dict(criar_mapa_visual(grafo).trajetos)


@dataclass(frozen=True)
class AmostraRua:
    ponto: XYZ
    tangente: XYZ
    restante_segmento: float
    proxima_tangente: XYZ | None


@dataclass(frozen=True)
class RuaMedida:
    pontos: tuple[XYZ, ...]
    segmentos: tuple[tuple[XYZ, XYZ], ...]
    acumulados: tuple[float, ...]

    @property
    def comprimento(self):
        return self.acumulados[-1]

    def distancia(self, fracao):
        return max(0., min(1., fracao)) * self.comprimento

    def amostrar(self, fracao):
        distancia = self.distancia(fracao)
        ultimo = len(self.segmentos) - 1
        indice = min(ultimo, bisect_right(self.acumulados, distancia) - 1)
        # O produto fração × comprimento pode cair um ULP antes da curva.
        fim = self.acumulados[indice + 1]
        if indice < ultimo and fim - distancia <= ulp(fim):
            indice += 1
            distancia = fim
        inicio, fim = self.acumulados[indice:indice + 2]
        a, b = self.segmentos[indice]
        vetor = tuple(v - u for u, v in zip(a, b))
        if distancia - inicio <= ulp(inicio):
            ponto = a
        elif distancia == fim:
            ponto = b
        else:
            t = (distancia - inicio) / (fim - inicio)
            ponto = tuple(u + t * d for u, d in zip(a, vetor))
        proxima = None
        if indice < ultimo:
            c, d = self.segmentos[indice + 1]
            proxima = tuple(v - u for u, v in zip(c, d))
        return AmostraRua(ponto, vetor, fim - distancia, proxima)


def medir_rua(pontos):
    """Meça a tupla imutável de waypoints usada pela cena e pelo veículo."""
    if not isinstance(pontos, tuple) or not all(isinstance(p, tuple) for p in pontos):
        pontos = tuple(map(tuple, pontos))
    return _medir_rua(pontos)


@lru_cache(maxsize=256)
def _medir_rua(pontos):
    if len(pontos) < 2:
        raise ValueError("Uma rua precisa de pelo menos dois pontos.")
    segmentos = tuple((a, b) for a, b in zip(pontos, pontos[1:]) if a != b)
    if not segmentos:
        segmentos = ((pontos[0], pontos[-1]),)
    acumulados = tuple(accumulate((dist(a, b) for a, b in segmentos), initial=0.))
    return RuaMedida(pontos, segmentos, acumulados)


def interpolar(pontos, fracao):
    amostra = medir_rua(pontos).amostrar(fracao)
    return amostra.ponto, amostra.tangente


def fracao_com_rotatoria(pontos, zonas, fracao):
    """Converte fração do relógio em distância, com desaceleração nas bocas."""
    if not zonas or not 0. < fracao < 1.:
        return fracao
    distancias, tempos, comprimento = _perfil_rotatoria(pontos, zonas)
    t = fracao * tempos[-1]
    i = bisect_right(tempos, t) - 1
    progresso = (t - tempos[i]) / (tempos[i + 1] - tempos[i])
    return (distancias[i] + progresso * (distancias[i + 1] - distancias[i])) / comprimento


def comprimento_no_ritmo_da_via(pontos, zonas):
    """Comprimento ponderado pela desaceleração usada na animação."""
    if zonas:
        return _perfil_rotatoria(pontos, zonas)[1][-1]
    return medir_rua(pontos).comprimento


@lru_cache(maxsize=64)
def _perfil_rotatoria(pontos, zonas):
    rua = medir_rua(pontos)
    inicio, fim = zonas
    fim_inicio = rua.acumulados[inicio] if inicio else None
    inicio_fim = rua.acumulados[-fim - 1] if fim else None
    passos = ceil(rua.comprimento / .20)
    passo = rua.comprimento / passos

    def densidade(s):
        distancias = [1.4]
        if fim_inicio is not None:
            distancias.append(max(0., s - fim_inicio))
        if inicio_fim is not None:
            distancias.append(max(0., inicio_fim - s))
        t = 1. - min(distancias) / 1.4
        return 1. + .85 * t * t * (3. - 2. * t)

    distancias = tuple(i * passo for i in range(passos + 1))
    densidades = tuple(map(densidade, distancias))
    tempos = tuple(accumulate(((a + b) * passo / 2 for a, b in zip(densidades, densidades[1:])),
                              initial=0.))
    return distancias, tempos, rua.comprimento


