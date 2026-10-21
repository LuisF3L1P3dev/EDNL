"""Alturas e encaixes visuais das vias, sem modificar o grafo da missão."""
import math

LARGURA_VIA = 2.0
ALTURA_PISO = .08


class PerfilViario:
    def __init__(self, cenario):
        self.cenario = cenario
        self.limite = (cenario.lado - 1) * cenario.espacamento / 2
        self.pontes = []
        for a, b, dados in cenario.grafo.edges(data=True):
            if not dados["ponte"]:
                continue
            pontos = dados["pontos"]
            p, q = pontos[0], pontos[-1]
            comprimento = math.hypot(q[0] - p[0], q[2] - p[2])
            ux, uz = (q[0] - p[0]) / comprimento, (q[2] - p[2]) / comprimento
            perfil = [((v[0] - p[0]) * ux + (v[2] - p[2]) * uz, v[1]) for v in pontos]
            self.pontes.append((p, q, comprimento, ux, uz, perfil))

    def terreno(self, x, z):
        c = self.cenario
        fx, fz = (x + self.limite) / c.espacamento, (z + self.limite) / c.espacamento
        coluna = max(0, min(c.lado - 2, math.floor(fx)))
        linha = max(0, min(c.lado - 2, math.floor(fz)))
        tx, tz = fx - coluna, fz - linha
        alturas = [c.posicao(linha * c.lado + coluna)[1],
                   c.posicao(linha * c.lado + coluna + 1)[1],
                   c.posicao((linha + 1) * c.lado + coluna)[1],
                   c.posicao((linha + 1) * c.lado + coluna + 1)[1]]
        sul = alturas[0] * (1 - tx) + alturas[1] * tx
        norte = alturas[2] * (1 - tx) + alturas[3] * tx
        return sul * (1 - tz) + norte * tz

    def altura(self, x, z):
        altura = self.terreno(x, z)
        raio = LARGURA_VIA / 2
        for p, q, comprimento, ux, uz, perfil in self.pontes:
            s = (x - p[0]) * ux + (z - p[2]) * uz
            lateral = abs(-(x - p[0]) * uz + (z - p[2]) * ux)
            if not 0 < s < comprimento or lateral >= raio * 2:
                continue
            for (inicio, y0), (fim, y1) in zip(perfil, perfil[1:]):
                if inicio <= s <= fim:
                    y = y0 + (y1 - y0) * (s - inicio) / (fim - inicio)
                    base = p[1] + (q[1] - p[1]) * s / comprimento
                    # A faixa central segue exatamente a ponte do grafo. A
                    # transição lateral mantém contínuos os acessos nas margens.
                    peso = min(1., (raio * 2 - lateral) / raio)
                    altura += (y - base) * peso
                    break
        return altura

    def normal(self, x, z, normal):
        delta = .0001
        gx = (self.altura(x + delta, z) - self.altura(x - delta, z)) / (2 * delta)
        gz = (self.altura(x, z + delta) - self.altura(x, z - delta)) / (2 * delta)
        nx, ny, nz = normal
        vetor = (nx - gx * ny, ny, nz - gz * ny)
        tamanho = max(1e-12, math.sqrt(sum(v * v for v in vetor)))
        return tuple(v / tamanho for v in vetor)

    def cortes(self, eixo, minimo, maximo):
        c = self.cenario
        valores = [-self.limite + i * c.espacamento for i in range(c.lado)]
        for p, q, comprimento, ux, uz, perfil in self.pontes:
            if abs(ux) > .99:
                novos = (p[0] + ux * s for s, _ in perfil) if eixo == 0 else (p[2] + d for d in (-2, -1, 1, 2))
            else:
                novos = (p[2] + uz * s for s, _ in perfil) if eixo == 2 else (p[0] + d for d in (-2, -1, 1, 2))
            valores.extend(novos)
        return sorted({v for v in valores if minimo + 1e-6 < v < maximo - 1e-6})


def recortar_poligono(poligono, eixo, limite, manter_menor):
    """Recorta posições e interpola também UVs/normais de cada novo vértice."""
    saida = []
    anterior = poligono[-1]
    dentro_anterior = anterior[eixo] <= limite if manter_menor else anterior[eixo] >= limite
    for atual in poligono:
        dentro = atual[eixo] <= limite if manter_menor else atual[eixo] >= limite
        if dentro != dentro_anterior:
            t = (limite - anterior[eixo]) / (atual[eixo] - anterior[eixo])
            novo = tuple(a + (b - a) * t for a, b in zip(anterior, atual))
            saida.append(novo)
        if dentro:
            saida.append(atual)
        anterior, dentro_anterior = atual, dentro
    return saida


def dividir_triangulo(triangulo, cortes_x, cortes_z):
    partes = [triangulo]
    for eixo, cortes in ((0, cortes_x), (2, cortes_z)):
        for limite in cortes:
            novas = []
            for poligono in partes:
                valores = [p[eixo] for p in poligono]
                if min(valores) < limite - 1e-7 and max(valores) > limite + 1e-7:
                    novas.extend(p for p in (recortar_poligono(poligono, eixo, limite, True),
                                             recortar_poligono(poligono, eixo, limite, False)) if len(p) >= 3)
                else:
                    novas.append(poligono)
            partes = novas
    for poligono in partes:
        for i in range(1, len(poligono) - 1):
            yield poligono[0], poligono[i], poligono[i + 1]


ABERTURAS = {
    "road-crossroad-path": {(1, 0), (-1, 0), (0, 1), (0, -1)},
    "road-intersection-path": {(1, 0), (-1, 0), (0, -1)},
    "road-bend-square": {(-1, 0), (0, -1)},
    "road-straight": {(1, 0), (-1, 0)},
    "road-end": {(1, 0)},
    "road-square": set(),
}


def escolher_cruzamento(direcoes):
    """Orienta o módulo pelas conexões reais, sem desenhar saídas inexistentes."""
    direcoes = set(direcoes)
    for nome, aberturas in ABERTURAS.items():
        for quarto in range(4):
            giradas = set()
            for x, z in aberturas:
                for _ in range(quarto):
                    x, z = z, -x
                giradas.add((x, z))
            if giradas == direcoes:
                return nome, quarto * 90
    raise ValueError(f"Cruzamento sem módulo compatível: {direcoes}.")
