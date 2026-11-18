# Prompt mestre --- Refinamento do game 3D NEXUS (Caixeiro Viajante)

> **Objetivo:** usar este documento como instrução para uma IA de
> programação que terá acesso ao projeto local. A IA deve analisar as
> imagens anexadas, inspecionar o código existente e executar as
> melhorias em etapas, sem recomeçar o projeto do zero.

------------------------------------------------------------------------

## 1. Referências que devem ser anexadas à IA

Anexe, de preferência nesta ordem:

1.  **Grafo original de 5 nós:** referência matemática para nós, arestas
    e pesos.
2.  **Grafo original de 18 nós:** referência matemática para a topologia
    e os pesos.
3.  **Capturas do jogo atual:** mostram os problemas atuais,
    principalmente ruas sobrepostas, conexões pouco claras e a van
    aparentando andar de ré.
4.  **Mockup visual refinado do mapa de 5 nós:** referência de estilo,
    cores, organização da cidade, HUD e disposição das ruas.
5.  **Mockup visual refinado do mapa de 18 nós:** referência de estilo e
    organização para o cenário maior.

### Hierarquia das referências

-   **Os grafos originais são a fonte da verdade matemática.** Eles
    definem quais nós existem, quais arestas conectam os nós e quais são
    os pesos.
-   **Os mockups refinados são referências visuais.** Use-os para
    orientar cores, estilo, composição, organização das ruas, edifícios,
    marcadores e interface. Não copie deles pesos, rotas ou conexões que
    não tenham sido confirmados nos grafos originais.
-   **As capturas do jogo atual servem para identificar defeitos** que
    precisam ser corrigidos.

------------------------------------------------------------------------

## 2. Papel da IA e objetivo geral

Atue como desenvolvedor experiente em Python, Pygame, renderização 3D,
grafos, algoritmos de otimização e desenvolvimento de jogos.

O projeto já possui um game 3D funcional. Sua tarefa é **refinar a
implementação existente**, principalmente a representação dos mapas, a
organização das ruas, a representação visual dos nós e a movimentação da
van.

O jogo deve parecer uma pequena cidade isométrica de entregas:

-   Cada nó deve ser representado por uma casa, prédio ou construção
    urbana.
-   As ruas devem formar uma malha organizada, com quarteirões
    retangulares/quadrados.
-   As conexões entre os nós devem ser visualmente claras.
-   A van deve percorrer as ruas no sentido correto, sempre apontando
    para a direção em que está se deslocando.
-   A interface deve manter o estilo limpo, com fundo verde-claro,
    painéis brancos, detalhes azuis e rota destacada em amarelo/laranja.

**Não recrie o projeto do zero.** Antes de alterar arquivos, entenda a
estrutura atual e preserve o que já funciona.

------------------------------------------------------------------------

## 3. Regras obrigatórias de implementação

1.  Não remover funcionalidades existentes sem justificativa técnica.
2.  Não substituir a renderização 3D por uma representação 2D.
3.  Não criar uma segunda implementação paralela quando for possível
    evoluir os módulos existentes.
4.  Não inventar nós, arestas, pesos ou resultados de algoritmos.
5.  Não alterar os dados matemáticos dos grafos para facilitar o desenho
    do cenário.
6.  Não permitir que ruas decorativas criem conexões que não existem no
    grafo.
7.  Não deixar modelos de ruas sobrepostos ou coplanares, causando
    z-fighting, aparência de cruzamento confuso ou falsa interligação.
8.  Não orientar a van apenas pela posição anterior do veículo: sua
    orientação deve ser calculada a partir do próximo trecho do
    percurso.
9.  Reutilizar os assets que já estão disponíveis na pasta local
    `assets/`.
10. Fazer as alterações por etapas, executar o jogo e validar cada etapa
    antes de avançar.

Se houver incompatibilidade entre um mockup e os dados do grafo
original, preserve os dados do grafo e adapte o cenário visual.

------------------------------------------------------------------------

# 4. Plano de execução por tasks

## TASK 01 --- Auditoria do projeto atual

Antes de programar:

-   Inspecione a estrutura de pastas e arquivos.
-   Identifique o ponto de entrada do jogo.
-   Identifique a biblioteca ou tecnologia responsável pela renderização
    3D.
