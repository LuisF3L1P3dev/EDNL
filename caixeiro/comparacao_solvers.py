"""Comparações somente entre resultados do mesmo problema, origem e pesos."""
from solvers import executar, ORIGINAL, FECHO, Orcamento


def metodos_comparaveis(variante):
    if variante not in (ORIGINAL, FECHO):
        raise ValueError("Comparação exige TSP original ou fecho.")
    comuns = ("forca", "held_karp", "nearest_neighbor", "two_opt", "ortools_solver")
    return (*comuns, "christofides") if variante == FECHO else (*comuns, "limitada")


def resumir(resultados):
    valores = tuple(resultados.values())
    if not valores:
        return {"oraculo": None, "otimo": None, "gaps": {}}
    chaves = {(r.instancia, r.variante, r.origem) for r in valores}
    if len(chaves) != 1 or not valores[0].instancia or valores[0].variante not in (ORIGINAL, FECHO):
        raise ValueError("Comparação exige mesma instância, modelo e origem.")
    exatos = [r for r in valores if r.termino == "otimo_comprovado" and r.caminho]
    if exatos and len({r.custo for r in exatos}) != 1:
        raise ValueError("Certificados de ótimo divergentes na mesma instância.")
    oraculo = next((r for r in exatos if r.metodo == "held_karp"), next(iter(exatos), None))
    otimo = oraculo.custo if oraculo else None
    gaps = {}
    for nome, r in resultados.items():
        relativo, absoluto = None, None
        if oraculo and r.caminho:
            absoluto = r.custo - otimo
            relativo = absoluto / otimo * 100 if otimo else (0.0 if r.custo == 0 else None)
        gaps[nome] = {"percentual": relativo, "absoluto": absoluto}
    return {"oraculo": oraculo.metodo if oraculo else None, "otimo": otimo, "gaps": gaps}


def comparar_solvers(grafo, origem, variante=FECHO, *, orcamento=None, cancelar=None, progresso=None):
    resultados = {}
    for nome in metodos_comparaveis(variante):
        if cancelar is not None and cancelar.is_set():
            break
        informar = (lambda fase, nome=nome: progresso(nome, fase)) if progresso else None
        resultados[nome] = executar(nome, grafo, origem, variante=variante,
                                   orcamento=orcamento or Orcamento(), cancelar=cancelar, progresso=informar)
    return resultados, resumir(resultados)
