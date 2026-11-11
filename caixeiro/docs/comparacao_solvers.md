# Comparação dos solvers — TSP-032

Origem 1; cada grupo usa os mesmos pesos/modelo. Orçamento: 15 s/método, 2 milhões de estados, 256 MiB de DP. OR-Tools usa GREEDY_DESCENT nesta evidência. Tempos incluem snapshots limitados, sem segunda execução.

## mapa_05 · original

Ótimo certificado: 15; oráculo: held_karp. Gap ausente quando não há certificado ou rota.

| Método | Custo | Término | Gap | P / O / R / total (ms) |
|---|---:|---|---:|---|
| forca | 15 | otimo_comprovado | 0.00% | 0.03 / 0.80 / 0.06 / 0.89 |
| held_karp | 15 | otimo_comprovado | 0.00% | 0.02 / 0.31 / 0.05 / 0.38 |
| nearest_neighbor | — | construcao_bloqueada | — | 0.02 / 0.13 / 0.00 / 0.16 |
| two_opt | — | construcao_bloqueada | — | 0.02 / 0.11 / 0.00 / 0.13 |
| ortools_solver | 15 | heuristica | 0.00% | 0.03 / 85.74 / 0.02 / 85.80 |
| limitada | 15 | otimo_comprovado | 0.00% | 0.01 / 0.13 / 0.02 / 0.16 |

## mapa_05 · fecho

Ótimo certificado: 15; oráculo: held_karp. Gap ausente quando não há certificado ou rota.

| Método | Custo | Término | Gap | P / O / R / total (ms) |
|---|---:|---|---:|---|
| forca | 15 | otimo_comprovado | 0.00% | 2.01 / 0.15 / 0.01 / 2.17 |
| held_karp | 15 | otimo_comprovado | 0.00% | 1.58 / 0.12 / 0.02 / 1.72 |
| nearest_neighbor | 17 | heuristica | 13.33% | 1.74 / 0.10 / 0.03 / 1.88 |
| two_opt | 15 | otimo_local | 0.00% | 1.98 / 0.12 / 0.01 / 2.11 |
| ortools_solver | 15 | heuristica | 0.00% | 2.74 / 3.59 / 0.06 / 6.39 |
| christofides | 15 | aproximacao | 0.00% | 5.43 / 0.43 / 0.04 / 5.90 |

## mapa_18 · original

Ótimo certificado: 391; oráculo: held_karp. Gap ausente quando não há certificado ou rota.

| Método | Custo | Término | Gap | P / O / R / total (ms) |
|---|---:|---|---:|---|
| forca | — | indisponivel | — | 0.00 / 0.01 / 0.00 / 0.01 |
| held_karp | 391 | otimo_comprovado | 0.00% | 0.08 / 688.50 / 0.13 / 688.71 |
| nearest_neighbor | — | construcao_bloqueada | — | 0.07 / 0.33 / 0.00 / 0.41 |
| two_opt | — | construcao_bloqueada | — | 0.06 / 0.33 / 0.00 / 0.39 |
| ortools_solver | 391 | heuristica | 0.00% | 0.06 / 12.33 / 0.11 / 12.50 |
| limitada | 391 | otimo_comprovado | 0.00% | 0.10 / 39.12 / 0.05 / 39.27 |

## mapa_18 · fecho

Ótimo certificado: None; oráculo: None. Gap ausente quando não há certificado ou rota.

| Método | Custo | Término | Gap | P / O / R / total (ms) |
|---|---:|---|---:|---|
| forca | — | indisponivel | — | 0.00 / 0.00 / 0.00 / 0.00 |
| held_karp | — | limite_tempo | — | 84.83 / 15035.25 / 0.01 / 15120.09 |
| nearest_neighbor | 412 | heuristica | — | 152.68 / 0.40 / 0.06 / 153.14 |
| two_opt | 388 | otimo_local | — | 161.52 / 5.04 / 0.12 / 166.67 |
| ortools_solver | 379 | heuristica | — | 160.46 / 29.10 / 0.18 / 189.74 |
| christofides | 402 | aproximacao | — | 154.60 / 4.20 / 0.06 / 158.86 |

391 é o ótimo Hamiltoniano do mapa 18 original. O fecho tem seu próprio certificado, quando concluído; não se transfere esse valor entre modelos. Detalhes, rotas físicas, memória em bytes, contadores e parâmetros estão no [JSON](comparacao_solvers.json).
