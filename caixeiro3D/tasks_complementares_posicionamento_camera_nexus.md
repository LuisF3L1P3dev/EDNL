# Tasks complementares --- Alinhamento dos nós, ruas e câmera do NEXUS 3D

## Objetivo

Corrigir a relação visual entre os pontos do grafo, as construções que
representam as cidades, as ruas e o trajeto percorrido pelo veículo.
Também implementar controles explícitos para aproximar/afastar a câmera
e acompanhar automaticamente a van durante a simulação.

**Use este documento junto com o prompt principal de refinamento do
NEXUS.** As duas imagens anexadas nesta solicitação são referências do
estado atual dos mapas de 5 e 18 nós.

Não recrie o projeto do zero. Inspecione a implementação atual e faça as
alterações nos módulos existentes, preservando os algoritmos, os dados
dos grafos e os recursos que já funcionam.

------------------------------------------------------------------------

# 1. Diagnóstico visual das imagens atuais

As capturas mostram problemas que precisam ser tratados:

### Mapa de 5 nós

-   Os marcadores dos nós 1, 4 e 5 aparecem muito próximos/agrupados,
    dificultando identificar cada ponto.
-   Algumas construções que deveriam representar os nós estão afastadas
    do marcador ou da rua pela qual o veículo deveria chegar ao ponto.
-   O marcador, a construção e o caminho da rua não parecem compartilhar
    uma referência espacial única.
-   A rota destacada passa por determinados pontos da malha, mas a
    representação visual da cidade pode estar em outra posição.

### Mapa de 18 nós

-   Há muitos pontos e conexões próximos, aumentando a dificuldade de
    identificar qual construção corresponde a cada nó.
-   Alguns marcadores parecem estar sobre a malha viária, mas as
    construções associadas ficam deslocadas ou pequenas demais para
    estabelecer a relação.
-   Etiquetas e marcadores próximos podem competir visualmente com as
    ruas e entre si.
-   É necessário melhorar a distribuição espacial dos nós sem alterar as
    conexões matemáticas do grafo.

### Problema central

A posição lógica do nó, o ponto em que a rua chega, o ponto em que o
carro passa e a construção que representa a cidade estão sendo tratados
visualmente como elementos independentes.

A implementação deve estabelecer uma referência espacial coerente para
todos eles.

------------------------------------------------------------------------

# 2. TASK 01 --- Criar uma referência espacial única para cada nó

**Prioridade: crítica**

Investigue como as posições dos nós são definidas e como essas posições
são utilizadas pelo renderizador, pelo gerador de ruas e pela animação
do veículo.

Implemente uma estrutura única de configuração visual para cada nó. A
estrutura deve manter, no mínimo:

-   `node_id`: identificador do nó no grafo.
-   `world_position`: posição 3D de referência do nó.
-   `road_anchor`: ponto exato em que a rua chega ao nó.
-   `building_position`: posição da construção que representa a cidade.
-   `building_rotation`: orientação da construção.
-   `entrance_position`: posição da entrada/saída da construção.
-   `marker_position`: posição do marcador numérico.
-   `label_offset`: deslocamento visual da etiqueta, quando necessário.

Os nomes acima são conceituais; adapte-os ao padrão de código existente.

## Regras obrigatórias

1.  O `road_anchor` deve coincidir com o ponto lógico de chegada do
    caminho.
2.  O waypoint correspondente ao nó deve utilizar esse mesmo ponto.
3.  O marcador numérico deve identificar visualmente esse ponto.
4.  A construção deve ficar posicionada no mesmo lote ou área visual do
    nó.
5.  A entrada da construção deve estar conectada ao `road_anchor` por
    uma pequena calçada, acesso ou driveway.
6.  O carro deve chegar ao ponto de acesso da cidade, não atravessar o
    interior da construção.
7.  Não criar uma posição independente para o carro, outra para o
    marcador e outra para a conexão sem uma relação explícita entre
    elas.

**Importante:** a construção pode ficar ao lado da rua para não bloquear
a passagem. O que deve coincidir é o ponto lógico do nó com o ponto em
que o veículo chega à conexão da cidade. A construção deve estar
claramente ligada a esse ponto por sua entrada.

