"""Algoritmos de grafos independentes do renderizador e da animação.

``executar`` pode rodar em uma thread de trabalho. O callback de progresso recebe
instantâneos independentes; a interface deve enfileirá-los e reproduzi-los na
thread do Pygame. Caminhos publicados sempre usam arestas do grafo original.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from heapq import heappop, heappush
from itertools import permutations
from math import inf, isfinite
from time import perf_counter
from typing import Callable, Protocol


class GrafoAlgoritmo(Protocol):
    ids: tuple[int, ...]

    def adjacencia(self) -> dict[int, dict[int, float]]: ...


@dataclass(frozen=True)
class Progresso:
    fase: str
    caminho: tuple[int, ...] = ()
    custo: float | None = None
    explorados: tuple[int, ...] = ()
    distancias: dict[int, float] = field(default_factory=dict)
    candidatas: int = 0


@dataclass(frozen=True)
class Resultado:
    caminho: tuple[int, ...]
    custo: float | None
    garantia: str
    termino: str
    tempo_ms: float
    explorados: tuple[int, ...] = ()
    distancias: dict[int, float] = field(default_factory=dict)
    candidatas: int = 0
    ordem_visita: tuple[int, ...] = ()
    indices_visita: tuple[int, ...] = ()
    circuitos_validos: int = 0


class _Cancelado(Exception):
    pass


class _Execucao:
    def __init__(self, cancelar, progresso, garantia):
        self.inicio = perf_counter()
        self.cancelar = cancelar
        self.progresso = progresso
        self.garantia = garantia
        self.caminho: tuple[int, ...] = ()
        self.custo: float | None = None
        self.explorados: tuple[int, ...] = ()
        self.distancias: dict[int, float] = {}
        self.candidatas = 0
        self.circuitos_validos = 0
        self.ordem_visita: tuple[int, ...] = ()
        self.indices_visita: tuple[int, ...] = ()

    def verificar(self):
        if self.cancelar is None:
            return
        sinal = self.cancelar() if callable(self.cancelar) else self.cancelar.is_set()
        if sinal:
            raise _Cancelado

    def emitir(self, fase, caminho=None, custo=None, explorados=None, distancias=None):
        if self.progresso is not None:
            self.progresso(Progresso(
                fase=fase,
                caminho=self.caminho if caminho is None else tuple(caminho),
                custo=self.custo if caminho is None and custo is None else custo,
                explorados=self.explorados if explorados is None else tuple(explorados),
                distancias=dict(self.distancias if distancias is None else distancias),
                candidatas=self.candidatas,
            ))

    def resultado(self, termino):
        if termino == "cancelado":
            self.garantia = "busca cancelada, sem garantia de ótimo"
        self.emitir(termino)
        return Resultado(
            self.caminho, self.custo, self.garantia, termino,
            (perf_counter() - self.inicio) * 1000,
            self.explorados, dict(self.distancias), self.candidatas,
            self.ordem_visita, self.indices_visita, self.circuitos_validos,
        )

    def definir_percurso(self, caminho, adj, *, ordem=None, indices=None):
        self.caminho = tuple(caminho)
        self.custo = sum(adj[a][b] for a, b in zip(caminho, caminho[1:]))
        self.ordem_visita = self.caminho if ordem is None else tuple(ordem)
        self.indices_visita = tuple(range(len(caminho))) if indices is None else tuple(indices)


def _adjacencia_validada(grafo):
    ids = tuple(grafo.ids)
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("O grafo deve possuir nós distintos e não pode ser vazio.")
    original = grafo.adjacencia()
    if set(original) != set(ids):
        raise ValueError("A adjacência deve incluir exatamente os nós do grafo.")
    adj = {}
    for origem in ids:
        adj[origem] = {}
        for destino, peso in original[origem].items():
            if destino not in original:
                raise ValueError("Aresta aponta para um nó inexistente.")
            peso = float(peso)
            if not isfinite(peso) or peso < 0:
                raise ValueError("Dijkstra requer pesos finitos e não negativos.")
            adj[origem][destino] = peso
    return ids, adj


def _reconstituir(anteriores, origem, destino):
    caminho = [destino]
    while caminho[-1] != origem:
        anterior = anteriores.get(caminho[-1])
        if anterior is None:
            return ()
        caminho.append(anterior)
    return tuple(reversed(caminho))


def _dijkstra(adj, origem, destino, estado, fase="dijkstra"):
    distancias = dict.fromkeys(adj, inf)
    distancias[origem] = 0.0
    anteriores = {}
    explorados = []
    fechados = set()
    fila = [(0.0, origem)]
    while fila:
        estado.verificar()
        distancia, atual = heappop(fila)
        if atual in fechados:
            continue
        fechados.add(atual)
        explorados.append(atual)
        if atual != destino:
            for vizinho, peso in sorted(adj[atual].items()):
                estado.verificar()
                nova = distancia + peso
                if nova < distancias[vizinho]:
                    distancias[vizinho] = nova
                    anteriores[vizinho] = atual
                    heappush(fila, (nova, vizinho))
        estado.explorados = tuple(explorados)
        estado.distancias = dict(distancias)
        estado.emitir(fase, _reconstituir(anteriores, origem, atual), distancia)
        estado.verificar()
        if atual == destino:
            break
    return distancias, anteriores


def _forca(ids, adj, origem, estado):
    if len(ids) > 9:
        raise ValueError("Força bruta é permitida somente para grafos de até 9 nós.")
    if len(ids) == 1:
        estado.definir_percurso((origem,), adj)
        estado.candidatas = 1
        estado.circuitos_validos = 1
        estado.emitir("enumeracao")
        return
    outros = tuple(no for no in ids if no != origem)
    for ordem in permutations(outros):
        estado.verificar()
        estado.candidatas += 1
        caminho = (origem,) + ordem + (origem,)
        custo = 0.0
        for a, b in zip(caminho, caminho[1:]):
            if b not in adj[a]:
                break
            custo += adj[a][b]
        else:
            estado.circuitos_validos += 1
            if estado.custo is None or custo < estado.custo:
                estado.definir_percurso(caminho, adj)
            estado.emitir("enumeracao", caminho, custo)
            continue
        # Não publicar uma candidata com uma conexão inexistente.
        if estado.candidatas % 256 == 0:
            estado.emitir("enumeracao")
    estado.explorados = ids if estado.caminho else ()


def _circuito(ids, adj, origem, estado):
    """Busca exata em ruas diretas, com poda e desempate por ID."""
    if len(ids) > 18:
        raise ValueError("Circuito exato é permitido somente para grafos de até 18 nós.")
    if any(adj[v].get(u) != peso for u in ids for v, peso in adj[u].items()):
        raise ValueError("O circuito exato requer um grafo não direcionado.")
    if len(ids) <= 2:
        _forca(ids, adj, origem, estado)
        return
    if any(len(adj[u]) < 2 for u in ids):
        return

    bits = {u: 1 << i for i, u in enumerate(ids)}
    vizinhos = {u: tuple((v, p, bits[v]) for v, p in sorted(adj[u].items())) for u in ids}
    menores = {u: sorted(adj[u].values())[:2] for u in ids}
    meia_soma = {u: sum(menores[u]) / 2 for u in ids}
    prefixos = {}
    caminho = [origem]

    def buscar(atual, restantes, custo, limite_restante):
        estado.verificar()
        if not restantes:
            volta = adj[atual].get(origem)
            if volta is not None:
                estado.candidatas += 1
                if estado.custo is None or custo + volta < estado.custo:
                    estado.definir_percurso((*caminho, origem), adj)
                    estado.emitir("circuito")
            return
        # Cada nó pendente precisa de duas ruas. A origem e o nó atual
        # ainda precisam de uma rua cada. Essa soma nunca excede o custo real.
        limite = custo + limite_restante + (menores[origem][0] + menores[atual][0]) / 2
        if estado.custo is not None and limite > estado.custo + 1e-9:
            return
        chave = atual, restantes
        if custo >= prefixos.get(chave, inf):
            return
        prefixos[chave] = custo
        for proximo, peso, bit in vizinhos[atual]:
            if restantes & bit:
                caminho.append(proximo)
                buscar(proximo, restantes ^ bit, custo + peso, limite_restante - meia_soma[proximo])
                caminho.pop()

    restantes = ((1 << len(ids)) - 1) ^ bits[origem]
    buscar(origem, restantes, 0., sum(meia_soma[u] for u in ids if u != origem))
    estado.explorados = ids if estado.caminho else ()


def _heuristica(ids, adj, origem, estado):
    def calcular_matriz(reservar_origem):
        matriz, caminhos = {}, {}
        sem_saida = adj | {origem: {}} if reservar_origem else adj
        for inicio in ids:
            estado.verificar()
            consulta = adj if inicio == origem else sem_saida
            distancias, anteriores = _dijkstra(consulta, inicio, None, estado, "matriz")
            if any(not isfinite(distancias[fim]) for fim in ids):
                return None
            matriz[inicio] = distancias
            caminhos[inicio] = {fim: _reconstituir(anteriores, inicio, fim) for fim in ids}
        return matriz, caminhos

    # Entre entregas, Dijkstra pode chegar à origem, mas não sair dela.
    # Grafos em que a origem é passagem obrigatória precisam do fecho original.
    dados = calcular_matriz(True) or calcular_matriz(False)
    if dados is None:
        return
    matriz, caminhos = dados
    estado.distancias = dict(matriz[origem])

    def expandir(ordem):
        resultado = [ordem[0]]
        entregas = [0]
        for a, b in zip(ordem, ordem[1:]):
            resultado.extend(caminhos[a][b][1:])
            entregas.append(len(resultado) - 1)
        return tuple(resultado), entregas

    def registrar(ordem):
        caminho, entregas = expandir(ordem)
        estado.definir_percurso(caminho, adj, ordem=ordem, indices=entregas)

    def custo_real(caminho):
        return sum(adj[a][b] for a, b in zip(caminho, caminho[1:]))

    ordem = [origem]
    restantes = set(ids) - {origem}
    while restantes:
        estado.verificar()
        proximo = min(restantes, key=lambda no: (matriz[ordem[-1]][no], no))
        ordem.append(proximo)
        restantes.remove(proximo)
        parcial, _ = expandir(ordem)
        estado.emitir("vizinho_proximo", parcial, custo_real(parcial))
    ordem.append(origem)
    registrar(ordem)
    estado.candidatas = 1
    estado.emitir("vizinho_proximo")
    custo_ordem = lambda rota: sum(matriz[a][b] for a, b in zip(rota, rota[1:]))
    melhor_custo = custo_ordem(ordem)
    melhorou = True
    while melhorou:
        melhorou = False
        for inicio in range(1, len(ordem) - 2):
            for fim in range(inicio + 1, len(ordem) - 1):
                estado.verificar()
                candidata = ordem[:inicio] + ordem[inicio:fim + 1][::-1] + ordem[fim + 1:]
                custo = custo_ordem(candidata)
                estado.candidatas += 1
                if custo < melhor_custo:
                    ordem, melhor_custo = candidata, custo
                    registrar(ordem)
                    estado.emitir("2-opt")
                    melhorou = True
                    break
                if estado.candidatas % 32 == 0:
                    estado.emitir("2-opt")
            if melhorou:
                break
    estado.verificar()
    if set(estado.caminho) != set(ids) or estado.caminho[0] != estado.caminho[-1]:
        raise RuntimeError("A heurística produziu um circuito incompleto.")
    estado.emitir("expansao")


def executar(
    metodo: str,
    grafo: GrafoAlgoritmo,
    origem: int,
    destino: int | None = None,
    *,
    cancelar=None,
    progresso: Callable[[Progresso], None] | None = None,
) -> Resultado:
    """Execute ``forca``, ``circuito`` exato, ``dijkstra`` (A→B) ou ``heuristica``.

    ``cancelar`` aceita uma função booleana ou ``threading.Event``. Um resultado
    cancelado pode conter o melhor circuito completo encontrado até a parada.
    Distâncias infinitas identificam nós ainda inalcançáveis; durante Dijkstra,
    somente as distâncias dos nós explorados são definitivas. ``candidatas``
    conta permutações examinadas ou circuitos avaliados pela heurística.
    """
    garantias = {
        "forca": "ótimo global",
        "circuito": "ótimo global entre circuitos hamiltonianos",
        "dijkstra": "caminho mínimo",
        "heuristica": "heurística, sem garantia de ótimo global",
    }
    if metodo not in garantias:
        raise ValueError(f"Método desconhecido: {metodo!r}.")
    estado = _Execucao(cancelar, progresso, garantias[metodo])
    ids, adj = _adjacencia_validada(grafo)
    if origem not in adj:
        raise ValueError("Nó de origem inexistente.")
    if metodo == "dijkstra" and destino not in adj:
        raise ValueError("Dijkstra requer um nó de destino existente.")
    try:
        estado.verificar()
        if metodo == "forca":
            _forca(ids, adj, origem, estado)
        elif metodo == "circuito":
            _circuito(ids, adj, origem, estado)
        elif metodo == "dijkstra":
            distancias, anteriores = _dijkstra(adj, origem, destino, estado)
            if isfinite(distancias[destino]):
                caminho = _reconstituir(anteriores, origem, destino)
                indices = (0,) if origem == destino else (0, len(caminho) - 1)
                estado.definir_percurso(caminho, adj, ordem=tuple(caminho[i] for i in indices),
                                        indices=indices)
        else:
            _heuristica(ids, adj, origem, estado)
        estado.verificar()
    except _Cancelado:
        return estado.resultado("cancelado")
    return estado.resultado("concluido" if estado.custo is not None else "sem_solucao")