-   Identifique como os modelos, texturas e materiais são carregados.
-   Localize as classes ou funções responsáveis por nós, arestas, ruas,
    câmera, van, animação, HUD e algoritmos.
-   Localize onde os grafos de 5 e 18 nós estão definidos.
-   Descubra qual é o eixo frontal original do modelo 3D da van (por
    exemplo, `+X`, `-X`, `+Z` ou `-Z`).
-   Execute o jogo no estado atual e registre uma captura de tela para
    comparação.

**Entrega da task:** relatório curto da arquitetura existente, arquivos
envolvidos, problemas identificados e plano de alteração. Não faça uma
refatoração ampla antes de compreender o projeto.

## TASK 02 --- Validar os dados dos grafos

### Mapa de 5 nós

Utilize os seguintes dados, conforme o grafo original:

``` python
edges_5 = [
    (1, 2, 2),
    (1, 4, 3),
    (1, 5, 6),
    (2, 3, 4),
    (2, 4, 3),
    (3, 4, 7),
    (3, 5, 3),
    (4, 5, 3),
]
```

Validações:

-   Existem exatamente 5 nós.
-   Existem exatamente 8 arestas.
-   O grafo é não direcionado.
-   Os pesos devem permanecer iguais aos da referência.

Resultado esperado para o TSP exato:

-   Circuito: `1 → 2 → 3 → 5 → 4 → 1`
-   Custo: `15`

A rota inversa é equivalente em um grafo não direcionado.

### Mapa de 18 nós

-   Transcreva os 18 nós, todas as conexões e seus pesos a partir da
    imagem original.
-   Confira a imagem com zoom antes de registrar os dados.
-   A conexão entre os nós **9 e 14 deve ter peso 1**.
-   Não interprete uma conexão sem peso como peso zero.
-   Não utilize os pesos ou as conexões dos mockups ilustrativos como
    fonte matemática.
-   Gere uma representação única e reutilizável do grafo, evitando
    duplicar dados entre renderização e algoritmos.

Antes de seguir, valide a lista transcrita visualmente com a imagem
original. Se alguma aresta ou peso estiver ilegível, registre a dúvida e
não invente um valor.

**Entrega da task:** dados dos dois grafos organizados em uma única
estrutura de dados e testes básicos de integridade.

## TASK 03 --- Separar a lógica do grafo da representação visual

A estrutura matemática deve ser independente da posição dos elementos na
cidade.

Cada nó deve ter:

-   Identificador.
-   Posição lógica no grafo.
-   Posição visual no cenário 3D.
-   Referência ao asset que representa sua cidade.
-   Lista de conexões válidas.

Cada aresta deve ter:

-   Nó de origem.
-   Nó de destino.
-   Peso.
-   Caminho visual da rua entre os nós.

A posição visual de um nó pode mudar sem alterar as conexões ou os pesos
do grafo.

A renderização deve consultar a estrutura do grafo. Não utilizar a
proximidade entre objetos 3D para determinar se dois nós estão
conectados.

**Critério de aceite:** reorganizar a cidade visualmente não pode
modificar o resultado dos algoritmos.

## TASK 04 --- Refazer o layout das ruas em quadrantes

Esta é uma das tarefas prioritárias.

O cenário atual apresenta ruas que se sobrepõem e dão a impressão de que
algumas conexões não estão realmente interligadas. Refazer a disposição
visual para formar uma cidade organizada em quarteirões.

### Direção visual

-   Criar uma malha de ruas predominantemente horizontais e verticais.
-   Organizar o terreno em quadrantes ou quarteirões
    quadrados/retangulares.
-   Usar ruas com largura consistente.
-   Manter espaço suficiente entre as ruas e os edifícios.
-   Criar curvas de 90 graus nos caminhos ortogonais.
-   Utilizar cruzamentos visualmente bem definidos.
-   Evitar trechos de rua desenhados exatamente uns sobre os outros.
-   Evitar z-fighting e sobreposição de meshes.
-   Não deixar ruas atravessarem casas, prédios ou outros elementos.

### Regras para as conexões

-   Cada aresta real do grafo deve possuir um caminho visual
    identificável.
