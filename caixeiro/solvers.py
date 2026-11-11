"""Contrato de execução independente de Pygame e registro dos solvers.

Os tempos incluem a coleta limitada de snapshots; não há segunda execução
escondida. Pesos e custos mantêm a unidade do cadastro, nunca pixels.
"""
from dataclasses import dataclass, field, replace
from itertools import permutations
from functools import lru_cache
from threading import Event
from time import perf_counter
from types import MappingProxyType
import math
import sys
import importlib.util
from hashlib import sha256
from fractions import Fraction

from tsp_core import Aresta, Grafo, Passo, ErroGrafo, dijkstra
from busca_limitada import tsp_branch_bound

ORIGINAL = "original"
FECHO = "fecho"
CAMINHO = "caminho_minimo"
MODELOS = {ORIGINAL: "Ciclo Hamiltoniano na malha original",
           FECHO: "Passeio fechado no fecho métrico", CAMINHO: "Caminho mínimo A → B"}


@dataclass(frozen=True, slots=True)
class Orcamento:
    segundos: float = 5.0
    max_estados: int = 2_000_000
    memoria_bytes: int = 256 * 1024 * 1024
    max_iteracoes: int = 1000
    max_eventos: int = 3000

    def __post_init__(self):
        if type(self.segundos) not in (int, float) or not math.isfinite(self.segundos) or self.segundos <= 0:
            raise ValueError("O orçamento de tempo deve ser finito e positivo.")
        for nome in ("max_estados", "memoria_bytes", "max_iteracoes", "max_eventos"):
            if type(getattr(self, nome)) is not int or getattr(self, nome) < 1:
                raise ValueError(f"{nome} deve ser inteiro positivo.")


@dataclass(frozen=True, slots=True)
class Contador:
    nome: str
    valor: int
    unidade: str


@dataclass(frozen=True, slots=True)
class ResultadoSolver:
    metodo: str
    pipeline: tuple[str, ...]
    variante: str
    origem: int
    ordem: tuple[int, ...]
    caminho_fisico: tuple[int, ...]
    custo: int | float
    garantia: str
    termino: str
    tempos_ms: tuple[tuple[str, float], ...]
    contadores: tuple[Contador, ...]
    eventos: tuple[Passo, ...] = ()
    parametros: tuple[tuple[str, str], ...] = ()
    instancia: str = ""

    @property
    def caminho(self):
        return self.caminho_fisico

    @property
    def otimo(self):
        return self.termino in ("otimo_comprovado", "inviavel_comprovado")

    @property
    def estado(self):
        return self.termino


@dataclass(frozen=True, slots=True)
class RegistroSolver:
    funcao: object
    variantes: tuple[str, ...]
    padrao: str
    limite_nos: int | None
    atalho: str
    dependencia: object = None


_REGISTRO = {}
REGISTRO = MappingProxyType(_REGISTRO)


def registrar(nome, funcao, variantes, padrao, limite_nos=None, atalho="", dependencia=None):
    _REGISTRO[nome] = RegistroSolver(funcao, tuple(variantes), padrao, limite_nos, atalho, dependencia)


def disponibilidade(nome, grafo, variante=None):
    registro = REGISTRO.get(nome)
    if registro is None:
        return "Solver não registrado."
    if not grafo.validado:
        return "Mapa não validado: cálculos bloqueados."
    if registro.limite_nos and len(grafo.ids) > registro.limite_nos:
        return f"Método limitado a {registro.limite_nos} nós."
    if variante is not None and variante not in registro.variantes:
        return "Variante incompatível com este método."
    if registro.dependencia:
        return registro.dependencia()
    return ""


class Interrompido(Exception):
    def __init__(self, motivo):
        self.motivo = motivo


