"""Roteamento visual ortogonal. Nenhuma célula desta malha é nó do grafo."""
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import combinations
from math import atan2, cos, hypot


PASSO = 1.5
RAIO_PRACA = 3.0
LARGURA_VIA = .95
ALTURA_RUA = .12
VAO_LIVRE = 1.4
ALTURA_PONTE = 1.65
RAMPA = 3.6
MEIO_TABULEIRO = .85
_DIRS = ((1, 0), (0, 1), (-1, 0), (0, -1))


class _SemRampa(ValueError):
    def __init__(self, celula, aresta, opcoes=()):
        self.celula, self.aresta, self.opcoes = celula, aresta, opcoes
        super().__init__(f"Cruzamento sem espaço para rampa: {celula}")


@dataclass(frozen=True)
class PracaVisual:
    no: int
    centro: tuple
    raio: float = RAIO_PRACA

    def contem(self, ponto, margem=0.):
        return (abs(ponto[0] - self.centro[0]) <= self.raio + margem and
                abs(ponto[1] - self.centro[1]) <= self.raio + margem)


@dataclass(frozen=True)
class PortaVisual:
    no: int
    vizinho: int
    posicao: tuple
    direcao: tuple


@dataclass(frozen=True)
class PonteVisual:
    aresta: tuple
    inferior: tuple
    centro: tuple
    inicio: tuple
    fim: tuple
    altura: float
    vao: float = VAO_LIVRE


@dataclass(frozen=True)
class RotasVisuais:
    caminhos: tuple
    pracas: tuple
    portas: tuple
    pontes: tuple
    expansoes: int = 0


def posicoes_planejadas(grafo):
    if len(grafo.ids) == 5 and set(grafo.ids) == set(range(1, 6)):
        return {1: (-18., 0., ALTURA_RUA), 2: (0., 16.5, ALTURA_RUA),
                3: (18., 0., ALTURA_RUA), 4: (0., 0., ALTURA_RUA),
                5: (0., -16.5, ALTURA_RUA)}
    if len(grafo.ids) == 18 and set(grafo.ids) == set(range(1, 19)):
        grade = {1: (0, 2), 2: (1, 3), 3: (2, 3), 4: (3, 3), 5: (4, 3),
                 6: (4, 2), 7: (5, 3), 8: (1, 2), 9: (2, 2), 10: (3, 2),
                 11: (5, 2), 12: (0, 1), 13: (2, 1), 14: (3, 1),
                 15: (4, 1), 16: (1, 0), 17: (3, 0), 18: (5, 0)}
        # A malha ampla reserva quarteirões entre prédios e deixa uma reta
        # suficiente para as rampas das passagens elevadas inevitáveis.
        return {no: ((c - 2.5) * 24, (l - 1.5) * 24, ALTURA_RUA)
                for no, (c, l) in grade.items()}
    return {n.id: ((n.x - .5) * 46, (.5 - n.y) * 38, ALTURA_RUA) for n in grafo.nos}


def _compactar(pontos):
    resultado = []
    for p in pontos:
        p = tuple(p)
        if resultado and p == resultado[-1]:
            continue
        if len(resultado) >= 2:
            a, b = resultado[-2:]
            ab, bc = tuple(b[i] - a[i] for i in range(3)), tuple(p[i] - b[i] for i in range(3))
            cruz = (ab[1]*bc[2]-ab[2]*bc[1], ab[2]*bc[0]-ab[0]*bc[2], ab[0]*bc[1]-ab[1]*bc[0])
            if max(abs(v) for v in cruz) < 1e-8 and sum(ab[i]*bc[i] for i in range(3)) > 0:
                resultado.pop()
        resultado.append(p)
    return tuple(resultado)