-   Uma rua só representa uma conexão lógica quando corresponde a uma
    aresta existente.
-   Um cruzamento visual não pode criar uma conexão lógica adicional.
-   Quando duas conexões se encontrarem em um nó, a interligação deve
    ser visualmente explícita.
-   Quando duas conexões precisarem cruzar sem compartilhar um nó, tente
    reorganizar o trajeto para evitar o cruzamento.
-   Se um cruzamento inevitável exigir passagem em níveis diferentes,
    represente a ponte ou passagem elevada de forma claramente separada,
    sem criar uma conexão lógica.

Implemente, se adequado à arquitetura existente, um sistema de
roteamento ortogonal para construir os caminhos das arestas na malha da
cidade. O roteamento deve respeitar largura das ruas, afastamento entre
caminhos e posição dos edifícios.

**Não force o grafo a virar uma grade regular se isso alterar sua
topologia.** A grade é uma solução visual; as conexões matemáticas
continuam sendo as do grafo original.

### Resultado esperado

O mapa deve parecer uma cidade planejada, com ruas limpas e legíveis, e
não um conjunto de modelos de rua empilhados.

## TASK 05 --- Transformar cada nó em uma cidade

Cada nó deve ser representado por uma construção urbana visível.

Utilize os assets locais para escolher uma representação adequada:

-   Casas para alguns pontos de entrega.
-   Prédios residenciais ou comerciais para outros.
-   Construções maiores para pontos que precisem de destaque.

Requisitos:

-   A construção deve ficar próxima ao ponto lógico do nó, sem bloquear
    a rua.
-   O número do nó deve aparecer em um marcador azul legível.
-   O marcador deve estar visualmente associado à construção correta.
-   A origem deve ter uma indicação específica, como uma pequena
    etiqueta `ORIGEM`.
-   A construção não deve esconder o marcador nem os pesos das arestas.
-   Todos os 5 ou 18 nós devem ser identificáveis sem ambiguidade.

Não representar os nós apenas como círculos soltos no chão. A construção
é a representação da cidade; o marcador numérico identifica o nó do
grafo.

## TASK 06 --- Reorganizar os pesos e a aparência das arestas

Manter a identidade visual dos mockups:

-   Ruas em cinza, com meio-fio ou bordas discretas.
-   Faixas tracejadas no centro das ruas, quando compatível com os
    assets.
-   Etiquetas claras com os pesos das arestas.
-   Rota selecionada em amarelo/laranja.
-   Nós em azul.
-   Nós já visitados em verde.

As etiquetas dos pesos devem:

-   Ficar próximas ao trecho correspondente.
-   Não ficar sobre construções ou marcadores.
-   Não se sobrepor a outras etiquetas.
-   Manter tamanho legível durante o zoom.
-   Ser posicionadas de forma consistente nos dois mapas.

Quando uma rota estiver em execução, destacar somente as arestas
efetivamente utilizadas no trecho correspondente.

## TASK 07 --- Corrigir a orientação e o movimento da van

Esta é outra tarefa prioritária.

Atualmente a van aparenta andar de ré. Corrigir a orientação do modelo
para que a parte frontal esteja sempre voltada para a direção do
deslocamento.

### Diagnóstico obrigatório

-   Identifique o eixo frontal original do modelo.
-   Verifique a orientação do asset quando carregado.
-   Determine se é necessário aplicar uma correção fixa de rotação no
    carregamento.
-   Teste o modelo parado em uma rua reta antes de integrar a animação.

### Orientação durante o percurso

Para cada trecho entre dois pontos consecutivos:

1.  Obtenha a posição atual da van.
2.  Obtenha a posição do próximo waypoint.
3.  Calcule o vetor de direção do deslocamento.
4.  Converta esse vetor para o ângulo de rotação esperado pelo
    renderizador.
5.  Considere o eixo frontal real do modelo e aplique a correção
    necessária.
6.  Faça a rotação suavemente até a direção desejada.
7.  Atualize a posição ao longo do trecho.

A rotação deve usar a diferença angular mais curta, evitando giros
bruscos de 360 graus.

### Comportamento esperado

