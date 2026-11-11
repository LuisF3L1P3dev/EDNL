"""Verifica o mapa real: Dijkstra, B&B e controle independente Held–Karp."""
from dataclasses import asdict
import json
import math
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from busca_limitada import tsp_branch_bound
from tsp_core import carregar_mapa, dijkstra


def controle_dp(grafo, origem):
    """Programação dinâmica independente da poda/MST; não enumera 17! ordens.

    Mantém uma camada por número de cidades visitadas. Guarda somente o custo
    mínimo por (subconjunto, última cidade); usada para auditar o ótimo real.
    """
    adj = grafo.adjacencia()
    bits = {i: 1 << k for k, i in enumerate(i for i in grafo.ids if i != origem)}
    camada = {(0, origem): 0}
    estados = 1
    for _ in bits:
        proxima = {}
        for (mask, atual), custo in camada.items():
            for vizinho, peso in adj[atual].items():
                if vizinho == origem or mask & bits[vizinho]:
                    continue
                chave = mask | bits[vizinho], vizinho
                candidato = custo + peso
                if candidato < proxima.get(chave, math.inf):
                    proxima[chave] = candidato
        camada = proxima
        estados += len(camada)
    custo = min((c + adj[i][origem] for (_, i), c in camada.items() if origem in adj[i]), default=math.inf)
    return custo, estados


def main():
    grafo = carregar_mapa(ROOT / "data/mapa_18.json")
    resultado = tsp_branch_bound(grafo, 1)
    adj = grafo.adjacencia()
    assert resultado.caminho and resultado.otimo
    assert set(resultado.caminho[:-1]) == set(grafo.ids)
    assert len(resultado.caminho) == len(grafo.nos) + 1
    assert sum(adj[a][b] for a, b in zip(resultado.caminho, resultado.caminho[1:])) == resultado.custo
    inicio = perf_counter()
    custo_dp, estados_dp = controle_dp(grafo, 1)
    tempo_dp = (perf_counter() - inicio) * 1000
    assert custo_dp == resultado.custo
    dados = {
        "mapa": grafo.id, "peso_9_14": adj[9][14],
        "fonte_peso_9_14": "definicao_explicita_usuario",
        "dijkstra_9_14": asdict(dijkstra(grafo, 9, 14)),
        "dijkstra_1_18": asdict(dijkstra(grafo, 1, 18)),
        "branch_bound": asdict(resultado),
        "controle_independente_held_karp": {"custo": custo_dp, "estados": estados_dp, "tempo_ms": tempo_dp},
    }
    (ROOT / "docs/resultados_mapa_18.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"B&B: custo {resultado.custo}, {resultado.estado}, {resultado.nos_expandidos} estados.")
    print(f"Controle Held–Karp: custo {custo_dp}, {estados_dp} estados, {tempo_dp:.1f} ms.")


if __name__ == "__main__":
    main()