def _portas(grafo, posicoes):
    livres = {}
    for no,(x,y,z) in posicoes.items():
        livres[no] = []
        for dx,dy in _DIRS:
            for offset in (PASSO,-PASSO):
                xx,yy=x+dx*RAIO_PRACA-dy*offset,y+dy*RAIO_PRACA+dx*offset
                livres[no].append(PortaVisual(no,0,(round(xx/PASSO)*PASSO,round(yy/PASSO)*PASSO,z),(dx,dy)))
    resultado={}
    ordem=sorted(grafo.arestas,key=lambda e:(abs(posicoes[e.origem][0]-posicoes[e.destino][0])+abs(posicoes[e.origem][1]-posicoes[e.destino][1]),e.origem,e.destino))
    for e in ordem:
        u,v=e.origem,e.destino
        melhor=None
        for i,a in enumerate(livres[u]):
            for j,b in enumerate(livres[v]):
                ax,ay,_=a.posicao; bx,by,_=b.posicao
                custo=abs(ax-bx)+abs(ay-by)
                for origem,destino,porta in ((u,v,a),(v,u,b)):
                    dx=posicoes[destino][0]-posicoes[origem][0]
                    dy=posicoes[destino][1]-posicoes[origem][1]
                    custo+=max(0.,-(dx*porta.direcao[0]+dy*porta.direcao[1]))*8
                opostas=a.direcao==tuple(-n for n in b.direcao)
                reta=opostas and ((a.direcao[0] and ay==by) or (a.direcao[1] and ax==bx))
                custo+=0 if reta else 9 if a.direcao[0]!=b.direcao[0] and a.direcao[1]!=b.direcao[1] else 18
                if melhor is None or custo<melhor[0]:melhor=custo,i,j
        _,i,j=melhor
        a,b=livres[u].pop(i),livres[v].pop(j)
        resultado[u,v]=PortaVisual(u,v,a.posicao,a.direcao)
        resultado[v,u]=PortaVisual(v,u,b.posicao,b.direcao)
    return resultado


def _interior(centro, porta):
    x, y, z = centro
    px, py, _ = porta.posicao
    if porta.direcao[0]:
        return _compactar((centro, (x, py, z), porta.posicao))
    return _compactar((centro, (px, y, z), porta.posicao))


def _slots(no,centro):
    x,y,z=centro
    return tuple(PortaVisual(no,0,((round(x/PASSO)+dx*2-dy*offset)*PASSO,
                                   (round(y/PASSO)+dy*2+dx*offset)*PASSO,z),(dx,dy))
                 for dx,dy in _DIRS for offset in (-1,1))


def _buscar_portas(u, v, livres, bloqueados, usos, acessos, limites, *, permitir_cruzar=False):
    fontes,alvos=livres[u],livres[v]
    destinos={(round(p.posicao[0]/PASSO),round(p.posicao[1]/PASSO)):(i,(_DIRS.index(p.direcao)+2)%4)
              for i,p in enumerate(alvos)}
    acesso_destino={(round(p.posicao[0]/PASSO)+p.direcao[0],round(p.posicao[1]/PASSO)+p.direcao[1]):i
                    for i,p in enumerate(alvos)}
    fila=[]; custos={}; anteriores={}; exp=0
    for i,p in enumerate(fontes):
        x,y=round(p.posicao[0]/PASSO),round(p.posicao[1]/PASSO); d=_DIRS.index(p.direcao)
        chave=x,y,d,i; custos[chave]=0.; heappush(fila,(0.,0.,x,y,d,i))
    while fila:
        _,custo,x,y,d,origem=heappop(fila); estado=x,y,d,origem
        if custo!=custos.get(estado):continue
        exp+=1
        if (x,y) in destinos and d==destinos[x,y][1]:
            caminho=[(x,y)]
            while estado in anteriores:
                estado=anteriores[estado]; caminho.append(estado[:2])
            return tuple(reversed(caminho)),exp,fontes[origem],alvos[destinos[x,y][0]]
        fonte=fontes[origem]
        inicio=(round(fonte.posicao[0]/PASSO),round(fonte.posicao[1]/PASSO))
        acesso_inicio=inicio[0]+fonte.direcao[0],inicio[1]+fonte.direcao[1]
        for dd,(dx,dy) in enumerate(_DIRS):
            if dd==(d+2)%4 or ((x,y)==inicio and dd!=d) or (usos.get((x,y)) and dd!=d):continue
            xx,yy=x+dx,y+dy; p=xx,yy
            if not(limites[0]<=xx<=limites[2] and limites[1]<=yy<=limites[3]):continue
            if p in bloqueados and p not in destinos:continue
            if p in acessos and p!=acesso_inicio and p not in acesso_destino:continue
            if p in acesso_destino:
                alvo=alvos[acesso_destino[p]]
                if dd!=(_DIRS.index(alvo.direcao)+2)%4:continue
            outros=usos.get(p,())
            # A primeira malha não cruza ruas. A segunda tentativa é limitada
            # à rua sem saída e pode abrir uma ponte perpendicular.
            if outros and (not permitir_cruzar or len(outros) != 1 or
                           outros[0][1] == dd % 2 or outros[0][2]):
                continue
            novo=custo+1+(3 if dd!=d else 0)+(900 if outros else 0)
            chave=xx,yy,dd,origem
            if novo>=custos.get(chave,float('inf')):continue
            custos[chave]=novo; anteriores[chave]=x,y,d,origem
            h=min(abs(xx-tx)+abs(yy-ty) for tx,ty in destinos)
            heappush(fila,(novo+h,novo,xx,yy,dd,origem))
    raise ValueError(f"Sem corredor para {u,v}")