class Contexto:
    def __init__(self, metodo, orcamento, cancelar, progresso):
        self.metodo, self.orcamento = metodo, orcamento
        self.cancelar, self.progresso = cancelar, progresso
        self.inicio = perf_counter()
        self.estados = 0
        self.eventos = []
        self.contadores = []
        self.parametros = []
        self.melhor = ()
        self.pipeline = (metodo,)
        self.preparacao_ms = 0.0
        self.reconstrucao_ms = 0.0

    def verificar(self, incremento=0):
        if self.cancelar.is_set():
            raise Interrompido("cancelado")
        if perf_counter() - self.inicio >= self.orcamento.segundos:
            raise Interrompido("limite_tempo")
        if self.estados + incremento > self.orcamento.max_estados:
            raise Interrompido("limite_estados")
        self.estados += incremento

    def fase(self, texto):
        self.verificar()
        if self.progresso:
            self.progresso(texto)

    def evento(self, tipo, **kwargs):
        passo = Passo(self.metodo, tipo, metodo_origem=self.metodo, **kwargs)
        if len(self.eventos) < self.orcamento.max_eventos:
            self.eventos.append(passo)
        else:
            self.eventos[-1] = passo


@dataclass(slots=True)
class Problema:
    grafo: Grafo
    origem: int
    variante: str
    custos: dict
    caminhos: dict
    conectado: bool = True

    def custo(self, ordem):
        return sum(self.custos.get((a, b), math.inf) for a, b in zip(ordem, ordem[1:]))

    def expandir(self, ordem):
        if not ordem:
            return ()
        rota = [ordem[0]]
        for a, b in zip(ordem, ordem[1:]):
            trecho = self.caminhos.get((a, b), ())
            if not trecho:
                raise ErroGrafo(f"Saída inválida: aresta {a}–{b} ausente.")
            rota.extend(trecho[1:])
        return tuple(rota)


def preparar(grafo, origem, variante, ctx):
    inicio = perf_counter()
    adj = grafo.adjacencia()
    custos, caminhos = {}, {}
    if variante == FECHO:
        ctx.fase("Dijkstra: calculando menores caminhos")
        for a in sorted(grafo.ids):
            for b in sorted(grafo.ids):
                eventos = []
                r = dijkstra(grafo, a, b, eventos=eventos,
                             controle=lambda: ctx.verificar())
                if not r.caminho:
                    raise ErroGrafo("Fecho métrico exige mapa conectado (todos os pares alcançáveis).")
                custos[a, b], caminhos[a, b] = r.custo, r.caminho
                for e in eventos:
                    if len(ctx.eventos) < ctx.orcamento.max_eventos // 2:
                        ctx.eventos.append(replace(e, metodo_origem=ctx.metodo))
        ctx.contadores.append(Contador("pares Dijkstra", len(custos), "pares"))
    else:
        for a in grafo.ids:
            custos[a, a], caminhos[a, a] = 0, (a,)
            for b, peso in adj[a].items():
                custos[a, b], caminhos[a, b] = peso, (a, b)
        # A conectividade é checada; desconexão prova inviabilidade do ciclo.
    ctx.preparacao_ms = (perf_counter() - inicio) * 1000
    def alcancados(reverso=False):
        vistos, pilha = {origem}, [origem]
        while pilha:
            ctx.verificar()
            a = pilha.pop()
            for b in grafo.ids:
                if b not in vistos and ((b, a) if reverso else (a, b)) in custos:
                    vistos.add(b)
                    pilha.append(b)
        return len(vistos) == len(grafo.ids)
    conectado = alcancados() and alcancados(True)
    return Problema(grafo, origem, variante, custos, caminhos, conectado)


def validar_saida(p, ordem, fisico, custo):
    if not ordem:
        if fisico or custo != math.inf:
            raise ErroGrafo("Resultado vazio deve ter custo infinito.")
        return
    if ordem[0] != p.origem or ordem[-1] != p.origem:
        raise ErroGrafo("Ciclo deve começar e terminar na origem.")
    cidades = ordem if len(p.grafo.ids) == 1 else ordem[:-1]
    if len(cidades) != len(p.grafo.ids) or set(cidades) != set(p.grafo.ids):
        raise ErroGrafo("Ciclo deve visitar cada cidade exatamente uma vez na ordem.")
    if fisico != p.expandir(ordem):
        raise ErroGrafo("Percurso não corresponde à expansão da ordem.")
    adj = p.grafo.adjacencia()
    try:
        real = sum(adj[a][b] for a, b in zip(fisico, fisico[1:]))
    except KeyError as erro:
        raise ErroGrafo("Percurso usa aresta física inexistente.") from erro
    if not math.isfinite(custo) or not math.isclose(real, custo, rel_tol=1e-10, abs_tol=1e-9):
        raise ErroGrafo("Custo físico diverge do custo informado.")


