"""Planejamento dos lotes urbanos do mapa de 18 pontos."""
from dataclasses import dataclass
from itertools import cycle
from math import atan2, degrees, hypot
from random import Random

from geometria3d import NIVEL_GRAMA, XYZ
from roteamento3d import LARGURA_VIA


_CASAS = tuple(f'building-type-{letra}' for letra in 'acdfghijklmnpqrst')
_PREDIOS = ('building-b', 'building-d', 'building-e', 'building-f',
            'low-detail-building-wide-a', 'low-detail-building-wide-b')
_PERFIS = (('residencial', (6, 1)), ('misto', (5, 2)), ('comercial', (4, 3)))
_AREAS = ((7.2, 4.6), (6.8, 4.4), (6.2, 4.2), (5.7, 4.), (5.2, 3.8), (4.7, 3.6))
_DIRECOES = ((1, 0), (-1, 0), (0, 1), (0, -1))
_MEIA_RUA = LARGURA_VIA / 2
COTA_PRACA = NIVEL_GRAMA + .025


@dataclass(frozen=True)
class LoteUrbano:
    tipo: str
    kit: str
    modelo: str
    posicao: XYZ
    rotacao: float
    tamanho: float
    paleta: str | None = None


@dataclass(frozen=True)
class CidadeVisual:
    no: int
    ancora_rua: XYZ
    centro: tuple[float, float]
    frente: tuple[int, int]
    area: tuple[float, float]  # largura entre fileiras e comprimento da alameda
    perfil: str
    via_acesso: tuple[int, int]
    ponto_na_via: XYZ
    grupos: tuple[tuple[LoteUrbano, ...], ...]

    @property
    def entrada(self):
        return (*self.ponto_local(0, self.area[1] / 2), COTA_PRACA)

    @property
    def meio_fio(self):
        dx, dy = self.frente
        x, y, z = self.ponto_na_via
        distancia = _MEIA_RUA + .002
        return x - dx * distancia, y - dy * distancia, z - .02

    @property
    def limites_acesso(self):
        x0, y0, x1, y1 = _retangulo(self.entrada, self.meio_fio)
        dx, dy = self.frente
        return x0 - abs(dy) * .26, y0 - abs(dx) * .26, x1 + abs(dy) * .26, y1 + abs(dx) * .26

    @property
    def construcoes(self):
        return tuple(lote for grupo in self.grupos for lote in grupo if lote.tipo == 'edificio')

    @property
    def limites_xy(self):
        x, y = self.centro
        largura, comprimento = self.area
        hx, hy = (comprimento / 2, largura / 2) if self.frente[0] else (largura / 2, comprimento / 2)
        return x - hx, y - hy, x + hx, y + hy

    def ponto_local(self, lateral, longitudinal):
        dx, dy = self.frente
        x, y = self.centro
        return x + lateral * dy + longitudinal * dx, y - lateral * dx + longitudinal * dy


def gerar_cidade(no, ancora, centro, frente, area, via, ponto_na_via, *,
                 perfil, densidade, casas=_CASAS, predios=_PREDIOS, semente=410):
    """Distribui casas, prédios e jardins em duas fileiras voltadas à alameda."""
    rng = Random(semente + no)
    largura, comprimento = area
    colunas = max(2, min(6, int(comprimento / 1.5)))
    passo = (comprimento - .65) / colunas
    largura_lote = (largura - .74) / 2
    capacidade = 2 * colunas - 1  # um lote fica livre para a árvore da praça
    qtd_predios = min(densidade[1], max(0, capacidade - min(4, densidade[0])))
    qtd_casas = min(densidade[0], capacidade - qtd_predios)

    dx, dy = frente
    orientacao = degrees(atan2(-dx, dy))
    x, y = centro
    # Reserva a esquina mais próxima da entrada para verde, e concentra os
    # prédios no fundo da alameda, longe da pista e do marcador de chegada.
    vagas = [(lado, indice) for indice in range(colunas) for lado in (-1, 1)]
    jardim = (1 if no % 2 else -1, colunas - 1)
    vagas.remove(jardim)
    vagas_predios = set(vagas[:qtd_predios])
    vagas_casas = set(vagas[qtd_predios:qtd_predios + qtd_casas])
    if (qtd_casas and not casas) or (qtd_predios and not predios):
        raise ValueError('Cada tipo de construção solicitado precisa de pelo menos um modelo.')
    casas = cycle(reversed(rng.sample(casas, len(casas))))
    predios = cycle(reversed(rng.sample(predios, len(predios))))
    grupos = []
    for lado in (-1, 1):
        grupo = []
        for indice in range(colunas):
            lateral = lado * (.34 + largura_lote / 2)
            longitudinal = (indice + .5 - colunas / 2) * passo
            posicao = (x + lateral * dy + longitudinal * dx,
                       y - lateral * dx + longitudinal * dy, COTA_PRACA)
            rotacao = orientacao + lado * 90
            vaga = lado, indice
            if vaga in vagas_predios:
                modelo = next(predios)
                tamanho = min(passo, largura_lote) - .18
                grupo.append(LoteUrbano('edificio', 'cidade', modelo, posicao, rotacao, tamanho))
            elif vaga in vagas_casas:
                modelo = next(casas)
                tamanho = min(passo, largura_lote) * rng.uniform(.76, .87)
                paleta = rng.choice(('a', 'b', None))
                grupo.append(LoteUrbano('edificio', 'suburbio', modelo, posicao, rotacao, tamanho, paleta))
            else:
                modelo = 'tree-small' if vaga == jardim else 'tree-large'
                grupo.append(LoteUrbano('arvore', 'suburbio', modelo, posicao, rotacao, .95))
        grupos.append(tuple(grupo))
    return CidadeVisual(no, ancora, centro, frente, area, perfil, via, ponto_na_via, tuple(grupos))


