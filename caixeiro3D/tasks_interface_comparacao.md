# NEXUS 3D — Comparação entre Força Bruta e Dijkstra

## Objetivo

Implementar um recurso interativo para comparar os resultados dos algoritmos utilizados no game NEXUS 3D.

Adicionar um botão **"Comparar soluções"** que abra um card com as informações das duas abordagens, permitindo avaliar custo total, sequência de nós, tempo de processamento e eficiência.

Preservar a identidade visual cartoon, a câmera isométrica, os mapas e seus pesos originais.

## TASK 01 — Implementar o botão "Comparar soluções"

**Prioridade: Alta**

### Implementação
- Adicionar o botão "Comparar soluções" ao painel de resultados.
- Exibir o botão somente nos modos em que a comparação fizer sentido.
- Ao clicar, abrir um card de comparação.
- Permitir fechar o card pelo botão X ou pelo mesmo botão.
- Manter o card oculto por padrão.
- Não interromper a simulação ao abrir o card.
- Preservar o estado da simulação e os dados calculados.

### Critérios de aceite
- O card aparece apenas quando solicitado.
- O usuário consegue abrir e fechar.
- O jogo continua funcionando normalmente.

## TASK 02 — Criar o card de comparação dos algoritmos

**Prioridade: Alta**

### Implementação

Criar um card com duas colunas:

**Coluna 1 — Força Bruta**
- Algoritmo: Força Bruta (TSP exato).
- Sequência completa da rota.
- Custo total.
- Tempo de processamento.
- Quantidade de circuitos avaliados.
- Identificação de solução ótima.

**Coluna 2 — Dijkstra + heurística**
- Algoritmo: Dijkstra + construção heurística do circuito.
- Sequência completa da rota.
- Custo total.
- Tempo de processamento.
- Quantidade de nós visitados.
- Indicação de solução aproximada.

### Design
- Fundo branco e bordas arredondadas.
- Cores compatíveis com a interface NEXUS.
- Ícones representando cada algoritmo.
- Números e resultados em destaque.
- Layout responsivo.
- Permitir rolagem do conteúdo quando necessário.

### Critérios de aceite
- Os resultados aparecem lado a lado.
- Os valores são fáceis de interpretar.
- O card não bloqueia permanentemente o mapa.

## TASK 03 — Implementar a comparação no mapa de 5 nós

**Prioridade: Crítica**

### Implementação

Executar os dois métodos sobre o mesmo grafo e a mesma origem.

**Força Bruta**
- Avaliar os circuitos Hamiltonianos válidos.
- Identificar o menor custo.
- Apresentar a solução ótima.

**Dijkstra + heurística**
- Calcular caminhos mínimos com Dijkstra.
- Construir um circuito com vizinho mais próximo.
- Aplicar 2-opt, quando apropriado.
- Expandir o percurso para as arestas originais.
- Apresentar o custo da rota.

### Referência de validação

Para o mapa de 5 nós:

- Rota ótima: 1 → 2 → 3 → 5 → 4 → 1.
- Custo ótimo: 15.

Os resultados heurísticos devem ser calculados, nunca fixados manualmente.

### Critérios de aceite
- Ambos utilizam o mesmo grafo.
- Ambos partem da mesma origem e retornam a ela.
- Os custos são calculados a partir dos pesos originais.
- É possível comparar corretamente os dois circuitos.

## TASK 04 — Comparar custo e desempenho

**Prioridade: Alta**

### Implementação

Adicionar indicadores:

- Custo da Força Bruta.
- Custo do circuito heurístico.
- Diferença absoluta entre custos.
- Diferença percentual em relação ao ótimo.
- Tempo de processamento de cada algoritmo.
- Quantidade de nós visitados.
- Identificação da melhor solução encontrada.

Calcular a diferença percentual por:

`((custo_heuristico - custo_otimo) / custo_otimo) * 100`

Os tempos devem ser medidos com um relógio de alta resolução, usando a mesma máquina e condições de execução.

Não apresentar uma solução mais rápida como matematicamente melhor quando ela possui custo superior.

### Critérios de aceite
- Resultados calculados automaticamente.
- Valores atualizados após nova execução.
- Nenhum indicador utiliza dados fictícios.

