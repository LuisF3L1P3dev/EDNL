# TASKS — Plano de implementação do TSP 2D → 3D

**Projeto:** NEXUS TSP — Caixeiro Viajante com Dijkstra e força bruta  
**Primeira entrega:** Python + Pygame **2D**, com os dois grafos fixos da aula.  
**Fase futura:** 3D, sem alterar a definição dos grafos.

## Convenção

- `[x]` Artefatos presentes neste repositório e aceite da tarefa conferido.
- `[ ]` Pendente de implementação, auditoria ou verificação local.
- `P0`: bloqueante; `P1`: essencial ao MVP; `P2`: aprimoramento; `P3`: evolução futura.
- **Dificuldade:** Low, Medium e High.
- O fato de uma tarefa de código estar marcada `[x]` não significa que a interface Pygame já foi validada em todas as máquinas. Rodar a interface visualmente ainda é necessário.

**Execução por etapas:** implementar uma tarefa por vez e aguardar autorização do usuário antes da próxima, permitindo revisão e commit. A base recebida em `docs/ativ/` contém as referências e os materiais da aula. As referências estáveis, os dois cadastros JSON, a representação/validação do grafo, Dijkstra e seus testes estão presentes; os algoritmos TSP e a interface serão implementados nas tarefas seguintes. O mapa 18 continua não validado pela falta do peso de `9–14`.

## Epic 01 — Especificação, referências e dados fixos

- [x] **TSP-001 — Organizar as referências originais** · `P0 / Low`
  - Guardar as duas imagens no repositório, com nomes estáveis.
  - **Aceite:** ambas acessíveis em `assets/referencias/`.
  - **Conferido:** cópias binariamente idênticas às imagens em `docs/ativ/` (SHA-256 iguais). Nenhum redimensionamento ou edição foi aplicado.

- [x] **TSP-002 — Transcrever e testar o mapa de 5 nós** · `P0 / Medium`
  - Preservar 5 IDs, 8 arestas e todos os pesos da figura.
  - Impedir criação automática de arestas ausentes.
  - **Aceite:** ciclo de referência `1-2-3-5-4-1` tem custo 15.
  - **Conferido:** `data/mapa_05.json` preserva os 5 IDs, as 8 arestas e seus pesos. Os 6 testes em `tests/test_mapa_05.py` passaram com `python -B -m unittest discover -s tests -v`; cobrem também as ligações ausentes e o ciclo inverso.

- [x] **TSP-003 — Preparar o cadastro do mapa de 18 nós** · `P0 / Medium`
  - Preservar os 18 IDs, coordenadas para desenho e pesos identificáveis.
  - Marcar explicitamente a dúvida sobre `9-14`.
  - **Aceite:** JSON contém 18 nós; nenhuma aresta com valor incerto recebe peso inventado.
  - **Conferido:** `data/mapa_18.json` contém 18 IDs, coordenadas normalizadas e 45 ligações provisórias: 44 pesos transcritos e `9-14` com `null`. A associação `4-14:56` está explicitamente pendente. `validado` permanece `false`. Os 6 testes do cadastro em `tests/test_mapa_18.py` passaram; total de 12 testes aprovados no projeto. Esses testes não substituem a auditoria dos pesos da TSP-004.

- [ ] **TSP-004 — Auditar integralmente o mapa de 18 nós** · `P0 / High` · **Bloqueante**
  - Revisar a linha/peso `9-14`, o rótulo `56` associado a `4-14` e todas as demais conexões.
  - Preferir imagem ou fonte original de maior resolução.
  - **Aceite:** tabela definitiva de adjacência revisada; `data/mapa_18.json` passa a `validado: true`; testes automatizados cobrindo todos os pesos.
  - **Avanço parcial:** fonte do próprio autor obtida em 1225 × 895 (pesos) e 1216 × 895 (ligações). As 45 conexões e os 44 pesos foram conferidos, incluindo `4-14:56`. A aresta `9-14` existe, mas não possui peso indicado nem nessa fonte. Tabela e evidências em `docs/auditoria_mapa_18.md`; regressão cobrindo os 44 pesos. `validado` permanece `false`; tarefa aberta até obter o custo faltante de fonte explícita ou definição do professor.

