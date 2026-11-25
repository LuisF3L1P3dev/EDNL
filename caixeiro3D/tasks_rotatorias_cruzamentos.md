# NEXUS 3D — Implementação de rotatórias em todos os cruzamentos

## TASK 01 — Identificar todos os cruzamentos do mapa

**Prioridade: Alta**

### Implementação
- Analisar todas as ruas dos mapas de 5 e 18 nós.
- Identificar cruzamentos em X, T e Y.
- Localizar os pontos onde duas ou mais ruas realmente se conectam.
- Identificar sobreposições de ruas que não representam conexões matemáticas.
- Preparar cada cruzamento válido para receber uma rotatória.
- Reorganizar as ruas que se cruzam apenas visualmente, evitando conexões inexistentes.

### Critérios de aceite
- Todos os cruzamentos reais são identificados.
- Nenhuma interseção válida fica sem tratamento.
- Nenhuma conexão matemática adicional é criada.

## TASK 02 — Substituir todos os cruzamentos por rotatórias

**Prioridade: Crítica**

### Implementação
- Inspecionar os assets da Kenney disponíveis na pasta `assets/`.
- Identificar modelos de rotatórias, curvas e segmentos de ruas.
- Criar um componente 3D de rotatória reutilizável.
- Substituir as interseções reais por rotatórias.
- Adaptar as rotatórias à quantidade de entradas e saídas.
- Criar ilhas centrais circulares com grama e vegetação.
- Padronizar largura, raio e altura das pistas.
- Evitar sobreposição de meshes e problemas de Z-fighting.
- Manter rotatórias proporcionais às ruas existentes.

### Critérios de aceite
- Todos os cruzamentos reais possuem rotatórias.
- As rotatórias têm aparência padronizada.
- As pistas são contínuas, sem interrupções.

## TASK 03 — Corrigir a conexão entre ruas e rotatórias

**Prioridade: Crítica**

### Implementação
- Alinhar todas as ruas às respectivas entradas e saídas.
- Criar transições suaves entre trechos retos e circulares.
- Ajustar as faixas de circulação.
- Eliminar espaços vazios entre as peças 3D.
- Garantir que nenhuma rua atravesse a ilha central.
- Manter a geometria compatível com a escala da van.
- Organizar o entorno para que casas e prédios não invadam as rotatórias.

### Critérios de aceite
- Nenhuma rua termina desconectada.
- Não existem modelos de asfalto sobrepostos indevidamente.
- Todas as rotatórias apresentam entradas e saídas contínuas.

## TASK 04 — Adaptar a movimentação da van

**Prioridade: Crítica**

### Implementação
- Atualizar os waypoints visuais de cada cruzamento.
- Fazer a van entrar pela pista correta.
- Fazer o veículo contornar a ilha central.
- Utilizar curvas suaves na trajetória.
- Manter a frente da van orientada no sentido do movimento.
- Evitar que a van atravesse o centro da rotatória.
- Fazer a van sair pelo acesso correspondente à rota calculada.
- Reduzir suavemente a velocidade nas curvas.
- Garantir que a linha destacada da rota acompanhe o percurso real do veículo.

### Critérios de aceite
- A van percorre as rotatórias sem dar ré.
- O veículo não corta caminho.
- A rotação e o deslocamento são suaves.
- A rota visual corresponde ao trajeto realizado.

## TASK 05 — Ajustar o tamanho e a distribuição das rotatórias

**Prioridade: Alta**

### Implementação
- Criar rotatórias compactas para cruzamentos pequenos.
- Utilizar rotatórias maiores onde houver mais acessos.
- Manter espaçamento proporcional entre rotatórias próximas.
- Reorganizar as ruas para impedir sobreposição de rotatórias.
- Evitar que o mapa de 18 nós fique excessivamente grande.
- Redistribuir construções próximas quando necessário.
- Preservar a organização dos quarteirões.
- Manter todos os nós facilmente identificáveis.

