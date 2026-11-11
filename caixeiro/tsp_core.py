"""Grafos, validação e caminhos mínimos, sem dependência da interface Pygame.

Mapas pendentes podem ser carregados para desenho. A adjacência numérica só
é disponibilizada após exigir_validado(), sem inventar pesos ou ligações.
"""

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import permutations
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


Peso = int | float


class ErroGrafo(ValueError):
    """Erro de dados ou de disponibilidade de um grafo para cálculo."""


class GrafoInvalidoError(ErroGrafo):
    """Arquivo, estrutura ou valores incompatíveis com o cadastro."""


class MapaNaoValidadoError(ErroGrafo):
    """Mapa ainda não autorizado pelos dados para uso em algoritmos."""


class LimiteTSPError(ErroGrafo):
    """Instância acima do limite seguro da busca didática."""


def _numero_finito(valor: object) -> bool:
    # bool é subclasse de int em Python, mas não representa um peso ou posição.
    return type(valor) is int or (type(valor) is float and math.isfinite(valor))


def _texto(valor: object, campo: str, *, vazio: bool = False) -> None:
    if not isinstance(valor, str) or (not vazio and not valor.strip()):
        raise GrafoInvalidoError(f"{campo}: esperado texto{' não vazio' if not vazio else ''}.")


def _id_valido(valor: object, campo: str) -> None:
    if type(valor) is not int or valor <= 0:
        raise GrafoInvalidoError(f"{campo}: esperado ID inteiro positivo.")


@dataclass(frozen=True, slots=True)
class No:
    id: int
    x: float
    y: float

    def __post_init__(self) -> None:
        _id_valido(self.id, "Nó.id")
        for eixo, valor in (("x", self.x), ("y", self.y)):
            if not _numero_finito(valor) or not 0 <= valor <= 1:
                raise GrafoInvalidoError(
                    f"Nó {self.id}.{eixo}: coordenada deve ser finita e estar entre 0 e 1."
                )


@dataclass(frozen=True, slots=True)
class Aresta:
    origem: int
    destino: int
    peso: Peso | None
    observacao: str = ""

    def __post_init__(self) -> None:
        _id_valido(self.origem, "Aresta.origem")
        _id_valido(self.destino, "Aresta.destino")
        if self.origem == self.destino:
            raise GrafoInvalidoError(f"Aresta {self.origem}-{self.destino}: laços não são aceitos.")
        if self.peso is not None and (not _numero_finito(self.peso) or self.peso < 0):
            raise GrafoInvalidoError(
                f"Aresta {self.origem}-{self.destino}: peso deve ser numérico, finito e não negativo."
            )
        _texto(self.observacao, "Aresta.observacao", vazio=True)


@dataclass(frozen=True, slots=True)
class Grafo:
    id: str
    nome: str
    direcionado: bool
    validado: bool
    referencia: str
    sistema_coordenadas: str
    nos: tuple[No, ...]
    arestas: tuple[Aresta, ...]
    pendencias: tuple[str, ...] = ()
    observacoes: str = ""

    def __post_init__(self) -> None:
        for campo in ("id", "nome", "referencia"):
            _texto(getattr(self, campo), campo)
        _texto(self.observacoes, "observacoes", vazio=True)
        if self.direcionado is not False:
            raise GrafoInvalidoError("direcionado deve ser false: somente grafos não direcionados são aceitos.")
        if type(self.validado) is not bool:
            raise GrafoInvalidoError("validado deve ser um booleano.")
        if self.sistema_coordenadas != "normalizadas_0_1":
            raise GrafoInvalidoError("sistema_coordenadas deve ser normalizadas_0_1.")
        if not isinstance(self.nos, tuple) or not self.nos or not all(isinstance(no, No) for no in self.nos):
            raise GrafoInvalidoError("nos deve conter uma tupla não vazia de objetos No.")
        if not isinstance(self.arestas, tuple) or not all(isinstance(a, Aresta) for a in self.arestas):
            raise GrafoInvalidoError("arestas deve ser uma tupla de objetos Aresta.")
        if not isinstance(self.pendencias, tuple):
            raise GrafoInvalidoError("pendencias deve ser uma tupla de textos.")
        for pendencia in self.pendencias:
            _texto(pendencia, "pendencias")

        ids = {no.id for no in self.nos}
        if len(ids) != len(self.nos):
            raise GrafoInvalidoError("IDs de nós duplicados.")
        pares = set()
        for aresta in self.arestas:
            par = tuple(sorted((aresta.origem, aresta.destino)))
            if not {aresta.origem, aresta.destino} <= ids:
                raise GrafoInvalidoError(f"Aresta {par[0]}-{par[1]} referencia nó inexistente.")
            if par in pares:
                raise GrafoInvalidoError(f"Aresta não direcionada duplicada: {par[0]}-{par[1]}.")
            pares.add(par)
        if self.validado and (self.pendencias or any(a.peso is None for a in self.arestas)):
            raise GrafoInvalidoError("Mapa marcado como validado contém pendências ou peso desconhecido.")

    @property
    def ids(self) -> tuple[int, ...]:
        return tuple(no.id for no in self.nos)

    def exigir_validado(self) -> None:
        """Guarda chamada na entrada dos algoritmos."""
        if not self.validado:
            detalhes = list(self.pendencias)
            desconhecidas = [f"{a.origem}-{a.destino}" for a in self.arestas if a.peso is None]
            if desconhecidas:
                detalhes.append(f"Peso desconhecido: {', '.join(desconhecidas)}.")
            motivo = " ".join(detalhes) or "Auditoria ainda não concluída."
            raise MapaNaoValidadoError(f"Mapa {self.id} não validado para algoritmos. {motivo}")

    def adjacencia(self) -> Mapping[int, Mapping[int, Peso]]:
        """Retorna apenas arestas reais, nos dois sentidos, em visão imutável.

        Um nó isolado possui vizinhança vazia. Aresta ausente não vira zero,
        infinito, distância euclidiana ou atalho calculado por outro algoritmo.
        Mapas pendentes são recusados, preservando null no cadastro para a UI.
        """
        self.exigir_validado()
        vizinhos: dict[int, dict[int, Peso]] = {no.id: {} for no in self.nos}
        for aresta in self.arestas:
            # __post_init__ rejeita validado=True com peso desconhecido.
            if aresta.peso is None:
                raise MapaNaoValidadoError("Adjacência exige todos os pesos conhecidos.")
            vizinhos[aresta.origem][aresta.destino] = aresta.peso
            vizinhos[aresta.destino][aresta.origem] = aresta.peso
        return MappingProxyType({no: MappingProxyType(v) for no, v in vizinhos.items()})


