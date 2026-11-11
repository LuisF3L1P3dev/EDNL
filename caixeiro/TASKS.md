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

**Execução autorizada:** o usuário autorizou implementar sequencialmente até a TSP-021 e fazer um commit por tarefa, sem pedir autorização entre etapas. Foram entregues algoritmos, eventos, Pygame, controles, animação, câmera, testes e relatórios. Após definir `9–14 = 1`, as TSP-004 e TSP-020 foram concluídas com execução no mapa real. Permanece aberta a inspeção manual nativa da TSP-017. A fase 3D não foi iniciada.

**Pedido posterior:** implementar a identificação visual TSP-025 e criar o planejamento dos novos métodos. TSP-026 a TSP-032 ficam pendentes para execução posterior; não foram iniciadas automaticamente.

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
  - **Histórico da entrega:** cadastro inicial com 18 IDs, coordenadas normalizadas e 45 ligações provisórias; 9–14 foi mantida com `null` até obter fonte explícita. A TSP-004 encerrou a pendência com o valor 1 fornecido pelo usuário e validou os 45 pesos.

- [x] **TSP-004 — Auditar integralmente o mapa de 18 nós** · `P0 / High`
  - Revisar a linha/peso `9-14`, o rótulo `56` associado a `4-14` e todas as demais conexões.
  - Preferir imagem ou fonte original de maior resolução.
  - **Aceite:** tabela definitiva de adjacência revisada; `data/mapa_18.json` passa a `validado: true`; testes automatizados cobrindo todos os pesos.
  - **Conferido:** 45 conexões e 44 pesos revisados nas figuras do autor; o usuário complementou explicitamente `9–14 = 1`. JSON validado, sem pendências, tabela e proveniência atualizadas; todos os 45 pesos cobertos por testes. O rótulo 56 permanece em 4–14. As guardas de mapas incompletos continuam testadas com fixture em memória.

- [x] **TSP-005 — Documentar as restrições acadêmicas** · `P0 / Low`
  - Esclarecer peso fixo ≠ distância em pixels.
  - Diferenciar caminho mínimo de TSP e marcar transcrições não validadas.
  - **Aceite:** `README.md` e `AUDITORIA_MAPAS.md` presentes.

## Epic 02 — Núcleo matemático em Python

- [x] **TSP-006 — Implementar representação do grafo** · `P1 / Medium` · depende de TSP-002
  - Carregar JSON, validar nós, pares de arestas e pesos não negativos.
  - Gerar adjacência não orientada sem criar ligações inexistentes.
  - **Aceite:** mapas malformados produzem erro; mapa pendente bloqueia os algoritmos.
  - **Conferido:** `tsp_core.py` carrega JSON UTF-8 e fornece `No`, `Aresta` e `Grafo` imutáveis. Valida metadados, IDs, coordenadas, duplicatas, extremos e pesos finitos não negativos. A adjacência exige mapa validado e preserva ligações reais nos dois sentidos. Guardas de mapas incompletos continuam testadas em fixture; o mapa 18 real está validado após a TSP-004.

- [x] **TSP-007 — Implementar Dijkstra com reconstrução do caminho** · `P1 / Medium` · depende de TSP-006
  - Usar fila de prioridade e vetor de predecessores.
  - Entrada: grafo, origem e destino. Saída: sequência e custo.
  - **Aceite:** no mapa 5, de 1 até 3 a distância mínima é 6 (`1-2-3`).
  - **Conferido:** Dijkstra usa heap mínimo, distâncias tentativas, nós finalizados e predecessores. Resultado imutável; caminho vazio/infinito sinaliza destino inalcançável. Testes cobrem mapa 5, mapas pendentes sintéticos, empates e entradas inválidas; após o complemento de peso, os 324 pares do mapa 18 foram conferidos contra Floyd–Warshall.

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
  - **Conferido:** renderiza cadastros sem recalcular custos; botões/atalhos 1/2, O para referência e P para pesos. Há suporte a `?` em cadastros incompletos; no mapa 18 validado, 9–14 é exibida com peso 1.

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
  - **Conferido:** zoom ancorado no cursor (roda ou +/−), arraste direito/meio, Z para reset; P alterna todos/incidentes ao nó/ocultos. Labels evitam nós e outros labels; inspeção identifica pares e custos em cruzamentos. As novas capturas exibem 9–14 com peso 1 e o ciclo real de custo 391.

- [ ] **TSP-017 — Smoke test visual em Pygame** · `P1 / Medium` · depende de TSP-011 a TSP-014
  - Instalar requisitos, abrir programa e testar todos os botões.
  - Validar clique nos nós, desenhos, cores, teclado, alternância de mapas e mensagens de erro.
  - **Aceite:** testes manuais reproduzíveis registrados em `docs/` ou no relatório da equipe.
  - **Avanço parcial:** requisitos instalados; 20 casos SDL passaram, incluindo identificação visual, método composto isolado, foco de rotas e mapa 18 validado. Logs/capturas revisados em `docs/`. A inspeção manual nativa permanece pendente de confirmação de acesso ao Python na ferramenta; autorização verbal recebida. O smoke SDL não é apresentado como teste manual. Roteiro em `docs/smoke_pygame.md`.

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

