# NEXUS 3D — Correção do grafo original e da rota do Caixeiro Viajante

## Objetivo

Corrigir as inconsistências entre o mapa original de 18 nós e a implementação atual do game NEXUS 3D.

O mapa original, utilizado como referência, possui uma estrutura específica de nós, conexões e pesos. O jogo atual está apresentando uma sequência diferente, com custo informado de 340, enquanto a referência apresenta uma rota de custo 391.

A implementação deve ser corrigida para que:

- O grafo do jogo corresponda exatamente ao grafo original.
- Os 18 nós sejam preservados.
- A quantidade de conexões seja exatamente a mesma da referência.
- Todos os pesos sejam preservados.
- A sequência de visita corresponda à rota de referência.
- O cálculo do custo considere todos os trechos percorridos, inclusive o retorno à origem.
- A representação visual corresponda à estrutura matemática do grafo.

**Não recrie o projeto do zero. Analise e corrija a implementação existente.**

---

## Referência matemática — Rota esperada

O mapa original de 18 nós utiliza a seguinte sequência:

```text
1 → 2 → 3 → 4 → 9 → 14 → 15 → 10 → 5 → 6 → 7 → 11 → 18 → 17 → 16 → 13 → 8 → 12 → 1
```

**Custo total esperado: 391**

### Tabela dos trechos e pesos

| Trecho | Peso |
|---|---:|
| 1 → 2 | 20 |
| 2 → 3 | 25 |
| 3 → 4 | 25 |
| 4 → 9 | 23 |
| 9 → 14 | 1 |
| 14 → 15 | 20 |
| 15 → 10 | 19 |
| 10 → 5 | 19 |
| 5 → 6 | 12 |
| 6 → 7 | 17 |
| 7 → 11 | 38 |
| 11 → 18 | 36 |
| 18 → 17 | 15 |
| 17 → 16 | 26 |
| 16 → 13 | 19 |
| 13 → 8 | 22 |
| 8 → 12 | 25 |
| 12 → 1 | 29 |
| **Total** | **391** |

Essa sequência deve ser utilizada como referência de validação do algoritmo.

---

## TASK 01 — Auditar o grafo original e o grafo implementado

**Prioridade: Crítica**

### Problema

O mapa atual pode estar utilizando conexões, pesos ou estruturas diferentes das presentes no grafo original.

### Implementação

- Localizar onde os 18 nós estão definidos no código.
- Identificar onde as conexões entre os nós são armazenadas.
- Identificar onde os pesos das arestas são definidos.
- Comparar o grafo implementado com a imagem original:
  `Captura de tela 2026-11-11 135747.png`.
- Conferir individualmente cada conexão.
- Conferir individualmente cada peso.
- Identificar arestas ausentes, duplicadas ou adicionadas indevidamente.
- Verificar se o grafo está sendo tratado corretamente como não direcionado.
- Identificar possíveis divergências entre os dados utilizados pelos algoritmos e os dados utilizados para desenhar o mapa.

### Critérios de aceite

- Os 18 nós devem corresponder aos identificadores originais.
- Todas as conexões devem corresponder à referência.
- Todos os pesos devem ser idênticos.
- Nenhuma conexão pode existir apenas na implementação visual ou apenas na estrutura matemática.

---

## TASK 02 — Criar uma única fonte de verdade para o grafo

**Prioridade: Crítica**

### Implementação

Organizar os dados do grafo em uma estrutura única e reutilizável.

Essa estrutura deve alimentar:

- Renderização das ruas.
- Posicionamento dos nós.
- Algoritmo de Dijkstra.
- Algoritmo do Caixeiro Viajante.
- Cálculo do custo.
- Exibição dos resultados no painel.

Cada aresta deve armazenar:

- Nó de origem.
- Nó de destino.
- Peso original.
- Identificação da conexão.

### Restrições

- Não manter cópias independentes dos pesos em módulos diferentes.
- Não utilizar a distância visual entre os nós como peso matemático.
- Não recalcular pesos com base no tamanho das ruas.
- Não permitir que alterações visuais modifiquem o grafo.

### Critérios de aceite

Todos os módulos devem consultar a mesma estrutura de dados.

---

## TASK 03 — Corrigir a sequência de visita do Caixeiro Viajante

**Prioridade: Crítica**

### Problema atual

O jogo apresenta:

```text
1 → 2 → 3 → 4 → 5 → 6 → 7 → 11 → 15 → 18 → 17 → 16 → 14 → 9 → 10 → 14 → 13 → 12 → 13 → 8 → 1
```

A sequência não corresponde à ordem de visita esperada.

### Implementação

Corrigir o processamento do TSP para utilizar a seguinte sequência de referência:

```text
1 → 2 → 3 → 4 → 9 → 14 → 15 → 10 → 5 → 6 → 7 → 11 → 18 → 17 → 16 → 13 → 8 → 12 → 1
```