-   A van deve avançar de frente.
-   Não deve parecer que está dando ré.
-   Ao chegar a uma curva, deve girar suavemente antes de seguir pelo
    novo trecho.
-   Não deve atravessar edifícios ou cortar caminho fora das ruas.
-   Deve permanecer alinhada ao centro da via.
-   Deve parar corretamente ao chegar a cada nó.
-   Deve respeitar pausa, retomada, reinício e velocidade da simulação.

Não resolva o problema apenas invertendo o sinal da velocidade. Corrija
a orientação do modelo e o cálculo do ângulo de deslocamento.

**Critério de aceite:** observar a van percorrendo uma rota com retas e
curvas, confirmando visualmente que a frente do veículo aponta para o
próximo trecho em todos os momentos.

## TASK 08 --- Câmera isométrica e enquadramento

Preservar a câmera isométrica.

-   Utilizar projeção ortográfica, se compatível com o renderizador
    atual.
-   Manter os nós e construções identificáveis.
-   Ajustar automaticamente o enquadramento ao trocar de mapa.
-   Permitir zoom pelo scroll.
-   Permitir movimentação da câmera com o botão direito do mouse.
-   Oferecer um comando `Centrar` para retornar ao enquadramento
    inicial.
-   Evitar que o zoom esconda ou corte permanentemente elementos
    importantes.

O mapa de 18 nós precisa caber no enquadramento inicial sem deixar os
marcadores ilegíveis.

## TASK 09 --- Refinar o HUD e os painéis

Usar os mockups refinados como referência.

### Barra superior

-   Identidade visual NEXUS.
-   Nome `NEXUS — ROTAS & ENTREGAS`.
-   Frase curta `Cada entrega encontra seu caminho.`
-   Seleção entre `01 / Bairro — 5 pontos` e `02 / Cidade — 18 pontos`.

### Painel esquerdo --- Planejar entrega

-   Título `Sua próxima rota`.
-   Seleção do algoritmo.
-   Seleção da origem.
-   Informação sobre circuito completo.
-   Botão `Limpar percurso`.
-   Botão `Configurações`.

### Painel direito --- Resultados

-   Quantidade de pontos.
-   Quantidade de ruas/arestas.
-   Algoritmo selecionado.
-   Custo da rota.
-   Nós visitados.
-   Distância percorrida, se aplicável.
-   Tempo de cálculo.
-   Sequência da rota.
-   Indicação clara de solução exata ou heurística.

### Barra inferior --- Simulação

-   Estado atual da simulação.
-   Trecho atual da van.
-   Botão `Iniciar entrega`.
-   Botão `Pausar/Continuar`.
-   Botão `Reiniciar`.
-   Controle de velocidade.
-   Botão `Centrar`.
-   Barra de progresso.

### Cores

-   Fundo geral: verde-claro suave.
-   Terreno: verde.
-   Ruas: cinza.
-   Painéis: branco.
-   Ações principais: azul.
-   Rota: amarelo/laranja.
-   Nós: azul.
-   Visitados: verde.

Os painéis devem ser compactos e não podem ocupar a área central do
cenário.

## TASK 10 --- Preservar e validar os algoritmos

### Mapa de 5 nós

Disponibilizar:

-   Força bruta para resolver o TSP de forma exata.
-   Dijkstra para demonstrar caminho mínimo entre uma origem e um
    destino.

A interface deve diferenciar claramente os dois modos.

### Mapa de 18 nós

Disponibilizar:

-   Dijkstra para caminhos mínimos entre origem e destino.
-   Dijkstra combinado com heurística para produzir um circuito que
    visite todos os nós.

Para o circuito heurístico:

1.  Calcular caminhos mínimos entre os nós relevantes usando Dijkstra.
2.  Construir uma rota inicial com vizinho mais próximo.
3.  Melhorar a ordem com 2-opt.
4.  Expandir os caminhos para as arestas do grafo original.
5.  Validar a visita dos 18 nós.
6.  Retornar à origem.
7.  Calcular o custo usando as arestas realmente percorridas.

Não apresentar a solução heurística como ótima global. Não executar
força bruta no mapa de 18 nós.

## TASK 11 --- Testes de integração

Executar e registrar testes para:

### Dados e algoritmos