## Critérios de aceite

-   Cada marcador identifica uma construção específica.
-   Cada construção possui um acesso visual até a rua.
-   O carro chega ao mesmo ponto indicado pelo marcador.
-   Não há nó visualmente flutuando longe da rua ou da construção que
    representa.
-   Alterar a posição visual de um nó atualiza, de maneira consistente,
    rua, marcador, entrada e waypoint.

------------------------------------------------------------------------

# 3. TASK 02 --- Reposicionar e distribuir os nós no cenário

**Prioridade: crítica**

Reorganize as posições visuais dos nós para evitar agrupamentos
excessivos e permitir que cada cidade seja identificada.

### Mapa de 5 nós

-   Corrigir principalmente o agrupamento visual dos nós 1, 4 e 5.
-   Criar espaço suficiente entre os marcadores.
-   Evitar que construções e marcadores fiquem empilhados ou escondidos.
-   Distribuir os pontos de maneira equilibrada pelo terreno.
-   Manter a área central e os quarteirões visualmente organizados.

### Mapa de 18 nós

-   Distribuir os 18 nós de forma que cada cidade tenha espaço visual
    próprio.
-   Evitar agrupamentos de marcadores e construções.
-   Reservar espaço para etiquetas de pesos e cruzamentos.
-   Considerar a densidade de conexões ao escolher a posição de cada nó.
-   Evitar que o marcador de um nó fique sobre a construção de outro.

### Restrições matemáticas

-   Não remover, adicionar ou trocar arestas.
-   Não alterar pesos.
-   Não renumerar nós.
-   Não mudar a origem lógica do percurso.
-   Não utilizar a distância visual entre cidades como substituta do
    peso da aresta.

A posição 3D pode ser reorganizada para melhorar a leitura do mapa,
desde que a estrutura matemática do grafo permaneça intacta.

Se necessário, crie posições visuais específicas para cada cenário,
mantendo os dados do grafo em uma estrutura separada.

## Critérios de aceite

-   Todos os nós aparecem separados e identificáveis.
-   Os marcadores não se sobrepõem.
-   As construções não escondem ruas ou cruzamentos.
-   O mapa continua representando exatamente o grafo original.

------------------------------------------------------------------------

# 4. TASK 03 --- Alinhar ruas, cruzamentos e acessos das cidades

**Prioridade: crítica**

Corrija a geometria das ruas para que cada conexão termine exatamente no
ponto de acesso do nó correspondente.

### Requisitos

-   A linha central da rua deve terminar no `road_anchor` do nó.
-   O caminho utilizado pelo carro deve seguir a linha central da rua.
-   A entrada da construção deve estar conectada ao ponto de acesso.
-   Os cruzamentos devem ser visualmente contínuos.
-   As ruas não podem terminar antes ou depois do marcador.
-   Evitar ruas atravessando construções.
-   Evitar sobreposição indevida de modelos de rua.
-   Evitar z-fighting e pequenos espaços entre segmentos que deveriam
    estar conectados.

Quando uma aresta tiver um trajeto com curvas, represente-a por uma
sequência de segmentos/waypoints. Essa sequência deve ser compartilhada
pela renderização da rua e pela movimentação do veículo.

### Cruzamentos

-   Identificar os pontos em que várias arestas compartilham um nó.
-   Construir um cruzamento visual único e bem definido.
-   Conectar todas as ruas incidentes ao mesmo ponto lógico.
-   Não criar conexões adicionais apenas porque duas ruas se cruzam
    graficamente.
-   Quando duas ruas precisarem cruzar sem compartilhar um nó, utilizar
    um roteamento que evite a interseção ou represente claramente níveis
    diferentes.

## Critérios de aceite

-   É possível seguir visualmente cada rua de um nó até o outro.
-   O veículo não sai do centro da via.
-   O veículo chega ao marcador correto.
-   Não existem pontas de ruas desconectadas dos nós.
-   Cruzamentos não criam arestas inexistentes no grafo.

------------------------------------------------------------------------

# 5. TASK 04 --- Criar ligação visual entre construção e ponto de entrega