def _astar(inicio, fim, saida, chegada, bloqueados, usos, proibidos, limites):
    fila = [(0., 0., inicio[0], inicio[1], saida)]
    custos = {(inicio[0], inicio[1], saida): 0.}
    anteriores = {}
    expansoes = 0
    while fila:
        _, custo, x, y, direcao = heappop(fila)
        estado = x, y, direcao
        if custo != custos.get(estado):
            continue
        expansoes += 1
        if (x, y) == fim and direcao == chegada:
            caminho = [(x, y)]
            while estado in anteriores:
                estado = anteriores[estado]
                caminho.append(estado[:2])
            return tuple(reversed(caminho)), expansoes
        ocupacao = usos.get((x, y), ())
        for d, (dx, dy) in enumerate(_DIRS):
            if d == (direcao + 2) % 4:
                continue
            if (x, y) == inicio and d != saida:
                continue
            # Ao cruzar uma via, seguir reto: nunca criar uma bifurcação visual.
            if ocupacao and d != direcao:
                continue
            xx, yy = x + dx, y + dy
            if not (limites[0] <= xx <= limites[2] and limites[1] <= yy <= limites[3]):
                continue
            if (xx, yy) in proibidos or ((xx, yy) in bloqueados and (xx, yy) != fim):
                continue
            outros = usos.get((xx, yy), ())
            eixo = d % 2
            if outros and (len(outros) != 1 or outros[0][1] == eixo or outros[0][2]):
                continue
            novo_custo = custo + 1 + (1.8 if d != direcao else 0) + (900 if outros else 0)
            chave = xx, yy, d
            if novo_custo >= custos.get(chave, float('inf')):
                continue
            custos[chave] = novo_custo
            anteriores[chave] = x, y, direcao
            estimativa = abs(xx - fim[0]) + abs(yy - fim[1])
            heappush(fila, (novo_custo + estimativa, novo_custo, xx, yy, d))
    raise ValueError("Não há corredor livre para a rua; amplie o layout visual.")


def _passos(pontos):
    for i, p in enumerate(pontos):
        eixos = set()
        for q in pontos[max(0, i-1):i] + pontos[i+1:i+2]:
            eixos.add(0 if p[0] != q[0] else 1)
        yield p, next(iter(eixos)), len(eixos) > 1


def _w5(grafo, posicoes):
    # Os quatro lados são derivados das posições recebidas. Assim uma cena
    # pode ser reorganizada sem reintroduzir coordenadas fixas na geometria.
    p1, p2, p3, p5 = (posicoes[no] for no in (1, 2, 3, 5))
    cantos = {(1, 2): (p1[0], p2[1], ALTURA_RUA),
              (2, 3): (p3[0], p2[1], ALTURA_RUA),
              (3, 5): (p3[0], p5[1], ALTURA_RUA),
              (1, 5): (p1[0], p5[1], ALTURA_RUA)}
    caminhos = []
    for e in grafo.arestas:
        par = tuple(sorted((e.origem, e.destino)))
        pontos = [posicoes[e.origem]]
        if par in cantos:
            pontos.append(cantos[par])
        pontos.append(posicoes[e.destino])
        caminhos.append(((e.origem, e.destino), tuple(pontos)))
    return RotasVisuais(tuple(caminhos), tuple(PracaVisual(n, p) for n, p in posicoes.items()), (), ())