- [x] **TSP-005 — Documentar as restrições acadêmicas** · `P0 / Low`
  - Esclarecer peso fixo ≠ distância em pixels.
  - Diferenciar caminho mínimo de TSP e marcar transcrições não validadas.
  - **Aceite:** `README.md` e `AUDITORIA_MAPAS.md` presentes.

## Epic 02 — Núcleo matemático em Python

- [x] **TSP-006 — Implementar representação do grafo** · `P1 / Medium` · depende de TSP-002
  - Carregar JSON, validar nós, pares de arestas e pesos não negativos.
  - Gerar adjacência não orientada sem criar ligações inexistentes.
  - **Aceite:** mapas malformados produzem erro; mapa pendente bloqueia os algoritmos.
  - **Conferido:** `tsp_core.py` carrega JSON UTF-8 e fornece `No`, `Aresta` e `Grafo` imutáveis. Valida metadados, IDs, coordenadas, duplicatas, extremos e pesos finitos não negativos. `Grafo.adjacencia()` exige mapa validado, preserva somente ligações reais e produz vizinhança simétrica imutável. O mapa 18 pode ser inspecionado sem habilitar cálculos. Os 19 testes do núcleo passaram; 33 testes aprovados no projeto com `python -B -m unittest discover -s tests -v`.

- [x] **TSP-007 — Implementar Dijkstra com reconstrução do caminho** · `P1 / Medium` · depende de TSP-006
  - Usar fila de prioridade e vetor de predecessores.
  - Entrada: grafo, origem e destino. Saída: sequência e custo.
  - **Aceite:** no mapa 5, de 1 até 3 a distância mínima é 6 (`1-2-3`).
  - **Conferido:** `dijkstra(grafo, origem, destino)` usa heap mínimo, distâncias tentativas, nós finalizados e predecessores em `tsp_core.py`. Retorna `ResultadoDijkstra` imutável; caminho vazio e custo infinito sinalizam destino inalcançável. Os 18 testes em `tests/test_dijkstra.py` cobrem os 25 pares do mapa 5, o caso de custo 6, bloqueio do mapa 18, empates, pesos zero/fracionários e entradas inválidas. Total: 51 testes aprovados com `python -B -m unittest discover -s tests -v`.

- [x] **TSP-008 — Implementar TSP trivial por força bruta** · `P1 / Medium` · depende de TSP-006
  - Enumerar ordens com origem fixa e retorno à origem.
  - Ignorar candidatos com arestas não existentes.
  - Impor limite de até 9 nós na versão didática.
  - **Aceite:** mapa 5 tem custo ótimo 15; mapa 18 não tenta avaliar `17!` permutações.
  - **Conferido:** `tsp_forca_bruta()` enumera 24 ordens no mapa 5, retorna ciclo de custo 15 e impõe limite de 9 nós antes da enumeração. Testes em `tests/test_tsp.py`.

- [x] **TSP-009 — Implementar fecho métrico por Dijkstra + busca exata** · `P1 / High` · depende de TSP-007 e TSP-008
  - Calcular caminhos mínimos entre todos os destinos.
  - Buscar a melhor ordem de entregas sobre a matriz de menores distâncias.
  - Reconstruir o percurso físico usando as arestas reais.
  - **Aceite:** no mapa 5, custo 15 e percurso físico com soma correta.
  - **Conferido:** `fecho_metrico()` e `tsp_dijkstra()` calculam distâncias, buscam a ordem exata e expandem o percurso sobre arestas reais. Testes incluem custo 15, estrela sem ciclo Hamiltoniano, grafo desconectado e limite de 9 nós.

- [x] **TSP-010 — Registrar passos intermediários dos algoritmos** · `P2 / High` · depende de TSP-007, TSP-008
  - Dijkstra: fila, distâncias tentativas, nós visitados, relaxamentos e predecessores.
  - Força bruta: candidato atual, custo, melhor solução e contador.
  - **Aceite:** histórico de eventos reproduzível sem depender do Pygame.
  - **Conferido:** snapshots imutáveis `Passo`, gravação opcional por `eventos=`, fila/distâncias/visitados/relaxamentos/predecessores e candidatos/melhor/custo/contador. Testes reproduzem históricos e confirmam que gravar não altera resultados.

## Epic 03 — Visualização 2D no Pygame