**Prioridade: alta**

Cada nó deve representar uma pequena cidade ou ponto de entrega, usando
os assets de casas e prédios já existentes em `assets/`.

### Implementação

-   Posicionar a construção em um lote próximo ao `road_anchor`.
-   Orientar a fachada ou entrada para a rua de acesso.
-   Criar calçada, entrada ou pequeno caminho ligando a construção ao
    ponto de entrega.
-   Manter o marcador numérico próximo ao acesso, sem esconder a
    construção.
-   Destacar o nó de origem com a etiqueta `ORIGEM`.
-   Diferenciar visualmente o nó atual, os nós visitados e os nós ainda
    não visitados.

### Aparência

-   Preservar o estilo low-poly/cartoon.
-   Manter a escala coerente entre casas, prédios, ruas e veículo.
-   Evitar construções minúsculas demais em relação aos marcadores.
-   Evitar construções grandes que bloqueiem a malha viária.
-   Reutilizar os modelos e materiais locais.

**Não colocar a construção obrigatoriamente no centro da rua.** A rua
deve chegar ao acesso da cidade; a construção pode ficar ao lado, em seu
lote.

------------------------------------------------------------------------

# 6. TASK 05 --- Unificar o caminho visual da rua com o caminho do veículo

**Prioridade: crítica**

Atualmente, a representação da rota e a movimentação do carro podem
utilizar coordenadas ou trajetos diferentes. Corrigir essa possível
duplicidade.

Implemente uma fonte única para a geometria percorrível de cada aresta.

Cada caminho de rua deve possuir uma sequência ordenada de waypoints:

``` python
road_path = [
    waypoint_0,
    waypoint_1,
    waypoint_2,
    waypoint_3,
]
```

A estrutura é ilustrativa; adapte-a ao projeto atual.

A mesma sequência deve alimentar:

1.  A renderização da rua.
2.  A linha de destaque da rota.
3.  A movimentação do veículo.
4.  O cálculo do progresso visual da viagem.
5.  A orientação da van entre os segmentos.

### Movimento

-   A van deve percorrer o centro da rua.
-   Não pode cortar curvas.
-   Não pode atravessar construções.
-   Deve passar pelo `road_anchor` de cada nó visitado.
-   Deve parar no ponto correto ao chegar a uma cidade.
-   Deve orientar a frente para o próximo waypoint.
-   Deve girar suavemente nas curvas.

Se o caminho de uma aresta for alterado, a animação deve utilizar
automaticamente o novo caminho, sem exigir uma segunda atualização
manual.

## Critério de aceite

A linha destacada da rota e o trajeto percorrido pela van devem
coincidir visualmente em todos os segmentos.

------------------------------------------------------------------------

# 7. TASK 06 --- Implementar botões de aproximar e afastar (Zoom)

**Prioridade: alta**

Adicionar controles visíveis de zoom à interface, sem remover o zoom
pelo scroll do mouse.

### Interface

Criar um pequeno conjunto de controles na área do mapa,
preferencialmente em um dos cantos, sem cobrir os nós ou os painéis
existentes:

-   Botão `+` --- Aproximar.
-   Botão `−` --- Afastar.
-   Botão `Centrar` --- Restaurar o enquadramento do mapa.
-   Indicador opcional do nível atual de zoom, por exemplo `100%`.

Os botões devem combinar com o HUD atual: painéis claros, cantos
arredondados, ícones simples e destaque azul para ações principais.

### Comportamento

**Aproximar (+)**

-   Aumentar o nível de zoom em incrementos consistentes.
-   Manter o mapa dentro dos limites de zoom definidos.
-   Não deslocar o mapa de maneira inesperada.

**Afastar (−)**

-   Diminuir o nível de zoom.
-   Impedir que o cenário fique tão pequeno que os nós deixem de ser
    identificáveis.
-   Respeitar o limite mínimo de zoom.

**Centrar**

-   Reenquadrar o mapa ativo.
-   Ajustar a visualização para que todos os nós e ruas importantes
    fiquem visíveis.
-   Restaurar um nível de zoom adequado ao cenário atual.

### Compatibilidade

