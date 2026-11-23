# Tasks — Refinamento visual do game NEXUS 3D

## Objetivo

Melhorar o visual do game para deixá-lo **mais cartunesco, suave e agradável**, reorganizar melhor as ruas, principalmente nos cruzamentos, **reduzir visualmente o mapa de 18 pontos** sem alterar os pesos ou conexões do grafo, e **popular mais o cenário com casas e prédios**.

**Regra principal:** não alterar a lógica dos algoritmos, os pesos das arestas ou a topologia dos grafos. As mudanças devem ser **visuais e estruturais no cenário**.

---

## TASK 01 — Deixar o estilo gráfico mais cartunesco e suave

**Prioridade:** Alta

### Objetivo

Melhorar a direção de arte do jogo para ficar com aparência mais cartoon, amigável e consistente com assets low-poly.

### Implementação

- Ajustar a paleta de cores para tons mais suaves e vibrantes.
- Reduzir o aspecto “duro” ou técnico do cenário.
- Deixar a grama, ruas, prédios e árvores com visual mais limpo e estilizado.
- Usar sombras suaves.
- Suavizar contrastes excessivos.
- Padronizar melhor o estilo entre casas, prédios, ruas e vegetação.
- Garantir que todos os elementos pareçam pertencer ao mesmo mundo visual.
- Se houver materiais/texturas muito realistas ou muito secas, simplificá-las para um estilo mais cartunesco.
- Melhorar a aparência geral do mapa sem prejudicar a leitura das conexões.

### Critérios de aceite

- O cenário deve parecer mais amigável e estilizado.
- O visual deve ficar mais suave e agradável.
- Casas, prédios, ruas e vegetação devem compartilhar a mesma linguagem visual.
- O mapa deve continuar legível.

---

## TASK 02 — Reduzir visualmente o mapa de 18 pontos

**Prioridade:** Alta

### Objetivo

Diminuir o tamanho visual do mapa de 18 pontos para que ele fique mais compacto, mais legível e com melhor aproveitamento do espaço da tela.

### Implementação

- Aproximar visualmente os 18 nós.
- Reduzir espaços vazios excessivos entre ruas e quarteirões.
- Reorganizar a malha urbana para ocupar menos área total.
- Ajustar a posição das cidades e construções para acompanhar a compactação.
- Preservar área suficiente para cruzamentos e circulação do carro.
- Ajustar o enquadramento inicial da câmera, se necessário.

### Restrições

- Não alterar os pesos.
- Não alterar as conexões entre os nós.
- Não renumerar os nós.
- Não modificar a lógica do algoritmo.

### Critérios de aceite

- O mapa de 18 pontos deve ficar menor visualmente.
- Os 18 nós devem continuar visíveis e identificáveis.
- O cenário deve parecer mais denso e melhor organizado.
- A compactação não pode gerar sobreposição problemática.

---

## TASK 03 — Organizar melhor as ruas

**Prioridade:** Alta

### Objetivo

Melhorar a organização das ruas para que o mapa fique mais limpo, coerente e fácil de entender.

### Implementação

- Reorganizar os trechos de rua para ficarem mais alinhados.
- Reduzir curvas desnecessárias.
- Melhorar a distribuição das vias entre os nós.
- Manter ruas com largura consistente.
- Organizar melhor o fluxo das conexões no mapa.
- Tornar os caminhos visuais mais claros para leitura do trajeto.
- Garantir que a rua represente melhor a aresta correspondente.

### Critérios de aceite

- As ruas devem ficar visualmente mais limpas.
- O traçado deve parecer mais planejado.
- O jogador deve conseguir entender melhor o caminho entre os pontos.
- A organização não pode alterar a lógica do grafo.

---

## TASK 04 — Melhorar principalmente os cruzamentos

**Prioridade:** Alta

### Objetivo

Corrigir cruzamentos confusos para que as interseções fiquem mais claras e visualmente organizadas.

### Implementação

- Reposicionar cruzamentos muito próximos.
- Criar interseções mais bem definidas.
- Garantir continuidade entre os segmentos de rua.
- Evitar aparência de ruas “quebradas” ou mal encaixadas.
- Evitar sobreposição indevida de modelos de rua.
- Corrigir cruzamentos que pareçam criar conexões falsas.
- Separar melhor vias paralelas ou vias próximas.
- Ajustar curvas e interseções para o carro trafegar de forma mais natural.

### Critérios de aceite

- Os cruzamentos devem ficar visualmente organizados.
- O jogador deve entender onde existe interseção real.
- As ruas não devem parecer desconectadas.
- Não devem surgir conexões visuais que não existam no grafo.

