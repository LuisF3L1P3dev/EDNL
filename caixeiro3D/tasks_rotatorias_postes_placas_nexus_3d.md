# Tasks — Melhorias das ruas, rotatórias e sinalização do NEXUS 3D

## Objetivo

Melhorar a organização das estradas nos mapas de **5 e 18 nós**, substituindo cruzamentos confusos por rotatórias onde fizer sentido, adicionando postes e placas com assets da **Kenney** e tornando a distribuição das ruas mais proporcional.

> **Regra obrigatória:** nenhuma melhoria visual pode alterar os **pesos das arestas**, a **quantidade de nós**, as **conexões originais dos grafos** ou a lógica dos algoritmos. Comprimentos e posições geométricas das ruas podem mudar; os custos matemáticos devem permanecer iguais.

---

## TASK 01 — Implementar rotatórias nos cruzamentos

**Prioridade:** Alta

### Problema

Algumas estradas se cruzam diretamente, formando interseções pouco organizadas e visualmente confusas.

### Implementação

- Identificar os cruzamentos reais das ruas.
- Substituir cruzamentos selecionados por rotatórias circulares.
- Procurar modelos de rotatórias nos assets Kenney já disponíveis no projeto.
- Caso não exista um modelo completo, construir a rotatória com peças modulares compatíveis.
- Criar uma ilha central com grama e vegetação.
- Conectar corretamente as ruas de entrada e saída.
- Manter a largura das pistas proporcional ao restante do cenário.
- Adicionar sinalização horizontal e vertical nas entradas.
- Garantir que a van percorra a rotatória suavemente, sem cortar caminho pelo centro.

### Critérios de aceite

- As rotatórias parecem integradas às ruas.
- O veículo executa as curvas sem movimentos bruscos.
- Não há peças de asfalto sobrepostas ou espaços vazios entre as conexões.
- Uma rotatória em um cruzamento visual **não cria novas conexões** entre arestas que não compartilham um nó no grafo.

---

## TASK 02 — Reorganizar a distribuição proporcional das estradas

**Prioridade:** Alta

### Implementação

- Padronizar a largura das ruas.
- Manter espaçamento consistente entre vias paralelas.
- Organizar a malha urbana em quarteirões retangulares e quadrados.
- Reduzir curvas e desvios desnecessários.
- Evitar ruas muito próximas que provoquem sobreposição de modelos.
- Ajustar a distribuição dos cruzamentos.
- Criar transições suaves entre ruas retas, curvas e rotatórias.
- Manter o mapa de 18 nós compacto.
- Reservar espaços proporcionais para construções e vegetação.

### Critérios de aceite

- As estradas apresentam espaçamento equilibrado e caminhos visualmente contínuos.
- O mapa permanece compacto e com todos os nós identificáveis.
- A reorganização espacial não altera pesos ou conexões matemáticas.

---

## TASK 03 — Adicionar postes ao lado das ruas

**Prioridade:** Média

### Implementação

- Identificar assets de postes de iluminação nos pacotes Kenney locais.
- Posicionar postes nas calçadas e margens das ruas.
- Manter espaçamento regular entre postes.
- Adicionar postes próximos às rotatórias e interseções.
- Ajustar a altura dos postes conforme a escala dos prédios.
- Evitar postes no centro das pistas.
- Evitar que os postes bloqueiem marcadores dos nós, placas ou a visão da câmera.
- Utilizar instanciamento ou reutilização de modelos para melhorar o desempenho.

### Critérios de aceite

- Os postes acompanham a organização das estradas.
- Não obstruem o percurso da van, as entradas das cidades ou a leitura dos nós.
- Mantêm estilo e escala compatíveis com os demais assets.

---

## TASK 04 — Adicionar placas de sinalização

**Prioridade:** Média

### Implementação

- Utilizar placas disponíveis nos assets Kenney do projeto.
- Adicionar placas de preferência nas entradas das rotatórias.
- Posicionar placas de direção em cruzamentos.
- Adicionar placas de limite de velocidade.
- Adicionar placas de identificação de ruas e cidades.
- Utilizar placas de advertência em curvas.
- Manter as placas voltadas para o sentido de circulação.
- Ajustar o tamanho para garantir legibilidade na câmera isométrica.

### Critérios de aceite

- As placas ficam nas margens das ruas e voltadas para os veículos.
- Não atravessam construções nem interferem no movimento da van.
- A sinalização é visualmente consistente e não cobre números ou pesos.

---

## TASK 05 — Melhorar a movimentação da van nas rotatórias

**Prioridade:** Alta

### Implementação

- Atualizar os **waypoints visuais** para acompanhar as curvas das rotatórias.
- Fazer a van entrar e sair pelos acessos correspondentes à rota calculada.
- Aplicar rotação gradual ao veículo.
- Manter a frente da van apontada na direção do movimento.
- Evitar que a van atravesse a ilha central.
- Reduzir suavemente a velocidade em curvas fechadas.
- Garantir que a rota destacada acompanhe o caminho real percorrido pelo carro.