-   Manter o scroll do mouse para zoom.
-   Fazer os botões utilizarem a mesma função interna de zoom do scroll.
-   Atualizar o indicador de zoom sempre que o usuário utilizar qualquer
    método.
-   Ao alternar entre os mapas de 5 e 18 nós, ajustar o enquadramento
    inicial para o tamanho do cenário.

### Critérios de aceite

-   Os botões `+` e `−` funcionam.
-   O scroll continua funcionando.
-   Os limites mínimo e máximo são respeitados.
-   `Centrar` recupera o enquadramento.
-   O zoom não altera posições, conexões ou pesos do grafo.

------------------------------------------------------------------------

# 8. TASK 07 --- Implementar modo "Acompanhar veículo"

**Prioridade: alta**

Adicionar um botão para a câmera acompanhar automaticamente a van
durante a execução da rota.

### Interface

Adicionar um botão identificável como:

-   `Acompanhar veículo`
-   Ícone sugerido: alvo, câmera ou localização.
-   Estados visuais distintos para ativado e desativado.

O botão pode ficar próximo dos controles de zoom ou na barra inferior de
simulação.

### Comportamento quando ativado

-   A câmera deve acompanhar a posição da van em tempo real.
-   A van deve permanecer próxima ao centro da área visível, ou em uma
    posição levemente abaixo do centro para permitir visualizar a rua à
    frente.
-   O movimento da câmera deve ser suave.
-   Não deve haver saltos bruscos entre posições.
-   A câmera deve preservar sua inclinação e orientação isométricas.
-   O zoom escolhido pelo usuário deve ser preservado.
-   A câmera deve antecipar discretamente a direção do deslocamento,
    quando possível, para mostrar o próximo trecho.

### Comportamento quando desativado

-   A câmera deixa de acompanhar o veículo.
-   O usuário recupera o controle manual do enquadramento.
-   A posição atual da câmera deve ser preservada, sem retornar
    automaticamente ao início.

### Integração com controles manuais

-   Se o usuário arrastar a câmera manualmente durante o acompanhamento,
    desative o modo automaticamente ou suspenda o acompanhamento
    temporariamente.
-   O estado do botão deve refletir o comportamento real.
-   O usuário deve conseguir ativar novamente o acompanhamento a
    qualquer momento.
-   O zoom manual deve continuar funcionando no modo de acompanhamento.

### Situações especiais

-   Ao iniciar uma entrega, não ativar o acompanhamento sem respeitar o
    estado escolhido pelo usuário.
-   Ao pausar, manter a câmera na posição atual.
-   Ao retomar, continuar acompanhando se o modo estiver ativo.
-   Ao reiniciar, reposicionar a câmera suavemente para acompanhar a van
    na origem, se o modo estiver ativo.
-   Ao finalizar a rota, não mover a câmera de forma inesperada.

### Critérios de aceite

-   A câmera acompanha a van durante todo o percurso quando ativada.
-   O movimento da câmera é suave.
-   A van permanece visível.
-   O usuário pode desligar o acompanhamento e controlar a câmera
    manualmente.
-   Zoom e acompanhamento funcionam simultaneamente.

------------------------------------------------------------------------

# 9. TASK 08 --- Melhorar a legibilidade dos marcadores e etiquetas

**Prioridade: média/alta**

Como os mapas possuem nós e arestas próximos, melhorar a distribuição
visual dos marcadores e pesos.

-   Evitar sobreposição entre marcadores numéricos.
-   Evitar que etiquetas de pesos cubram construções.
-   Ajustar o deslocamento das etiquetas sem alterar o ponto real da
    aresta.
-   Manter o marcador do nó associado ao seu `road_anchor`.
-   Utilizar linhas-guia discretas quando um marcador precisar ficar
    deslocado para melhorar a leitura.
-   Manter a etiqueta `ORIGEM` próxima ao nó de origem.
-   Preservar legibilidade em diferentes níveis de zoom.

O deslocamento de uma etiqueta é apenas visual. Ele não pode alterar a
posição do nó ou o caminho da van.

------------------------------------------------------------------------

# 10. TASK 09 --- Testes de integração e validação visual