def executar(nome, grafo, origem, *, destino=None, variante=None, orcamento=None,
             cancelar=None, progresso=None, **opcoes):
    grafo.exigir_validado()
    if type(origem) is not int or origem not in grafo.ids:
        raise ErroGrafo("Origem inexistente.")
    registro = REGISTRO.get(nome)
    variante = variante or (registro.padrao if registro else ORIGINAL)
    ctx = Contexto(nome, orcamento or Orcamento(), cancelar or Event(), progresso)
    p, ordem, fisico, custo = None, (), (), math.inf
    termino, garantia = "indisponivel", "Indisponível"
    motivo = disponibilidade(nome, grafo, variante)
    if motivo:
        ctx.parametros.append(("indisponibilidade", motivo))
    else:
        try:
            ctx.verificar()
            if variante == CAMINHO:
                if type(destino) is not int or destino not in grafo.ids:
                    raise ErroGrafo("Destino inexistente.")
                eventos = []
                r = dijkstra(grafo, origem, destino, eventos=eventos,
                             controle=lambda: ctx.verificar(1))
                ordem = fisico = r.caminho
                custo = r.custo
                ctx.eventos = [replace(e, metodo_origem=nome) for e in eventos[:ctx.orcamento.max_eventos]]
                termino = "otimo_comprovado" if ordem else "inviavel_comprovado"
                garantia = "Caminho mínimo exato" if ordem else "Destino inalcançável"
            else:
                p = preparar(grafo, origem, variante, ctx)
                ctx.fase("Buscando a ordem de visitas")
                if not p.conectado:
                    ordem, termino, garantia = (), "inviavel_comprovado", "Mapa desconectado · ciclo impossível"
                else:
                    ordem, termino, garantia = registro.funcao(p, ctx, **opcoes)
                ctx.melhor = ordem
        except Interrompido as e:
            ordem, termino = ctx.melhor, e.motivo
            garantia = "Melhor conhecida · sem prova" if ordem else "Nenhuma rota encontrada · sem prova"
        if p is not None:
            inicio = perf_counter()
            fisico, custo = p.expandir(ordem), p.custo(ordem) if ordem else math.inf
            validar_saida(p, ordem, fisico, custo)
            ctx.reconstrucao_ms = (perf_counter() - inicio) * 1000
            ctx.evento("fim", candidato=ordem, caminho=fisico, custo=custo,
                       melhor=ordem, melhor_custo=custo, contador=ctx.estados)
    total = (perf_counter() - ctx.inicio) * 1000
    tempos = (("preparacao", ctx.preparacao_ms),
              ("otimizacao", max(0, total - ctx.preparacao_ms - ctx.reconstrucao_ms)),
              ("reconstrucao", ctx.reconstrucao_ms), ("total", total))
    identidade = repr((grafo.direcionado, tuple(sorted(grafo.ids)),
                      tuple(sorted((a.origem, a.destino, a.peso) for a in grafo.arestas))))
    return ResultadoSolver(nome, ctx.pipeline, variante, origem, tuple(ordem), tuple(fisico), custo,
                           garantia, termino, tempos,
                           tuple(ctx.contadores) + (Contador("trabalho", ctx.estados, "estados"),),
                           tuple(ctx.eventos), tuple(ctx.parametros), sha256(identidade.encode()).hexdigest())


