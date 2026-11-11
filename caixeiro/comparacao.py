"""Medição reproduzível; tempo sem gravação e contadores fora do cronômetro."""
from statistics import median
from time import perf_counter
import math
from tsp_core import Aresta, Grafo, fecho_metrico, tsp_forca_bruta, tsp_dijkstra, dijkstra


def medir(funcao, grafo, *args, repeticoes=7):
    if type(repeticoes) is not int or repeticoes < 1:
        raise ValueError("repeticoes deve ser inteiro positivo")
    tempos = []
    for _ in range(repeticoes):
        inicio = perf_counter()
        resultado = funcao(grafo, *args)
        tempos.append((perf_counter() - inicio) * 1000)
    eventos = []
    observado = funcao(grafo, *args, eventos=eventos)
    assert observado == resultado
    return {
        "custo": resultado.custo if resultado.custo != math.inf else None,
        "caminho": list(resultado.caminho),
        "ordem": list(getattr(resultado, "ordem", ())),
        "tempo_ms_mediana": median(tempos), "repeticoes": repeticoes,
        "ordens_testadas": getattr(resultado, "estados_testados", 0),
        "nos_finalizados_dijkstra": sum(p.tipo == "visita" for p in eventos),
        "execucoes_dijkstra": sum(p.algoritmo == "dijkstra" and p.tipo == "inicio" for p in eventos),
    }


def comparar(grafo, origem, destino, repeticoes=7):
    original = {
        "dijkstra_A_B": medir(dijkstra, grafo, origem, destino, repeticoes=repeticoes),
        "hamiltoniano_direto": medir(tsp_forca_bruta, grafo, origem, repeticoes=repeticoes),
        "passeio_no_fecho": medir(tsp_dijkstra, grafo, origem, repeticoes=repeticoes),
    }
    # Controle separado: os dois métodos recebem EXATAMENTE o mesmo grafo
    # métrico completo. Esta instância derivada não substitui o cadastro da aula.
    f = fecho_metrico(grafo)
    ids = sorted(grafo.ids)
    controle = Grafo(
        f"{grafo.id}_controle_metrico", "Controle métrico", False, True,
        grafo.referencia, grafo.sistema_coordenadas, grafo.nos,
        tuple(Aresta(a, b, f[a, b].custo) for i, a in enumerate(ids) for b in ids[i+1:]
              if f[a, b].caminho),
    )
    return {
        "mapa": grafo.id, "origem": origem, "destino_dijkstra": destino,
        "malha_original": original,
        "comparacao_original_mesmo_problema": False,
        "controle_mesma_instancia_metrica": {
            "instancia": controle.id,
            "preparacao_da_instancia_fora_do_cronometro_para_ambos": True,
            "forca_bruta": medir(tsp_forca_bruta, controle, origem, repeticoes=repeticoes),
            "dijkstra_mais_busca_exata": medir(tsp_dijkstra, controle, origem, repeticoes=repeticoes),
        },
    }