## TASK 05 — Permitir visualizar as duas rotas no mapa

**Prioridade: Alta**

### Implementação
- Adicionar o botão "Visualizar rota" para cada algoritmo.
- Ao selecionar Força Bruta, destacar o circuito exato.
- Ao selecionar Dijkstra + heurística, destacar o circuito calculado.
- Manter cores diferentes para distinguir as soluções.
- Permitir alternar entre as rotas.
- Sincronizar a rota selecionada com o movimento da van.
- Atualizar os indicadores da simulação conforme o algoritmo selecionado.

### Critérios de aceite
- O mapa apresenta a rota correspondente ao algoritmo.
- A van percorre os trechos corretos.
- A visualização não modifica os pesos ou conexões.

## TASK 06 — Adequar a comparação ao mapa de 18 nós

**Prioridade: Alta**

### Implementação
- Não executar Força Bruta no mapa de 18 nós.
- Permitir visualizar os resultados de Dijkstra e da heurística de circuito.
- Exibir uma informação esclarecendo que a Força Bruta está desabilitada nesse mapa.
- Não apresentar o circuito heurístico como ótimo global.
- Diferenciar o modo de caminho mínimo A → B do modo de circuito completo.

**Importante:** Dijkstra isolado resolve caminhos mínimos entre pontos; não é um algoritmo que determina sozinho o melhor circuito do Caixeiro Viajante. A comparação direta com Força Bruta TSP deve utilizar Dijkstra combinado com uma heurística para obter um circuito completo.

### Critérios de aceite
- O mapa de 18 nós não utiliza Força Bruta.
- O painel identifica corretamente a natureza de cada solução.
- Nenhum resultado é apresentado como ótimo sem comprovação.

## TASK 07 — Integrar o card ao HUD existente

**Prioridade: Média/Alta**

### Implementação
- Integrar o botão ao painel direito de resultados.
- Manter o card fechado inicialmente.
- Abrir o card como painel flutuante ou diálogo.
- Evitar que o card cubra controles essenciais.
- Permitir interação com zoom e câmera após fechar.
- Garantir funcionamento em diferentes resoluções.
- Manter tipografia e cores do NEXUS.

### Critérios de aceite
- O card segue o estilo visual do jogo.
- Não interfere nos controles principais.
- As informações continuam legíveis.

## TASK 08 — Testes e validação

**Prioridade: Obrigatória**

### Verificações
- [ ] O botão abre o card.
- [ ] O card fecha corretamente.
- [ ] Ambos os algoritmos utilizam os pesos originais.
- [ ] A comparação do mapa de 5 nós utiliza a mesma origem.
- [ ] A Força Bruta encontra custo 15 no mapa de 5 nós.
- [ ] O circuito heurístico visita todos os nós e retorna à origem.
- [ ] O cálculo percentual está correto.
- [ ] Os tempos são medidos durante a execução.
- [ ] As rotas podem ser visualizadas separadamente.
- [ ] A van acompanha a rota selecionada.
- [ ] A Força Bruta permanece desabilitada no mapa de 18 nós.
- [ ] Nenhum peso ou conexão é modificado.

## Ordem de execução

| Ordem | Task | Prioridade |
|---|---|---|
| 1 | Botão Comparar soluções | Alta |
| 2 | Card de comparação | Alta |
| 3 | Comparação no mapa de 5 nós | Crítica |
| 4 | Métricas e desempenho | Alta |
| 5 | Visualização das rotas | Alta |
| 6 | Tratamento do mapa de 18 nós | Alta |
| 7 | Integração ao HUD | Média/Alta |
| 8 | Testes e validação | Obrigatória |

## Instrução final para a IA

Implemente o sistema de comparação diretamente no projeto NEXUS 3D existente.

Utilize os algoritmos atuais, corrigindo possíveis inconsistências antes de apresentar os resultados.

O card deve permanecer oculto até o usuário clicar no botão "Comparar soluções".

No mapa de 5 nós, permita comparar a solução TSP exata por Força Bruta com o circuito obtido utilizando Dijkstra e heurística.

No mapa de 18 nós, não executar Força Bruta; manter apenas os métodos apropriados e informar suas limitações.

**Não alterar nós, pesos, conexões ou regras matemáticas dos grafos.**