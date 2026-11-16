# Implementação do Caixeiro Viajante — Game 3D com Pygame

## Objetivo

Implementar e aprimorar o jogo 3D existente em Python com Pygame, transformando-o em uma aplicação interativa e educativa para demonstrar o Problema do Caixeiro Viajante (TSP), utilizando dois grafos ponderados fornecidos como referência.

O projeto já possui uma base funcional e assets 3D locais. Portanto, **não recrie o projeto do zero**. Analise a estrutura existente, identifique a arquitetura de renderização, preserve os recursos funcionais e realize as adaptações necessárias.

O resultado deve ter aparência profissional de um jogo de estratégia e entregas, com câmera isométrica, ambiente urbano low-poly, veículo animado, algoritmos de grafos e interface HUD integrada ao estilo artístico.

## 1. Restrições técnicas

- Linguagem principal: Python.
- Framework de gerenciamento do jogo: Pygame.
- Renderização: reutilizar a tecnologia 3D já presente no projeto; se necessário, avaliar integração compatível com OpenGL, sem substituir desnecessariamente a arquitetura.
- Assets: utilizar os modelos Kenney já disponíveis na pasta local `assets/`.
- Não baixar novos assets antes de verificar o conteúdo existente.
- Utilizar uma câmera de projeção ortográfica isométrica.
- Manter separação entre lógica dos grafos, algoritmos, renderização, animação e interface.
- Preservar os controles e funcionalidades existentes que não conflitem com os novos requisitos.

## 2. Analisar os assets locais

Inspecione recursivamente a pasta `assets/` e identifique modelos de:

- Carros e veículos de entrega.
- Ruas, cruzamentos e curvas.
- Casas e edifícios comerciais.
- Prédios e construções urbanas.
- Árvores, jardins, grama e parques.
- Calçadas, sinalizações e decoração.

Verifique os formatos presentes, como GLB, OBJ e FBX.

Priorize GLB quando existir suporte adequado na arquitetura atual. Caso o renderizador existente suporte outro formato de maneira mais estável, preserve a compatibilidade.

Implemente carregamento reutilizável dos recursos, com cache de modelos e texturas, tratamento de erros e normalização da escala.

Não substituir modelos 3D por imagens 2D se o jogo já oferecer renderização 3D funcional.

## 3. Construção dos mapas

Criar dois cenários independentes, baseados nas imagens originais dos grafos anexadas.

### Mapa 1 — Grafo de 5 nós

Representar exatamente os nós 1, 2, 3, 4 e 5.

Arestas não direcionadas, com os seguintes pesos:

