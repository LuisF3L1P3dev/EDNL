# Christofides — TSP-030

O solver implementa MST por Prim, vértices de grau ímpar, matching perfeito
de peso mínimo **exato**, multigrafo com identidade por aresta, Hierholzer e
atalhamento. Todas as etapas têm snapshots. O modo padrão prepara o fecho
por Dijkstra e expande o passeio físico sem alterar os JSON.

Não há dependência extra de matching: DP memoizada fixa um ímpar e testa
todos os seus pares, O(k² 2ᵏ), com k ≤ 18. Essa escolha atende à dimensão
didática; não é uma implementação polinomial de Blossom nem matching guloso.
O orçamento cooperativo limita essa etapa também.

Pré-condições conferidas: grafo não direcionado, matriz completa e simétrica,
pesos não negativos e desigualdade triangular (tolerância numérica de 1e-12).
O modo original só é aceito se satisfizer essas condições; os mapas esparsos
devem usar fecho. A garantia ≤ 1,5 × ótimo refere-se ao **mesmo problema
métrico**, não ao ótimo Hamiltoniano 391 da malha original.

Testes comparam 21 instâncias métricas pequenas a Held–Karp, conferem ambos
os mapas, multiarestas, precondições e um matching em que a escolha gulosa
seria pior. Referência das condições: [documentação oficial NetworkX](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.approximation.traveling_salesman.christofides.html).
