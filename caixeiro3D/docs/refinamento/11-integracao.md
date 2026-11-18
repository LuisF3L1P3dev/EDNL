# TASK 11 — validação de integração

A suíte reúne verificações dos dados matemáticos, algoritmos, geometria urbana,
câmera, van e interface. `tests/__init__.py` habilita a descoberta padrão do
`unittest`; sem ele, `python -m unittest discover` não encontrava os testes.

| Área | Cobertura principal |
| --- | --- |
| Grafos e algoritmos | `test_grafos`, `test_contratos`, `test_solvers`: contagens e pesos originais, ótimo 15 no mapa 5, Dijkstra em caminhos válidos, circuito heurístico fechado no mapa 18, soma dos pesos reais e limite da força bruta. |
| Ruas e construções | `test_layout_visual`, `test_render3d`: caminhos das arestas, pontes em níveis separados, afastamento de lotes e ruas, uma construção e um pin por nó, assets locais preservados. |
| Câmera | `test_camera3d`, `test_render3d`: projeção isométrica, enquadramento completo dos dois mapas, zoom, pan limitado, centralização e redimensionamento. |
| Van | `test_mundo3d`, `test_integracao`: orientação fixa do modelo, heading cardinal e transição curta, antecipação de curva, rampa, pausa, reinício, velocidades e destaque da aresta atual. |
| Interface | `test_hud`, `test_integracao`: mapa, métodos disponíveis, origem/destino, métricas, trecho atual, botões, progresso e layouts em 1100×760 e 1440×960. |

Execução completa: `..\venv\Scripts\python.exe -m unittest discover -v` —
**82 testes passaram, 0 falharam, em 48,325 s**. Panda3D emitiu o aviso esperado
de que o framebuffer disponível oferece mais bits que o mínimo solicitado; o
renderizador continuou e os testes de cena passaram. `git diff --check` também
passou.

As capturas finais dos mapas e a conferência visual da van em curva ficam na
TASK 12.
