# TASK03 — Modelo visual independente

O grafo matemático permanece em `tsp_core.py`, carregado dos mesmos JSONs. A
apresentação agora é um `MapaVisual` imutável em `geometria3d.py`:

- `NoVisual` referencia o objeto `No` original e expõe identificador e posição
  lógica por propriedades. Acrescenta posição 3D, endereço e conexões validadas.
- `ConstrucaoVisual` reserva posição, kit/modelo local e tamanho do lote para
  cada endereço. Essa referência determinística será usada pela TASK05; nesta
  etapa a decoração legada continua sendo desenhada da mesma forma.
- `ArestaVisual` referencia o objeto `Aresta` original. Origem, destino e peso
  são propriedades delegadas, sem outro cadastro de pesos. Somente o caminho
  visual é acrescentado.
- `MapaVisual` valida a correspondência exata dos nós, arestas e adjacência.
  As propriedades `posicoes` e `ruas` são mapas somente de leitura, com tuplas
  imutáveis e percursos bidirecionais.

`criar_mapa_visual(grafo, posicoes=..., construcoes=...)` permite reorganizar os
elementos sem modificar o grafo. Sua cache é limitada a 16 apresentações e usa
identidade do objeto Grafo mais a configuração imutável: recarregar um grafo
igual não reutiliza referências pertencentes ao objeto anterior. Chamadas
repetidas com a mesma configuração devolvem a mesma apresentação.

`Cena3D.mapa_visual` consome essa fábrica; `Cena3D.posicoes` e `Cena3D.ruas`
apontam para as propriedades da mesma apresentação. Os auxiliares existentes
`posicoes_mundo` e `ruas_mundo` continuam disponíveis e devolvem cópias mutáveis
dos mesmos dados, preservando a interface anterior e protegendo a cache.

O envelope `limites_xy` inclui todos os waypoints das ruas e os perímetros dos
lotes. O terreno acrescenta margem a esse envelope, incluindo futuros desvios
de ruas e pontes além da posição dos nós. Não depende apenas de nó + 4 unidades.

## Escopo preservado

As coordenadas e as polilinhas legadas permanecem idênticas nesta etapa. Não
foram alterados JSONs, topologia, pesos, algoritmos, animação, HUD ou orientação
da van. O roteamento ortogonal e suas estruturas de portas, praças e pontes
pertencem à TASK04. O desenho dos endereços associados pertence à TASK05.

## Validação

`tests/test_layout_visual.py` verifica a referência aos objetos originais, a
correspondência exata dos 5/18 nós e 8/45 arestas, os endereços determinísticos,
a imutabilidade da cache e suas cópias de compatibilidade. Também reorganiza
posições e confirma que adjacência, Dijkstra, TSP exato e heurística mantêm os
mesmos percursos e custos. Cadastros incompletos, falsos, copiados ou com
coordenadas inválidas são rejeitados. Um desvio distante e um lote afastado
confirmam que o envelope inclui elementos além dos nós.

Comandos de verificação:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p test_layout_visual.py -v
.venv\Scripts\python.exe -m unittest discover -s tests -p test_mundo3d.py -v
.venv\Scripts\python.exe -m unittest discover -s tests -p test_render3d.py -v
.venv\Scripts\python.exe main.py --offscreen --frames 2 --mapa 5
.venv\Scripts\python.exe main.py --offscreen --frames 2 --mapa 18
```

Resultado desta etapa: 8 testes do modelo visual aprovados, 21 testes de
assets/câmera/mundo/renderização aprovados e execução offscreen de 2 frames nos
dois mapas encerrada sem erro. As dimensões mínimas do terreno dos cenários
existentes continuam sendo 52 × 46 unidades.
