# NEXUS 3D — Implementar circuito completo com Dijkstra

## Objetivo

Implementar um modo de execução que permita percorrer todos os pontos do mapa utilizando Dijkstra combinado com uma heurística para o Problema do Caixeiro Viajante (TSP).

O usuário poderá selecionar um ponto inicial, por exemplo, ponto 1, e executar uma rota que visite todos os outros pontos, retornando ao ponto inicial.

Exemplo para o mapa de 18 nós:

- Origem: Ponto 1.
- Destino final: Ponto 1.
- Pontos a visitar: 18.
- Objetivo: visitar todos os nós e retornar à origem.

A van deve percorrer fisicamente todo o trajeto no cenário 3D, passando pelos pontos de entrega e finalizando exatamente no local de partida.

---

## TASK 01 — Criar modo de execução "Circuito completo"

**Prioridade: Crítica**

### Implementação

Adicionar uma opção de seleção do tipo de percurso:

1. Caminho entre dois pontos.
2. Circuito completo.

**Caminho entre dois pontos:**
- Usuário seleciona origem e destino.
- Dijkstra calcula o caminho mínimo.
- A van percorre somente o trajeto entre os dois pontos.

**Circuito completo:**
- Usuário seleciona a origem.
- O destino final é automaticamente definido como a própria origem.
- O algoritmo deve visitar todos os nós do mapa.
- Após visitar todos os pontos, a van retorna à origem.
- O percurso deve ser fechado, formando um circuito.

### Critérios de aceite

- Os dois modos funcionam independentemente.
- Selecionar origem 1 e destino 1 no modo de caminho simples não deve iniciar um circuito completo.
- O modo circuito completo deve percorrer todos os nós antes de retornar à origem.

---

## TASK 02 — Implementar Dijkstra combinado com heurística para TSP

**Prioridade: Crítica**

### Implementação

Utilizar Dijkstra para calcular os caminhos mínimos entre os nós e uma heurística para determinar a ordem de visita.

Etapas:

1. Selecionar o nó inicial.
2. Calcular os caminhos mínimos entre os nós relevantes utilizando Dijkstra.
3. Construir uma rota inicial utilizando vizinho mais próximo.
4. Aplicar 2-opt para tentar melhorar a sequência.
5. Garantir que todos os nós sejam contemplados.
6. Adicionar o retorno ao nó inicial.
7. Expandir cada trecho para o caminho real de arestas do grafo.
8. Calcular o custo total utilizando os pesos originais.

### Regras

- Não utilizar força bruta no mapa de 18 nós.
- Não modificar os pesos das arestas.
- Não adicionar conexões inexistentes.
- Não utilizar distância visual do cenário 3D como peso.
- Não apresentar a solução heurística como ótimo global garantido.

### Critérios de aceite

- O algoritmo gera um circuito completo.
- Todos os nós são visitados.
- A van retorna à origem.
- O custo é calculado corretamente.

---

## TASK 03 — Permitir selecionar a origem do circuito

**Prioridade: Alta**

### Implementação

Adicionar um seletor de ponto inicial.

Exemplo:

- Ponto 1
- Ponto 2
- Ponto 3
- ...
- Ponto 18

O usuário poderá escolher qualquer nó como origem.

Após selecionar a origem:

- O destino final deve ser automaticamente definido como o mesmo nó.
- A sequência deve começar na origem selecionada.
- O circuito deve terminar na mesma origem.
- A heurística deve recalcular a rota considerando a nova origem.

### Critérios de aceite

- Todos os 18 pontos podem ser utilizados como origem.
- A rota é recalculada ao trocar a origem.
- O primeiro e o último ponto da sequência são iguais.

---

## TASK 04 — Expandir corretamente os caminhos calculados pelo Dijkstra

**Prioridade: Crítica**

### Implementação

Cada trecho da rota lógica do TSP deve ser convertido em um caminho físico utilizando Dijkstra.

Exemplo de ordem lógica:

1 → 2 → 3 → 4 → 9 → 14 → 15 → ... → 1

O caminho físico deve conter as arestas necessárias para conectar cada par de pontos consecutivos.

### Regras

- Utilizar exclusivamente conexões existentes no grafo.
- Preservar os pesos originais.
- Não confundir nós intermediários com novas entregas.
- Não eliminar repetições necessárias para percorrer os caminhos.
- Garantir que todos os nós sejam efetivamente alcançados.
- Garantir que o retorno à origem seja executado.

Manter separadas:
- Ordem lógica de visita do TSP.
- Caminho físico percorrido pela van.

### Critérios de aceite

- A van percorre todos os trechos necessários.
- Nenhuma conexão inexistente é utilizada.
- O percurso físico termina na origem.
- Os nós intermediários não são contabilizados incorretamente como novas entregas.

---

## TASK 05 — Atualizar o painel de resultados

**Prioridade: Alta**

### Implementação

