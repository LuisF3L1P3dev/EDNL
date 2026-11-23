# Tasks --- Refinamento do cenário 3D NEXUS

## Objetivo

Refinar o cenário 3D do game NEXUS, corrigindo a continuidade visual das
ruas com as pontes, compactando o mapa de 18 nós e aumentando a
quantidade de casas, prédios, árvores e elementos de ambientação.

O trabalho deve aproveitar os assets Kenney já disponíveis localmente,
especialmente:

-   [Mini Forest --- Kenney](https://kenney.nl/assets/mini-forest)
-   [Nature Kit --- Kenney](https://kenney.nl/assets/nature-kit)

**Regra principal:** melhorar o visual sem alterar a topologia dos
grafos, os pesos das arestas ou o funcionamento dos algoritmos.

------------------------------------------------------------------------

## TASK 01 --- Corrigir a continuidade visual das ruas com as pontes

**Prioridade:** Alta

### Problema

As ruas e pontes não apresentam continuidade visual adequada, dando a
impressão de que são elementos separados.

### Implementação

-   Unificar visualmente o asfalto da rua com a superfície da ponte.
-   Manter a mesma largura das ruas e da pista da ponte.
-   Criar rampas de transição suaves entre rua e ponte.
-   Alinhar as faixas e marcações da pista.
-   Corrigir espaços vazios entre os modelos 3D.
-   Evitar sobreposição de meshes e problemas de altura (Z-fighting).
-   Adicionar calçadas e guarda-corpos nas laterais da ponte.
-   Manter o rio abaixo da estrutura da ponte.

### Critérios de aceite

-   O veículo atravessa da rua para a ponte e retorna à rua sem
    aparentar saltos.
-   Não existem interrupções visuais entre as superfícies.
-   A transição de altura é suave.
-   A largura da pista permanece consistente.

------------------------------------------------------------------------

## TASK 02 --- Compactar o mapa de 18 nós

**Prioridade:** Alta

### Problema

O mapa está muito espalhado, deixando grandes espaços vazios entre os
nós e aumentando desnecessariamente o tamanho do cenário.

### Implementação

-   Aproximar visualmente os 18 nós.
-   Reduzir os espaços entre os quarteirões.
-   Diminuir a área total ocupada pelo mapa.
-   Redistribuir as construções para aproveitar melhor o espaço.
-   Ajustar o posicionamento das ruas conforme a nova distribuição.
-   Reduzir áreas verdes vazias excessivas.
-   Manter espaço suficiente para veículos, construções e cruzamentos.

### Restrições

-   Alterar somente as coordenadas visuais do cenário.
-   Não modificar os pesos das arestas.
-   Não adicionar ou remover conexões.
-   Não alterar a identificação dos nós.
-   Não comprometer a circulação do veículo.

### Critérios de aceite

-   O mapa ocupa uma área menor.
-   Os 18 nós continuam visíveis e identificáveis.
-   As ruas e conexões permanecem claramente legíveis.
-   A compactação não cria sobreposição de construções ou ruas.

------------------------------------------------------------------------

## TASK 03 --- Reorganizar os quarteirões e a distribuição das cidades

**Prioridade:** Alta

### Implementação

-   Organizar as ruas em quarteirões quadrados e retangulares.
-   Distribuir casas e prédios nos espaços entre as ruas.
-   Evitar grandes regiões sem construções.
-   Manter os cruzamentos bem definidos.
-   Evitar construções bloqueando ruas ou pontes.
-   Preservar os acessos dos veículos aos pontos de entrega.
-   Manter a identidade visual isométrica.

### Critérios de aceite

-   O cenário transmite a aparência de uma cidade planejada.
-   Os quarteirões aproveitam melhor a área disponível.
-   As construções não bloqueiam a leitura do grafo nem a circulação do
    veículo.

------------------------------------------------------------------------

## TASK 04 --- Aumentar a quantidade de casas e prédios

**Prioridade:** Alta

### Implementação

-   Adicionar mais casas residenciais.
-   Adicionar prédios comerciais e residenciais.
-   Utilizar diferentes modelos e tamanhos.
-   Criar pequenos conjuntos de construções por quarteirão.
-   Adicionar garagens, lojas e construções menores quando houver assets
    disponíveis.
-   Variar a orientação das construções.
-   Evitar repetição excessiva do mesmo modelo.
-   Preservar espaço para circulação e visualização das ruas.

### Critérios de aceite

-   Os quarteirões apresentam maior densidade urbana.
-   Existe variedade de construções.
-   A ambientação não prejudica a leitura do grafo.
-   As construções não bloqueiam ruas, pontes ou acessos dos nós.

------------------------------------------------------------------------

## TASK 05 --- Popular o mapa com árvores e vegetação

**Prioridade:** Média/Alta

### Referências de assets

**Mini Forest --- Kenney** - Referência para árvores, vegetação e
ambientação natural. - https://kenney.nl/assets/mini-forest

**Nature Kit --- Kenney** - Pacote 3D com elementos de natureza,
árvores, pedras e folhagens. - https://kenney.nl/assets/nature-kit

### Implementação

-   Adicionar árvores de diferentes tamanhos.
-   Distribuir arbustos e vegetação pelos quarteirões.
-   Criar pequenos jardins próximos às casas.
-   Adicionar árvores nas calçadas e áreas verdes.
-   Criar pequenas áreas arborizadas.
-   Variar a distribuição dos modelos para evitar aparência repetitiva.
-   Utilizar os assets locais, caso já estejam baixados.
-   Verificar formatos, materiais e texturas antes da integração.

### Critérios de aceite

-   O cenário apresenta vegetação distribuída naturalmente.
-   As árvores não bloqueiam ruas, construções, marcadores ou a visão da
    câmera.
-   A vegetação mantém escala coerente com casas, prédios e veículos.
-   Não existe repetição visual excessiva.

------------------------------------------------------------------------

## TASK 06 --- Melhorar a distribuição dos elementos decorativos

**Prioridade:** Média

### Implementação

-   Adicionar postes de iluminação.
-   Adicionar bancos e elementos urbanos.
-   Adicionar calçadas e pequenos jardins.
-   Criar áreas verdes entre os quarteirões.
-   Adicionar elementos próximos às pontes.
-   Distribuir elementos decorativos sem prejudicar a circulação.
-   Evitar posicionamentos aleatórios que gerem colisões.

### Critérios de aceite

-   O mapa parece uma cidade habitada e organizada.
-   Os elementos decorativos complementam o cenário.
-   Nenhum objeto decorativo bloqueia a rota do veículo ou esconde os
    nós.

------------------------------------------------------------------------

## TASK 07 --- Refinar a escala e a densidade visual do cenário

**Prioridade:** Alta

### Implementação

-   Ajustar a proporção entre ruas, casas, prédios, árvores e veículos.
-   Garantir que as construções tenham tamanho compatível com as ruas.
-   Ajustar a altura e largura das pontes.
-   Evitar árvores maiores que os prédios sem justificativa visual.
-   Ajustar a densidade de construções conforme o tamanho de cada
    quarteirão.
-   Preservar a legibilidade dos marcadores e pesos das arestas.
-   Testar o cenário em diferentes níveis de zoom.

### Critérios de aceite

-   Todos os elementos parecem pertencer ao mesmo ambiente 3D.
-   A escala é consistente nos mapas de 5 e 18 nós.
-   Os marcadores e pesos continuam legíveis.
-   A câmera enquadra o cenário sem esconder elementos importantes.

------------------------------------------------------------------------

## TASK 08 --- Testes visuais e validação final

**Prioridade:** Obrigatória

### Implementação

-   Testar o mapa de 5 nós.
-   Testar o mapa de 18 nós.
-   Verificar a continuidade entre ruas e pontes.
-   Verificar se o carro atravessa as pontes corretamente.
-   Conferir se nenhuma construção bloqueia a rota.
-   Verificar se os 18 nós continuam corretamente posicionados.
-   Conferir se os pesos das arestas permanecem inalterados.
-   Verificar se a compactação não criou sobreposição de construções.
-   Avaliar a densidade de árvores e prédios.
-   Comparar o resultado com as referências visuais.

### Entregáveis

-   Captura do mapa de 5 nós.
-   Captura do mapa de 18 nós.
-   Captura de uma travessia de ponte.
-   Relatório dos assets utilizados.
-   Lista dos arquivos modificados.
-   Registro dos testes executados e seus resultados.

------------------------------------------------------------------------

## Ordem recomendada de execução

    Ordem Task                               Prioridade
  ------- ---------------------------------- -------------
        1 Continuidade das ruas com pontes   Alta
        2 Compactação do mapa de 18 nós      Alta
        3 Organização dos quarteirões        Alta
        4 Casas e prédios                    Alta
        5 Árvores e vegetação                Média/Alta
        6 Elementos decorativos              Média
        7 Escala e densidade visual          Alta
        8 Testes e validação                 Obrigatória

------------------------------------------------------------------------

## Instruções finais para a IA de programação

Não faça apenas alterações estéticas superficiais. Trabalhe na geometria
real do cenário 3D, reutilizando os modelos disponíveis na pasta local
`assets/`.

Priorize os seguintes pontos:

1.  As ruas devem se conectar perfeitamente às pontes, formando uma
    pista contínua.
2.  O mapa de 18 nós deve ficar mais compacto, sem perder a legibilidade
    das conexões.
3.  A cidade deve ficar mais populada, com casas, prédios e árvores,
    aproveitando os assets Kenney.

Antes de procurar ou baixar novos modelos, inspecione a pasta `assets/`
e verifique quais recursos já estão disponíveis. Reutilize os assets
existentes sempre que possível.

Execute as tasks na ordem recomendada. Após cada etapa, rode o jogo e
valide visualmente o resultado antes de avançar.

**Preserve integralmente a lógica dos algoritmos e a topologia dos
grafos. O objetivo é melhorar o cenário, não modificar o problema
matemático.**