- [x] **TSP-020 — Definir estratégia segura para o mapa de 18 nós** · `P1 / High` · depende de TSP-004
  - Dijkstra em pares funciona após validação; **não** executar força bruta ingênua de 18 nós.
  - Selecionar busca melhorada (Held–Karp, branch-and-bound ou OR-Tools) com justificativa.
  - **Aceite:** algoritmo para o mapa 18 termina dentro de um limite razoável e identifica se a solução é ótima comprovada ou apenas conhecida.
  - **Conferido:** branch-and-bound executado no mapa real com 9–14=1: custo 391, `otimo_comprovado`, 1159 estados, cerca de 18 ms na execução registrada. Held–Karp independente confirma 391 (153860 estados). Resultados em `docs/resultados_mapa_18.json`, reproduzidos por `scripts/validar_mapa_18.py`. Limites de 2 s/200 mil estados e guardas de dados pendentes preservados; UI e smoke incluem o mapa real.

- [x] **TSP-021 — Elaborar relatório e demonstração da aula** · `P2 / Medium` · depende de TSP-017 a TSP-020
  - Explicar grafos incompletos, pesos, Dijkstra, força bruta, complexidade e resultados.
  - Incluir capturas da versão 2D, referências originais, limitações e casos de teste.
  - **Aceite:** roteiro permite apresentar o projeto do início ao fim.
  - **Conferido:** relatório e README atualizados com dados, complexidade, comparação, capturas, roteiro e resultado real de custo 391, conferido independentemente. `scripts/verificar.py` registra a suíte (96 testes após a TSP-025). A única dependência ainda aberta até esta etapa é a inspeção manual nativa da TSP-017.

## Epic 05 — Identificação visual e novos algoritmos 2D (prioridade antes do 3D)

O usuário pediu primeiro a identificação visual dos métodos atuais e o planejamento dos próximos. Somente a TSP-025 foi implementada nesta etapa. TSP-026 entregue: contrato, registro, validação de saída, cancelamento e orçamento. As demais entregas são registradas abaixo conforme implementação.

- [x] **TSP-025 — Identificar método, execução, etapa e resultado na interface** · `P1 / Medium`
  - Manter nome, modelo do problema, estado e garantia visíveis em uma faixa dedicada.
  - Identificar as fases de Dijkstra + TSP e preservar o método de origem durante a reprodução.
  - Disponibilizar Dijkstra + TSP isoladamente (botão/tecla T) e selecionar a rota de cada resultado na comparação.
  - **Aceite:** distinguir Pronto, Em execução, Concluído, Reproduzindo, Pausado, Indisponível e Erro sem depender apenas de cores; não declarar busca interrompida como ótima.
  - **Conferido:** metadados em `identidade_algoritmos.py`, progresso por fila, eventos com método de origem, cards/estado/garantia, foco de rota e layout mínimo testados. Evidências em `docs/interface_algoritmos.md`; 96 testes e 20 casos SDL aprovados. A inspeção manual nativa da TSP-017 permanece separada.

- [x] **TSP-026 — Padronizar contrato e registro de solvers** · `P1 / High` · depende de TSP-025
  - Contrato comum para `ordem`, `caminho_fisico`, `custo`, método/pipeline, variante do problema, garantia, motivo de término, tempos e contadores com unidade.
  - Separar explicitamente modo Hamiltoniano da malha original e modo passeio no fecho métrico; validar origem, conectividade e todas as arestas da saída.
  - Registrar capacidades, restrições, atalhos e disponibilidade por dependência/limite; evoluir o catálogo visual existente sem criar botões fictícios.
  - Padronizar progresso, cancelamento cooperativo, orçamento e snapshots, preservando o worker e as guardas de mapas não validados.
  - **Aceite:** métodos atuais adaptados sem mudar os custos 6/15/391; resultado impossível, indisponibilidade, cancelamento e limite possuem estados distintos e testes.

- [x] **TSP-027 — Implementar `nearest_neighbor`** · `P1 / Medium` · depende de TSP-026
  - Construir a ordem pelo vizinho ainda não visitado de menor custo, com desempate determinístico por ID e retorno à origem.
  - Modo padrão no fecho métrico por Dijkstra, expandindo a ordem nas arestas reais; modo direto opcional deve recusar ou sinalizar bloqueio em grafos esparsos.
  - Identificar como heurística sem prova de ótimo; registrar candidato escolhido e acumulado para reprodução.
  - **Aceite:** rota fechada cobre todos os IDs nos mapas conectados; soma física correta; testes de empate, nó isolado e origem igual; não confundir uma construção bloqueada com prova de inexistência. Comparar custo com busca exata apenas no mesmo modelo.