def rotear(grafo, posicoes, construcoes, *, w5=False):
    if w5:
        return _w5(grafo, posicoes)
    portas = {}
    livres={no:list(_slots(no,p)) for no,p in posicoes.items()}
    pracas = tuple(PracaVisual(n, p) for n, p in posicoes.items())
    limites = (int(min(p[0] for p in posicoes.values()) / PASSO) - 10,
               int(min(p[1] for p in posicoes.values()) / PASSO) - 10,
               int(max(p[0] for p in posicoes.values()) / PASSO) + 10,
               int(max(p[1] for p in posicoes.values()) / PASSO) + 10)
    bloqueados = set()
    for x in range(limites[0], limites[2] + 1):
        for y in range(limites[1], limites[3] + 1):
            p = x * PASSO, y * PASSO
            if any(praca.contem(p, .2) for praca in pracas):
                bloqueados.add((x, y))
                continue
            for c in construcoes.values():
                x0, y0, x1, y1 = c.limites_xy
                if x0 - .7 <= p[0] <= x1 + .7 and y0 - .7 <= p[1] <= y1 + .7:
                    bloqueados.add((x, y))
                    break
    usos, roteadas, expansoes, passos_por_par = {}, {}, 0, {}
    acessos = {}
    for no, slots in livres.items():
      for porta in slots:
        x, y = round(porta.posicao[0]/PASSO), round(porta.posicao[1]/PASSO)
        dx, dy = porta.direcao
        acessos.setdefault((x+dx,y+dy),set()).add(no)
    # Os hubs de grau alto escolhem seus portões antes das ruas periféricas.
    # Ordenar só por distância consumia os oito encaixes de 4 e 14 e podia
    # deixar a ligação entre eles sem saída.
    graus = {no: len(vizinhos) for no, vizinhos in grafo.adjacencia().items()}
    ordem = sorted(
        grafo.arestas,
        key=lambda e: (-max(graus[e.origem], graus[e.destino]),
                       -(graus[e.origem] + graus[e.destino]),
                       abs(posicoes[e.origem][0] - posicoes[e.destino][0]) +
                       abs(posicoes[e.origem][1] - posicoes[e.destino][1]),
                       e.origem, e.destino),
    )
    for e in ordem:
        par = e.origem, e.destino
        # A* não precisa varrer a cidade inteira para a maioria das ruas.
        # O corredor local inclui um quarteirão de desvio; somente a última
        # tentativa abre os limites globais para uma passagem elevada.
        pu, pv = posicoes[par[0]], posicoes[par[1]]
        margem = 12
        limites_locais = (
            max(limites[0], int(min(pu[0], pv[0]) / PASSO) - margem),
            max(limites[1], int(min(pu[1], pv[1]) / PASSO) - margem),
            min(limites[2], int(max(pu[0], pv[0]) / PASSO) + margem),
            min(limites[3], int(max(pu[1], pv[1]) / PASSO) + margem),
        )
        try:
            passos,n,a,b=_buscar_portas(*par,livres,bloqueados,usos,acessos,limites_locais)
        except ValueError:
            try:
                passos,n,a,b=_buscar_portas(*par,livres,bloqueados,usos,acessos,limites_locais,
                                             permitir_cruzar=True)
            except ValueError:
                # Esta é a única forma de introduzir um cruzamento em nível
                # diferente; as ruas que já cabem na malha permanecem no solo.
                passos,n,a,b=_buscar_portas(*par,livres,bloqueados,usos,acessos,limites,
                                             permitir_cruzar=True)
        livres[par[0]].remove(a); livres[par[1]].remove(b)
        a=PortaVisual(par[0],par[1],a.posicao,a.direcao)
        b=PortaVisual(par[1],par[0],b.posicao,b.direcao)
        portas[par],portas[par[::-1]]=a,b
        inicio = round(a.posicao[0]/PASSO), round(a.posicao[1]/PASSO)
        fim = round(b.posicao[0]/PASSO), round(b.posicao[1]/PASSO)
        saida, chegada = _DIRS.index(a.direcao), (_DIRS.index(b.direcao) + 2) % 4
        expansoes += n
        pontos = list(_interior(posicoes[e.origem], a))
        pontos.extend((x*PASSO, y*PASSO, ALTURA_RUA) for x,y in passos)
        pontos.extend(reversed(_interior(posicoes[e.destino], b)))
        roteadas[par] = _compactar(pontos)
        passos_por_par[par] = passos
        for celula, eixo, curva in _passos(passos):
            usos.setdefault(celula, []).append((par, eixo, curva))
    proibidos_por_par = {}
    for tentativa in range(80):
        cruzamentos = [(celula, ocupacao) for celula, ocupacao in usos.items() if len(ocupacao) == 2]
        try:
            caminhos, pontes = _pontes(roteadas, cruzamentos, pracas)
            break
        except _SemRampa as conflito:
            par, (cx, cy) = conflito.aresta, conflito.celula
            proibidos = proibidos_por_par.setdefault(par,set())
            proibidos.add((cx,cy))
            usos = {}
            for outra, passos in passos_por_par.items():
                if outra != par:
                    for celula,eixo,curva in _passos(passos):
                        usos.setdefault(celula,[]).append((outra,eixo,curva))
            a,b = portas[par],portas[par[::-1]]
            inicio = round(a.posicao[0]/PASSO),round(a.posicao[1]/PASSO)
            fim = round(b.posicao[0]/PASSO),round(b.posicao[1]/PASSO)
            acesso_proprio={(inicio[0]+a.direcao[0],inicio[1]+a.direcao[1]),(fim[0]+b.direcao[0],fim[1]+b.direcao[1])}
            acesso_alheio = set(acessos)-acesso_proprio
            try:
                passos,n = _astar(inicio,fim,_DIRS.index(a.direcao),(_DIRS.index(b.direcao)+2)%4,
                                  bloqueados,usos,proibidos|acesso_alheio,limites)
            except ValueError as erro:
                raise ValueError(f"Rua {par}, desvio {conflito.celula}, opções {conflito.opcoes}: {erro}") from erro
            expansoes += n
            pontos = list(_interior(posicoes[par[0]],a))
            pontos.extend((x*PASSO,y*PASSO,ALTURA_RUA) for x,y in passos)
            pontos.extend(reversed(_interior(posicoes[par[1]],b)))
            roteadas[par] = _compactar(pontos)
            passos_por_par[par] = passos
            for celula,eixo,curva in _passos(passos):
                usos.setdefault(celula,[]).append((par,eixo,curva))
    else:
        raise ValueError("Não foi possível reservar rampas locais sem conflitos.")
    return RotasVisuais(tuple(caminhos.items()), pracas, tuple(portas.values()), tuple(pontes), expansoes)


