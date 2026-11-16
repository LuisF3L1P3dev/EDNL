# NEXUS TSP 2D

Aplicativo acadêmico em **Python + Pygame** para explorar os dois grafos fixos da aula de Estrutura de Dados Não Linear. A interface disponibiliza Dijkstra para caminho mínimo e força bruta para o ciclo Hamiltoniano, com reprodução das etapas.

Os outros algoritmos continuam preservados no código, mas seus registros estão comentados em `solvers.py` e não aparecem na interface. Para reativar um método no futuro, habilite seu registro e sua identificação visual.

## Executar

Requer Python 3.10+. Ambiente conferido: Windows, Python 3.14 e pygame-ce 2.5.8, distribuição compatível com a API `pygame`.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

Linux/macOS: usar `.venv/bin/python`. Não é necessário ativar o ambiente ou alterar a política de execução do Windows. A aplicação usa fontes locais e não exige conexão após a instalação.

## Controles

| Comando | Ação |
|---|---|
| `1` / `2` | Alternar mapas |
| Clique nos nós | Definir origem e destino, alternadamente |
| `D` | Dijkstra: menor caminho A→B |
| `V` | Alternar entre visita unica e revisitas no TSP |
| `F` | TSP Hamiltoniano por força bruta, até 9 nós |
| `X` / Cancelar | Cancelamento cooperativo da execução |
| Play / Pausar / `<` / `>` | Reproduzir histórico e navegar |
| Velocidade / Final | Mudar velocidade ou exibir resultado final |
| `O` | Exibir/ocultar a referência original |
| `P` | Pesos: todos → do nó sob o cursor (ou origem) → ocultos |
| Roda / `+` / `−` | Zoom; roda ancorada no cursor |
| Arraste direito ou do meio | Mover o desenho |
| `Z` | Reset do zoom e posição |
| Cursor sobre aresta | Inspecionar par e peso, inclusive em cruzamentos |
| `L` / `Esc` | Limpar / sair |

Os algoritmos rodam em um worker; a reprodução usa o tempo entre frames. Seleções ficam estáveis enquanto há cálculo. Coordenadas servem ao desenho e não determinam pesos.

## Resultados e limitações

| Caso | Resultado |
|---|---|
| Mapa 5 | 5 IDs, 8 arestas; sem ligações 1–3 e 2–5 |
| Dijkstra 1→3 | 1–2–3, custo **6** |
| Força bruta, mapa 5 | Ciclo ótimo com custo **15**; 24 ordens por origem fixa |
| Mapa 18 real | Validado: 45 ligações e 45 pesos; **9–14 = 1** definido pelo usuário |

No TSP, a rota visita todas as cidades e retorna à origem. Selecione a mesma cidade como origem e destino e execute Dijkstra para buscar o ciclo. A busca acompanha a cidade atual e as cidades visitadas, respeitando a escolha de permitir ou não revisitas. A quantidade de estados cresce exponencialmente; limites de tempo, estados e memória podem interromper a busca antes de encontrar uma solução.

Dijkstra funciona nos dois mapas. A força bruta está limitada a 9 cidades; no mapa de 18 cidades o cartão fica indisponível. O mapa e os pesos permanecem em `data/` e podem ser auditados em [auditoria](docs/auditoria_mapa_18.md).

## Registros anteriores

Os testes, scripts e relatórios existentes em `tests/`, `scripts/` e `docs/` também documentam a versão expandida do projeto, que incluía os algoritmos agora desativados. A interface atual oferece somente Dijkstra e força bruta.

## Organização e API

| Arquivo | Responsabilidade |
|---|---|
| `main.py` / `tsp_ui.py` | Entrada, desenho e eventos Pygame |
| `identidade_algoritmos.py` | Nomes, modelos, cores, limites e garantias visíveis |
| `tsp_core.py` | Grafo imutável, validação, Dijkstra, TSP direto/fecho e snapshots |
| `reprodutor.py` | Relógio da animação, independente de Pygame |
| `busca_limitada.py` | Branch-and-bound com orçamento |
| `comparacao.py` | Medições sem histórico e contadores separados |
| `solvers.py` | Execução e registro dos dois métodos ativos; registros dos outros comentados |
| `comparacao_solvers.py` | Implementação de comparação preservada para possível uso futuro |
| `data/` / `assets/referencias/` | Cadastros fixos e referências preservadas |
| `tests/` / `scripts/` | Testes e geração de evidências |

```python
from tsp_core import carregar_mapa, dijkstra, tsp_forca_bruta
from solvers import executar, Orcamento

grafo = carregar_mapa("data/mapa_05.json")
print(dijkstra(grafo, 1, 3).caminho)    # (1, 2, 3)
print(tsp_forca_bruta(grafo, 1).custo) # 15
eventos = []
dijkstra(grafo, 1, 3, eventos=eventos)  # snapshots imutáveis
resultado = executar("forca", grafo, 1, orcamento=Orcamento(segundos=2))
print(resultado.pipeline, resultado.custo, resultado.garantia)
```

Destino inalcançável retorna caminho vazio e custo infinito. `GrafoInvalidoError` informa dados/IDs inválidos; `MapaNaoValidadoError` bloqueia cadastros pendentes. Pesos negativos, booleanos e não finitos são recusados. Dados e adjacência são imutáveis; não há geração de cidades ou pesos aleatórios.

## Entrega

[Relatório e roteiro da aula](docs/RELATORIO.md) · [Comparação](docs/comparacao.md) · [Auditoria](AUDITORIA_MAPAS.md) · [Checklist](TASKS.md).

Há um commit por tarefa da TSP-008 à TSP-021, com commits posteriores concluindo as TSP-004 e TSP-020 após a definição do peso 1. Permanece aberta a TSP-017 (inspeção manual nativa). O relatório TSP-021 foi atualizado com os resultados do mapa real. A fase 3D (TSP-022 a TSP-024) não foi iniciada.

Os métodos adicionais e as comparações continuam documentados no histórico do projeto, mas estão desativados na interface atual. Reative os registros comentados quando precisar disponibilizá-los novamente.
