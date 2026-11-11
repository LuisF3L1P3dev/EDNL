# NEXUS TSP 2D — Caixeiro Viajante, Dijkstra e Força Bruta

Projeto acadêmico em **Python + Pygame** para a disciplina **Estrutura de Dados Não Linear — Aula 06**. O objetivo é representar **dois grafos fixos** apresentados nas imagens da aula e estudar a diferença entre **caminho mínimo** e **ciclo de menor custo que visita todas as cidades**.

> **Escopo inicial: 2D.** A migração para 3D será uma etapa posterior, preservando os dados dos grafos e o código dos algoritmos. **Não gerar cidades, arestas ou pesos aleatórios.**

> **Andamento real:** TSP-001 concluída: as duas referências foram copiadas de `docs/ativ/` para `assets/referencias/`, preservando os bytes originais (SHA-256 conferido). Os arquivos Python, JSON, requisitos e testes descritos neste documento ainda fazem parte do planejamento. As seções abaixo especificam o comportamento esperado; não representam funcionalidades já executáveis. A implementação segue uma tarefa por vez, com revisão e commit entre etapas.

## Situação atual

| Item | Estado |
|---|---|
| Referências dos mapas 1 e 2 | ✅ Organizadas e conferidas em `assets/referencias/` |
| Mapa 1 — 5 nós, 8 arestas | ⏳ Cadastro JSON e testes pendentes |
| Mapa 2 — 18 nós | ⚠️ Cadastro e auditoria pendentes |
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

**Verificação de referência:** origem em `1`; um ciclo ótimo encontrado por força bruta é `1 → 2 → 3 → 5 → 4 → 1`, com custo **15** (`2+4+3+3+3`). Sua rota inversa tem o mesmo custo.

O grafo grande contém **18 nós numerados de 1 a 18**, com posição e ligações conforme a figura. Os **44 pesos identificados** estão em [`data/mapa_18.json`](data/mapa_18.json), junto de uma conexão `9–14` com `peso: null`. **Não substitua `null` por um valor suposto.** Por causa da resolução da imagem, a base do mapa grande foi marcada como `"validado": false` e nenhuma solução é declarada correta até uma auditoria dos dados.

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

Os algoritmos são **independentes de Pygame**, permitindo testes sem interface:

```bash
python -m unittest discover -s tests -v
```

Casos incluídos:

- 5 nós e 8 arestas preservados;
- ligações inexistentes não são inventadas;
- Dijkstra `1 → 3` retorna custo 6;
- força bruta retorna ciclo Hamiltoniano de custo 15;
- TSP usando fecho métrico por Dijkstra retorna custo 15;
- rota física expandida preserva soma dos custos;
- grafo de 18 nós bloqueia cálculos até validação;
- força bruta é limitada a instâncias pequenas.

## Estrutura de arquivos

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
│   └── mapa_18.json            # 18 nós (pendente de conferência)
├── assets/
│   └── referencias/
│       ├── mapa_05_original.png
│       └── mapa_18_original.png
└── tests/
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
