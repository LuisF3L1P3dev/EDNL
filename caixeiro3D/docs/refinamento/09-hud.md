# TASK 09 — HUD e painéis de entrega

O HUD preserva a identidade **NEXUS · ROTAS & ENTREGAS**, os seletores de mapa,
os painéis de planejamento e resultados, métricas, legendas e controles de
entrega já presentes no layout de referência. Cores permanecem semânticas:
azul para pontos/ação principal, amarelo para rota e verde para visitas.

A barra inferior agora inclui um resumo fixo do trecho da van, separado dos
botões e da barra de progresso: informa o ponto que aguarda uma rota, a aresta
em execução, a mesma aresta quando pausada, a espera no nó de chegada com a
próxima aresta e o último trecho ao concluir. Isso acompanha a viagem sem
alterar os pesos, a rota ou a renderização do mapa.

Validação: `python -m unittest tests.test_hud -v` cobre os controles e painéis
em `1100×760` e `1440×960`, a ausência de sobreposição, o trecho em todos os
estados e a nomenclatura NEXUS.
