# TASK 06 — etiquetas e rota ativa

As ruas preservam os assets cinza e os cotovelos/ponte da TASK04. O HUD passou
a escolher a posição de cada peso entre frações da polilinha da própria
aresta, com pequenos deslocamentos de tela. Uma caixa só é aceita dentro do
viewport e fora de todos os pins, etiquetas `ORIGEM`/`DESTINO`, título da cena
e pesos já posicionados. O resultado é determinístico e mantém as 8 ou 45
etiquetas visíveis nos dois mapas.

O preenchimento e borda amarelo/laranja indicam a aresta selecionada. Durante
uma viagem — inclusive em pausa — somente `Viagem.trecho` recebe o destaque.
A cena troca a mesh uma vez quando a van muda de aresta, evitando recriá-la a
cada frame. Quando a viagem termina, HUD e cena voltam uma única vez a exibir
o percurso inteiro calculado.

Os testes verificam que as 8/45 caixas de peso não colidem com pins, título ou
outras caixas; que o estado de destaque do HUD acompanha o trecho atual em
execução, pausa e conclusão; e que `Cena3D.mostrar_trecho` não reconstrói a
mesh quando a aresta não muda.