- [x] **TSP-011 — Criar janela e layout 2D inicial** · `P1 / Medium`
  - Janela com mapa central, controle lateral e painel de resultados.
  - **Aceite:** código em `main.py` com UI separada do núcleo matemático.
  - **Conferido:** entrada em `main.py`, apresentação em `tsp_ui.py`, janela redimensionável com mapa, controle lateral e resultados. Ambiente virtual com pygame-ce 2.5.8 (API pygame) instalado; renderização inicial conferida com driver dummy. Smoke visual completo permanece na TSP-017.

- [x] **TSP-012 — Desenhar mapas, pesos e nós fixos** · `P1 / Medium` · depende de TSP-001, TSP-003
  - Renderizar nós e arestas sem recalcular pesos pela posição.
  - Permitir alternar os dois mapas e visualizar as referências originais.
  - **Aceite:** 5 ou 18 nós desenhados conforme o mapa escolhido; peso incerto apresentado como `?`.
  - **Conferido:** renderiza os cadastros sem recalcular custos; botões/atalhos 1/2, O para referência original e P para pesos. O custo ausente de 9–14 é desenhado como `?`.

- [x] **TSP-013 — Implementar seleção de origem/destino e botões** · `P1 / Medium` · depende de TSP-011
  - Clique em nós; botões para força bruta, Dijkstra, comparação e alternância de mapas.
  - **Aceite:** comandos de teclado e mouse implementados.
  - **Conferido:** seleção alternada de origem/destino por clique; F/D/C executam algoritmos em worker, com validação antes de iniciar; 1/2/O/P/L e botões implementados. Seleções ficam estáveis durante cálculo; resultados são entregues ao loop sem bloquear eventos.

- [x] **TSP-014 — Destacar caminho calculado** · `P1 / Medium` · depende de TSP-007, TSP-008
  - Mostrar caminho em cor distinta, custo e rota textual.
  - **Aceite:** caminho visual segue os IDs resultantes do algoritmo.
  - **Conferido:** caminhos físicos destacados nas arestas reais; força bruta em verde, Dijkstra em azul e fecho em roxo. Resultados exibem tipo do problema, custo, percurso e ordens testadas; limpar remove o destaque.

- [x] **TSP-015 — Criar animação passo a passo** · `P2 / High` · depende de TSP-010
  - Botões Reproduzir, Pausar, Próxima etapa, Voltar e Velocidade.
  - **Aceite:** animação não bloqueia processamento de eventos do Pygame.
  - **Conferido:** `Reprodutor` desacoplado, controle por delta de tempo, Play/Pausar/Voltar/Próximo/Velocidade/Final. Mostra distâncias, fila, visitados, relaxamentos e candidatos; candidatos no fecho têm percurso físico expandido. Testes de relógio e histórico sem Pygame.

- [x] **TSP-016 — Melhorar responsividade e legibilidade do grafo de 18 nós** · `P2 / Medium` · depende de TSP-012, TSP-004
  - Zoom, pan, exibição seletiva de pesos e labels que evitem colisões.
  - **Aceite:** arestas, IDs e pesos podem ser inspecionados sem ambiguidade visual.
  - **Conferido:** zoom ancorado no cursor (roda ou +/−), arraste com botão direito/meio, Z para reset; P alterna todos/incidentes ao nó/ocultos. Labels evitam nós e outros labels; inspeção por cursor identifica pares e custos inclusive em cruzamentos. A pendência da TSP-004 não impede a inspeção visual; `?` permanece para 9–14.

- [ ] **TSP-017 — Smoke test visual em Pygame** · `P1 / Medium` · depende de TSP-011 a TSP-014
  - Instalar requisitos, abrir programa e testar todos os botões.
  - Validar clique nos nós, desenhos, cores, teclado, alternância de mapas e mensagens de erro.
  - **Aceite:** testes manuais reproduzíveis registrados em `docs/` ou no relatório da equipe.
  - **Avanço parcial:** requisitos instalados; 11 casos SDL passaram em `scripts/smoke_pygame.py`, com log e capturas inspecionadas em `docs/`. A janela nativa foi iniciada, mas a ferramenta de captura permaneceu na aprovação de acesso ao Python. A autorização verbal do usuário foi recebida; a confirmação na interface ainda precisa ser concluída. Teste manual nativo não foi declarado realizado. Roteiro em `docs/smoke_pygame.md`.

