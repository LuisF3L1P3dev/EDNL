# Vizinho mais próximo — TSP-027

`executar("nearest_neighbor", grafo, origem)` usa o fecho por padrão. A cada
passo escolhe o menor peso entre cidades não visitadas; empate pelo ID. Fecha
na origem e expande os saltos nas arestas reais. Complexidade da construção:
O(n²), além da preparação Dijkstra. Não prova ótimo.

`variante="original"` usa somente as ligações cadastradas. Uma escolha que
trava, inclusive no retorno, termina em `construcao_bloqueada`; isso não prova
inviabilidade. Um mapa desconectado é recusado para o fecho. Uma cidade produz
rota trivial e custo zero. Eventos `escolha` guardam rota parcial, cidade,
custo acumulado e caminho físico, sob orçamento e cancelamento comuns.

Testes cobrem os dois mapas, custos físicos, desempate, origem arbitrária,
cidade única, desconexão, construção bloqueada apesar de haver ciclo e
comparação com força bruta na mesma variante. Integração visual conjunta na
TSP-032; o solver já está disponível pelo registro do núcleo.
