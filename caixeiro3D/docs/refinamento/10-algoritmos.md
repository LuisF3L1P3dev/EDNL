# TASK 10 — algoritmos e limites

Os algoritmos continuam separados da renderização e trabalham exclusivamente
com a adjacência canônica dos mapas. A força bruta enumera circuitos com origem
fixa e é limitada a grafos de até 9 nós; no mapa de 18 nós ela é recusada antes
de iniciar a enumeração. Dijkstra calcula somente o menor caminho entre origem
e destino. Para o circuito grande, a heurística constrói a matriz por Dijkstra,
aplica vizinho mais próximo e 2-opt e expande cada salto de volta para ruas
reais do grafo. Portanto pode revisitar nós intermediários, mas visita todas as
cidades e termina na origem sem inventar conexões.

A interface segue o mesmo limite: força bruta fica disponível apenas no mapa
de 5 pontos, heurística apenas no de 18 e Dijkstra nos dois. Os controles
recusam uma seleção indisponível sem trocar o método atual.

Validação: `tests/test_contratos.py` verifica especificamente o mapa canônico
de 18 pontos: circuito fechado, todos os ids, cada par consecutivo adjacente,
custo igual à soma das arestas reais e recusa da força bruta. A integração
verifica a disponibilidade dos três métodos nos dois mapas.