def _forca(p, ctx):
    ids, origem = p.grafo.ids, p.origem
    if len(ids) == 1:
        return (origem,), "otimo_comprovado", "Ótimo comprovado"
    melhor_custo = math.inf
    for resto in permutations(sorted(i for i in ids if i != origem)):
        ctx.verificar(1)
        rota = (origem, *resto, origem)
        custo = p.custo(rota)
        if custo < melhor_custo:
            ctx.melhor, melhor_custo = rota, custo
        ctx.evento("candidato", candidato=rota if math.isfinite(custo) else (),
                   caminho=p.expandir(rota) if math.isfinite(custo) else (), custo=custo,
                   melhor=ctx.melhor, melhor_custo=melhor_custo, contador=ctx.estados)
    return ctx.melhor, ("otimo_comprovado" if ctx.melhor else "inviavel_comprovado"), (
        "Ótimo comprovado" if ctx.melhor else "Ausência de ciclo comprovada")


def _limitada(p, ctx):
    r = tsp_branch_bound(p.grafo, p.origem, limite_segundos=ctx.orcamento.segundos,
                         max_estados=ctx.orcamento.max_estados,
                         controle=lambda: ctx.verificar(1),
                         ao_melhor=lambda rota: setattr(ctx, "melhor", rota))
    if not r.otimo:
        return r.ordem, "limite_estados", "Melhor conhecida · sem prova"
    return r.ordem, ("otimo_comprovado" if r.ordem else "inviavel_comprovado"), (
        "Ótimo comprovado" if r.ordem else "Ausência de ciclo comprovada")


registrar("dijkstra", None, (CAMINHO,), CAMINHO, atalho="D")
registrar("forca", _forca, (ORIGINAL, FECHO), ORIGINAL, 9, "F")
registrar("fecho", _forca, (FECHO,), FECHO, 9, "T")
registrar("limitada", _limitada, (ORIGINAL,), ORIGINAL, 18, "B")


def nearest_neighbor(p, ctx):
    """Construção determinística O(n²); não fornece certificado de ótimo."""
    origem = p.origem
    rota, restantes, acumulado = [origem], set(p.grafo.ids) - {origem}, 0
    ctx.fase("Vizinho mais próximo: construindo a rota")
    while restantes:
        ctx.verificar(1)
        atual = rota[-1]
        peso, proximo = min(((p.custos[atual, b], b) for b in restantes
                              if (atual, b) in p.custos), default=(math.inf, None))
        if proximo is None:
            return (), "construcao_bloqueada", "Construção gulosa bloqueada · sem prova de inviabilidade"
        rota.append(proximo)
        restantes.remove(proximo)
        acumulado += peso
        ctx.evento("escolha", atual=proximo, candidato=tuple(rota),
                   caminho=p.expandir(rota), custo=acumulado, contador=ctx.estados)
    if len(rota) > 1:
        if (rota[-1], origem) not in p.custos:
            return (), "construcao_bloqueada", "Retorno guloso bloqueado · sem prova de inviabilidade"
        rota.append(origem)
    ctx.melhor = tuple(rota)
    return ctx.melhor, "heuristica", "Heurística · sem prova de ótimo"


registrar("nearest_neighbor", nearest_neighbor, (ORIGINAL, FECHO), FECHO, atalho="N")