**Prioridade: obrigatória**

Executar testes nos dois mapas.

### Posicionamento

-   [ ] Todos os nós têm uma posição de referência única.
-   [ ] Todos os marcadores correspondem ao nó correto.
-   [ ] Todas as construções estão ligadas visualmente ao respectivo
    acesso.
-   [ ] Os nós 1, 4 e 5 do mapa pequeno não ficam agrupados ou
    sobrepostos.
-   [ ] Os 18 nós são identificáveis no mapa maior.
-   [ ] Nenhuma construção bloqueia a passagem do veículo.

### Ruas e veículo

-   [ ] Todas as ruas chegam aos pontos de acesso corretos.
-   [ ] A rota destacada coincide com o centro das ruas.
-   [ ] A van percorre exatamente a geometria visual da rota.
-   [ ] A van passa pelo ponto de cada nó visitado.
-   [ ] A van não atravessa construções.
-   [ ] A orientação frontal permanece correta nas curvas.

### Câmera

-   [ ] Botão `+` aproxima.
-   [ ] Botão `−` afasta.
-   [ ] Scroll continua funcionando.
-   [ ] Botão `Centrar` reenquadra o mapa.
-   [ ] Botão `Acompanhar veículo` ativa o acompanhamento.
-   [ ] O acompanhamento é suave.
-   [ ] O usuário pode desativar o acompanhamento.
-   [ ] Zoom funciona durante o acompanhamento.
-   [ ] Pausar, retomar e reiniciar não quebram o controle da câmera.

### Integridade do grafo

-   [ ] Nenhum nó foi removido ou renumerado.
-   [ ] Nenhuma aresta foi adicionada ou removida.
-   [ ] Nenhum peso foi alterado.
-   [ ] Os resultados dos algoritmos continuam iguais para os mesmos
    dados.
-   [ ] O reposicionamento visual não modifica o custo matemático das
    rotas.

------------------------------------------------------------------------

# 11. Ordem recomendada de execução

Execute as tarefas nesta sequência para evitar retrabalho:

1.  **TASK 01:** estabelecer a referência espacial única dos nós.
2.  **TASK 02:** redistribuir os nós no cenário.
3.  **TASK 03:** alinhar ruas e cruzamentos aos pontos de acesso.
4.  **TASK 04:** posicionar construções e entradas.
5.  **TASK 05:** compartilhar a geometria entre ruas e animação da van.
6.  **TASK 06:** adicionar os botões de zoom.
7.  **TASK 07:** implementar o acompanhamento do veículo.
8.  **TASK 08:** melhorar a legibilidade dos marcadores.
9.  **TASK 09:** executar testes e capturar imagens dos dois mapas.

Ao concluir cada tarefa:

-   Informe o que foi alterado.
-   Liste os arquivos modificados.
-   Execute os testes pertinentes.
-   Registre problemas ainda existentes.
-   Não marque uma task como concluída sem validar o comportamento no
    jogo.

------------------------------------------------------------------------

# 12. Instrução final para a IA de programação

Analise cuidadosamente as duas imagens anexadas. Compare o
posicionamento dos marcadores, construções, ruas e pontos por onde a van
deveria passar.

**O problema mais importante a resolver é a falta de alinhamento
espacial entre a cidade representada, o nó do grafo e o caminho
percorrido pelo veículo.**

Não faça apenas um ajuste visual nos marcadores. Corrija a origem dos
dados de posição para que a construção, sua entrada, o ponto de conexão
da rua, o waypoint e a animação estejam relacionados por uma referência
espacial consistente.

Implemente também os botões de aproximar, afastar e acompanhar o
veículo, integrados à câmera isométrica já existente.

Preserve os algoritmos e os dados originais dos grafos. Trabalhe
diretamente no projeto local, reutilize os assets disponíveis e valide o
resultado nos mapas de 5 e 18 nós.

**Resultado esperado:** cada cidade deve estar claramente conectada à
rua pela qual o veículo chega; o carro deve passar pelo ponto correto de
cada nó; o usuário deve conseguir controlar o zoom por botões e
acompanhar a van automaticamente durante a entrega.