Quando o modo Circuito completo estiver selecionado, apresentar:

- Algoritmo: Dijkstra + heurística.
- Tipo: Circuito completo.
- Origem selecionada.
- Quantidade total de pontos.
- Pontos visitados.
- Custo total.
- Distância percorrida, se disponível.
- Tempo de cálculo.
- Sequência lógica da rota.
- Progresso da entrega.

Exemplo:

**Circuito completo — 18 pontos**

Origem: Ponto 01

Sequência:
1 → 2 → 3 → 4 → 9 → 14 → 15 → 10 → 5 → 6 → 7 → 11 → 18 → 17 → 16 → 13 → 8 → 12 → 1

O exemplo acima serve como referência de apresentação. A sequência efetiva deve ser calculada pelo algoritmo, não fixada na interface.

### Critérios de aceite

- O painel apresenta os resultados reais.
- O custo corresponde à soma das arestas percorridas.
- O progresso é atualizado durante a simulação.

---

## TASK 06 — Implementar a execução completa da van

**Prioridade: Crítica**

### Implementação

A van deve executar o circuito completo de maneira contínua.

Comportamento:

1. Iniciar no ponto de origem.
2. Seguir a rota calculada.
3. Passar pelos pontos de entrega.
4. Atualizar o estado dos pontos visitados.
5. Continuar até visitar todos os nós.
6. Retornar à origem.
7. Finalizar a simulação.

### Controles

- Iniciar entrega.
- Pausar.
- Continuar.
- Reiniciar.
- Alterar velocidade.
- Acompanhar veículo.
- Centralizar câmera.

### Regras

- A van deve seguir sempre de frente.
- Não pode cortar caminhos.
- Deve acompanhar o centro das ruas.
- Deve realizar curvas suavemente.
- Deve parar no local correto ao finalizar.
- O retorno à origem precisa ser animado, não apenas indicado no painel.

### Critérios de aceite

A van deve percorrer visualmente todo o mapa e retornar ao ponto inicial.

---

## TASK 07 — Destacar os pontos visitados no mapa

**Prioridade: Média/Alta**

### Implementação

Utilizar cores diferentes para representar:

- Origem: destaque especial.
- Próximo ponto: destaque azul.
- Ponto visitado: verde.
- Ponto ainda não visitado: azul padrão.
- Rota percorrida: amarelo/laranja.

Durante a execução:

- Atualizar os marcadores.
- Destacar a rua percorrida.
- Atualizar a quantidade de pontos visitados.
- Destacar o retorno à origem.

### Critérios de aceite

O usuário consegue acompanhar visualmente o progresso do circuito.

---

## TASK 08 — Validar o circuito completo

**Prioridade: Obrigatória**

### Testes

- [ ] Selecionar o mapa de 18 pontos.
- [ ] Selecionar Circuito completo.
- [ ] Selecionar origem 1.
- [ ] Gerar a rota com Dijkstra + heurística.
- [ ] Verificar se todos os 18 nós foram contemplados.
- [ ] Verificar se a rota termina no ponto 1.
- [ ] Conferir se todas as arestas utilizadas existem.
- [ ] Conferir se os pesos permanecem inalterados.
- [ ] Conferir o custo total.
- [ ] Executar a animação completa.
- [ ] Confirmar que a van retorna fisicamente à origem.
- [ ] Testar outras origens.
- [ ] Testar pausa, retomada e reinício.

### Resultado esperado

O game deve permitir executar um circuito completo, começando em qualquer cidade, visitando todos os 18 pontos e retornando à cidade inicial.

---

## Ordem recomendada de execução

| Ordem | Task | Prioridade |
|---|---|---|
| 1 | Criar modo Circuito completo | Crítica |
| 2 | Dijkstra + heurística para TSP | Crítica |
| 3 | Seleção da origem | Alta |
| 4 | Expandir caminhos pelo Dijkstra | Crítica |
| 5 | Atualizar painel de resultados | Alta |
| 6 | Executar circuito com a van | Crítica |
| 7 | Destacar pontos visitados | Média/Alta |
| 8 | Testes e validação | Obrigatória |

## Instrução final para a IA

Implemente essa funcionalidade no projeto NEXUS 3D existente.

O objetivo é permitir que o usuário selecione uma origem, por exemplo, ponto 1, e execute uma rota que visite todos os 18 nós, retornando ao ponto 1.

Não confundir o caminho mínimo entre origem e destino com o circuito completo do Caixeiro Viajante.

Utilize Dijkstra para calcular os caminhos mínimos e uma heurística para construir a ordem de visita.

**Não fixe a sequência da rota no código.** O algoritmo deve calcular o circuito de acordo com a origem selecionada e os pesos reais do grafo.

Preserve a topologia, os pesos e os identificadores dos nós originais.

A entrega deve incluir a execução visual completa da van, desde a origem até o retorno ao mesmo ponto.