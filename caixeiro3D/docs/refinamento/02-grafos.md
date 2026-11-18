# TASK 02 — Conferência dos grafos

Os arquivos `data/mapa_05.json` e `data/mapa_18.json` permanecem a fonte única dos dados matemáticos. O registro `carregar_cenarios` os abre nessa ordem e verifica identidade, identificadores 1–5 ou 1–18, respectivamente 8 ou 45 arestas, ausência de pendências e conectividade. `Grafo` também valida pesos positivos finitos, extremos e duplicações. O registro não substitui os testes das listas e pesos exatos.

## Fontes e decisões

A referência de cinco nós é `ref/Mapa Isométrico do Caixeiro Viajante.png`; as oito arestas e seus pesos são prescritos explicitamente por `tasks.md`. O ótimo é custo **15**, por exemplo 1 → 2 → 3 → 5 → 4 → 1 ou seu inverso.

A referência de 18 nós é `ref/Mapa Isométrico da Rota Mais Curta.png`. Foram consultados os PNGs originais pela cópia em Git, sem restaurar os arquivos removidos do diretório de trabalho. Na referência maior, algumas marcações são ambíguas: o segmento 9–13 tem o peso preto 34 e um realce azul com 1; o traço vermelho entre 1 e 13 não tem peso próprio legível; a ligação 1–3 = 37 foi confirmada pelo usuário e não é inferida apenas da ilustração. Prevalecem as decisões explícitas anteriores: **1–3 = 37**, **9–13 = 34**, **9–14 = 1**. Não foi criada aresta 1–13. Cruzamentos gráficos sem nó comum não criam conexões. As ruas decorativas e o formato da rota não modificam essas adjacências.

A transcrição completa está em [grafos.md](../grafos.md), inclusive as 45 arestas. O oráculo independente em `tests/test_grafos.py` confere cada tripla e a adjacência simétrica; `tests/test_cenarios.py` verifica o registro e suas falhas. `tests/test_contratos.py` compara Dijkstra com Floyd–Warshall nos 349 pares, confere os circuitos expandidos da heurística para todas as origens e verifica o ótimo 15 a partir de cada nó do mapa pequeno. Esses testes comprovam os dados implementados e os contratos algorítmicos, não eliminam a ambiguidade visual documentada.