## Epic 04 — Comparação e validação acadêmica

- [x] **TSP-018 — Criar testes automáticos iniciais** · `P1 / Medium` · depende de TSP-006 a TSP-009
  - Validar estrutura, distâncias, custos, ciclo e bloqueio do mapa incompleto.
  - **Aceite:** `python -m unittest discover -s tests -v` executa sem falhas.
  - **Conferido:** suíte cobre cadastros, núcleo, Dijkstra, TSP direto/fecho, históricos, reprodução, câmera e integração da interface. Acrescentados testes da diferença entre Hamiltoniano e passeio, expansão física, imutabilidade dos arquivos, worker, cliques e bloqueio do mapa pendente. Executar no ambiente com requirements instalados para incluir os testes SDL.

- [x] **TSP-019 — Publicar comparação formal entre métodos** · `P1 / Medium` · depende de TSP-017
  - Apresentar Dijkstra sozinho como caminho mínimo A→B, e não como TSP.
  - Comparar corretamente dois métodos completos para o mesmo TSP: força bruta direta × Dijkstra + busca exata no fecho métrico.
  - Medir custo, tempo e nós visitados/estados testados, sem misturar grandezas.
  - **Aceite:** tela/relatório esclarece por que os problemas comparados são distintos.
  - **Conferido:** `comparacao.py` e script geram relatório/JSON com mediana sem histórico, contadores separados e um controle em que ambos recebem a mesma instância métrica. UI identifica Hamiltoniano versus passeio. Contraexemplos testados. A publicação do núcleo independe da inspeção manual nativa pendente na TSP-017.

- [ ] **TSP-020 — Definir estratégia segura para o mapa de 18 nós** · `P1 / High` · depende de TSP-004
  - Dijkstra em pares funciona após validação; **não** executar força bruta ingênua de 18 nós.
  - Selecionar busca melhorada (Held–Karp, branch-and-bound ou OR-Tools) com justificativa.
  - **Aceite:** algoritmo para o mapa 18 termina dentro de um limite razoável e identifica se a solução é ótima comprovada ou apenas conhecida.

- [ ] **TSP-021 — Elaborar relatório e demonstração da aula** · `P2 / Medium` · depende de TSP-017 a TSP-020
  - Explicar grafos incompletos, pesos, Dijkstra, força bruta, complexidade e resultados.
  - Incluir capturas da versão 2D, referências originais, limitações e casos de teste.
  - **Aceite:** roteiro permite apresentar o projeto do início ao fim.

## Epic 05 — Conversão futura para 3D (não iniciar antes de concluir o 2D)

- [ ] **TSP-022 — Planejar renderização 3D desacoplada** · `P3 / High` · depende de TSP-017
  - Escolher Ursina/Panda3D e definir câmeras, posições XYZ e objetos de cena.
  - Preservar os arquivos JSON, arestas e pesos originais.
  - **Aceite:** o 3D apenas representa a mesma instância matemática.

- [ ] **TSP-023 — Migrar nós e arestas para representação 3D** · `P3 / High` · depende de TSP-022
  - Adicionar marcadores 3D de cidades e linhas de ligação no espaço.
  - **Aceite:** os mesmos testes de custo passam no 2D e no 3D.

- [ ] **TSP-024 — Animar veículo e percursos em 3D** · `P3 / High` · depende de TSP-023
  - Animar deslocamento sobre as arestas do grafo; manter algoritmos fora do render loop.
  - **Aceite:** a animação respeita a sequência e os pesos fixados na fase 2D.

## Dependências principais

```text
TSP-001 -> TSP-002 -> TSP-006 -> TSP-007 -> TSP-009
                         |            |          |
                         +-> TSP-008 -+----------+-> TSP-019

TSP-001 -> TSP-003 -> TSP-004 -> TSP-020

TSP-006..009 -> TSP-011..014 -> TSP-017 -> TSP-021
                                       |
                                       +-> TSP-022 -> TSP-023 -> TSP-024
```

## Próxima ação recomendada

**TSP-008: implementar TSP trivial por força bruta**, após autorização para a próxima etapa. A TSP-004 permanece aberta até obter o peso de `9-14`, ausente inclusive na fonte do autor. Dijkstra já bloqueia cálculos com esse mapa; o desenvolvimento prossegue com o mapa 5 validado.
