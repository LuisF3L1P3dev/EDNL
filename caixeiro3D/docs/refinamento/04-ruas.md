# TASK 04 — malha de ruas planejada

O layout canônico passou a separar a apresentação urbana da topologia do
grafo. `roteamento3d.py` posiciona os cinco pontos em quatro quadrantes com o
nó 4 no centro e os dezoito pontos em uma grade ampla de quarteirões.

Para cada aresta existente, o roteador reserva duas portas junto às praças dos
nós e encontra uma polilinha cardinal no espaço entre os lotes. A ordem dá
prioridade aos hubs 4 e 14, ambos de grau sete, para que suas portas não sejam
esgotadas pelas ruas periféricas. Arestas não incidentes não ganham adjacência
quando se cruzam: a passagem superior recebe rampas e o asset `road-bridge`.

O mapa de 5 nós tem oito caminhos e não usa ponte. O mapa de 18 nós tem os 45
caminhos correspondentes às arestas originais; seus desvios e níveis pertencem
somente a `ArestaVisual`, que mantém a referência ao objeto `Aresta` original.
Layouts fornecidos explicitamente continuam aceitos pela API anterior e usam
polilinhas ortogonais simples, sem mudar dados matemáticos.

Validação automatizada cobre extremos, identidade das arestas, segmentos
cardinais, nível das rampas, ausência de passagem pelo centro de nó não
incidente e ausência de pontes no mapa pequeno. A cena usa `road-straight`
para ruas/rampas, `road-bend` nos cotovelos, `road-bridge` para tabuleiros
elevados e `bridge-pillar-wide` como apoio.

## Medição e limitação registrada

Em execução fria do roteador com os lotes canônicos do mapa grande, foram
medidos 1,94 s e 26 cruzamentos elevados (191.030 expansões de A*); a
apresentação é armazenada no cache de `criar_mapa_visual`, portanto o acesso
quente não repete a busca. A primeira medição de 23,69 s foi descartada por
concorrer com um processo externo de Python no ambiente. O mapa pequeno gera
8 caminhos, 0 pontes e não executa a busca geral.

O grafo grande contém 45 arestas e hubs de grau 7 (4 e 14), enquanto cada
praça reserva oito portas separadas. O roteador primeiro proíbe cruzamentos e
somente libera uma travessia perpendicular se a rua ficar sem corredor. Ainda
assim, a malha local produz 26 passagens elevadas. Os pares são mantidos como
`PonteVisual(aresta, inferior, centro, ...)`; exemplos representativos são
`4–10 × 5–10`, `10–14 × 10–11`, `9–16 × 3–4`, `4–9 × 1–3`, `6–7 × 4–5` e
`2–12 × 1–3`. Cada uma sobe 1,65 u sobre a rua de base (vão livre de 1,4 u)
e tem 3,6 u de rampa de cada lado. A necessidade geométrica mínima de cada
uma não foi provada: esta é uma limitação do roteador local determinístico,
não dos dados matemáticos do grafo.
