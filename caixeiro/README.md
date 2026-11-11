# NEXUS TSP 2D — Caixeiro Viajante, Dijkstra e Força Bruta

Projeto acadêmico em **Python + Pygame** para a disciplina **Estrutura de Dados Não Linear — Aula 06**. O objetivo é representar **dois grafos fixos** apresentados nas imagens da aula e estudar a diferença entre **caminho mínimo** e **ciclo de menor custo que visita todas as cidades**.

> **Escopo inicial: 2D.** A migração para 3D será uma etapa posterior, preservando os dados dos grafos e o código dos algoritmos. **Não gerar cidades, arestas ou pesos aleatórios.**

> **Andamento real:** TSP-001 a TSP-003 concluídas. As referências originais estão em `assets/referencias/` (SHA-256 conferido); os dois mapas têm cadastro JSON, com 12 testes aprovados. O mapa 18 permanece provisório e não validado. O núcleo matemático, os requisitos e a interface Pygame ainda fazem parte do planejamento. A implementação segue uma tarefa por vez, com revisão e commit entre etapas.

## Situação atual

| Item | Estado |
|---|---|
| Referências dos mapas 1 e 2 | ✅ Organizadas e conferidas em `assets/referencias/` |
| Mapa 1 — 5 nós, 8 arestas | ✅ JSON cadastrado e 6 testes aprovados |
| Mapa 2 — 18 nós | ⚠️ Cadastro provisório criado; auditoria pendente |
| Mapa 2 — 45 ligações transcritas | ⚠️ Uma ligação está sem peso legível (9–14); outras devem ser cotejadas com a fonte original |
| Dijkstra no mapa 1 | ⏳ Implementação pendente |
| Força bruta Hamiltoniana no mapa 1 | ⏳ Implementação pendente |
| Dijkstra + força bruta no fecho métrico | ⏳ Implementação pendente |
| Interface 2D em Pygame | ⏳ Implementação e teste visual pendentes |
| Resultados algorítmicos do mapa 2 | ⛔ Bloqueados até conferir a transcrição completa |
| Migração para 3D | ⏳ Fora do escopo desta primeira etapa |

### As figuras são a fonte de verdade

- [`assets/referencias/mapa_05_original.png`](assets/referencias/mapa_05_original.png)
- [`assets/referencias/mapa_18_original.png`](assets/referencias/mapa_18_original.png)

O pequeno grafo foi transcrito com os seguintes pesos, **sem completar artificialmente as ligações ausentes**:

| Aresta | Peso | Aresta | Peso |
|---|---:|---|---:|
| 1–2 | 2 | 1–4 | 3 |
| 1–5 | 6 | 2–3 | 4 |
| 2–4 | 3 | 3–4 | 7 |
| 3–5 | 3 | 4–5 | 3 |

**Verificação de referência:** o ciclo `1 → 2 → 3 → 5 → 4 → 1` e sua rota inversa têm custo **15** (`2+4+3+3+3`), conferido pelos testes dos dados. A busca automática pelo ciclo ótimo será implementada na TSP-008.

O cadastro em [`data/mapa_05.json`](data/mapa_05.json) lista cada aresta não direcionada uma única vez, com `origem`, `destino` e `peso`. Os nós têm `id`, `x` e `y`; as coordenadas normalizadas entre 0 e 1 preservam a disposição da figura apenas para desenho. As arestas ausentes `1–3` e `2–5` não constam do cadastro.

O grafo grande contém **18 nós numerados de 1 a 18**, com posição e ligações conforme a figura. Os **44 pesos identificados** estão em [`data/mapa_18.json`](data/mapa_18.json), junto de uma conexão `9–14` com `peso: null`. **Não substitua `null` por um valor suposto.** Por causa da resolução da imagem, a base do mapa grande foi marcada como `"validado": false` e nenhuma solução é declarada correta até uma auditoria dos dados.

O JSON também registra a dúvida sobre a associação do rótulo `56` a `4–14`. As pendências gerais e as observações nessas duas ligações devem ser preservadas até a TSP-004. Os testes do cadastro verificam estrutura e registro das dúvidas; não certificam a transcrição integral dos pesos.

## Por que Dijkstra não resolve o TSP sozinho?

São problemas diferentes:

1. **Dijkstra:** a partir de uma origem `s`, encontra o caminho de menor custo até um destino `t`, usando pesos não negativos. Exemplo no mapa pequeno: `1 → 2 → 3`, custo **6**.
2. **TSP por força bruta:** testa ordens de visita de cidades e retorna à origem; no **modo Hamiltoniano**, somente usa arestas existentes no grafo da imagem. Para `n` nós e origem fixa, testa até `(n−1)!` ordens (ou menos ciclos viáveis).
3. **TSP apoiado por Dijkstra:** aplica Dijkstra entre os pares de cidades para montar a matriz de menores distâncias (*fecho métrico*). **Depois** uma busca de TSP escolhe a ordem das visitas. O percurso físico pode repetir nós intermediários; não equivale a exigir um ciclo Hamiltoniano na malha original.

No mapa pequeno, ambas as estratégias TSP encontraram custo **15**. Isso é um **resultado daquele grafo**, não uma garantia de igualdade em qualquer instância.