- Garantir que todos os 18 nós sejam visitados.
- Cada cidade deve aparecer uma única vez na ordem lógica de visita.
- O percurso deve começar no nó 1.
- O percurso deve terminar no nó 1.
- Corrigir a ordenação dos nós.
- Verificar a heurística utilizada para construir o circuito.
- Verificar critérios de desempate para evitar resultados inconsistentes entre execuções.

Não resolver o problema simplesmente fixando a sequência no código. O algoritmo deve continuar calculando a rota utilizando os dados reais do grafo.

A sequência de referência deve funcionar como teste de regressão.

### Critérios de aceite

A ordem lógica de visita deve corresponder à referência, com 18 cidades visitadas e retorno à origem.

---

## TASK 04 — Separar ordem de visita e caminho expandido pelo Dijkstra

**Prioridade: Crítica**

### Problema

O Dijkstra pode inserir nós intermediários durante a expansão dos caminhos mínimos entre duas cidades.

Isso pode fazer um mesmo identificador aparecer mais de uma vez no percurso físico, mesmo que a cidade já tenha sido visitada.

### Implementação

Separar duas estruturas:

**1. Ordem lógica de visita**

Representa a sequência do TSP:

```text
1 → 2 → 3 → 4 → 9 → 14 → 15 → 10 → 5 → 6 → 7 → 11 → 18 → 17 → 16 → 13 → 8 → 12 → 1
```

**2. Caminho físico expandido**

Representa todos os nós e trechos efetivamente percorridos pelo veículo, incluindo possíveis nós intermediários encontrados pelo Dijkstra.

### Regras

- Um nó intermediário não deve ser contabilizado como uma nova entrega.
- Não confundir passagem por uma cidade com visita programada pelo TSP.
- A contagem de cidades visitadas deve considerar somente a ordem lógica.
- O caminho expandido deve utilizar exclusivamente arestas existentes.
- Não eliminar repetições necessárias para a movimentação física do veículo.

### Critérios de aceite

O painel deve mostrar corretamente as 18 cidades visitadas, sem confundir nós intermediários com novas entregas.

---

## TASK 05 — Corrigir o cálculo do custo total

**Prioridade: Crítica**

### Problema

O game informa custo 340, que não corresponde ao custo esperado da rota original.

É necessário verificar se o cálculo está ignorando trechos finais, o retorno à origem ou nós intermediários do caminho expandido.

### Implementação

- Somar os pesos reais das arestas percorridas.
- Incluir todos os trechos da rota.
- Incluir obrigatoriamente o retorno ao nó 1.
- Evitar somar apenas os trechos até um determinado ponto.
- Não utilizar distância geométrica do cenário 3D.
- Não utilizar a distância em pixels entre os marcadores.
- Não contar o peso de uma aresta duas vezes por erro de processamento.
- Quando houver expansão pelo Dijkstra, somar os pesos das arestas originais que compõem o caminho expandido.

### Verificação obrigatória

O resultado de referência deve ser:

```text
Custo total = 391
```

O cálculo precisa ser feito a partir dos pesos reais, e não simplesmente atribuindo o valor 391 ao painel.

### Diagnóstico adicional

Na sequência atual, utilizando os pesos da referência, o custo acumulado dos trechos até `10 → 14` é exatamente 340.

Ainda existem trechos posteriores:

```text
14 → 13 = 24
13 → 12 = 27
12 → 13 = 27
13 → 8  = 22
8 → 1   = 29
```

Esses trechos somam 129.

Portanto, a sequência física atual, se todos esses trechos forem realmente percorridos com os pesos originais, não pode apresentar custo total 340.

Investigue especialmente se o acumulador está sendo encerrado antes de processar o restante do percurso.

### Critérios de aceite

- O custo é calculado integralmente.
- O retorno à origem é contabilizado.
- O valor exibido corresponde à soma dos pesos.
- A rota de referência apresenta custo 391.

---

## TASK 06 — Garantir a integridade das conexões

**Prioridade: Crítica**

### Implementação

- Conferir todas as conexões do grafo original.
- Remover conexões indevidas.
- Recuperar conexões ausentes.
- Eliminar arestas duplicadas.
- Preservar os pesos originais.
- Garantir simetria entre origem e destino no grafo não direcionado.
- Conferir a conexão 9–14, cujo peso definido no projeto é 1.
- Garantir que nenhuma rua decorativa seja interpretada como uma nova aresta matemática.

### Critérios de aceite

A quantidade de nós e arestas deve ser exatamente igual à do grafo original.

---

## TASK 07 — Alinhar a representação visual com o grafo matemático

**Prioridade: Alta**

### Implementação