@dataclass(frozen=True, slots=True)
class ResultadoDijkstra:
    """Caminho mínimo e custo; destino inalcançável resulta em () e infinito."""

    caminho: tuple[int, ...]
    custo: Peso


def dijkstra(grafo: Grafo, origem: int, destino: int) -> ResultadoDijkstra:
    """Calcula o menor caminho entre dois nós de um mapa validado.

    Usa heap mínimo de (distância, ID) e mapa de predecessores. Entradas
    antigas do heap são descartadas após uma melhoria de distância. O destino
    só é aceito ao sair da fila com sua distância mínima, não ao ser descoberto.
    Empates preservam o primeiro predecessor; vizinhos e prioridades usam ID
    para produzir resultado reproduzível mesmo se a ordem das arestas mudar.
    """
    if not isinstance(grafo, Grafo):
        raise GrafoInvalidoError("Dijkstra exige um objeto Grafo.")
    grafo.exigir_validado()
    for campo, node_id in (("origem", origem), ("destino", destino)):
        _id_valido(node_id, campo)
        if node_id not in grafo.ids:
            raise GrafoInvalidoError(f"{campo}: nó {node_id} inexistente no mapa {grafo.id}.")

    adjacencia = grafo.adjacencia()
    distancias: dict[int, Peso] = {node_id: math.inf for node_id in grafo.ids}
    predecessores: dict[int, int] = {}
    visitados: set[int] = set()
    distancias[origem] = 0
    fila: list[tuple[Peso, int]] = [(0, origem)]

    while fila:
        custo, atual = heappop(fila)
        if atual in visitados or custo != distancias[atual]:
            continue
        visitados.add(atual)
        if atual == destino:
            caminho = [destino]
            while caminho[-1] != origem:
                caminho.append(predecessores[caminho[-1]])
            caminho.reverse()
            return ResultadoDijkstra(tuple(caminho), custo)

        for vizinho, peso in sorted(adjacencia[atual].items()):
            if vizinho in visitados:
                continue
            try:
                candidato = custo + peso
            except OverflowError as erro:
                raise ErroGrafo("Custo acumulado excede a capacidade numérica de ponto flutuante.") from erro
            if type(candidato) is float and not math.isfinite(candidato):
                raise ErroGrafo("Custo acumulado excede a capacidade numérica de ponto flutuante.")
            if candidato < distancias[vizinho]:
                distancias[vizinho] = candidato
                predecessores[vizinho] = atual
                heappush(fila, (candidato, vizinho))

    return ResultadoDijkstra((), math.inf)


@dataclass(frozen=True, slots=True)
class ResultadoTSP:
    ordem: tuple[int, ...]
    caminho: tuple[int, ...]
    custo: Peso
    estados_testados: int
    ciclos_validos: int
    otimo: bool = True