```python
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

Algoritmos disponíveis:

**Força bruta (TSP exato)**

- Enumerar as permutações possíveis dos nós, mantendo uma origem fixa.
- Considerar somente percursos formados por arestas existentes.
- Visitar todos os nós uma única vez antes de retornar à origem.
- Calcular o custo completo de cada circuito.
- Encontrar e destacar o circuito de menor custo.
- Permitir visualizar as rotas candidatas ou acompanhar progressivamente a busca.

Resultado esperado para validação:

- Rota ótima: 1 → 2 → 3 → 5 → 4 → 1.
- Custo total: 15.
- A rota inversa é equivalente por se tratar de grafo não direcionado.

**Dijkstra (caminho mínimo)**

- Permitir escolher nó de origem e nó de destino.
- Exibir o menor caminho entre eles.
- Apresentar os nós explorados, distâncias calculadas e custo do caminho.
- Diferenciar claramente esse modo do TSP de força bruta.

**Importante:** Não apresentar Dijkstra isolado como solução exata do TSP.

### Mapa 2 — Grafo de 18 nós

Implementar os nós numerados de 1 até 18.

Utilizar a segunda imagem anexada como referência obrigatória para transcrever todas as arestas e seus pesos.

**Regra específica: a aresta entre os nós 9 e 14 possui peso 1.**

Não atribuir peso zero às conexões sem indicação. Não criar arestas ou inventar pesos.

Antes de implementar o cenário, apresentar a lista completa de arestas transcritas e validar a topologia conforme a imagem.

Algoritmos:

**Dijkstra**

- Calcular caminhos mínimos entre os nós.
- Permitir selecionar origem e destino.
- Visualizar o processo e destacar o caminho encontrado.

**Circuito completo usando Dijkstra + heurística**

Como Dijkstra isolado não resolve o TSP, utilizar a seguinte estratégia:

1. Construir o grafo original ponderado.
2. Executar Dijkstra para calcular caminhos mínimos entre os nós relevantes.
3. Formar uma matriz de distâncias mínimas.
4. Construir uma rota inicial utilizando a heurística do vizinho mais próximo.
5. Aplicar 2-opt para tentar melhorar a solução.
6. Expandir cada trecho da rota para seus respectivos caminhos no grafo original.
7. Validar que os 18 nós foram visitados pelo menos uma vez e que o percurso retorna à origem.
8. Somar corretamente os pesos de todas as arestas efetivamente percorridas.

Apresentar essa solução como **heurística, sem garantia de ótimo global**.

Não executar força bruta no modo de 18 nós.

Permitir acompanhar o processo visualmente.

## 4. Ambiente 3D e direção artística

A aparência deve seguir o estilo low-poly/cartoon dos assets Kenney e os mockups fornecidos.

O foco principal deve ser o cenário do jogo, com o mapa ocupando a maior parte da tela.

Criar um ambiente urbano com:

- Ruas conectando os nós conforme a estrutura dos grafos.
- Cruzamentos representando os pontos de visita.
- Casas, prédios, lojas e vegetação posicionados ao redor.
- Calçadas, árvores e elementos de decoração urbana.
- Iluminação suave, sombras e cores vibrantes.
- Um carro de entregas claramente identificável.

A cidade deve ser visualmente agradável, mas não pode esconder o significado do grafo.

**Regra crítica:** as ruas decorativas não podem gerar conexões válidas adicionais entre os nós. Somente as arestas do grafo original podem ser utilizadas pelo algoritmo.

Quando duas conexões se cruzarem visualmente sem compartilhar um nó, o cruzamento não deverá criar uma nova conexão lógica.

Os pesos do grafo são custos lógicos e não precisam corresponder à distância geométrica exata das ruas.

## 5. Câmera isométrica

Configurar a câmera com projeção ortográfica e orientação isométrica aproximada:

- Rotação horizontal em torno de 45 graus.
- Elevação aproximada de 35 graus.
- Enquadramento centralizado no mapa ativo.
- Zoom adaptável ao tamanho do cenário.

Controles:

- Scroll do mouse: zoom.
- Botão direito arrastado: movimentar a câmera.
- Rotação opcional com tecla modificadora.
- Botão para centralizar o cenário.
- Limites para evitar zoom excessivo ou perda do mapa.

O cenário de 18 nós deve se ajustar automaticamente para que todos os nós fiquem acessíveis.

## 6. Veículo e animação

Utilizar um veículo 3D da pasta `assets/`.

O carro deverá:

- Iniciar no nó de origem selecionado.
- Deslocar-se suavemente pelas ruas válidas.
- Orientar sua rotação conforme a direção do movimento.
- Seguir a sequência de nós produzida pelo algoritmo.
- Parar ou sinalizar visualmente a chegada a cada nó.
- Retornar à origem quando estiver executando um circuito TSP.
- Permitir pausa, retomada e reinício.
- Ter velocidade configurável em 1×, 2× e 4×.

A animação precisa ser independente do cálculo dos algoritmos, evitando travamentos do Pygame.

Nos trajetos com Dijkstra, utilizar a sequência completa de nós do caminho mínimo.

## 7. Interface visual e HUD

Desenvolver um HUD moderno, minimalista e cartunesco, seguindo os mockups.

Manter os elementos compactos e próximos às bordas, deixando o centro livre para o mapa.

**Painel esquerdo — Controles**

- Alternar entre mapa de 5 e 18 nós.
- Selecionar o algoritmo.
- Selecionar origem e destino quando aplicável.
- Exibir uma legenda das cores.
- Acessar configurações por um botão que abre uma janela de diálogo.

**Painel direito — Resultados**

- Quantidade de nós.
- Algoritmo selecionado.
- Custo total ou custo acumulado.
- Lista ou sequência da rota.
- Quantidade de nós visitados.
- Estado da execução.
- Distância percorrida e tempo de processamento, quando disponíveis.

**Barra inferior — Simulação**

- Iniciar.
- Pausar ou continuar.
- Reiniciar.
- Alterar velocidade.
- Acompanhar o progresso.

Destacar os elementos do grafo com uma linguagem visual consistente:

- Azul: nós e pontos de interesse.
- Amarelo: rota calculada ou selecionada.
- Verde: nós visitados.
- Cinza: ruas e conexões não selecionadas.
- Vermelho: estados de erro ou conexões inválidas.

As etiquetas de números e pesos devem ser legíveis, usando recursos como labels 2D projetados sobre o mundo 3D.

No mapa de 18 nós, oferecer opções para mostrar ou ocultar pesos e legendas a fim de evitar poluição visual.

## 8. Arquitetura e qualidade

Separar as responsabilidades em módulos compatíveis com a estrutura já existente:

- Grafo e carregamento de cenários.
- Algoritmos de força bruta, Dijkstra e heurísticas.
- Câmera isométrica.
- Renderização de objetos e ruas.
- Veículo e animação.
- HUD e eventos.
- Estado da simulação.

A separação acima é conceitual: reutilize os módulos existentes sempre que possível.

Evitar dependências desnecessárias, alterações extensas sem justificativa e carregamento repetitivo dos mesmos assets.

Garantir desempenho fluido, inclusive no mapa de 18 nós.

## 9. Testes e validação

Implementar testes que confirmem:

- O mapa de 5 nós possui exatamente as arestas especificadas.
- O circuito ótimo do mapa de 5 nós possui custo 15.
- O mapa de 18 nós possui 18 nós e suas arestas foram transcritas corretamente.
- A aresta 9–14 possui peso 1.
- Dijkstra retorna caminhos válidos e suas distâncias corretas.
- Nenhum algoritmo utiliza arestas inexistentes.
- A rota TSP heurística visita todos os nós e retorna à origem.
- O custo total considera as arestas realmente percorridas.
- O carro acompanha a rota calculada.
- Alternar entre mapas não provoca erros.
- O carregamento dos modelos preserva materiais e texturas.

## 10. Plano de execução

Siga a seguinte ordem:

1. Inspecionar o projeto funcional existente e identificar seu sistema de renderização.
2. Inventariar os assets Kenney locais.
3. Implementar e validar os dados dos dois grafos.
4. Implementar os algoritmos com testes automatizados.
5. Construir os cenários tridimensionais reutilizando os assets.
6. Ajustar câmera ortográfica isométrica.
7. Implementar movimentação e animação do veículo.
8. Construir o HUD.
9. Integrar algoritmos, interface e simulação.
10. Executar os testes e verificar o jogo em funcionamento.

## 11. Resultado esperado

Entregar o game 3D funcionando, permitindo alternar entre os dois cenários e visualizar os algoritmos aplicados aos grafos.

O resultado precisa transmitir a aparência de um verdadeiro jogo de entregas e otimização de rotas, sem perder o caráter educativo.

Ao finalizar, informar:

- Arquivos criados ou alterados.
- Assets reutilizados.
- Algoritmos implementados.
- Dependências utilizadas.
- Testes realizados e seus resultados.
- Comando para iniciar o jogo.
- Eventuais limitações pendentes.

**Prioridades finais:** preservar o projeto existente, garantir a correção matemática dos grafos e algoritmos, aproveitar os assets locais, manter câmera isométrica e oferecer uma experiência visual clara e interativa.