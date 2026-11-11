# TSP-020 — Busca segura até 18 nós

Foi implementado `tsp_branch_bound()` em `busca_limitada.py`, acessível pelo botão **B Busca limitada**. Resolve o TSP Hamiltoniano sobre as ligações existentes. Dijkstra A→B continua disponível em qualquer mapa validado, independentemente do limite didático de 9 nós dos enumeradores.

## Escolha e limites

Branch-and-bound foi escolhido por aproveitar a malha esparsa sem instalar um solver externo. Ordena vizinhos por custo e usa limite inferior admissível: árvore geradora mínima dos vértices restantes mais as ligações mínimas das duas pontas do percurso. Uma conclusão necessariamente contém essas conexões e uma árvore entre os restantes; portanto essa poda não descarta uma solução melhor.

Orçamento padrão: **2 segundos ou 200 mil estados**, o que ocorrer primeiro. Cache de árvores limitado a 8192 subconjuntos; profundidade máxima de 18 cidades. Verifica o orçamento a cada expansão; há pequeno custo adicional para terminar a expansão em curso. Não há garantia polinomial: em instâncias difíceis o algoritmo pode terminar sem achar uma rota, e isso não prova inexistência.

O resultado informa explicitamente:

| Estado | Interpretação |
|---|---|
| `otimo_comprovado` | Busca esgotada/podada com solução; ótimo provado |
| `sem_ciclo_comprovado` | Busca esgotada sem ciclo Hamiltoniano |
| `melhor_conhecida` | Limite atingido com rota viável; ótimo não provado |
| `limite_sem_solucao` | Limite atingido sem rota encontrada; não prova inexistência |

Os estados expandidos não são permutações completas; a interface os identifica separadamente. O solver roda no worker e não bloqueia o loop Pygame.

## Validação executada e limitação real

Os testes comparam o resultado ao enumerador exato em todas as origens do mapa 5. Uma instância **sintética** de 18 nós em anel é resolvida com custo 18 e prova de ótimo dentro do orçamento. Também são testados cortes com/sem solução e ausência comprovada de ciclo.

**TSP-020 concluída no mapa real**, após o usuário definir `9–14 = 1` e a TSP-004 validar o cadastro. Dijkstra 9→14 retorna custo 1; Dijkstra 1→18 retorna custo 93. A força bruta ingênua continua recusando 18 nós.

Resultado real de `tsp_branch_bound(carregar_mapa('data/mapa_18.json'), 1)`:

- Custo: **391**, `otimo_comprovado`.
- Estados expandidos: **1159**; aproximadamente **18 ms** nesta execução, dentro do orçamento padrão de 2 segundos. O tempo varia por máquina.
- Ciclo: `1 → 2 → 3 → 4 → 9 → 14 → 15 → 10 → 5 → 6 → 7 → 11 → 18 → 17 → 16 → 13 → 8 → 12 → 1`.
- Controle independente por programação dinâmica Held–Karp: **391**, 153860 estados, aproximadamente 173 ms nesta execução. Esse controle não usa o limite inferior/MST do branch-and-bound.

Reproduzir com `python scripts/validar_mapa_18.py`. Dados completos e tempos medidos: [resultados_mapa_18.json](resultados_mapa_18.json). A suíte compara também todos os 324 pares de Dijkstra com Floyd–Warshall e confere a soma das arestas reais do ciclo. Os testes de recusa de mapas pendentes continuam usando cópia sintética em memória.
