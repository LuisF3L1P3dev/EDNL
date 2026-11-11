# NEXUS TSP 2D

Aplicativo acadêmico em **Python + Pygame** para explorar os dois grafos fixos da aula de Estrutura de Dados Não Linear. Permite escolher origem/destino, inspecionar pesos, calcular percursos e reproduzir os algoritmos passo a passo.

![Comparação dos métodos](docs/capturas/comparacao.png)

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
| `F` | TSP Hamiltoniano por força bruta, até 9 nós |
| `C` | Exibir TSP direto e TSP no fecho, com suas diferenças |
| `B` | Branch-and-bound até 18 nós, com orçamento explícito |
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
| TSP direto e TSP no fecho, mapa 5 | Ambos com custo **15**; 24 ordens por origem fixa |
| Branch-and-bound | Mapa 18 real: custo ótimo **391**, confirmado também por Held–Karp |
| Mapa 18 real | Validado: 45 ligações e 45 pesos; **9–14 = 1** definido pelo usuário |
| Testes automáticos | **89 aprovados**, incluindo os 324 pares do mapa 18 e integração SDL |
| Roteiro SDL | **15 casos aprovados**, com capturas renderizadas |
| Inspeção manual nativa | Pendente de conclusão |

**O mapa 18 está liberado para Dijkstra e para a busca limitada (B).** O usuário definiu explicitamente **9–14 = 1**, complementando o rótulo ausente nas imagens. O JSON registra a proveniência, todos os pesos e `validado: true`. A força bruta didática e o enumerador do fecho continuam limitados a 9 nós; no mapa 18 use B. Ver [auditoria](docs/auditoria_mapa_18.md) e [resultados reais](docs/resultados_mapa_18.json).

Dijkstra sozinho resolve A→B. O TSP direto exige ciclo Hamiltoniano nas arestas existentes; o TSP no fecho permite repetir cidades de passagem. São problemas distintos na malha original, mesmo quando os custos coincidem. A [comparação formal](docs/comparacao.md) apresenta também um controle em que os dois métodos recebem exatamente a mesma instância métrica.

Força bruta ingênua é limitada a 9 nós antes da enumeração. A busca limitada usa até 2 segundos/200 mil estados e distingue ótimo comprovado, inexistência comprovada, melhor solução conhecida e limite sem solução encontrada. Ver [estratégia para 18 nós](docs/estrategia_18.md).

## Verificações

```powershell
.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.venv\Scripts\python.exe -B scripts\smoke_pygame.py
.venv\Scripts\python.exe -B scripts\comparar_metodos.py
.venv\Scripts\python.exe -B scripts\validar_mapa_18.py
.venv\Scripts\python.exe -B scripts\verificar.py
```

Use o ambiente com os requisitos para incluir os testes Pygame; sem Pygame, esses testes são pulados. O smoke gera [log](docs/smoke_resultados.json) e [capturas](docs/capturas/). `verificar.py` registra a saída completa em [validacao_final.txt](docs/validacao_final.txt). O [roteiro manual](docs/smoke_pygame.md) distingue testes SDL da inspeção nativa pendente.

## Organização e API

| Arquivo | Responsabilidade |
|---|---|
| `main.py` / `tsp_ui.py` | Entrada, desenho e eventos Pygame |
| `tsp_core.py` | Grafo imutável, validação, Dijkstra, TSP direto/fecho e snapshots |
| `reprodutor.py` | Relógio da animação, independente de Pygame |
| `busca_limitada.py` | Branch-and-bound com orçamento |
| `comparacao.py` | Medições sem histórico e contadores separados |
| `data/` / `assets/referencias/` | Cadastros fixos e referências preservadas |
| `tests/` / `scripts/` | Testes e geração de evidências |

```python
from tsp_core import carregar_mapa, dijkstra, tsp_forca_bruta, tsp_dijkstra

grafo = carregar_mapa("data/mapa_05.json")
print(dijkstra(grafo, 1, 3).caminho)    # (1, 2, 3)
print(tsp_forca_bruta(grafo, 1).custo) # 15
print(tsp_dijkstra(grafo, 1).caminho)  # percurso físico
eventos = []
dijkstra(grafo, 1, 3, eventos=eventos)  # snapshots imutáveis
```

Destino inalcançável retorna caminho vazio e custo infinito. `GrafoInvalidoError` informa dados/IDs inválidos; `MapaNaoValidadoError` bloqueia cadastros pendentes. Pesos negativos, booleanos e não finitos são recusados. Dados e adjacência são imutáveis; não há geração de cidades ou pesos aleatórios.

## Entrega

[Relatório e roteiro da aula](docs/RELATORIO.md) · [Comparação](docs/comparacao.md) · [Auditoria](AUDITORIA_MAPAS.md) · [Checklist](TASKS.md).

Há um commit por tarefa da TSP-008 à TSP-021, com commits posteriores concluindo as TSP-004 e TSP-020 após a definição do peso 1. Permanece aberta a TSP-017 (inspeção manual nativa). O relatório TSP-021 foi atualizado com os resultados do mapa real. A fase 3D (TSP-022 a TSP-024) não foi iniciada.
