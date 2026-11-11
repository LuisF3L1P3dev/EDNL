# Contrato dos solvers — TSP-026

`solvers.executar` é a entrada do worker. O resultado imutável identifica método,
pipeline, origem, variante, ordem de cidades, caminho físico, custo, garantia e
motivo de término. Tempos em milissegundos separam preparação, otimização e
reconstrução; o total inclui snapshots limitados, sem repetir a busca.
Contadores declaram sua unidade. O registro informa variantes, limite, atalho
e disponibilidade de dependências. As APIs didáticas anteriores continuam públicas.

`original` exige ciclo nas arestas cadastradas. `fecho` usa Dijkstra em todos os
pares e expande cada salto na malha física. `caminho_minimo` aceita origem/destino
e não é TSP. A saída TSP é conferida por cobertura, origem, fechamento, expansão,
arestas reais e soma física. A conectividade é verificada; o fecho desconectado
é recusado. Os JSON permanecem intactos.

O orçamento limita tempo, estados, memória de DP, iterações e snapshots. O sinal
de cancelamento é cooperativo: X/botão Cancelar ou fechamento da janela. A fila
de fases continua sendo consumida pelo loop Pygame. Uma interrupção preserva
o melhor ciclo completo encontrado, sem prova. `inviavel_comprovado`,
`indisponivel`, `cancelado` e `limite_*` são términos diferentes.

Validação: 101 testes; adaptadores preservam 6 (Dijkstra), 15 (mapa 5) e
391 (branch-and-bound no mapa 18 original), além de estados, orçamento,
snapshots, progresso e guardas. Os limites de memória/iterações são usados
pelos solvers que possuem essas estruturas, nas tarefas seguintes.
