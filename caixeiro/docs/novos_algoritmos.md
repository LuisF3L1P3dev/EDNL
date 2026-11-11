# Algoritmos 2D — TSP-026 a TSP-032 concluídas

As sete tarefas foram implementadas e commitadas individualmente. Os cinco
novos métodos estão disponíveis na segunda página da interface (Tab), com
modelo, orçamento e garantia. OR-Tools é opcional e foi instalado/testado no
ambiente Python 3.14. Os IDs 022–024 do 3D foram preservados e continuam futuros.

| Tarefa | Método / entrega | Natureza | Base e cuidado principal |
|---|---|---|---|
| TSP-026 | Contrato e registro comum | Infraestrutura | Mesma descrição de problema, custo, rota física, garantia e término |
| TSP-027 | `nearest_neighbor` | Heurística construtiva | Fecho métrico por padrão; desempate determinístico, sem prova de ótimo |
| TSP-028 | `two_opt` | Melhoria local | Exige rota inicial viável; manter modelo e mostrar o pipeline que gerou a rota |
| TSP-029 | `held_karp` | Busca exata por DP | Reconstrução da ordem, memória e orçamento; não é somente o verificador de custo já existente |
| TSP-030 | `christofides` | Aproximação para TSP métrico | Pré-condições verificadas, matching perfeito mínimo e expansão física |
| TSP-031 | `ortools_solver` | Solver configurável | Dependência opcional, limites e status sem presumir ótimo |
| TSP-032 | Integração e comparação | Validação | Mesmo problema/matriz e métricas com unidades consistentes |

## Contrato que a interface precisa receber

O [contrato implementado](contrato_solvers.md) identifica método e pipeline,
variante, ordem de entregas, percurso físico, custo, término e garantia.
Validação, orçamento, cancelamento e snapshots são comuns ao registro/worker.

A garantia precisa distinguir busca exata concluída, heurística, aproximação sob pré-condições, melhor solução conhecida, ótimo local, cancelamento, limite e prova de inexistência. Tempo de preparo do fecho e tempo de otimização devem ser separados e acompanhados do custo total do pipeline.

## Condições de aplicação

**Nearest neighbor:** escolher a cidade não visitada mais próxima e fechar a rota é uma construção heurística. Na malha esparsa pode bloquear; isso não prova que não existe ciclo. O fecho é o modo padrão proposto para garantir trechos entre cidades conectadas, seguido da expansão pelos caminhos reais.

**2-opt:** refina uma rota fornecida, não constrói sozinho uma rota inicial. A interface deve mostrar, por exemplo, `nearest_neighbor + two_opt`. Uma troca só é aceita se preservar a viabilidade e reduzir custo. No fecho, a nova ordem deve ser reexpandida; no modo direto, não pode introduzir ligações ausentes. Esgotar a vizinhança permite falar em ótimo local dessa vizinhança, sem provar ótimo global.

**Held–Karp:** [solver com predecessores](held_karp.md), limites de memória/tempo
e reconstrução implementado. O controle independente de custo foi preservado.
391 é referência Hamiltoniana original, não um ótimo presumido para o fecho.

**Christofides:** a garantia clássica de 3/2 exige grafo completo e não direcionado, pesos não negativos e desigualdade triangular. O pipeline inclui MST, vértices ímpares, matching perfeito de peso mínimo, ciclo Euleriano e atalhamento. Nos mapas esparsos, o plano é aplicar ao fecho métrico e expandir os trechos. A garantia refere-se ao ótimo dessa mesma instância métrica. Ver a documentação de [NetworkX](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.approximation.traveling_salesman.christofides.html) e [JGraphT](https://jgrapht.org/javadoc/org.jgrapht.core/org/jgrapht/alg/tour/ChristofidesThreeHalvesApproxMetricTSP.html).

**OR-Tools:** [adaptador opcional](ortools_solver.md) implementado e validado com
9.15.6755/cp314/Windows. Registra parâmetros/status, remove arcos ausentes do
domínio e valida a rota física. Não promove sucesso a certificado de ótimo.
Ver a [documentação oficial](https://developers.google.com/optimization/routing/tsp).

## Aceite de integração

Os dois JSON e pesos fixos permanecem intactos. Todo resultado é conferido pela soma das arestas físicas. A comparação só agrupa métodos com o mesmo modo/matriz, origem e regras, e calcula gap apenas quando há ótimo comprovado do mesmo problema. A UI mantém nome, etapa e garantia durante cálculo e reprodução e não apresenta um algoritmo planejado como disponível.

Entregas: [nearest neighbor](nearest_neighbor.md), [2-opt](two_opt.md),
[Held–Karp](held_karp.md), [Christofides](christofides.md), [OR-Tools](ortools_solver.md),
[integração e capturas](integracao_solvers.md), [comparação do mesmo problema](comparacao_solvers.md).
Critérios e dependências no [TASKS.md](../TASKS.md).