-   Mapa de 5 nós: 5 nós e 8 arestas.
-   Mapa de 5 nós: custo ótimo igual a 15.
-   Mapa de 18 nós: 18 nós e conexões transcritas da imagem original.
-   Aresta 9--14: peso igual a 1.
-   Dijkstra: caminho composto apenas por arestas válidas.
-   Circuito heurístico: visita todos os nós e retorna à origem.
-   Custo da rota: soma correta dos pesos.

### Visualização

-   Nenhuma rua sobreposta de forma indevida.
-   Nenhuma construção bloqueando uma conexão.
-   Cada nó representado por uma casa ou prédio.
-   Todos os marcadores numéricos legíveis.
-   Pesos posicionados corretamente.
-   Cruzamentos sem conexões lógicas acidentais.
-   Câmera isométrica funcionando.
-   Zoom e movimentação funcionando.

### Van

-   Frente do veículo apontando para o movimento.
-   Curvas realizadas sem giro invertido.
-   Movimento alinhado à rua.
-   Pausa e retomada funcionando.
-   Reinício levando a van à origem.
-   Velocidades diferentes funcionando.

### Interface

-   Troca entre os dois mapas.
-   Seleção de algoritmos.
-   Seleção de origem.
-   Atualização dos resultados.
-   Controles da simulação.

## TASK 12 --- Comparação visual e entrega

Depois de implementar:

-   Execute o jogo nos dois mapas.
-   Capture uma imagem do mapa de 5 nós.
-   Capture uma imagem do mapa de 18 nós.
-   Compare com os mockups refinados.
-   Corrija desalinhamentos, sobreposições, problemas de escala e
    legibilidade.
-   Verifique a movimentação da van em pelo menos uma rota com curvas.

Ao concluir, apresente:

1.  Resumo das alterações.
2.  Arquivos criados e modificados.
3.  Assets reutilizados.
4.  Problemas corrigidos.
5.  Testes executados e resultados.
6.  Capturas de tela dos dois mapas.
7.  Comando para executar o jogo.
8.  Limitações ou pendências reais.

------------------------------------------------------------------------

# 5. Critérios finais de aceite

O refinamento só pode ser considerado concluído quando:

-   [ ] Os dois mapas preservam exatamente a topologia e os pesos dos
    grafos originais.
-   [ ] O mapa de 5 nós apresenta o circuito ótimo de custo 15.
-   [ ] O mapa de 18 nós utiliza Dijkstra e heurística, sem força bruta.
-   [ ] As ruas estão organizadas em quadrantes/quarteirões.
-   [ ] Não existem meshes de ruas sobrepostas de forma indevida.
-   [ ] Não existem conexões lógicas criadas acidentalmente por
    cruzamentos visuais.
-   [ ] Cada nó é representado por uma casa ou prédio.
-   [ ] Cada construção possui seu marcador numérico.
-   [ ] Os pesos das arestas são legíveis.
-   [ ] A van aponta para a frente durante todo o percurso.
-   [ ] A van acompanha as ruas e realiza curvas corretamente.
-   [ ] A câmera isométrica permite visualizar e controlar os dois
    mapas.
-   [ ] O HUD segue a identidade visual das referências.
-   [ ] Os testes automatizados e os testes visuais foram executados.

------------------------------------------------------------------------

# 6. Instrução de execução para a IA

**Execute as tasks na ordem apresentada. Não responda apenas com
sugestões ou exemplos de código: trabalhe diretamente no projeto local,
implementando e validando as alterações.**

Ao terminar cada task:

1.  Informe o que foi analisado ou implementado.
2.  Liste os arquivos modificados.
3.  Execute os testes pertinentes.
4.  Registre qualquer problema encontrado.
5.  Só avance quando a etapa estiver funcional ou quando uma limitação
    real estiver documentada.

Não faça alterações desnecessárias em partes que já funcionam. Priorize
primeiro a organização das ruas, a representação dos nós e a orientação
correta da van. Depois finalize o HUD e os refinamentos visuais.

**Prioridade máxima:** o cenário deve parecer uma cidade organizada,
cada nó deve ser uma construção urbana e a van deve percorrer as ruas
sempre de frente, sem aparentar movimento de ré.
