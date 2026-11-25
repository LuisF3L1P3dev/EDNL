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
| Bairro, 5 pontos | 8 | Força bruta, Dijkstra A → B e passeio heurístico | Circuito ótimo 1 → 2 → 3 → 5 → 4 → 1, custo **15** |
| Região, 18 cidades | 45 | Circuito exato, Dijkstra A → B e passeio heurístico | Circuito ótimo de custo **391** |

O circuito exato é o padrão da região. Encontra o circuito de menor custo em
ruas diretas que entrega uma vez em cada cidade e retorna à origem. O passeio
heurístico usa Dijkstra, vizinho mais próximo e 2-opt. Ele aceita passagens
intermediárias e pode revisitar cidades. Dijkstra A → B calcula o caminho
mínimo entre os dois pontos selecionados.

O botão **Comparar soluções** calcula as rotas em segundo plano. No bairro,
compare os dois circuitos a partir da mesma origem, com custo, tempo e diferença
percentual. Na região, o card mostra o caminho A → B para o destino selecionado
e o circuito heurístico completo. Escolher **Visualizar rota** fecha o card,
destaca o percurso na cor do método e inicia a viagem selecionada.

A [transcrição completa](docs/grafos.md) documenta a imagem original e os pesos
das 45 ruas da região, incluindo **1–13 = 37**, **9–13 = 34** e **9–14 = 1**.
Sobreposições de ruas sem um ponto numerado não criam conexões. Os pesos são
custos lógicos; a distância exibida em `u.` mede unidades geométricas do cenário.

## Controles

| Controle | Ação |
| --- | --- |
| Botões superiores / `1`, `2` | Trocar de mapa; a busca anterior é cancelada |
| Painel esquerdo / `F`, `T`, `D`, `H` | Selecionar força bruta, circuito exato, Dijkstra ou passeio heurístico |
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
| Ver percurso físico / Ver ordem de entrega | Alternar entre as duas sequências quando há passagens intermediárias |
| Comparar soluções / `×` | Abrir ou fechar o card sem pausar a viagem |
| Roda do mouse sobre o card | Rolar os detalhes e percursos, quando necessário |
| `Esc` | Fechar o card ou diálogo aberto ou encerrar o jogo |

O diálogo permite ocultar pesos e legendas e desativar a reprodução da busca.
As cores identificam pontos em azul, rota e exploração em amarelo, entregas em
verde, passagens intermediárias em azul acinzentado, ponto atual em roxo e
erros em vermelho. A animação sinaliza as entregas. A barra indica a distância
física percorrida. O custo soma os pesos de cada trecho percorrido, incluindo
passagens repetidas e o retorno à origem.

## Arquivos e responsabilidades

| Arquivo/pasta | Responsabilidade |
| --- | --- |
| `main.py`, `tsp_3d.py` | Entrada, eventos, trabalhador de algoritmos e estado da execução |
| `tsp_core.py`, `data/` | Grafo validado e dados independentes dos dois cenários |
| `solvers.py` | Força bruta, circuito exato, Dijkstra, fecho métrico, vizinho próximo e 2-opt |
| `assets3d.py` | Cache de OBJ/MTL, texturas e normalização de escala |
| `geometria3d.py`, `render3d.py` | Ruas por aresta, cidade, decoração e realce de rota |
| `cidades3d.py` | Lotes, calçadas de acesso e composição visual das 18 cidades |
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
alinhamento dos marcadores, acompanha cada circuito a 4× com zoom de 300% e
verifica as rotas selecionadas no card de comparação.

Os resultados e as capturas das tasks complementares estão no
[relatório de posicionamento e câmera](docs/complementares/validacao.md).

O [relatório do refinamento gráfico](docs/refinamento-grafico/validacao.md)
reúne as medidas da cidade compactada, os testes e as capturas das ruas,
dos cruzamentos e das quadras.

O [relatório das 18 cidades](docs/18-cidades/validacao.md) reúne a vista
geral da região, detalhes dos três perfis de cidade e as medições do HUD.

O [relatório de rotatórias e sinalização](docs/rotatorias/validacao.md)
reúne as capturas dos novos acessos, postes e placas e os testes do percurso.

O [relatório de todos os cruzamentos](docs/rotatorias-cruzamentos/validacao.md)
mostra as 23 rotatórias, os testes do grafo e a demonstração da curva da van.

O [relatório da correção da rota](docs/correcao-sequencia/validacao.md) reúne
a auditoria do grafo, as capturas do percurso de custo 391 e o vídeo completo da van.
O vídeo pode ser regravado com `python scripts/smoke_3d.py --demo-regiao` e FFmpeg.

Captura rápida, sem manter uma janela aberta:

```powershell
.\.venv\Scripts\python.exe main.py --offscreen --frames 120 --mapa 18 --algoritmo circuito --iniciar --screenshot tmp\cidade.png
```

O [relatório de validação](docs/validacao.md) registra os resultados e os limites
observados. A resolução mínima da interface é 1100×760. O jogo usa sombras de
contato e materiais originais; a aparência depende do driver gráfico disponível.