def _validar_tsp(grafo: Grafo, origem: int, *, limite: int = 9) -> None:
    if not isinstance(grafo, Grafo):
        raise GrafoInvalidoError("TSP exige um objeto Grafo.")
    grafo.exigir_validado()
    _id_valido(origem, "origem")
    if origem not in grafo.ids:
        raise GrafoInvalidoError(f"origem: nó {origem} inexistente.")
    if len(grafo.nos) > limite:
        raise LimiteTSPError(f"Busca exata didática limitada a {limite} nós; mapa possui {len(grafo.nos)}.")


def tsp_forca_bruta(grafo: Grafo, origem: int) -> ResultadoTSP:
    """Enumera até (n-1)! ordens, somente sobre arestas reais; máximo 9 nós.

    Sem ciclo viável, retorna tuplas vazias e infinito (inexistência provada).
    Uma única cidade tem percurso trivial de custo zero.
    """
    _validar_tsp(grafo, origem)
    adj = grafo.adjacencia()
    if len(grafo.nos) == 1:
        return ResultadoTSP((origem,), (origem,), 0, 1, 1)
    melhor = ()
    custo_melhor = math.inf
    testados = validos = 0
    for ordem in permutations(sorted(node_id for node_id in grafo.ids if node_id != origem)):
        rota = (origem, *ordem, origem)
        testados += 1
        custo = 0
        for a, b in zip(rota, rota[1:]):
            if b not in adj[a]:
                break
            custo += adj[a][b]
            if type(custo) is float and not math.isfinite(custo):
                raise ErroGrafo("Custo acumulado excede a capacidade numérica.")
        else:
            validos += 1
            if custo < custo_melhor:
                melhor, custo_melhor = rota, custo
    return ResultadoTSP(melhor, melhor, custo_melhor, testados, validos)


def _campos(objeto: object, obrigatorios: tuple[str, ...], contexto: str) -> dict:
    if not isinstance(objeto, dict):
        raise GrafoInvalidoError(f"{contexto}: esperado objeto JSON.")
    faltantes = [campo for campo in obrigatorios if campo not in objeto]
    if faltantes:
        raise GrafoInvalidoError(f"{contexto}: campos obrigatórios ausentes: {', '.join(faltantes)}.")
    return objeto


def _objeto_sem_chaves_duplicadas(pares: list[tuple[str, object]]) -> dict:
    objeto = {}
    for chave, valor in pares:
        if chave in objeto:
            raise GrafoInvalidoError(f"Chave JSON duplicada: {chave}.")
        objeto[chave] = valor
    return objeto


def carregar_mapa(caminho: str | Path) -> Grafo:
    """Lê e valida um cadastro UTF-8; mapas pendentes são somente inspecionáveis.

    Campos extras de documentação/auditoria são permitidos. Não são usados
    para inferir pesos ou para promover um cadastro a validado.
    """
    caminho = Path(caminho)
    try:
        with caminho.open(encoding="utf-8") as arquivo:
            dados = json.load(arquivo, object_pairs_hook=_objeto_sem_chaves_duplicadas)
    except json.JSONDecodeError as erro:
        raise GrafoInvalidoError(
            f"JSON inválido em {caminho}, linha {erro.lineno}, coluna {erro.colno}."
        ) from erro
    except (OSError, UnicodeError) as erro:
        raise GrafoInvalidoError(f"Não foi possível ler {caminho}: {erro}.") from erro

    dados = _campos(dados, (
        "id", "nome", "direcionado", "validado", "referencia",
        "sistema_coordenadas", "nos", "arestas",
    ), "Mapa")
    for campo in ("nos", "arestas", "pendencias"):
        if not isinstance(dados.get(campo, []), list):
            raise GrafoInvalidoError(f"{campo}: esperado array JSON.")

    nos = []
    for indice, valor in enumerate(dados["nos"]):
        no = _campos(valor, ("id", "x", "y"), f"nos[{indice}]")
        nos.append(No(no["id"], no["x"], no["y"]))
    arestas = []
    for indice, valor in enumerate(dados["arestas"]):
        aresta = _campos(valor, ("origem", "destino", "peso"), f"arestas[{indice}]")
        arestas.append(Aresta(
            aresta["origem"], aresta["destino"], aresta["peso"], aresta.get("observacao", "")
        ))
    return Grafo(
        id=dados["id"], nome=dados["nome"], direcionado=dados["direcionado"],
        validado=dados["validado"], referencia=dados["referencia"],
        sistema_coordenadas=dados["sistema_coordenadas"],
        nos=tuple(nos), arestas=tuple(arestas),
        pendencias=tuple(dados.get("pendencias", [])), observacoes=dados.get("observacoes", ""),
    )
