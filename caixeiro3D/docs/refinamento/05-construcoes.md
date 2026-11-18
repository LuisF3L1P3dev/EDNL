# TASK 05 — cidades dos nós

Cada `NoVisual` agora gera uma construção persistente na `Cena3D`. A cena usa
o `kit`, `nome`, `tamanho` e lote definidos em `NoVisual.construcao`; não há
mais escolha aleatória para os pontos do grafo. O endereço padrão fica no
quadrante que aponta para o centro da malha, a `4,5 u` da praça. Isso
distribui telhados e pins pelo mapa e os mantém fora das oito portas
reservadas e dos eixos das ruas.

`Cena3D.construcoes_no` associa o identificador do nó ao edifício instanciado
e `Cena3D.marcadores_no` registra uma âncora acima do seu telhado. O HUD usa
essa âncora para desenhar o disco azul e a haste do número, preservando
`posicoes_tela` para seleção por clique. A etiqueta `ORIGEM` continua ligada
ao identificador selecionado pela aplicação.

O raio de ocupação circunscreve todo o lote, por isso árvores e edifícios
aleatórios não invadem seus cantos. Os testes verificam exatamente 5 ou 18
construções indexadas pelos ids corretos, a correspondência com o asset
registrado, âncora acima do telhado, marcador projetado no viewport, origem
identificada e folga do lote em relação ao eixo das vias.

Ao reservar os lotes voltados ao centro antes do roteamento, a malha canônica
do mapa grande passou de 26 para 18 passagens elevadas. Isso é uma mudança de
apresentação para dar espaço aos edifícios; as 45 arestas, seus pesos e a
adjacência do grafo permanecem inalterados.
