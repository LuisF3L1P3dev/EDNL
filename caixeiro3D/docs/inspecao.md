# Inspeção da base e plano de execução

Inspeção em 16/11/2026, antes da implementação. Escopo de edição: somente
`caixeiro3D/`, na branch atual do repositório pai `EDNL`.

## Base encontrada

A pasta de destino inicialmente continha apenas `tasks.md`, `assets/` e `ref/`.
O projeto irmão `../caixeiro/`, consultado somente para leitura, preserva partes
da base 3D:

- `tsp_3d.py`: cena Panda3D, iluminação, projeção ortográfica, importação de
  objetos, HUD desenhado com Pygame e aplicado como textura, eventos e simulação.
- `assets3d.py`: importador OBJ/MTL com normais, UVs, cache de malhas e texturas;
  converte modelos Kenney de Y-up para Z-up.
- `mundo3d.py`: posições dos nós, polilinhas por aresta, interpolação e relógio
  da viagem, independente do renderizador.
- `tests/test_mundo3d.py` e `scripts/smoke_3d.py`: contratos e verificação gráfica
  que ajudam a identificar o comportamento original.

Essa base não está executável isoladamente no estado encontrado: seus imports
`tsp_core` e `solvers`, além de `data/mapa_05.json` e `data/mapa_18.json`, estão
ausentes. A documentação irmã descreve resultados históricos, que não devem ser
apresentados como testes desta entrega.

## Decisões de reaproveitamento

Preservar Panda3D para renderização 3D real e Pygame para a interface. Reaproveitar
o importador de recursos e a geometria/animação existente, com atribuição de origem
nos módulos adaptados. Separar dados e algoritmos da apresentação. A camada de
gerenciamento do jogo deve integrar eventos, temporização e interface Pygame sem
substituir desnecessariamente o renderizador.

Os modelos OBJ são a alternativa já comprovada nesta arquitetura; os kits também
fornecem GLB e FBX. Não é necessário baixar recursos ou introduzir outro motor.
Os quatro kits locais contêm 226 modelos por formato (OBJ, GLB e FBX), 226 MTL e
257 imagens PNG, incluindo texturas e prévias. O inventário detalhado pertence ao
passo 2.

Os contratos de reaproveitamento são: grafo com nós, arestas ponderadas e
adjacência; resultado de algoritmo com sequência completa de nós, custo, etapas
e classificação exata/heurística; ruas indexadas por pares de nós; viagem validada
exclusivamente contra a adjacência. A câmera e o HUD consomem esse estado, sem
modificar os dados do grafo.

## Referências e limites de fidelidade

Os dois JPG de `ref/` são referências artísticas. Os dois PNG apresentam os grafos.
Para 5 nós, a lista explícita de `tasks.md` é a fonte dos oito pesos e prevalece
sobre detalhes decorativos da imagem.

O PNG de 18 nós exige uma transcrição auditável antes da construção da cena.
Há elementos conflitantes na ilustração: 9–13 apresenta etiquetas preta e azul,
e o traçado vermelho entre 1 e 13 não tem peso legível. A regra explícita 9–14 = 1
prevalece. A afirmação histórica de 45 arestas no projeto irmão não fornece o
peso ausente e não basta para reconstruir dados. Não converter conexões sem peso
em peso zero nem confundir realces de rota com novas ruas. Registrar separadamente
as ambiguidades e as decisões; não afirmar correspondência integral onde ela não
puder ser verificada.

## Dez passos e commits

1. Inspecionar a base e registrar tecnologia, reaproveitamento e riscos (este
   documento e regras locais de arquivos temporários).
2. Inventariar os assets e adaptar carregamento com cache, materiais, texturas,
   normalização e erros legíveis.
3. Implementar dados dos dois grafos e documentar a transcrição e validação.
4. Implementar força bruta para 5 nós, Dijkstra e circuito heurístico com fecho
   métrico, vizinho mais próximo, 2-opt e expansão, com testes matemáticos.
5. Construir cenários 3D com os assets e ruas correspondentes às arestas.
6. Ajustar câmera ortográfica, enquadramento, zoom, arraste e centralização.
7. Implementar veículo, orientação, paradas, pausa, reinício e velocidades.
8. Construir HUD com controles, resultados, legenda e diálogo de configurações.
9. Integrar algoritmos, apresentação progressiva, eventos e troca de mapas.
10. Executar testes e inspeção visual do jogo; documentar execução e limitações.

Cada passo deve gerar um commit restrito a `caixeiro3D/`. Não incluir alterações
preexistentes em diretórios irmãos. Testes de lógica devem funcionar sem janela;
testes gráficos precisam registrar separadamente disponibilidade do contexto 3D
e resultados efetivamente observados.

## Riscos a controlar

- Topologia ambígua no PNG de 18 nós, exigindo rastreabilidade das decisões.
- Importações ausentes na base irmã; preservação não significa copiar dependências
  quebradas ou restaurar comportamentos que conflitem com os novos requisitos.
- A base chama uma busca em estados de Dijkstra/ciclo; o novo circuito de 18 nós
  deve ser identificado como heurístico e usar a estratégia solicitada.
- Sobreposição visual de ruas não pode criar adjacências; decoração não integra
  os algoritmos.
- Peso lógico e distância geométrica são distintos; o custo deve somar os pesos
  de cada aresta efetivamente percorrida, inclusive revisitas.
- A documentação e capturas históricas não substituem a validação da aplicação
  adaptada nem comprovam seu desempenho atual.