def two_opt(p, ctx, *, ordem_inicial=None):
    """Primeira melhoria estrita, custo completo (também verifica arcos ausentes)."""
    if ordem_inicial is None:
        ctx.pipeline = ("nearest_neighbor", "two_opt")
        rota, termino, garantia = nearest_neighbor(p, ctx)
        if not rota:
            return rota, termino, garantia
    else:
        ctx.pipeline = ("rota_fornecida", "two_opt")
        if isinstance(ordem_inicial, ResultadoSolver):
            if ordem_inicial.variante != p.variante or ordem_inicial.origem != p.origem:
                raise ErroGrafo("Rota inicial pertence a outra variante/origem.")
            rota = ordem_inicial.ordem
            validar_saida(p, rota, ordem_inicial.caminho, ordem_inicial.custo)
        else:
            rota = tuple(ordem_inicial)
            validar_saida(p, rota, p.expandir(rota), p.custo(rota))
        if not rota:
            raise ErroGrafo("2-opt exige uma rota inicial viável.")
    ctx.melhor = tuple(rota)
    custo = p.custo(rota)
    inicial, trocas = custo, 0
    ctx.parametros.append(("custo_inicial", str(custo)))
    ctx.fase("nearest_neighbor + two_opt: procurando melhorias")
    for iteracao in range(1, ctx.orcamento.max_iteracoes + 1):
        melhorou = False
        for i in range(1, len(rota) - 2):
            for j in range(i + 1, len(rota) - 1):
                ctx.verificar(1)
                candidato = (*rota[:i], *reversed(rota[i:j + 1]), *rota[j + 1:])
                novo = p.custo(candidato)
                if novo < custo:
                    ctx.evento("troca_2opt", candidato=candidato, caminho=p.expandir(candidato),
                               custo=novo, custo_anterior=custo, contador=iteracao,
                               removidas=((rota[i - 1], rota[i]), (rota[j], rota[j + 1])),
                               adicionadas=((rota[i - 1], rota[j]), (rota[i], rota[j + 1])))
                    rota, custo, melhorou = candidato, novo, True
                    ctx.melhor = rota
                    trocas += 1
                    break
            if melhorou:
                break
        if not melhorou:
            ctx.contadores.extend((Contador("trocas 2-opt", trocas, "trocas"),
                                   Contador("varreduras 2-opt", iteracao, "varreduras")))
            return tuple(rota), "otimo_local", "Ótimo local 2-opt · sem prova de ótimo global"
    ctx.contadores.append(Contador("trocas 2-opt", trocas, "trocas"))
    return tuple(rota), "limite_iteracoes", "Limite de iterações · sem prova de ótimo local/global"


registrar("two_opt", two_opt, (ORIGINAL, FECHO), FECHO, atalho="I")


def held_karp(p, ctx):
    """DP O(n²2ⁿ), custos por camada e predecessores para reconstrução.

    Memória: contabilização conservadora via getsizeof dos contêineres e
    objetos armazenados (inclui compartilhamentos mais de uma vez).
    """
    origem = p.origem
    ids = sorted(i for i in p.grafo.ids if i != origem)
    if not ids:
        return (origem,), "otimo_comprovado", "Ótimo comprovado"
    bits = {i: 1 << k for k, i in enumerate(ids)}
    vizinhos = {a: [(b, p.custos[a, b]) for b in ids if b != a and (a, b) in p.custos]
                for a in p.grafo.ids}
    camada, pais = {(0, origem): 0}, {}
    payload_atual, payload_pais, pico, estados_dp = 128, 0, 0, 1
    try:
        for tamanho in range(1, len(ids) + 1):
            ctx.fase(f"Held–Karp: camada {tamanho}/{len(ids)}")
            proxima, payload_proxima = {}, 0
            for (mask, atual), custo in camada.items():
                ctx.verificar(1)
                for vizinho, peso in vizinhos[atual]:
                    if mask & bits[vizinho]:
                        continue
                    chave = mask | bits[vizinho], vizinho
                    candidato = custo + peso
                    anterior = proxima.get(chave, math.inf)
                    if candidato < anterior:
                        if chave not in proxima:
                            payload_proxima += sys.getsizeof(chave) + sys.getsizeof(chave[0]) + sys.getsizeof(chave[1])
                            payload_pais += sys.getsizeof(chave) + sys.getsizeof(chave[0]) + sys.getsizeof(chave[1]) + sys.getsizeof(atual)
                            payload_proxima += sys.getsizeof(candidato)
                            estados_dp += 1
                        else:
                            delta = sys.getsizeof(candidato) - sys.getsizeof(anterior)
                            payload_proxima += delta
                            proxima[chave], pais[chave] = candidato, atual
                            if delta <= 0:
                                continue
                        proxima[chave], pais[chave] = candidato, atual
                        memoria = (sys.getsizeof(camada) + sys.getsizeof(proxima) + sys.getsizeof(pais)
                                   + payload_atual + payload_proxima + payload_pais)
                        pico = max(pico, memoria)
                        if memoria > ctx.orcamento.memoria_bytes:
                            raise Interrompido("limite_memoria")
            camada, payload_atual = proxima, payload_proxima
            ctx.evento("camada_dp", contador=tamanho)
            if not camada:
                break
        ctx.verificar()
        finais = ((c + p.custos[atual, origem], atual, mask)
                  for (mask, atual), c in camada.items()
                  if mask == (1 << len(ids)) - 1 and (atual, origem) in p.custos)
        custo, atual, mask = min(finais, default=(math.inf, None, 0))
        if atual is None:
            return (), "inviavel_comprovado", "Ausência de ciclo comprovada"
        reverso = [origem, atual]
        while mask:
            anterior = pais[mask, atual]
            mask ^= bits[atual]
            atual = anterior
            reverso.append(atual)
        rota = tuple(reversed(reverso))
        ctx.melhor = rota
        return rota, "otimo_comprovado", "Ótimo comprovado por Held–Karp"
    finally:
        ctx.contadores.extend((Contador("estados DP", estados_dp, "estados"),
                               Contador("memória DP contabilizada (pico)", pico, "bytes")))