def _pontes(roteadas, cruzamentos, pracas):
    # Uma ponte cabe somente numa reta com rampas livres dos nós e das curvas.
    necessidades = {}
    pontes = []
    for (cx, cy), ocupacao in cruzamentos:
        x, y = cx*PASSO, cy*PASSO
        candidatos = []
        for par, _, _ in ocupacao:
            for i, (a,b) in enumerate(zip(roteadas[par], roteadas[par][1:])):
                if (min(a[0],b[0])-1e-8 <= x <= max(a[0],b[0])+1e-8 and
                        min(a[1],b[1])-1e-8 <= y <= max(a[1],b[1])+1e-8):
                    livre = min(hypot(x-a[0],y-a[1]), hypot(x-b[0],y-b[1]))
                    # O trecho interno da praça nunca pode virar rampa.
                    for praca in pracas:
                        if praca.no in par:
                            livre = min(livre, max(abs(x-praca.centro[0]),abs(y-praca.centro[1])) - praca.raio)
                    candidatos.append((livre, par, i, a, b))
        livre, superior, indice, a, b = max(candidatos)
        if livre < RAMPA + MEIO_TABULEIRO:
            raise _SemRampa((cx,cy),ocupacao[-1][0],tuple((v,p) for v,p,*_ in candidatos))
        inferior = next(par for par, _, _ in ocupacao if par != superior)
        comprimento = hypot(b[0]-a[0], b[1]-a[1])
        t = hypot(x-a[0],y-a[1])
        necessidades.setdefault((superior, indice), []).append((t-MEIO_TABULEIRO, t+MEIO_TABULEIRO))
        dx,dy = (b[0]-a[0])/comprimento, (b[1]-a[1])/comprimento
        inicio = x-dx*(RAMPA+MEIO_TABULEIRO), y-dy*(RAMPA+MEIO_TABULEIRO), ALTURA_RUA
        fim = x+dx*(RAMPA+MEIO_TABULEIRO), y+dy*(RAMPA+MEIO_TABULEIRO), ALTURA_RUA
        pontes.append(PonteVisual(superior,inferior,(x,y,ALTURA_RUA+ALTURA_PONTE),inicio,fim,ALTURA_PONTE))
    caminhos = {}
    for par, pontos in roteadas.items():
        novo = [pontos[0]]
        for i,(a,b) in enumerate(zip(pontos,pontos[1:])):
            intervalos = sorted(necessidades.get((par,i),()))
            unidos = []
            for inicio,fim in intervalos:
                if unidos and inicio-RAMPA <= unidos[-1][1]+RAMPA:
                    unidos[-1] = unidos[-1][0], max(unidos[-1][1],fim)
                else:
                    unidos.append((inicio,fim))
            comprimento = hypot(b[0]-a[0],b[1]-a[1])
            for inicio,fim in unidos:
                for s,h in ((inicio-RAMPA,0),(inicio,ALTURA_PONTE),(fim,ALTURA_PONTE),(fim+RAMPA,0)):
                    t=s/comprimento
                    novo.append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,ALTURA_RUA+h))
            novo.append(b)
        caminhos[par] = _compactar(novo)
    return caminhos,pontes