### Critérios de aceite
- O mapa continua compacto.
- Nenhuma rotatória invade outra.
- Casas, prédios e marcadores continuam visíveis.

## TASK 06 — Adicionar ambientação às rotatórias

**Prioridade: Média**

### Implementação
- Utilizar vegetação dos assets Kenney.
- Adicionar grama, árvores pequenas e arbustos às ilhas centrais.
- Adicionar placas de preferência e sinalização de rotatória.
- Posicionar postes de iluminação nas laterais.
- Criar faixas de aproximação e sinalização horizontal.
- Utilizar cores e materiais compatíveis com o estilo low-poly cartoon.
- Evitar objetos decorativos que bloqueiem a visão dos veículos.

### Critérios de aceite
- As rotatórias integram-se visualmente ao cenário.
- A decoração não prejudica a circulação.
- A sinalização mantém escala e posicionamento coerentes.

## TASK 07 — Preservar os grafos e os pesos originais

**Prioridade: Obrigatória**

### Implementação
- Manter os dados matemáticos separados da geometria das rotatórias.
- Não alterar os pesos das arestas.
- Não adicionar rotatórias como novos nós do grafo matemático.
- Utilizar waypoints intermediários somente para animação e renderização.
- Não criar novas conexões entre arestas que apenas se cruzam visualmente.
- Para cruzamentos visuais sem conexão lógica, reorganizar o traçado ou utilizar separação de níveis, em vez de criar uma ligação inexistente.
- Preservar o resultado dos algoritmos.

### Validações
- Mapa de 5 nós: preservar 5 nós e 8 arestas.
- Mapa de 18 nós: preservar todos os nós e conexões originais.
- Manter o peso da aresta 9–14 igual a 1.
- Manter o circuito ótimo de custo 15 no mapa de 5 nós.

## TASK 08 — Testes de integração

**Prioridade: Obrigatória**

### Implementação
- Testar todas as rotatórias dos dois mapas.
- Verificar a movimentação da van em cada entrada e saída utilizada.
- Identificar e corrigir possíveis colisões.
- Verificar sobreposição de ruas, rotatórias e construções.
- Testar rotatórias próximas umas das outras.
- Conferir o comportamento da van com diferentes velocidades.
- Validar o funcionamento da câmera isométrica e do acompanhamento do veículo.
- Verificar a legibilidade dos pesos e marcadores dos nós.
- Comparar os resultados dos algoritmos antes e depois das alterações.

### Entregáveis
- Captura do mapa de 5 nós.
- Captura do mapa de 18 nós.
- Captura aproximada de uma rotatória.
- Demonstração da van realizando uma curva.
- Lista dos arquivos modificados.
- Resultado dos testes de integridade dos grafos.

---

## Ordem de execução

| Ordem | Task | Prioridade |
|---|---|---|
| 1 | Identificar todos os cruzamentos | Alta |
| 2 | Implementar rotatórias | Crítica |
| 3 | Conectar ruas e rotatórias | Crítica |
| 4 | Adaptar a movimentação da van | Crítica |
| 5 | Ajustar distribuição e tamanho | Alta |
| 6 | Adicionar ambientação | Média |
| 7 | Preservar grafos e pesos | Obrigatória |
| 8 | Executar testes | Obrigatória |

## Instrução final para a IA

Implemente rotatórias em todos os cruzamentos reais dos mapas de 5 e 18 nós, utilizando os assets Kenney já presentes no projeto.

Priorize a continuidade visual das ruas, a movimentação natural da van e a organização proporcional das rotatórias.

**Não altere os pesos, as conexões ou a quantidade de nós dos grafos.**

Se duas ruas se cruzarem visualmente sem uma conexão matemática, reorganize o traçado para eliminar a interseção ou represente uma passagem em níveis diferentes.

Não recrie o projeto do zero. Reutilize a arquitetura existente, implemente as melhorias progressivamente e valide o funcionamento de cada etapa.