registrar("held_karp", held_karp, (ORIGINAL, FECHO), ORIGINAL, 18, "H")


def _matching_exato(impares, custos, ctx):
    """Matching perfeito mínimo: fixa o primeiro ímpar e testa todos os pares.

    O(2^k k²) para k ímpares (k <= 18); sem dependência externa de matching.
    """
    @lru_cache(maxsize=None)
    def resolver(restantes):
        ctx.verificar(1)
        if not restantes:
            return 0, ()
        a, resto = restantes[0], restantes[1:]
        melhor = (math.inf, ())
        for j, b in enumerate(resto):
            custo, pares = resolver(resto[:j] + resto[j + 1:])
            candidato = custos[a, b] + custo, ((a, b), *pares)
            if candidato < melhor:
                melhor = candidato
        return melhor
    resultado = resolver(tuple(sorted(impares)))
    ctx.contadores.append(Contador("subconjuntos matching", resolver.cache_info().currsize, "subconjuntos"))
    return resultado


def christofides(p, ctx):
    ids = sorted(p.grafo.ids)
    if p.grafo.direcionado:
        raise ErroGrafo("Christofides exige grafo não direcionado.")
    for a in ids:
        ctx.verificar()
        for b in ids:
            if (a, b) not in p.custos or p.custos[a, b] != p.custos.get((b, a)):
                raise ErroGrafo("Christofides exige matriz completa e simétrica.")
    for a in ids:
        ctx.verificar()
        for b in ids:
            for c in ids:
                direto, via = p.custos[a, b], p.custos[a, c] + p.custos[c, b]
                if direto > via and not math.isclose(direto, via, rel_tol=1e-12, abs_tol=1e-12):
                    raise ErroGrafo("Christofides exige desigualdade triangular.")
    ctx.pipeline = ("dijkstra", "christofides") if p.variante == FECHO else ("christofides",)
    if len(ids) == 1:
        return (p.origem,), "aproximacao", "Aproximação ≤ 1,5 × ótimo da mesma instância métrica"
    ctx.fase("Christofides: árvore geradora mínima (MST)")
    dentro, fora, mst = {p.origem}, set(ids) - {p.origem}, []
    graus = dict.fromkeys(ids, 0)
    while fora:
        ctx.verificar(1)
        _, a, b = min((p.custos[a, b], a, b) for a in dentro for b in fora)
        mst.append((a, b))
        graus[a] += 1
        graus[b] += 1
        dentro.add(b)
        fora.remove(b)
        ctx.evento("mst", adicionadas=tuple(mst), contador=len(mst))
    impares = tuple(a for a in ids if graus[a] % 2)
    ctx.evento("vertices_impares", visitados=impares)
    ctx.fase("Christofides: matching perfeito de peso mínimo (exato)")
    custo_matching, matching = _matching_exato(impares, p.custos, ctx)
    ctx.evento("matching_minimo", adicionadas=matching, custo=custo_matching)
    ctx.fase("Christofides: circuito Euleriano no multigrafo")
    adj = {a: [] for a in ids}
    for indice, (a, b) in enumerate((*mst, *matching)):
        adj[a].append((b, indice))
        adj[b].append((a, indice))
    for lista in adj.values():
        lista.sort(reverse=True)
    usados, pilha, circuito = set(), [p.origem], []
    while pilha:
        ctx.verificar(1)
        a = pilha[-1]
        while adj[a] and adj[a][-1][1] in usados:
            adj[a].pop()
        if not adj[a]:
            circuito.append(pilha.pop())
        else:
            b, indice = adj[a].pop()
            usados.add(indice)
            pilha.append(b)
    circuito.reverse()
    ctx.evento("circuito_euleriano", candidato=tuple(circuito), caminho=p.expandir(circuito))
    ctx.fase("Christofides: atalhamento e expansão física")
    vistos, rota = set(), []
    for a in circuito:
        if a not in vistos:
            vistos.add(a)
            rota.append(a)
    rota.append(p.origem)
    ctx.melhor = tuple(rota)
    ctx.evento("atalhamento", candidato=ctx.melhor, caminho=p.expandir(rota), custo=p.custo(rota))
    return ctx.melhor, "aproximacao", "Aproximação ≤ 1,5 × ótimo da mesma instância métrica"