- Fazer cada rua representar uma conexão real do grafo.
- Garantir que os marcadores estejam posicionados nos nós corretos.
- Fazer a rota destacada acompanhar a sequência calculada.
- Eliminar ruas visuais que sugiram conexões inexistentes.
- Preservar os pesos exibidos nas etiquetas.
- Garantir que as rotatórias e os cruzamentos não criem conexões matemáticas adicionais.
- Fazer a van percorrer exatamente o caminho expandido pelo algoritmo.

### Critérios de aceite

O mapa visual deve representar a mesma estrutura matemática utilizada pelo algoritmo.

---

## TASK 08 — Corrigir o painel de resultados

**Prioridade: Alta**

### Implementação

Garantir que o painel apresente:

- Quantidade de nós: 18.
- Quantidade de conexões: conforme o grafo original.
- Algoritmo utilizado.
- Custo total calculado.
- Quantidade de cidades visitadas.
- Sequência lógica de visita.
- Percurso físico realizado pela van.
- Tempo de cálculo.

Diferenciar visualmente:

- Nó de entrega visitado.
- Nó intermediário de passagem.
- Nó ainda não visitado.
- Origem e destino final.

### Critérios de aceite

Os resultados do painel devem corresponder ao resultado real do algoritmo, sem divergência entre sequência, percurso e custo.

---

## TASK 09 — Criar testes automatizados de integridade

**Prioridade: Obrigatória**

### Testes do grafo

- [ ] Existem exatamente 18 nós.
- [ ] A quantidade de arestas corresponde ao mapa original.
- [ ] Nenhuma aresta original está ausente.
- [ ] Nenhuma aresta adicional foi criada.
- [ ] Nenhum peso foi alterado.
- [ ] O grafo é não direcionado.
- [ ] A conexão 9–14 possui peso 1.

### Testes da rota

- [ ] A origem é o nó 1.
- [ ] O destino final é o nó 1.
- [ ] Todos os 18 nós são visitados.
- [ ] Cada nó aparece uma única vez na ordem lógica de visita.
- [ ] A sequência corresponde à referência.
- [ ] Todas as transições utilizam caminhos válidos.
- [ ] Nós intermediários não são contabilizados como novas entregas.

### Testes do custo

- [ ] Todos os pesos são somados.
- [ ] O retorno à origem é contabilizado.
- [ ] O custo não depende da distância visual do cenário.
- [ ] A rota de referência apresenta custo 391.
- [ ] O painel apresenta o mesmo custo calculado pelo algoritmo.

---

## TASK 10 — Validar o game completo

**Prioridade: Obrigatória**

### Implementação

Executar o game com o mapa de 18 nós e validar:

1. Selecionar o mapa de 18 pontos.
2. Selecionar a origem no ponto 1.
3. Executar o algoritmo.
4. Conferir a sequência apresentada.
5. Conferir o custo total.
6. Iniciar a simulação.
7. Acompanhar a van durante todo o percurso.
8. Conferir se a van passa pelos 18 pontos.
9. Verificar o retorno ao ponto 1.
10. Conferir se a animação corresponde à rota calculada.

### Entregáveis

- Captura do mapa de 18 nós corrigido.
- Captura do painel com a sequência correta.
- Captura do custo total.
- Demonstração da van percorrendo a rota.
- Relatório dos testes.
- Lista de arquivos modificados.

---

## Ordem recomendada de execução

| Ordem | Task | Prioridade |
|---|---|---|
| 1 | Auditar o grafo original | Crítica |
| 2 | Criar fonte única dos dados | Crítica |
| 3 | Corrigir sequência do TSP | Crítica |
| 4 | Separar visita e caminho expandido | Crítica |
| 5 | Corrigir cálculo do custo | Crítica |
| 6 | Validar conexões e pesos | Crítica |
| 7 | Alinhar representação visual | Alta |
| 8 | Corrigir painel de resultados | Alta |
| 9 | Criar testes automatizados | Obrigatória |
| 10 | Validar o game completo | Obrigatória |

---

## Instrução final para a IA de programação

Trabalhe diretamente no projeto local existente.

Utilize a imagem original de 18 nós como fonte de verdade para a estrutura do grafo e utilize a sequência e o custo informados neste documento como referência de validação.

Não faça alterações apenas na interface para exibir uma sequência diferente. Corrija a lógica responsável por carregar o grafo, calcular a rota, expandir os caminhos pelo Dijkstra e somar os pesos.

**A sequência de referência é:**

```text
1 → 2 → 3 → 4 → 9 → 14 → 15 → 10 → 5 → 6 → 7 → 11 → 18 → 17 → 16 → 13 → 8 → 12 → 1
```

**O custo de referência é 391.**

Preserve exatamente os 18 nós, a quantidade original de conexões e todos os pesos.

Não altere a geometria visual para tentar compensar erros matemáticos. Primeiro corrija os dados e os algoritmos; depois garanta que a representação 3D corresponda ao resultado correto.

Ao finalizar, execute os testes e apresente evidências de que o game está utilizando o mesmo grafo e produzindo o resultado esperado.