No grafo de 18 nós, força bruta ingênua seria impraticável: com a origem fixa, até `17! = 355687428096000` ordens seriam examinadas. Por isso há um limite didático de 9 nós no protótipo. Para a próxima fase, serão discutidas programação dinâmica, branch-and-bound e heurísticas/OR-Tools, sempre como extensões separadas.

## Instalação e execução

Requer **Python 3.10+**.

```bash
python -m venv .venv
```

No Windows:

```powershell
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

No Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

### Controles da interface

| Ação | Comando |
|---|---|
| Selecionar grafo de 5 nós | Botão **Mapa 1** ou tecla `1` |
| Selecionar grafo de 18 nós | Botão **Mapa 2** ou tecla `2` |
| Escolher origem/destino | Clique em dois nós, alternadamente |
| Calcular TSP por força bruta | Botão **Força bruta** ou `F` |
| Calcular caminho mínimo | Botão **Dijkstra** ou `D` |
| Comparar TSP direto com TSP após Dijkstra | Botão **Comparar** ou `C` |
| Exibir referência original | Botão correspondente ou `O` |
| Mostrar/ocultar pesos | Botão correspondente ou `P` |
| Sair | `Esc` |

**Importante:** o mapa 2 aparece visualmente (incluindo a opção de exibir a imagem original), mas os botões algorítmicos são bloqueados nele **de propósito**, até a revisão do peso ilegível e dos demais dados.

## Testes

Os 12 testes atuais verificam os dados do mapa 5 e o cadastro provisório do mapa 18, usando somente a biblioteca padrão do Python. Execute a partir da pasta do projeto:

```bash
python -m unittest discover -s tests -v
```

Casos implementados em [`tests/test_mapa_05.py`](tests/test_mapa_05.py) (6 testes):

- metadados e referência original;
- 5 IDs únicos preservados;
- coordenadas normalizadas com a disposição da figura;
- exatamente 8 arestas e todos os pesos conferidos;
- ausência das ligações `1–3` e `2–5`;
- ciclo de referência e seu inverso com custo 15.

Casos implementados em [`tests/test_mapa_18.py`](tests/test_mapa_18.py) (6 testes):

- estado não validado e referência original;
- 18 IDs únicos e coordenadas normalizadas distintas;
- 45 ligações sem duplicatas, com extremos válidos e 44 pesos numéricos positivos;
- peso desconhecido de `9–14` preservado como `null`;
- associação provisória de `56` a `4–14` documentada.

Casos previstos para as tarefas do núcleo matemático:

- Dijkstra `1 → 3` retorna custo 6;
- força bruta retorna ciclo Hamiltoniano de custo 15;
- TSP usando fecho métrico por Dijkstra retorna custo 15;
- rota física expandida preserva soma dos custos;
- grafo de 18 nós bloqueia cálculos até validação;
- força bruta é limitada a instâncias pequenas.

## Estrutura de arquivos planejada

```text
tsp_grafos_2d/
├── README.md
├── TASKS.md
├── AUDITORIA_MAPAS.md
├── requirements.txt
├── main.py                     # Interface e renderização 2D (Pygame)
├── tsp_core.py                 # Algoritmos e validação, sem UI
├── data/
│   ├── mapa_05.json            # 5 nós, 8 arestas (validado)
│   └── mapa_18.json            # Cadastro provisório implementado; auditoria pendente
├── assets/
│   └── referencias/
│       ├── mapa_05_original.png
│       └── mapa_18_original.png
└── tests/
    ├── test_mapa_05.py         # Testes dos dados (implementado)
    ├── test_mapa_18.py         # Testes do cadastro provisório (implementado)
    └── test_tsp_core.py
```

## Regras de imutabilidade dos mapas

- As duas instâncias são **fixas**: exatamente **5** e **18** nós, respectivamente.
- Não recalcular pesos pela distância visual na tela; **peso exibido é o custo da aresta fornecida**.
- Não adicionar arestas para completar o grafo.
- Não alterar os IDs; coordenadas `x,y` são apenas para desenho e não determinam pesos.
- Se uma aresta estiver ausente, ela **não pode** ser percorrida no modo Hamiltoniano direto.
- Não aceitar peso negativo para Dijkstra.
- Qualquer correção de peso deve vir acompanhada da fonte e de atualização nos testes.
- Separar `algoritmos`, `dados` e `renderização`: isso permitirá converter a visualização 2D em cena 3D sem reescrever a lógica.

## Roteiro para a evolução do jogo

1. **Concluir a auditoria do mapa de 18 nós.** Ver `TASKS.md` e `AUDITORIA_MAPAS.md`.
2. **Testar manualmente o Pygame**, corrigir responsividade, clique e legibilidade de pesos.
3. **Visualização didática passo a passo** de Dijkstra (distâncias, fila de prioridade, relaxamentos e predecessores).
4. **Comparação em condições equivalentes** de TSP direto e TSP após Dijkstra, com métricas claras.
5. **Expansão para 18 nós** com heurísticas apropriadas; força bruta apenas até um limite seguro.
6. **Migração posterior para 3D**, mantendo os JSON fixos e o núcleo Python.

Consulte [`TASKS.md`](TASKS.md) para divisão por tarefas, prioridades, dependências e critérios de aceite.
