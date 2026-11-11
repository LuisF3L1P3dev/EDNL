"""TSP Hamiltoniano com branch-and-bound e orçamento explícito de execução."""
from dataclasses import dataclass
from functools import lru_cache
import math
from time import perf_counter
from tsp_core import Peso, _validar_tsp


@dataclass(frozen=True, slots=True)
class ResultadoBusca:
    caminho: tuple[int, ...]
    custo: Peso
    nos_expandidos: int
    otimo: bool
    estado: str
    tempo_ms: float

    @property
    def ordem(self):
        return self.caminho


def tsp_branch_bound(grafo, origem, *, limite_segundos=2.0, max_estados=200_000):
    """Máximo 18 nós. Nunca chama o enumerador de permutações.

    Limite inferior: MST dos não visitados mais uma ligação de cada ponta.
    É admissível porque toda conclusão contém um caminho entre os restantes
    e precisa conectar a ponta atual e a origem. Poda não elimina um ótimo.
    Tempo/estados limitam trabalho, sem declarar ótimo se houver corte.
    """
    _validar_tsp(grafo, origem, limite=18)
    if type(max_estados) is not int or max_estados < 1:
        raise ValueError("max_estados deve ser inteiro positivo")
    if type(limite_segundos) not in (float, int) or not math.isfinite(limite_segundos) or limite_segundos <= 0:
        raise ValueError("limite_segundos deve ser finito e positivo")
    inicio = perf_counter()
    prazo = inicio + limite_segundos
    adj = grafo.adjacencia()
    ids = frozenset(grafo.ids)
    melhor, melhor_custo = (), math.inf
    estados, cortado = 0, False

    @lru_cache(maxsize=8192)
    def mst(restantes):
        if len(restantes) < 2:
            return 0
        dentro = {restantes[0]}
        fora = set(restantes[1:])
        total = 0
        while fora:
            escolhas = ((adj[a][b], b) for a in dentro for b in fora if b in adj[a])
            peso, proximo = min(escolhas, default=(math.inf, None))
            if proximo is None:
                return math.inf
            total += peso
            dentro.add(proximo)
            fora.remove(proximo)
        return total

    def visitar(rota, usados, custo):
        nonlocal melhor, melhor_custo, estados, cortado
        if cortado:
            return
        if estados >= max_estados or perf_counter() >= prazo:
            cortado = True
            return
        estados += 1
        atual = rota[-1]
        restantes = ids - usados
        if not restantes:
            if len(ids) == 1:
                melhor, melhor_custo = rota, 0
            elif origem in adj[atual] and custo + adj[atual][origem] < melhor_custo:
                melhor, melhor_custo = (*rota, origem), custo + adj[atual][origem]
            return
        entrada = min((adj[atual][i] for i in restantes if i in adj[atual]), default=math.inf)
        saida = min((adj[origem][i] for i in restantes if i in adj[origem]), default=math.inf)
        inferior = custo + entrada + saida + mst(tuple(sorted(restantes)))
        if inferior >= melhor_custo:
            return
        for proximo in sorted((i for i in restantes if i in adj[atual]), key=lambda i: (adj[atual][i], i)):
            visitar((*rota, proximo), usados | {proximo}, custo + adj[atual][proximo])
            if cortado:
                return

    visitar((origem,), frozenset({origem}), 0)
    estado = ("melhor_conhecida" if melhor else "limite_sem_solucao") if cortado else (
        "otimo_comprovado" if melhor else "sem_ciclo_comprovado")
    return ResultadoBusca(melhor, melhor_custo, estados, not cortado, estado, (perf_counter() - inicio) * 1000)
