"""Apresentação imutável do grafo, independente de Panda3D e dos algoritmos.

O cadastro matemático continua em ``tsp_core``. Este módulo associa posições,
endereços e polilinhas aos mesmos objetos No/Aresta, sem copiar seus pesos.
"""
from dataclasses import dataclass, field
from functools import lru_cache
from math import dist, isfinite
from types import MappingProxyType
from typing import Mapping

from tsp_core import Aresta, Grafo, No
from roteamento3d import ALTURA_RUA, posicoes_planejadas, rotear


XYZ = tuple[float, float, float]


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

    def __post_init__(self):
        object.__setattr__(self, 'posicao', _xyz(self.posicao))
        if not isinstance(self.kit, str) or not isinstance(self.nome, str) or not self.kit or not self.nome:
            raise ValueError("A construção precisa de referências ao kit e ao modelo.")
        if not isfinite(self.tamanho) or self.tamanho <= 0:
            raise ValueError("O tamanho da construção deve ser positivo e finito.")
        if not isfinite(self.margem_lote) or self.margem_lote < 0:
            raise ValueError("A margem do lote deve ser finita e não negativa.")

    @property
    def limites_xy(self):
        x, y, _ = self.posicao
        metade = self.tamanho / 2 + self.margem_lote
        return x - metade, y - metade, x + metade, y + metade


@dataclass(frozen=True)
class NoVisual:
    no: No
    posicao_3d: XYZ
    construcao: ConstrucaoVisual
    conexoes: tuple[int, ...]

    def __post_init__(self):
        object.__setattr__(self, 'posicao_3d', _xyz(self.posicao_3d))
        object.__setattr__(self, 'conexoes', tuple(self.conexoes))
        if not isinstance(self.construcao, ConstrucaoVisual):
            raise ValueError("O endereço deve ser uma ConstrucaoVisual imutável.")

    @property
    def id(self):
        return self.no.id

    @property
    def posicao_logica(self):
        return self.no.x, self.no.y


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
        posicoes = {n.id: n.posicao_3d for n in self.nos}
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

    @property
    def posicoes(self):
        return self._posicoes

    @property
    def ruas(self):
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
def _criar_em_cache(identidade, posicoes, construcoes):
    grafo = identidade.grafo
    posicoes, construcoes = dict(posicoes), dict(construcoes)
    adj = grafo.adjacencia()
    nos = tuple(NoVisual(n, posicoes[n.id], construcoes[n.id], tuple(sorted(adj[n.id])))
                for n in grafo.nos)
    # A malha urbana canônica é exclusivamente visual. Cada caminho continua
    # referenciando a mesma Aresta imutável fornecida pelo grafo. Um layout
    # explicitamente fornecido permanece livre para ferramentas e testes da
    # task anterior; ele recebe uma polilinha ortogonal simples, sem mudar
    # topologia nem exigir que seus pontos caibam na grade planejada.
    if posicoes == posicoes_planejadas(grafo):
        rotas = rotear(grafo, posicoes, construcoes, w5=len(grafo.ids) == 5)
        por_aresta = dict(rotas.caminhos)
        pontes = rotas.pontes
    else:
        por_aresta = {}
        for aresta in grafo.arestas:
            a, b = posicoes[aresta.origem], posicoes[aresta.destino]
            curva = (b[0], a[1], ALTURA_RUA)
            por_aresta[aresta.origem, aresta.destino] = (a, curva, b) if curva not in (a, b) else (a, b)
        pontes = ()
    arestas = [ArestaVisual(aresta, por_aresta[aresta.origem, aresta.destino])
               for aresta in grafo.arestas]
    return MapaVisual(grafo, nos, tuple(arestas), tuple(pontes))


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
    for i, no in enumerate(grafo.ids):
        x, y, _ = posicoes[no]
        kit = 'cidade' if i % 3 == 1 else 'suburbio'
        nome = f'building-{chr(97 + i % 8)}' if kit == 'cidade' else f'building-type-{chr(97 + i % 12)}'
        enderecos[no] = ConstrucaoVisual((x - 2.2, y + 2.6, -.295), kit, nome)
    if construcoes is not None:
        if not set(construcoes) <= set(grafo.ids):
            raise ValueError("Endereço associado a um nó inexistente.")
        if not all(isinstance(c, ConstrucaoVisual) for c in construcoes.values()):
            raise ValueError("Endereços devem ser objetos ConstrucaoVisual imutáveis.")
        enderecos.update(construcoes)
    return _criar_em_cache(_IdentidadeGrafo(grafo),
                          tuple((no, posicoes[no]) for no in grafo.ids),
                          tuple((no, enderecos[no]) for no in grafo.ids))


criar_mapa_visual.cache_info = _criar_em_cache.cache_info
criar_mapa_visual.cache_clear = _criar_em_cache.cache_clear


def posicoes_mundo(grafo):
    """Compatibilidade: cópia mutável das posições da apresentação padrão."""
    return dict(criar_mapa_visual(grafo).posicoes)


def ruas_mundo(grafo):
    """Compatibilidade: ruas bidirecionais da mesma apresentação em cache."""
    return dict(criar_mapa_visual(grafo).ruas)


def interpolar(pontos, fracao):
    comprimentos = [dist(a, b) for a, b in zip(pontos, pontos[1:])]
    restante = max(0., min(1., fracao)) * sum(comprimentos)
    for i, comprimento in enumerate(comprimentos):
        if restante <= comprimento or i == len(comprimentos) - 1:
            a, b = pontos[i:i + 2]
            t = restante / comprimento if comprimento else 0.
            return tuple(a[k] + (b[k] - a[k]) * t for k in range(3)), tuple(b[k] - a[k] for k in range(3))
        restante -= comprimento
    raise ValueError("Uma rua precisa de pelo menos dois pontos.")


