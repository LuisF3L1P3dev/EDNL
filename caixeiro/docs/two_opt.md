# Melhoria 2-opt — TSP-028

`executar("two_opt", grafo, origem)` executa o pipeline
`nearest_neighbor + two_opt`. Aceita `ordem_inicial` como tupla ou resultado do
contrato comum, conferindo origem, modelo, cidades, fechamento e custo físico.
O algoritmo usa primeira melhoria estrita e recalcula o custo da rota completa:
O(n³) por varredura, até `max_iteracoes`, além do orçamento de tempo/estados.

Trocas com arcos ausentes têm custo infinito e são rejeitadas no modo original.
No fecho, cada melhoria é reexpandida nas arestas reais. Eventos `troca_2opt`
contêm arestas removidas/adicionadas e custos anterior/novo. A rota válida
incumbente permanece disponível durante cortes; seu custo nunca piora.

Somente uma varredura completa sem melhoria certifica `otimo_local`, relativo
à vizinhança de reversões 2-opt, nunca ao ótimo global. Corte por iterações,
estados, cancelamento ou tempo não recebe esse rótulo. Testes incluem uma
troca conhecida, rota já localmente ótima, restrições esparsas, orçamento e
os dois mapas. Integração visual conjunta na TSP-032.
