# Tasks — Transformar os 18 nós em pequenas cidades no NEXUS 3D

## Objetivo

Refinar o **mapa de 18 nós** do game NEXUS 3D para que **cada nó represente uma pequena cidade**, formada por um aglomerado de casas, prédios, árvores e elementos urbanos, em vez de uma construção isolada.

O cenário deve continuar **compacto, organizado, cartunesco e isométrico**, utilizando prioritariamente os modelos 3D já existentes em `assets/`.

> **Regra inegociável:** a transformação é **visual**. O grafo continua com exatamente 18 nós e suas arestas e pesos originais. A aresta entre os nós **9 e 14 permanece com peso 1**. Casas, prédios, quarteirões e ruas internas decorativas **não se tornam novos nós ou arestas**.

---

## TASK 01 — Definir uma pequena cidade para cada nó

**Prioridade:** Alta

### O que fazer

- Criar o conceito visual de **18 pequenas cidades**, identificadas de `1` a `18`.
- Manter um ponto lógico central/de chegada (`road_anchor`) para cada nó, separado das posições dos edifícios.
- Associar ao nó uma **área visual de cidade** (limite ou raio do lote urbano) e uma coleção de construções decorativas.
- Definir uma entrada da cidade conectada à rua principal do grafo.
- Posicionar o marcador numérico junto à entrada ou ao ponto de chegada, sem esconder as construções.
- Permitir variações de tamanho e composição, mas manter as cidades reconhecíveis e visualmente equilibradas.

### Critérios de aceite

- Cada nó possui seu **próprio aglomerado de construções** claramente identificável.
- Há exatamente **18 cidades visuais para 18 nós lógicos**.
- O marcador corresponde à cidade correta e ao ponto em que a van chega.

---

## TASK 02 — Criar um gerador reutilizável de aglomerados urbanos

**Prioridade:** Alta

### O que fazer

- Inspecionar os assets existentes de casas, prédios, lojas, calçadas, árvores e mobiliário urbano.
- Criar um componente reutilizável, por exemplo `CityCluster`, adaptado à arquitetura atual.
- Receber como parâmetros: ID do nó, posição da cidade, orientação da via de acesso, área disponível, densidade e variação de modelos.
- Distribuir **como ponto de partida**, de forma configurável, **4 a 8 casas e 1 a 3 prédios por cidade**, diminuindo a quantidade quando o espaço não comportar os objetos.
- Variar modelos, cores e rotações de maneira controlada, evitando repetições evidentes.
- Utilizar uma semente fixa para a distribuição procedural, garantindo que o cenário não mude aleatoriamente a cada execução.
- Compartilhar meshes e materiais sempre que possível, evitando carregar repetidamente o mesmo asset.

### Critérios de aceite

- O mesmo componente consegue montar aglomerados diferentes para os 18 nós.
- As construções seguem a mesma identidade visual low-poly/cartoon do jogo.
- Os assets são reutilizados, sem duplicação desnecessária de carregamento.

---

## TASK 03 — Posicionar casas e prédios em pequenos quarteirões

**Prioridade:** Alta

### O que fazer

- Organizar as construções de cada cidade em **2 ou 3 pequenos grupos de lotes**, conforme o espaço disponível.
- Preferir alinhamento em quarteirões retangulares, com fachadas voltadas para uma rua ou praça interna.
- Manter afastamentos consistentes entre casas, prédios, árvores e calçadas.
- Distribuir edifícios de maior porte em posições que não escondam os marcadores nem bloqueiem a câmera isométrica.
- Evitar colisões e sobreposições entre modelos.
- Impedir que uma cidade invada as ruas principais ou a área reservada à cidade vizinha.
- Preservar o enquadramento compacto do mapa de 18 nós, fazendo as cidades crescerem em **densidade**, não necessariamente no tamanho total do terreno.

### Critérios de aceite

- Cada nó parece um **pequeno bairro/cidade**, não uma casa isolada.
- As cidades permanecem separadas e identificáveis.
- As construções não se sobrepõem nem escondem a malha viária.

---

## TASK 04 — Integrar a entrada de cada cidade às ruas do grafo

**Prioridade:** Crítica

### O que fazer

- Manter a geometria da rua principal ligada ao `road_anchor` do nó.
- Criar calçadas, entrada urbana, pequena praça ou acesso visual entre a rua principal e o aglomerado.
- Posicionar o marcador `NÓ 01`, `NÓ 02` etc. na chegada da via, associado à respectiva cidade.
- Garantir que o veículo pare ou passe pelo ponto do nó sem atravessar casas ou prédios.
- Se houver ruas internas ilustrativas, distinguir essas ruas das conexões do grafo: elas **não podem criar caminhos lógicos adicionais**.
- Revisar cruzamentos próximos às cidades para evitar peças de rua sobrepostas e falsos acessos.

### Critérios de aceite

- A van chega ao **ponto de acesso de cada cidade** e não ao meio de uma construção.
- A rua, o ponto de parada, o marcador e a cidade têm uma relação espacial clara.
- Nenhuma via decorativa altera o percurso calculado pelos algoritmos.

---

## TASK 05 — Variar a identidade visual das 18 cidades

**Prioridade:** Média/Alta

### O que fazer

