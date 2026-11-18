# NEXUS — Caixeiro Viajante 3D

Jogo educativo de entregas em Python, com cidade low-poly, câmera isométrica
ortográfica e veículo que percorre somente as ruas do grafo. A cena Panda3D e
o HUD Pygame reaproveitam a base local `../caixeiro`; os quatro kits Kenney
foram preservados com modelos, materiais, texturas e licenças originais.

## Iniciar

Python 3.11 ou mais recente, ambiente gráfico com suporte a OpenGL.
Dependências: **Panda3D 1.10.16** e **pygame-ce 2.5.8** (importado como `pygame`).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

O ambiente `.venv` desta implementação já foi preparado com as dependências
disponíveis localmente. Para executá-lo agora, basta o último comando.

## Mapas e algoritmos

| Mapa | Ruas | Métodos | Resultado de referência, origem 1 |
| --- | --- | --- | --- |
| Bairro, 5 pontos | 8 | Força bruta e Dijkstra A → B | Circuito ótimo 1 → 2 → 3 → 5 → 4 → 1, custo **15** |
| Cidade, 18 pontos | 45 | Dijkstra A → B e circuito heurístico | Circuito heurístico de custo **340** |

O circuito de 18 pontos usa Dijkstra para obter distâncias e caminhos entre
todos os pares, vizinho mais próximo, melhoria 2-opt e expansão de cada trecho
pelas ruas reais. Pode revisitar pontos e **não garante ótimo global**. Dijkstra
isolado calcula apenas o caminho mínimo entre origem e destino. Força bruta
fica indisponível no mapa de 18 pontos.

A [transcrição completa](docs/grafos.md) documenta a referência visual e as
correções explícitas fornecidas pelo usuário: **1–3 = 37, 9–13 = 34 e 9–14 = 1**.
Sobreposições de ruas sem um ponto numerado não criam conexões. Os pesos são
custos lógicos; a distância exibida em `u.` mede unidades geométricas do cenário.

## Controles

| Controle | Ação |
| --- | --- |
| Botões superiores / `1`, `2` | Trocar de mapa; a busca anterior é cancelada |
| Painel esquerdo / `F`, `D`, `H` | Selecionar algoritmo |
| Origem ou destino e clique no ponto | Selecionar ponto de partida ou chegada |
| Setas junto ao seletor | Percorrer os números dos pontos |
| Iniciar entrega / espaço quando pronto | Calcular e acompanhar a busca e a viagem |
| Pausar / espaço durante execução | Pausar e retomar busca visual ou veículo |
| Reiniciar | Voltar ao início do percurso calculado |
| `←`, `→` | Voltar ou avançar uma chegada |
| Botão `1×`, `2×`, `4×` | Alterar velocidade |
| `+`, `−` ou roda do mouse | Aproximar ou afastar a câmera de 65% a 300% |
| Arraste com botão direito | Mover a câmera e desligar o acompanhamento |
| Centrar / `Z` | Enquadrar todo o mapa e voltar a 100% |
| Acompanhar veículo | Ligar ou desligar o acompanhamento da van |
| Configurações / `C` | Abrir diálogo de opções visuais |
| `P` | Mostrar ou ocultar pesos |
| Ver todas as distâncias | Inspecionar distâncias e nós explorados de Dijkstra |
| `Esc` | Fechar diálogo ou encerrar jogo |

O diálogo permite ocultar pesos e legendas e desativar a reprodução da busca.
As cores identificam pontos em azul, rota e exploração em amarelo, visitados em
verde, ponto atual em roxo e erros em vermelho. A animação tem uma breve
sinalização a cada chegada. A barra indica a distância física percorrida. O
custo conta os pesos das arestas efetivamente percorridas, incluindo revisitas.

## Arquivos e responsabilidades

| Arquivo/pasta | Responsabilidade |
| --- | --- |
| `main.py`, `tsp_3d.py` | Entrada, eventos, trabalhador de algoritmos e estado da execução |
| `tsp_core.py`, `data/` | Grafo validado e dados independentes dos dois cenários |
| `solvers.py` | Força bruta, Dijkstra, fecho métrico, vizinho próximo e 2-opt |
| `assets3d.py` | Cache de OBJ/MTL, texturas e normalização de escala |
| `geometria3d.py`, `render3d.py` | Ruas por aresta, cidade, decoração e realce de rota |
| `camera3d.py` | Projeção, enquadramento, zoom, arraste e acompanhamento |
| `mundo3d.py` | Relógio e validação da viagem, pausa, velocidades e chegadas |
| `hud.py` | Interface Pygame, resultados, etiquetas e diálogos |
| `tests/`, `scripts/smoke_3d.py` | Testes automáticos e verificação OpenGL com capturas |
| `docs/`, `ref/` | Inspeção, inventário, transcrição, validação e referências originais |

O [inventário dos assets](docs/assets.md) identifica os quatro kits. A cena usa
`road-straight`, `road-crossroad`, edifícios comerciais `building-a` a `building-h`,
casas suburbanas `building-type-*`, `tree-small`, `tree-large` e veículo `delivery`.
OBJ foi mantido por compatibilidade com o carregador da base; GLB e FBX locais
também foram preservados. Não houve download de assets.

## Validação

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\smoke_3d.py
# Opcional: abre e fecha uma janela nativa para verificar resize e encerramento.
.\.venv\Scripts\python.exe scripts\smoke_3d.py --janela
```

O smoke usa OpenGL real em framebuffer fora da tela e salva imagens e o resumo
em `tmp/3d-review/`. Verifica os dois mapas em 1440×960 e 1100×760, custo,
retorno físico à origem, pausa, reinício, velocidades, seleção por clique,
cancelamento, diálogos e troca de mapa durante uma busca. Também confere o
alinhamento dos marcadores e acompanha cada circuito a 4× com zoom de 300%.

Os resultados e as capturas das tasks complementares estão no
[relatório de posicionamento e câmera](docs/complementares/validacao.md).

Captura rápida, sem manter uma janela aberta:

```powershell
.\.venv\Scripts\python.exe main.py --offscreen --frames 120 --mapa 18 --algoritmo heuristica --iniciar --screenshot tmp\cidade.png
```

O [relatório de validação](docs/validacao.md) registra os resultados e os limites
observados. A resolução mínima da interface é 1100×760. O jogo usa sombras de
contato e materiais originais; a aparência depende do driver gráfico disponível.
