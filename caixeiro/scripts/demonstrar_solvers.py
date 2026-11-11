"""Evidências dos métodos no mesmo modelo; sem embutir milhares de snapshots."""
from dataclasses import asdict
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from comparacao_solvers import metodos_comparaveis, resumir
from solvers import executar, Orcamento, ORIGINAL, FECHO
from tsp_core import carregar_mapa


def main():
    grupos = []
    for arquivo in ("mapa_05.json", "mapa_18.json"):
        g = carregar_mapa(ROOT / "data" / arquivo)
        for variante in (ORIGINAL, FECHO):
            resultados, registros = {}, {}
            for nome in metodos_comparaveis(variante):
                r = executar(nome, g, 1, variante=variante, orcamento=Orcamento(segundos=15),
                             **({"busca_local": "GREEDY_DESCENT"} if nome == "ortools_solver" else {}))
                resultados[nome] = r
                dados = asdict(r)
                dados.pop("eventos")
                dados["snapshots"] = len(r.eventos)
                if not math.isfinite(r.custo):
                    dados["custo"] = None
                registros[nome] = dados
                print(f"{g.id}/{variante}/{nome}: {r.custo} ({r.termino})", flush=True)
            grupos.append({"mapa": g.id, "variante": variante, "origem": 1,
                           "resumo": resumir(resultados), "resultados": registros})
    saida = {"orcamento_segundos_por_metodo": 15, "unidade_custo": "pesos originais",
             "tempos": "ms, com snapshots limitados, sem segunda execução",
             "ortools_busca_local": "GREEDY_DESCENT", "grupos": grupos}
    (ROOT / "docs/comparacao_solvers.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    linhas = ["# Comparação dos solvers — TSP-032", "", "Origem 1; cada grupo usa os mesmos pesos/modelo. Orçamento: 15 s/método, 2 milhões de estados, 256 MiB de DP. OR-Tools usa GREEDY_DESCENT nesta evidência. Tempos incluem snapshots limitados, sem segunda execução.", ""]
    for grupo in grupos:
        resumo = grupo["resumo"]
        linhas += [f"## {grupo['mapa']} · {grupo['variante']}", "", f"Ótimo certificado: {resumo['otimo']}; oráculo: {resumo['oraculo']}. Gap ausente quando não há certificado ou rota.", "", "| Método | Custo | Término | Gap | P / O / R / total (ms) |", "|---|---:|---|---:|---|"]
        for nome, r in grupo["resultados"].items():
            gap = resumo["gaps"][nome]["percentual"]
            t = dict(r["tempos_ms"])
            tempos = " / ".join(f"{t[k]:.2f}" for k in ("preparacao", "otimizacao", "reconstrucao", "total"))
            linhas.append(f"| {nome} | {r['custo'] if r['custo'] is not None else '—'} | {r['termino']} | {f'{gap:.2f}%' if gap is not None else '—'} | {tempos} |")
        linhas.append("")
    linhas += ["391 é o ótimo Hamiltoniano do mapa 18 original. O fecho tem seu próprio certificado, quando concluído; não se transfere esse valor entre modelos. Detalhes, rotas físicas, memória em bytes, contadores e parâmetros estão no [JSON](comparacao_solvers.json).", ""]
    (ROOT / "docs/comparacao_solvers.md").write_text("\n".join(linhas), encoding="utf-8")


if __name__ == "__main__":
    main()
