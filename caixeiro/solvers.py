"""Contrato de execução independente de Pygame e registro dos solvers.

Os tempos incluem a coleta limitada de snapshots; não há segunda execução
escondida. Pesos e custos mantêm a unidade do cadastro, nunca pixels.
"""
from dataclasses import dataclass, field, replace
from itertools import permutations
from threading import Event
from time import perf_counter
from types import MappingProxyType
import math

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
    return ResultadoSolver(nome, ctx.pipeline, variante, origem, tuple(ordem), tuple(fisico), custo,
                           garantia, termino, tempos,
                           tuple(ctx.contadores) + (Contador("trabalho", ctx.estados, "estados"),),
                           tuple(ctx.eventos), tuple(ctx.parametros))


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