- Criar alguns padrões de composição reutilizáveis, por exemplo: **residencial**, **misto** e **comercial**.
- Alternar proporções de casas, prédios baixos, lojas, jardins e árvores.
- Adicionar pequenas praças, estacionamentos e bancos apenas quando houver espaço e assets adequados.
- Usar vegetação de referências como [Mini Forest](https://kenney.nl/assets/mini-forest) e [Nature Kit](https://kenney.nl/assets/nature-kit), priorizando os arquivos já disponíveis localmente.
- Preservar uma paleta consistente, com materiais suaves e iluminação cartunesca.
- Evitar que um aglomerado tenha elementos tão altos ou densos que impeçam visualizar cidades vizinhas.

### Critérios de aceite

- As 18 cidades compartilham o mesmo estilo, mas não parecem cópias exatas.
- O cenário fica mais populado sem se tornar visualmente confuso.

---

## TASK 06 — Melhorar a legibilidade da cidade e dos nós

**Prioridade:** Alta

### O que fazer

- Posicionar os marcadores numéricos acima ou ao lado dos acessos, sem sobrepor telhados.
- Utilizar tamanho de marcador consistente e legível no zoom padrão.
- Evitar que árvores e edifícios ocultem o marcador ou o veículo.
- Manter pesos das arestas posicionados sobre ou próximos às ruas principais, não dentro dos quarteirões.
- Destacar a cidade atual, cidades visitadas e cidade de origem usando contorno, iluminação discreta ou cor do marcador.
- Testar o resultado com a câmera isométrica nos níveis de zoom aproximado e afastado.

### Critérios de aceite

- O usuário identifica rapidamente qual cidade corresponde a cada nó.
- Marcadores, pesos e trajeto da van continuam legíveis.

---

## TASK 07 — Otimizar o desempenho do mapa mais populado

**Prioridade:** Alta

### O que fazer

- Medir o desempenho atual antes das alterações.
- Reutilizar geometria, modelos e texturas comuns às cidades.
- Empregar instanciamento, batching ou outro recurso compatível com o renderizador existente quando possível.
- Aplicar redução de detalhes ou ocultação de objetos distantes apenas se necessário, preservando marcadores e ruas importantes.
- Evitar animações ou cálculos individuais desnecessários em elementos estáticos.
- Ajustar a densidade das cidades caso o cenário prejudique significativamente a fluidez do jogo.

### Critérios de aceite

- O mapa de 18 cidades continua responsivo ao movimentar a câmera e ao executar a simulação.
- Não há travamentos causados pelo carregamento repetido de modelos.

---

## TASK 08 — Validar as 18 cidades e preservar o grafo

**Prioridade:** Obrigatória

### O que fazer

- Verificar visualmente que **todos os nós de 1 a 18** têm um aglomerado próprio.
- Conferir que todos os marcadores correspondem às construções corretas.
- Testar o percurso da van próximo aos acessos de várias cidades.
- Conferir que nenhuma construção bloqueia ruas, pontes ou cruzamentos.
- Validar a ausência de sobreposições indevidas e o enquadramento isométrico.
- Comparar os dados do grafo antes e depois: mesmos nós, mesmas arestas, mesmos pesos.
- Confirmar especificamente que a conexão `9–14` mantém **peso 1**.
- Executar testes de caminho mínimo e de rota no mapa de 18 nós.
- Registrar capturas de tela do mapa inteiro e de pelo menos três cidades em zoom aproximado.

### Critérios de aceite

- [ ] Exatamente 18 nós lógicos e 18 cidades visuais.
- [ ] Cada cidade tem várias construções (não apenas uma casa isolada).
- [ ] Cada cidade possui um acesso claramente conectado à rua principal.
- [ ] A van percorre somente arestas válidas do grafo.
- [ ] Não há casas ou prédios atravessando as vias.
- [ ] O mapa permanece compacto e legível.
- [ ] Pesos e conexões permanecem inalterados, incluindo `9–14 = 1`.
- [ ] O jogo mantém desempenho satisfatório.

---

## Ordem recomendada de execução

| Ordem | Task | Prioridade |
|---:|---|---|
| 1 | Definir uma cidade para cada nó | Alta |
| 2 | Criar o gerador de aglomerados urbanos | Alta |
| 3 | Organizar casas e prédios em quarteirões | Alta |
| 4 | Integrar cada cidade às ruas e ao ponto de chegada | Crítica |
| 5 | Variar a identidade das cidades | Média/Alta |
| 6 | Melhorar a legibilidade dos nós | Alta |
| 7 | Otimizar o desempenho | Alta |
| 8 | Validar o cenário e o grafo | Obrigatória |

---

## Prompt final para a IA de programação

> Analise o projeto NEXUS 3D existente, as capturas do mapa de 18 nós e os assets disponíveis em `assets/`. Implemente, em etapas, um sistema de pequenas cidades: **cada um dos 18 nós deve ser representado por um aglomerado de casas, prédios, vegetação e quarteirões**, com um acesso claro à rua principal e um marcador numérico associado. Reaproveite os assets e a renderização existentes, sem recomeçar o jogo do zero. Mantenha o mapa compacto, cartunesco, organizado e com boa performance. **Não modifique os nós, as conexões nem os pesos**, especialmente a aresta **9–14, com peso 1**. As construções e ruas decorativas não devem criar novos nós ou arestas. Execute as tasks na ordem proposta, teste cada etapa e apresente os arquivos alterados, resultados e capturas de tela.
