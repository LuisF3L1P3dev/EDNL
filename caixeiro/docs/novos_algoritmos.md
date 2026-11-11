# Planejamento dos próximos algoritmos 2D

Esta etapa implementou a identificação visual da TSP-025. As tarefas abaixo estão **planejadas**, não representam implementações ou dependências já instaladas. Os IDs 022–024 do 3D foram preservados; os novos métodos 2D têm prioridade antes dessa migração.

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

O resultado deve identificar método e pipeline, variante do problema, ordem de entregas, percurso físico, custo na unidade original, motivo de término e garantia. Origem/destino, limites de nós/memória/tempo e disponibilidade da dependência devem ser validados antes de iniciar. Progresso e eventos precisam preservar a identidade do método sem a UI acessar estado mutável do worker.

A garantia precisa distinguir busca exata concluída, heurística, aproximação sob pré-condições, melhor solução conhecida, ótimo local, cancelamento, limite e prova de inexistência. Tempo de preparo do fecho e tempo de otimização devem ser separados e acompanhados do custo total do pipeline.

## Condições de aplicação

**Nearest neighbor:** escolher a cidade não visitada mais próxima e fechar a rota é uma construção heurística. Na malha esparsa pode bloquear; isso não prova que não existe ciclo. O fecho é o modo padrão proposto para garantir trechos entre cidades conectadas, seguido da expansão pelos caminhos reais.

**2-opt:** refina uma rota fornecida, não constrói sozinho uma rota inicial. A interface deve mostrar, por exemplo, `nearest_neighbor + two_opt`. Uma troca só é aceita se preservar a viabilidade e reduzir custo. No fecho, a nova ordem deve ser reexpandida; no modo direto, não pode introduzir ligações ausentes. Esgotar a vizinhança permite falar em ótimo local dessa vizinhança, sem provar ótimo global.

**Held–Karp:** promover o controle independente de custo já existente a um solver com predecessores, ordem e percurso reconstruídos. A DP exata precisa de limites de memória/tempo e estado honesto quando interrompida. O custo 391 é referência do TSP Hamiltoniano no mapa 18 original, não um ótimo presumido para o problema de passeio no fecho.

**Christofides:** a garantia clássica de 3/2 exige grafo completo e não direcionado, pesos não negativos e desigualdade triangular. O pipeline inclui MST, vértices ímpares, matching perfeito de peso mínimo, ciclo Euleriano e atalhamento. Nos mapas esparsos, o plano é aplicar ao fecho métrico e expandir os trechos. A garantia refere-se ao ótimo dessa mesma instância métrica. Ver a documentação de [NetworkX](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.approximation.traveling_salesman.christofides.html) e [JGraphT](https://jgrapht.org/javadoc/org.jgrapht.core/org/jgrapht/alg/tour/ChristofidesThreeHalvesApproxMetricTSP.html).

**OR-Tools:** o Routing Solver não garante sempre a solução ótima e as meta-heurísticas exigem limite de busca. Por isso a tarefa exige status e parâmetros registrados, validação física da saída e dependência opcional. A instalação/compatibilidade será verificada quando a tarefa for executada. Ver a [documentação oficial de TSP do OR-Tools](https://developers.google.com/optimization/routing/tsp).

## Aceite de integração

Os dois JSON e pesos fixos permanecem intactos. Todo resultado é conferido pela soma das arestas físicas. A comparação só agrupa métodos com o mesmo modo/matriz, origem e regras, e calcula gap apenas quando há ótimo comprovado do mesmo problema. A UI mantém nome, etapa e garantia durante cálculo e reprodução e não apresenta um algoritmo planejado como disponível.

Implementar na ordem TSP-026 → TSP-027 → TSP-028; depois TSP-029, TSP-030/TSP-031 e TSP-032. Os critérios detalhados e dependências estão no [TASKS.md](../TASKS.md).