- [x] **TSP-028 — Implementar `two_opt` como melhoria de uma rota inicial** · `P1 / High` · depende de TSP-027
  - Receber uma rota viável (por exemplo `nearest_neighbor`) e aplicar trocas 2-opt de melhoria estrita, preservando origem, fechamento e cidades.
  - Respeitar a mesma matriz/variante da rota inicial. Na malha original, rejeitar trocas que usem arestas ausentes; no fecho, reexpandir o percurso físico.
  - Registrar arestas removidas/adicionadas, custo anterior/novo, limite de iterações/tempo e condição de parada.
  - **Aceite:** custo final nunca piora o inicial; teste conhecido com melhoria e teste sem melhoria; exibir `nearest_neighbor + two_opt` e "ótimo local" somente quando o critério foi esgotado, sem afirmar ótimo global.

- [ ] **TSP-029 — Promover `held_karp` a solver exato com reconstrução** · `P1 / High` · depende de TSP-026
  - Evoluir o controle de custo de `scripts/validar_mapa_18.py` para um solver do núcleo, com DP por subconjunto/última cidade e predecessores para reconstruir a ordem.
  - Suportar malha original e fecho em modos separados, com orçamento de memória/tempo e sem transformar uma execução cortada em prova de ótimo.
  - Explicar o custo `O(n² 2ⁿ)` e disponibilizar progresso por camadas na interface.
  - **Aceite:** custos iguais à força bruta em instâncias pequenas; ciclo Hamiltoniano de custo 391 no mapa 18 original; caminho físico e memória medidos; falta de rota e limite tratados. O script de controle existente não deve ser apresentado como solver de UI antes desta tarefa.

- [ ] **TSP-030 — Implementar `christofides` no TSP métrico** · `P2 / High` · depende de TSP-026, TSP-029
  - Trabalhar em grafo completo, não direcionado, simétrico, com pesos não negativos e desigualdade triangular; nos mapas esparsos, construir o fecho por Dijkstra sem modificar os JSON.
  - Implementar MST, nós de grau ímpar, matching perfeito de peso mínimo, multigrafo Euleriano e atalhamento; matching guloso não sustenta a garantia clássica.
  - Reconstruir o passeio físico e registrar as etapas para visualização; escolher e documentar eventual dependência de matching.
  - **Aceite:** pré-condições verificadas; testes métricos pequenos com custo até 1,5 vezes o ótimo de Held–Karp para a mesma instância; saída viável nos mapas conectados e erro em desconectados. Não aplicar essa garantia ao ótimo Hamiltoniano da malha esparsa original.

- [ ] **TSP-031 — Integrar `ortools_solver` como dependência opcional** · `P2 / High` · depende de TSP-026, TSP-029
  - Verificar compatibilidade com o Python suportado; manter instalação opcional e mostrar indisponibilidade compreensível quando faltar OR-Tools.
  - Modelar origem/retorno, limites, estratégia inicial e busca local; tratar custos inteiros/escalonamento sem alterar a unidade dos resultados.
  - No modo direto, proibir arcos ausentes; não usar uma penalidade arbitrária como se tornasse o percurso válido. No modo fecho, expandir a solução nas arestas reais.
  - **Aceite:** orçamento obrigatório, status/versão/parâmetros registrados, rota validada e custo conferido. Sucesso do solver não será rotulado "ótimo comprovado" sem prova; testar dependência ausente, timeout sem solução, rota conhecida e instâncias pequenas contra Held–Karp.

- [ ] **TSP-032 — Integrar, comparar e demonstrar os novos métodos** · `P2 / High` · depende de TSP-027 a TSP-031
  - Integrar os cinco métodos ao catálogo, worker, faixa de execução, cards, garantia e histórico; 2-opt aparece como pipeline com o construtor da rota inicial.
  - Comparar somente métodos no mesmo modo/matriz, origem e orçamento; separar preparação do fecho, otimização e reconstrução nas métricas.
  - Usar Held–Karp como referência quando viável; calcular gap/razão apenas contra ótimo comprovado do mesmo problema, sem usar 391 como ótimo do fecho por suposição.
  - **Aceite:** testes de integração e smoke cobrindo todos os métodos e estados; capturas, relatório da aula e README atualizados; dados fixos intactos e UI responsiva.

Detalhamento e referências técnicas: [`docs/novos_algoritmos.md`](docs/novos_algoritmos.md). Ordem proposta: **026 → 027 → 028**, depois **029 → 030/031 → 032**.

## Epic 06 — Conversão futura para 3D (após consolidar a versão 2D)

- [ ] **TSP-022 — Planejar renderização 3D desacoplada** · `P3 / High` · depende de TSP-017, TSP-032
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

TSP-025 -> TSP-026 -> TSP-027 -> TSP-028 -> TSP-032
                 |                         ^
                 +-> TSP-029 -> TSP-030 ----+
                            +-> TSP-031 ----+

TSP-017 + TSP-032 -> TSP-022 (3D somente após consolidar o 2D)
```

## Próxima ação recomendada

Revisar a identificação visual entregue na **TSP-025** e, quando solicitado, iniciar a **TSP-026** para preparar o contrato dos novos métodos 2D. TSP-027 a TSP-032 estão planejadas, não implementadas. A inspeção manual nativa da TSP-017 continua pendente. Nenhuma tarefa 3D foi iniciada.