### Critérios de aceite

- A van entra, contorna e sai das rotatórias de maneira natural.
- O veículo não aparenta andar de ré, não corta curvas e permanece sobre a pista.
- A linha de destaque coincide com o caminho animado.
- Os waypoints de animação **não são adicionados como novos nós matemáticos**.

---

## TASK 06 — Melhorar a integração entre ruas e cidades

**Prioridade:** Alta

### Implementação

- Ajustar as estradas ao redor dos aglomerados de casas e prédios que representam cada nó.
- Criar acessos bem definidos para cada cidade.
- Posicionar os marcadores dos nós nos pontos de chegada da van.
- Manter calçadas entre prédios e ruas.
- Evitar construções sobre as rotatórias.
- Adicionar pequenas áreas verdes nos espaços livres.
- Preservar a identidade visual *low-poly cartoon*.

### Critérios de aceite

- Cada cidade está claramente conectada às estradas do grafo.
- Construções, pontos de entrega e acessos estão visualmente alinhados.
- A van consegue alcançar cada nó sem atravessar prédios ou calçadas indevidamente.

---

## TASK 07 — Padronizar os modelos Kenney

**Prioridade:** Média

### Referências de assets

- **City Kit (Roads):** https://kenney.nl/assets/city-kit-roads
- **3D Road Tiles:** https://kenney.nl/assets/3d-road-tiles
- **Catálogo Kenney:** https://kenney.nl/assets

> Primeiro inspecione a pasta local `assets/`. Os links são referências; não pressupõem que um pacote específico já esteja presente nem que contenha uma rotatória pronta.

### Implementação

- Inspecionar os modelos já existentes de ruas, sinalização e elementos urbanos.
- Manter a escala dos modelos consistente.
- Não misturar estilos visuais incompatíveis.
- Reutilizar materiais e texturas existentes.
- Utilizar os modelos locais sempre que possível.
- Quando não houver uma rotatória pronta, criar uma composição modular mantendo o estilo Kenney.
- Registrar quais assets foram reutilizados ou adaptados.

### Critérios de aceite

- Todos os novos elementos mantêm estilo, escala e materiais coerentes.
- Os assets carregam corretamente e não causam falhas na renderização.
- A implementação aproveita a estrutura atual do projeto.

---

## TASK 08 — Validar pesos e conexões dos grafos

**Prioridade:** Obrigatória

Antes e depois das alterações, executar testes para confirmar:

- [ ] O mapa de 5 nós mantém **5 nós e 8 arestas**.
- [ ] O mapa de 18 nós mantém todos os nós e conexões originais.
- [ ] Nenhum peso foi alterado.
- [ ] A aresta **9–14** continua com peso **1**.
- [ ] As rotatórias não criaram conexões matemáticas adicionais.
- [ ] Os resultados dos algoritmos permanecem consistentes para os mesmos dados.
- [ ] A van percorre as ruas corretamente, inclusive as rotatórias.
- [ ] Placas e postes não bloqueiam as pistas.
- [ ] As entradas e saídas das rotatórias estão visualmente conectadas às ruas.
- [ ] Nenhum elemento urbano cobre marcadores importantes ou pesos das arestas.

### Entregáveis

- Capturas dos mapas de 5 e 18 nós com as melhorias.
- Captura aproximada de uma rotatória com postes e placas.
- Registro dos arquivos alterados e dos assets utilizados.
- Resumo dos testes executados e seus resultados.

---

## Ordem recomendada de execução

| Ordem | Task | Prioridade |
|---:|---|---|
| 1 | TASK 02 — Reorganizar as estradas | Alta |
| 2 | TASK 01 — Implementar rotatórias | Alta |
| 3 | TASK 05 — Corrigir movimentação da van | Alta |
| 4 | TASK 06 — Integrar ruas e cidades | Alta |
| 5 | TASK 03 — Adicionar postes | Média |
| 6 | TASK 04 — Adicionar placas | Média |
| 7 | TASK 07 — Padronizar assets Kenney | Média |
| 8 | TASK 08 — Executar testes | Obrigatória |

**Observação:** inspecione os assets disponíveis no início do trabalho; a TASK 07 finaliza a padronização e registra os modelos escolhidos.

---

## Instrução final para a IA de programação

Implemente estas tasks diretamente no projeto existente em **Python/Pygame**, preservando a câmera isométrica e a identidade visual cartoon.

A prioridade é construir uma cidade organizada, com estradas proporcionais, rotatórias bem integradas, postes e placas posicionados corretamente, aproveitando os assets Kenney da pasta `assets/`.

Não recomece o projeto do zero. Antes de modificar o código, identifique como as ruas, os nós, o veículo e a câmera estão implementados. Execute as alterações por etapas e valide cada uma no jogo.

> **Não altere os pesos, a topologia dos grafos ou os algoritmos.** O comprimento visual das estradas pode mudar, mas o custo matemático de cada aresta deve permanecer exatamente igual ao original.