---

## TASK 05 — Popular o mapa com mais casas e prédios

**Prioridade:** Alta

### Objetivo

Deixar o cenário mais vivo, urbano e interessante, com maior densidade de construções.

### Implementação

- Adicionar mais casas residenciais.
- Adicionar mais prédios comerciais e residenciais.
- Criar conjuntos de construções por quarteirão.
- Distribuir melhor os edifícios no cenário.
- Variar tamanho, rotação e posicionamento dos modelos.
- Evitar repetição excessiva do mesmo asset.
- Preencher áreas muito vazias do mapa.
- Manter espaços livres suficientes para ruas, cruzamentos e leitura visual.

### Critérios de aceite

- O mapa deve parecer mais populado.
- Os quarteirões devem ter mais vida urbana.
- A ambientação deve enriquecer o cenário.
- As construções não podem atrapalhar a leitura do grafo ou o trajeto do carro.

---

## TASK 06 — Refinar a distribuição urbana do mapa

**Prioridade:** Média/Alta

### Objetivo

Melhorar a composição geral da cidade para que o cenário pareça melhor planejado.

### Implementação

- Distribuir melhor casas, prédios, árvores e espaços livres.
- Evitar grandes áreas vazias sem propósito visual.
- Organizar os quarteirões de forma mais coerente.
- Posicionar construções próximas às ruas, como em uma cidade real.
- Criar melhor equilíbrio entre área construída e área verde.
- Preservar destaque visual para os nós e marcadores.

### Critérios de aceite

- O cenário deve parecer uma cidade planejada.
- A distribuição dos elementos deve ficar mais equilibrada.
- O mapa deve parecer mais completo e menos vazio.

---

## TASK 07 — Melhorar a consistência visual entre ruas e construções

**Prioridade:** Média/Alta

### Objetivo

Fazer ruas, casas e prédios parecerem parte do mesmo ambiente, evitando sensação de elementos soltos.

### Implementação

- Ajustar escala das construções em relação às ruas.
- Ajustar posicionamento das construções em relação aos quarteirões.
- Criar relação mais natural entre calçadas, ruas e edifícios.
- Garantir que os prédios não pareçam “jogados” no mapa.
- Melhorar o encaixe visual entre ambiente urbano e malha viária.

### Critérios de aceite

- O cenário deve parecer mais coeso.
- Casas e prédios devem se integrar melhor ao mapa.
- O ambiente deve parecer mais convincente e organizado.

---

## TASK 08 — Validar o impacto visual sem alterar a lógica do grafo

**Prioridade:** Obrigatória

### Objetivo

Confirmar que todas as melhorias visuais preservaram os dados matemáticos e o funcionamento do jogo.

### Verificações

- Confirmar que o mapa de 18 pontos continua com os mesmos pesos.
- Confirmar que nenhuma aresta foi removida ou adicionada.
- Confirmar que os nós mantêm seus identificadores.
- Validar que os algoritmos continuam retornando os mesmos resultados para os mesmos dados.
- Testar se o carro continua trafegando corretamente pelas ruas.
- Conferir se os cruzamentos continuam funcionais visualmente.
- Verificar se a compactação do mapa não prejudicou a navegação.

### Entregáveis

- Captura do mapa de 18 pontos atualizado.
- Captura mostrando ruas e cruzamentos reorganizados.
- Captura mostrando aumento de casas e prédios.
- Relatório dos arquivos modificados.
- Relatório dos testes executados.

---

## Ordem recomendada de execução

| Ordem | Task | Prioridade |
|---:|---|---|
| 1 | Deixar o visual mais cartunesco e suave | Alta |
| 2 | Reduzir visualmente o mapa de 18 pontos | Alta |
| 3 | Organizar melhor as ruas | Alta |
| 4 | Melhorar os cruzamentos | Alta |
| 5 | Popular com mais casas e prédios | Alta |
| 6 | Refinar a distribuição urbana | Média/Alta |
| 7 | Melhorar consistência visual geral | Média/Alta |
| 8 | Validar sem alterar a lógica | Obrigatória |

---

## Instrução final para a IA

Implemente essas melhorias **no projeto existente**, sem reconstruir o jogo do zero.

**Prioridades principais:**

1. Deixar o gráfico mais cartunesco e suave.
2. Diminuir visualmente o mapa de 18 pontos.
3. Organizar melhor as ruas, principalmente os cruzamentos.
4. Popular o cenário com mais casas e prédios.

**Importante:** não altere pesos, conexões, nós ou resultados matemáticos do problema. O objetivo é melhorar a **qualidade visual e a organização do cenário**, preservando a lógica do game.