def _retangulo(a, b):
    return min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])


def _intersecta(a, b, margem=0.):
    return (a[0] <= b[2] + margem and a[2] >= b[0] - margem and
            a[1] <= b[3] + margem and a[3] >= b[1] - margem)


def planejar_cidades(mapa, meia_largura, meia_altura, agua=()):
    """Encaixa os lotes no espaço livre da malha viária já calculada."""
    ruas = [(par, a, b, _retangulo(a, b)) for par, caminho in mapa.eixos_pavimento.items()
            if par[0] < par[1] for a, b in zip(caminho, caminho[1:])]
    cidades = {}
    for no, ancora in mapa.posicoes.items():
        x, y, z = ancora
        vizinhanca = (x - 11, y - 11, x + 11, y + 11)
        vias = [r for r in ruas if _intersecta(vizinhanca, r[3])]
        acessos = [r for r in vias if no in r[0] and r[1][2] == r[2][2] == z]
        # A área de busca fica aquém da metade dos 18 u. entre âncoras.
        # Os conectores também são reservados para as cidades seguintes.
        reservas = [r.limites_xy for r in mapa.rotatorias]
        reservas.extend(cidade.limites_xy for cidade in cidades.values())
        reservas.extend(cidade.limites_acesso for cidade in cidades.values())
        dados = _melhor_lote(ancora, (meia_largura, meia_altura), vias, acessos, (*agua, *reservas))
        if dados is None:
            raise ValueError(f'Não há lote urbano com acesso para o nó {no}.')
        perfil, densidade = _PERFIS[(no - 1) % len(_PERFIS)]
        if no % 4 == 0:
            densidade = (densidade[0] - 1, densidade[1]) if densidade[0] > 4 else (4, 2)
        cidades[no] = gerar_cidade(no, mapa.chegadas[no], *dados, perfil=perfil, densidade=densidade)
    return cidades


def _melhor_lote(ancora, terreno, vias, acessos, reservas):
    px, py, pz = ancora
    melhor = None
    for comprimento, largura in _AREAS:
        for dx, dy in _DIRECOES:
            hx, hy = (comprimento / 2, largura / 2) if dx else (largura / 2, comprimento / 2)
            # Em volta de cada nó, alinha os lotes a uma grade de meio metro.
            for ix in range(-16, 17):
                x = px + ix / 2
                if abs(ix / 2) + hx > 8.6 or abs(x) + hx > terreno[0] - .85:
                    continue
                for iy in range(-16, 17):
                    y = py + iy / 2
                    if abs(iy / 2) + hy > 8.6 or abs(y) + hy > terreno[1] - .85:
                        continue
                    distancia = hypot(x - px, y - py)
                    if not 3.6 <= distancia <= 8.1:
                        continue
                    caixa = (x - hx, y - hy, x + hx, y + hy)
                    if (any(_intersecta(caixa, r[3], .74) for r in vias) or
                            any(_intersecta(caixa, r, .35) for r in reservas)):
                        continue
                    ex, ey = x + dx * hx, y + dy * hy
                    for via, _, _, (x0, y0, x1, y1) in acessos:
                        if dx and x0 == x1 and y0 + .20 <= ey <= y1 - .20:
                            folga = (x0 - ex) * dx
                        elif dy and y0 == y1 and x0 + .20 <= ex <= x1 - .20:
                            folga = (y0 - ey) * dy
                        else:
                            continue
                        if not .74 < folga <= 2.65:
                            continue
                        via_x, via_y = ex + dx * folga, ey + dy * folga
                        bx, by = via_x - dx * (_MEIA_RUA + .002), via_y - dy * (_MEIA_RUA + .002)
                        x0c, y0c, x1c, y1c = _retangulo((bx, by), (ex, ey))
                        conector = (x0c - abs(dy) * .27, y0c - abs(dx) * .27,
                                    x1c + abs(dy) * .27, y1c + abs(dx) * .27)
                        if (any(_intersecta(conector, r[3], _MEIA_RUA) for r in vias) or
                                any(_intersecta(conector, r, .27) for r in reservas)):
                            continue
                        # O acesso perto da chegada ajuda a ler a relação
                        # entre o pin e o bairro na vista isométrica.
                        nota = (distancia + .8 * hypot(via_x - px, via_y - py) + folga,
                                x, y, dx, dy, via, (via_x, via_y, pz))
                        if melhor is None or nota < melhor:
                            melhor = nota
        if melhor is not None:
            _, x, y, dx, dy, via, ponto = melhor
            return (x, y), (dx, dy), (largura, comprimento), via, ponto
    return None
