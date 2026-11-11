# TSP-004 — Auditoria do mapa de 18 nós

## Resultado

**Auditoria parcial: 45 ligações e 44 pesos conferidos; falta o peso de 9–14 na própria fonte.** O aceite completo da TSP-004 não foi atingido. `data/mapa_18.json` permanece com `validado: false` e `9–14` com `peso: null`.

O desenho não apresenta setas; sua representação foi mantida como não direcionada. Os cruzamentos não geram novos vértices. Os 18 IDs e as coordenadas de desenho existentes foram preservados. As duas figuras do autor confirmam a conectividade cadastrada; a figura de custos permite conferir os 44 valores numéricos. Nenhuma aresta ou peso foi removido ou acrescentado nesta revisão.

## Evidências reproduzíveis

Publicação do próprio autor, Dhiego Pardini: [O Problema do Caixeiro Viajante](https://otimizacaonapratica.wordpress.com/2015/11/09/o-problema-do-caixeiro-viajante/), de 09/11/2015. O autor informa nos comentários que produziu o desenho em PowerPoint. As figuras foram baixadas nos endereços originais, sem parâmetro de redução e sem transformação, em 11/11/2026.

| Figura do autor | Cópia local | Resolução |
|---|---|---|
| [PCV-Exemplo (pesos)](https://otimizacaonapratica.wordpress.com/wp-content/uploads/2015/11/pcv-exemplo.png) | [mapa_18_pardini_pesos.png](../assets/referencias/mapa_18_pardini_pesos.png) | 1225 × 895 |
| [PCV-Grafo (ligações)](https://otimizacaonapratica.wordpress.com/wp-content/uploads/2015/11/pcv-grafo.png) | [mapa_18_pardini_ligacoes.png](../assets/referencias/mapa_18_pardini_ligacoes.png) | 1216 × 895 |

SHA-256 das cópias, também registrados no JSON e verificados pelos testes:

- Pesos: `ada90739e682474072701df4da460b04414ef4c818ea267c4740a2e1edede27e`.
- Ligações: `ca42f5d66f22f3ca505423187ba342ae2965ce3e6d8ec0520e533c57cccd5fc4`.

A captura fornecida na aula continua preservada em `assets/referencias/mapa_18_original.png`. As figuras complementares apresentam a mesma disposição de nós e conexões e foram usadas para cotejo visual, sem substituir a captura recebida.

## Pontos que exigiam revisão

| Ponto | Resultado observado |
|---|---|
| `4–14` | A linha longa liga os nós 4 e 14; o rótulo `56` está associado a ela. Peso confirmado: 56. |
| `9–14` | Linha diagonal visível nas duas figuras. Não há rótulo numérico nessa linha, inclusive na figura original de 1225 × 895. Existência confirmada; custo desconhecido. |
| `9–16` | A linha quase vertical tem rótulo `43`. Esse valor não foi transferido para `9–14`. |
| `6–11` | Linha com peso `30`; não corresponde a uma ligação `5–11`. |
| Cruzamentos | Conferidos seguindo as linhas até os círculos numerados. Não representam cidades ou junções adicionais. |

## Tabela de adjacência revisada

Cada célula lista `vizinho (peso)`. A tabela é simétrica e contém 90 incidências, correspondentes a 45 arestas. `?` representa o único custo não informado; não é zero. A tabela preserva essa pendência e ainda não define uma instância totalmente ponderada.

| Nó | Vizinhos e pesos |
|---:|---|
| 1 | 2 (20), 8 (29), 12 (29), 13 (37) |
| 2 | 1 (20), 3 (25), 8 (28), 12 (39) |
| 3 | 2 (25), 4 (25), 8 (30), 13 (54) |
| 4 | 3 (25), 5 (39), 6 (32), 7 (42), 9 (23), 10 (33), 14 (56) |
| 5 | 4 (39), 6 (12), 7 (26), 10 (19) |
| 6 | 4 (32), 5 (12), 7 (17), 10 (35), 11 (30) |
| 7 | 4 (42), 5 (26), 6 (17), 11 (38) |
| 8 | 1 (29), 2 (28), 3 (30), 12 (25), 13 (22) |
| 9 | 4 (23), 10 (26), 13 (34), 14 (?), 16 (43) |
| 10 | 4 (33), 5 (19), 6 (35), 9 (26), 11 (24), 14 (30), 15 (19) |
| 11 | 6 (30), 7 (38), 10 (24), 15 (26), 18 (36) |
| 12 | 1 (29), 2 (39), 8 (25), 13 (27), 16 (43) |
| 13 | 1 (37), 3 (54), 8 (22), 9 (34), 12 (27), 14 (24), 16 (19) |
| 14 | 4 (56), 9 (?), 10 (30), 13 (24), 15 (20), 16 (19), 17 (17) |
| 15 | 10 (19), 11 (26), 14 (20), 17 (18), 18 (21) |
| 16 | 9 (43), 12 (43), 13 (19), 14 (19), 17 (26) |
| 17 | 14 (17), 15 (18), 16 (26), 18 (15) |
| 18 | 11 (36), 15 (21), 17 (15) |

## Testes e pendência de aceite

`tests/test_mapa_18.py` fixa todos os 44 pesos conferidos e a ligação `9–14` com `null`, além de conferir estrutura, metadados, hashes e resoluções das fontes. Os testes detectam alterações posteriores; a leitura dos rótulos foi feita por inspeção visual das figuras, não por inferência de distância.

Para concluir a TSP-004, é necessário obter uma referência que informe explicitamente o peso de `9–14` ou uma definição do professor. Então atualizar o registro de evidência, a tabela, o JSON e os testes antes de mudar `validado` para `true`. Não atribuir média, distância em pixels, zero, `43` ou `56`, nem excluir a ligação para contornar a ausência do custo.