registrar("christofides", christofides, (ORIGINAL, FECHO), FECHO, 18, "A")


def dependencia_ortools():
    if importlib.util.find_spec("ortools") is None:
        return "OR-Tools opcional ausente: instale requirements-ortools.txt neste Python."
    return ""


def _custos_inteiros(custos, n):
    """Escala decimal exata, sem arredondar pesos nem ultrapassar int64."""
    fracoes = {par: Fraction(str(peso)) for par, peso in custos.items()}
    escala = math.lcm(*(f.denominator for f in fracoes.values()))
    inteiros = {par: f.numerator * (escala // f.denominator) for par, f in fracoes.items()}
    if max(inteiros.values(), default=0) * max(1, n) >= 2**62:
        raise ErroGrafo("Precisão dos pesos excede a capacidade int64 do OR-Tools; não houve arredondamento.")
    return inteiros, escala


def ortools_solver(p, ctx, *, busca_local="GUIDED_LOCAL_SEARCH", limite_solucoes=None):
    try:
        import ortools
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    except (ImportError, OSError) as erro:
        ctx.parametros.append(("indisponibilidade", str(erro)))
        return (), "indisponivel", "OR-Tools indisponível neste Python"
    if busca_local not in ("GUIDED_LOCAL_SEARCH", "GREEDY_DESCENT"):
        raise ValueError("Busca local deve ser GUIDED_LOCAL_SEARCH ou GREEDY_DESCENT.")
    if limite_solucoes is not None and (type(limite_solucoes) is not int or limite_solucoes < 1):
        raise ValueError("limite_solucoes deve ser inteiro positivo.")
    ctx.fase("OR-Tools: modelando arcos e custos inteiros")
    ids = sorted(p.grafo.ids)
    inteiros, escala = _custos_inteiros(p.custos, len(ids))
    manager = pywrapcp.RoutingIndexManager(len(ids), 1, ids.index(p.origem))
    routing = pywrapcp.RoutingModel(manager)
    solver = routing.solver()
    def cidade(indice):
        return ids[manager.IndexToNode(indice)]
    def custo(a, b):
        # Arcos ausentes são removidos do domínio abaixo. Não há penalidades.
        return inteiros.get((cidade(a), cidade(b)), 0)
    callback = routing.RegisterTransitCallback(custo)
    routing.SetArcCostEvaluatorOfAllVehicles(callback)
    proibidos = 0
    for a in range(routing.Size()):
        for b in range(routing.Size() + 1):
            if (cidade(a), cidade(b)) not in p.custos:
                routing.NextVar(a).RemoveValue(b)
                proibidos += 1
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = getattr(routing_enums_pb2.LocalSearchMetaheuristic, busca_local)
    restante = max(0, ctx.orcamento.segundos - (perf_counter() - ctx.inicio))
    params.time_limit.FromMilliseconds(max(1, int(restante * 1000)))
    if limite_solucoes is not None:
        params.solution_limit = limite_solucoes
    ctx.parametros.extend((("versao_ortools", ortools.__version__), ("escala_inteira", str(escala)),
                           ("primeira_solucao", "PATH_CHEAPEST_ARC"), ("busca_local", busca_local),
                           ("limite_ms_busca", str(max(1, int(restante * 1000)))),
                           ("limite_solucoes", str(limite_solucoes))))
    parada = None
    def verificar_limite():
        nonlocal parada
        if ctx.cancelar.is_set():
            parada = "cancelado"
        elif perf_counter() - ctx.inicio >= ctx.orcamento.segundos:
            parada = "limite_tempo"
        elif solver.Branches() >= ctx.orcamento.max_estados:
            parada = "limite_estados"
        return parada is not None
    monitor = solver.CustomLimit(verificar_limite)
    routing.AddSearchMonitor(monitor)
    solucoes = 0
    def registrar_solucao():
        nonlocal solucoes
        indice, rota = routing.Start(0), []
        while not routing.IsEnd(indice) and len(rota) <= len(ids):
            rota.append(cidade(indice))
            indice = routing.NextVar(indice).Value()
        if not routing.IsEnd(indice):
            return
        if len(ids) > 1:
            rota.append(p.origem)
        rota = tuple(rota)
        if len(ids) == 1:
            rota = (p.origem,)
        solucoes += 1
        if not ctx.melhor or p.custo(rota) < p.custo(ctx.melhor):
            ctx.melhor = rota
            ctx.evento("solucao_ortools", candidato=rota, caminho=p.expandir(rota),
                       custo=p.custo(rota), contador=solucoes)
    routing.AddAtSolutionCallback(registrar_solucao)
    ctx.fase("OR-Tools: busca local com orçamento")
    solucao = routing.SolveWithParameters(params)
    status = routing.status()
    nomes = {0: "NOT_SOLVED", 1: "SUCCESS", 2: "PARTIAL_SUCCESS_LOCAL_OPTIMUM_NOT_REACHED",
             3: "FAIL", 4: "FAIL_TIMEOUT", 5: "INVALID", 6: "INFEASIBLE", 7: "OPTIMAL"}
    ctx.parametros.append(("status_ortools", f"{status}:{nomes.get(status, 'DESCONHECIDO')}"))
    ctx.estados = solver.Branches()
    ctx.contadores.extend((Contador("soluções OR-Tools", solucoes, "soluções"),
                           Contador("arcos proibidos", proibidos, "arcos")))
    # Uma atribuição retornada pode ser melhor que o último callback registrado.
    if solucao is not None:
        indice, rota = routing.Start(0), []
        while not routing.IsEnd(indice):
            rota.append(cidade(indice))
            indice = solucao.Value(routing.NextVar(indice))
        if len(ids) > 1:
            rota.append(p.origem)
        ctx.melhor = tuple(rota)
    verificar_limite()
    if status == 4:
        parada = parada or "limite_tempo"
    if parada:
        return ctx.melhor, parada, "Melhor conhecida · sem prova" if ctx.melhor else "Limite/cancelamento · nenhuma rota encontrada"
    if ctx.melhor:
        return ctx.melhor, "heuristica", "OR-Tools: rota viável · sem certificado de ótimo"
    # O adaptador não converte o status do Routing Solver em certificado global.
    return (), "sem_solucao", "Nenhuma rota encontrada pelo OR-Tools · sem prova"


registrar("ortools_solver", ortools_solver, (ORIGINAL, FECHO), FECHO, 18, "R", dependencia_ortools)
