Algoritmo de Dijkstra 

# Caminhos mínimos em Grafos 

- Considere um grafo orientado ponderado _G_ = ( _V_ , _E_ ) em que cada aresta possui um rótulo não negativo associado que define o custo da aresta, e um dos vértices é especificado como _origem_ . 

- Nosso problema é determinar quais são os caminhos mais curtos do vértice origem para cada um dos demais vértices em _V_ e os seus custos. 

- O caminho **_mais curto_** ou **_mínimo_** é definido pelo o caminho cuja soma dos custos dos vértices encontrados no caminho é mínimo. 

Slide: Gustavo E.A.P.A. Batista - http://www.lcad.icmc.usp.br/~jbatista/sce183/mat/Didatica.pdf 

**Grafo direcionado** – (arestas com ‘setas’) ( **digrafo** ) **Grafo ponderado** – grafos com pesos (arestas  com ‘números’) 



<!-- Start of picture text -->
0<br>(Q) = erie’<br>re,<br>7 ——_—$—<br><!-- End of picture text -->

https://www.youtube.com/watch?v=8Ls1RqHCOPw 

# Algortimo de Dijkstra 

> • O algoritmo  de **Dijkstra** permite encontrar o menor caminho entre um nó origem (ex. **A** ) e todos os outros vértices do grafo 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Dijkstra 

- Inicia em A, e verifica as saídas de A 

   - De A podemos ir para 

      - B 

      - D 

      - G 

   - Estabelecemos o custo olhando o peso das 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Dijkstra 

- Custos 

   - De A podemos ir para 

      - B = 20 

      - D = 80 

      - G = 90 

   - Outros nós: 

      - Custo infinito (não é possível acessar) 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->



<!-- Start of picture text -->
0<br>® = ee<br>Dijkstra Soe<br>ac| Be<br>de B C D E F G H<br>| | | | |<br>Fe; 30 =<br>A 20  inf 80  inf inf 90  inf<br>de: A de: A de: A<br><!-- End of picture text -->

# Qual o menor custo? 

|de<br>~~Fe~~|B<br>~~;~~<br>||C<br>|D<br>|<br>||E<br>|F<br>||G<br>~~|~~|H|
|---|---|---|---|---|---|---|---|
|A<br>|20<br>|inf|80|inf|inf|90|inf|
||de: A||de: A|||de: A||





<!-- Start of picture text -->
0<br>® = ee<br>Soe<br>ac| Be<br>30 =<br><!-- End of picture text -->



# Qual o menor custo? 

|de<br>|B<br><br>|C<br>|D<br>|E<br>|F<br>|G<br>|H<br><br><br>|
|---|---|---|---|---|---|---|---|
|A|20<br>|inf|80|inf|inf|90|inf<br>|
||de: A<br>||de: A|||de: A||





Qual o menor custo? 2. e*( Pp de B C D E F G H ~~<u><mark>a</mark></u>~~ A 20 inf 80 inf inf 90 inf de: A de: A de: A ~~<u><mark>a</mark></u>~~ = Já sabemos então que o menor caminho entre A e B é de custo 20, e é formado pelo seguinte caminho: A,B 





- Como já sabemos que o menor caminho saindo de A é ir para B, vamos no próximo passo analisar o menor caminho entre B e os outros nós da rede. 

# Dijkstra 

- Inicia em B, e verifica as saídas de B 

   - De B podemos ir para 

      - F 

   - Estabelecemos o custo olhando o peso das arestas 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Dijkstra 

- Custos 

   - De B podemos ir para 

      - F = 10 

   - Outros nós: 

      - Custo infinito (não é possível acessar) 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Dijkstra 

- Custos 

   - De B podemos ir para 

      - F = 10 

   - O custo para chegar em F a partir de A era infinito. Agora podemos chegar em F por meio de B 

   - O custo para chegar em F é então somado ao custo para chegar em B 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Dijkstra 

|de<br>|B<br>|C<br>|D<br>|E<br>|F<br>|G<br>|H<br>|
|---|---|---|---|---|---|---|---|
|A<br>|20<br>de: A<br><br>||inf<br>|80<br>de: A<br>|inf<br>|inf<br>|90<br>de:<br>A<br>|inf<br>|
|B|||||20+10<br>de: B|||





<!-- Start of picture text -->
(@) = ee<br>As0<br>38<br>—_ —O—_—<br><!-- End of picture text -->



Dijkstra de B C D E F G H ~~<u><mark>TT</mark></u>~~ A 20 inf 80 inf inf 90 inf de: A de: A de: A ~~<u><mark>a</mark></u>~~ B 30 de: B 



<!-- Start of picture text -->
(@) = ee<br>90<br>38<br>SS<br><!-- End of picture text -->





- E o custo dos outros nós não acessíveis por B? 

   - Nada muda, copiamos então o custo anterior 

   - Exemplo: 

      - Custo para ir de A até E: inf – mantém infinito 

      - Custo para ir de A até G: 90 – mantém 90 

# Qual o menor caminho? 

|de<br>|B<br>|C<br>|D<br>|E<br>|F<br>|G<br>|H<br>|
|---|---|---|---|---|---|---|---|
|A<br>|20<br>de: A<br><br>~~a~~|inf<br>|80<br>de: A<br>|inf<br>|inf<br>|90<br>de: A<br>|inf<br>|
|B||inf|80|inf|30|90|inf|
||||de: A||de: B|de: A||





<!-- Start of picture text -->
0<br>(@) = epi"<br>Soe<br>38<br>—<br><!-- End of picture text -->



> Dijkstra Soe de B C D E F G H ~~<mark>Ree</mark>~~ 3 38 A 20 inf 80 inf inf 90 inf 2G de: A de: A de: A ~~<u><mark>a</mark></u>~~ 3o B inf 80 inf 30 90 inf de: A de: B de: A Já sabemos então que o menor caminho entre A e F é de custo 30, e é formado pelo seguinte caminho: A,B,F 



# Dijkstra 

- Inicia em F, e verifica as saídas de F 

   - De F podemos ir para 

      - C 

      - D 

   - Estabelecemos o custo olhando o peso das arestas 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Dijkstra 

- Inicia em F, e verifica as saídas de F 

   - De F podemos ir para 

      - C = 10 

      - D = 40 

   - Outros nós: 

      - Custo infinito (não é possível acessar) 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Dijkstra 

- Custos 

   - De F podemos ir para 

      - C = 10 

   - O custo para chegar em C a partir de A era infinito. Agora podemos chegar em C por meio de F 

   - O custo para chegar em C é então somado ao custo para chegar em F 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Qual o menor caminho? 

|de|B|C|D|E|F|G|H|
|---|---|---|---|---|---|---|---|
|A|20<br>de: A<br>~~=~~|inf<br>|80<br>de: A|inf|inf|90<br>de: A|inf|
|B||inf<br>|80|inf|30|90|inf|
||||de: A||de: B|de: A||
|F||30+10<br>de: F||||||





<!-- Start of picture text -->
® = epi"<br>90<br>eae<br><!-- End of picture text -->



|Qu<br>de<br>|al o<br>B<br><br>|m<br>C<br>|enor<br>D<br>|ca<br>E<br>|min<br>F<br>|ho<br>G<br>|?<br>H<br><br><br>|
|---|---|---|---|---|---|---|---|
|A<br>|20<br>de: A<br><br>~~SS~~|inf<br>|80 de:<br>A<br>|inf<br>|inf<br>|90<br>de: A<br>|inf<br><br>=|
|B||inf|80 de:<br>A|inf|30<br>de: B|90<br>de: A|inf|
|F||40<br>de: F||||||





# Dijkstra 

- Custos 

   - De F podemos ir para 

      - D = 40 

   - O custo para chegar em D a partir de A era **80** . Agora podemos chegar em D por meio de F 

   - O custo para chegar em D é então somado ao custo para chegar em F 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

|Qu<br>de<br>|al o<br>B<br><br>|m<br>C<br>|enor<br>D<br>|ca<br>E<br>|min<br>F<br>|ho<br>G<br>|?<br>H<br><br><br>|
|---|---|---|---|---|---|---|---|
|A<br>|20<br>de: A<br><br>~~SS~~|inf<br>|80 de:<br>A<br>|inf<br>|inf<br>|90<br>de: A<br>|inf<br><br>=|
|B||inf|80 de:<br>A|inf|30<br>de: B|90<br>de: A|inf<br>|
|F||40<br>de: F|30+40<br>de: F|||||





|Qu<br>de<br>A<br>|al o<br>B<br>20<br>de: A<br><br>~~SS~~|m<br>C<br>inf<br>|eno<br>D<br>80<br>de: A<br>|r ca<br>E<br>inf<br>|min<br>F<br>inf<br>|ho<br>G<br>90<br>de: A<br>|?<br>H<br>inf<br> <br><br><br> «| ))<br>= @ ™|
|---|---|---|---|---|---|---|---|
|B||inf|80<br>de: A|inf|30<br>de: B|90<br>de: A|inf|
|F||40<br>de: F|70<br>de: F|||||







- Antes, para sair de A e chegar em D o custo era 80 

- Agora, para sair de A e chegar em D, via F, o custo é 70. Então devemos manter este como sendo o menor caminho entre A e D 

- Não há mudanças nos outros caminhos de A 

Copiando os valores de B C D E F G H A 20 inf 80 inf inf 90 inf ~~<u>|</u>~~ de: A de: A de: A ~~<u><mark>a</mark></u>~~ B inf 80 inf 30 90 inf de: A de: B de: A F 40 70 inf 90 inf de: F de: F de: A 



<!-- Start of picture text -->
(@) = epi"<br>94<br>|)<br>30 ™<br>en<br><!-- End of picture text -->



Qual o menor caminho? de B C D E F G H A 20 inf 80 inf inf 90 inf ~~<u>|</u>~~ de: A de: A de: A ~~<u><mark>a</mark></u>~~ B inf 80 inf 30 90 inf de: A de: B de: A F 40 70 inf 90 inf de: F de: F de: A 



<!-- Start of picture text -->
(@) = epi"<br>IS4<br>|)<br>30 ™<br>en<br><!-- End of picture text -->



Qual o menor caminho? de B C D E F G H A 20 inf 80 inf inf 90 inf ~~<u>|</u>~~ 6 de: A de: A de: A ~~<u><mark>=</mark></u>~~ eae3 20 B inf 80 inf 30 90 inf de: A de: B de: A F 40 70 inf 90 inf de: F de: F de: A ~~Já sabemos então que o menor caminho entr~~ e A e C é de <u>custo 40, e é formado pelo seguinte caminho: A,B,F,C</u> 



# Dijkstra 

- Inicia em C, e verifica as saídas de C 

   - De C podemos ir para 

      - H 

      - D 

      - F 

   - Estabelecemos o custo olhando o peso das 



<!-- Start of picture text -->
4,<br>(Q) = epee<br>re,<br>oP<br>FF<br><!-- End of picture text -->

# Dijkstra 

- Custos 

   - De C podemos ir para 

      - H = 20 

      - • D = 10 • F = 50 



<!-- Start of picture text -->
0<br>(Q) = erie’<br>Se<br>So<br><!-- End of picture text -->

# Dijkstra 

- Custos 

   - De C podemos ir para 

      - H = 20 

   - O custo para chegar em H a partir de A era infinito. Agora podemos chegar em H por meio de C 

   - O custo para chegar em H é então somado ao custo para chegar em C 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Qual o menor caminho? 

|de|B|C|D|E|F|G|H|
|---|---|---|---|---|---|---|---|
|A|20<br>de: A|inf|80 de:<br>A|inf|inf<br>|90<br>de:<br>A<br>|inf|
|B||inf|80 de:<br>A|inf|30<br>de: B<br>~~'~~|90<br>de:<br>A<br>|inf|
|F||40<br>de: F|70 de:<br>F|inf||90<br>de:<br>A|inf|
|C|||||||40+20<br>de:C|





<!-- Start of picture text -->
= Dijkstex'<br>® Gee<br>mc)<br>o*( 6<br><!-- End of picture text -->



# Qual o menor caminho? 

|de|B|C|D|E|F|G|H|
|---|---|---|---|---|---|---|---|
|A|20<br>de: A|inf|80 de:<br>A|inf|inf<br>|90<br>de:<br>A<br>|inf|
|B||inf|80 de:<br>A|inf|30<br>de: B<br>~~|~~|90<br>de:<br>A<br>|inf|
|F||40<br>de: F|70 de:<br>F|inf||90<br>de:<br>A|inf|
|C|||||||60<br>de:C|





<!-- Start of picture text -->
= Dijkstex'<br>Qe<br>oc)<br>oP<br><!-- End of picture text -->



# Dijkstra 

- Custos 

   - De C podemos ir para 

      - H = 20 

      - D = 10 

      - F = 50 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Dijkstra 

- Custos 

   - De C podemos ir para 

      - D = 10 

   - O custo para chegar em D a partir de A era **70** . Agora podemos chegar em D por meio de C 

   - O custo para chegar em D é então somado ao custo para chegar em C 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Qual o menor caminho? 

|de|B<br>|C|D|E|F|G|H|
|---|---|---|---|---|---|---|---|
|A|20<br>de: A<br>~~a~~|inf|80 de:<br>A|inf|inf<br>|90<br>de:<br>A|inf|
|B||inf|80 de:<br>A|inf|30<br>de: B<br>~~a~~|90<br>de:<br>A|inf|
|F||40<br>de: F|70 de:<br>F|inf||90<br>de:<br>A|inf|
|C|||||||60<br>de:C|





<!-- Start of picture text -->
a Dijkstex’<br>Qe<br>mc)<br>oP<br><!-- End of picture text -->



# Qual o menor caminho? 

|de|B<br>|C|D|E|F|G|H|
|---|---|---|---|---|---|---|---|
|A|20<br>de: A<br>~~a~~|inf|80 de:<br>A|inf|inf<br>|90<br>de:<br>A|inf|
|B||inf|80 de:<br>A|inf|30<br>de: B<br>~~a~~|90<br>de:<br>A|inf|
|F||40<br>de: F|70 de:<br>F|inf||90<br>de:<br>A|inf|
|C|||40+10<br>de: C||||60<br>de:C|





<!-- Start of picture text -->
a Dijkstex’<br>Qe<br>mc)<br>oP<br><!-- End of picture text -->



|Q<br>de<br>|ual<br>B<br>|o m<br>C<br>~~e~~|eno<br>D<br>|r ca<br>E<br>~~e~~|min<br>F<br>|ho<br>G<br>|?<br>H<br>a<br>Dijkste<br>|
|---|---|---|---|---|---|---|---|
|A<br>B<br>|20<br>de: A<br>|inf<br>inf<br>|80<br>de: A<br>80<br>de: A<br>|inf<br>inf<br>|inf<br>30<br>de: B<br> <br>~~|~~|90<br>de:<br>A<br>90<br>de:<br>A<br> <br>|inf<br>inf<br><br><br>~~e~~ite<br>ops<br>clo|
|F||40<br>de: F|70<br>de: F|inf||90<br>de:<br>A|inf<br>|
|C|||50<br>de: C||||60<br>de:C|





# Dijkstra 

- Custos 

   - De C podemos ir para 

      - H = 20 

      - D = 10 

      - F = 50 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Dijkstra 

- Custos 

   - De C podemos ir para 

      - F = 50 

   - O custo para chegar em F a partir de A era **30** . Agora podemos chegar em F por meio de C 

   - O custo para chegar em F é então somado ao custo para chegar em C 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Qual o menor caminho? 

|de|B<br>|C|D|E|F|G|H|
|---|---|---|---|---|---|---|---|
|A|20<br>|inf|80|inf|inf|90 de:|inf|
||de: A<br>||de: A|||A<br>||
|B||inf|80<br>de: A|inf|30 de:<br>B<br>~~i~~|90 de:<br>A<br>|inf|
|F||40|70|inf||90 de:|inf|
|||de: F|de: F|||A||
|C|||50|inf|40+50|90 de:|60|
||||de: C||de: C|A|de:C|





<!-- Start of picture text -->
= Dijkstex'<br>® Gee<br>mc)<br>by<br>——<br><!-- End of picture text -->



# Qual o menor caminho? 

|de|B<br>|C<br>|D|E|F|G|H<br>|
|---|---|---|---|---|---|---|---|
|A|20<br>de: A<br>~~i~~|inf<br>|80<br>de: A|inf|inf<br>|90 de:<br>A<br>|inf<br>L<br>|
|B||inf<br>|80<br>de: A|inf|30 de:<br>B<br>~~i~~|90 de:<br>A<br>|inf<br> <br>S|
|F||40<br>de: F|70<br>de: F|inf||90 de:<br>A|inf|
|C|||50<br>de: C|inf|~~90 de:~~<br>~~C~~|90 de:<br>A|60<br>de:C|
|||**~~Com~~**<br>**tín**|**~~certeza~~**<br>**hamos d**|**~~o cust~~**<br>**eterm**|**~~o vindo d~~**<br>**inado o**|**~~e C será~~**<br>**menor ca**|**~~maior,  p~~ois já**<br>**minho até F**|





**~~Na  verdade, F nem seria verificado por já te~~ mos calculado o caminho mínimo** 

# Qual o menor caminho? 

|de|B<br>|C|D|E<br>F|G|H<br>|
|---|---|---|---|---|---|---|
|A|20<br>de: A<br>~~—~~|inf|80<br>de: A|inf<br>inf<br>|90 de:<br>A|inf<br>b<br>|
|B||inf|80<br>de: A|inf<br>30<br>de: B<br>~~a~~|90 de:<br>A|inf<br><br>i|
|F||40<br>de: F|70<br>de: F|inf|90 de:<br>A|inf|
|C|||50<br>de: C|inf|90 de:<br>A|60<br>de:C|
|||Já sa<br>~~cust~~|bemos e<br>~~o 50, e é~~|ntão que o menor<br>~~formado pelo se~~|caminho<br>~~guinte ca~~|entre A e D é de<br>~~minho: A,B~~,F,C,D|



# Dijkstra 

- Inicia em D, e verifica as saídas de D 

   - De D podemos ir para 

      - G 

      - C já foi determinado o menor caminho 

   - Estabelecemos o custo olhando o peso das arestas 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Qual o menor caminho? 

|de|B<br>|C<br>|D|E|F|G|H|
|---|---|---|---|---|---|---|---|
|A|20<br>de: A<br>~~—~~|inf<br>|80<br>de: A|inf|inf<br>|90 de:<br>A<br>|inf|
|B||inf<br>|80<br>de: A|inf|30<br>de: B<br>~~a~~|90 de:<br>A<br>|inf|
|F||40<br>de: F|70<br>de: F|inf||90 de:<br>A|inf|
|C|||50<br>de: C|inf||90 de:<br>A|60<br>de:C|
|D||||||50+20<br>de: D||





<!-- Start of picture text -->
= Dijkstex'<br>Qe<br>20)<br>eis<br>Sa<br><!-- End of picture text -->



# Qual o menor caminho? 

|de|B<br>|C|D|E|F|G|H|
|---|---|---|---|---|---|---|---|
|A|20<br>de: A<br>~~—~~|inf|80<br>de: A|inf|inf|90<br>de: A|inf|
|B||inf|80<br>de: A|inf|30<br>de: B<br>~~a~~|90<br>de: A<br>|inf|
|F||40<br>de: F|70<br>de: F|inf||90<br>de: A|inf|
|C|||50<br>de: C|inf||90<br>de: A|60<br>de: C|
|D||||inf||70<br>de: D|60<br>de: C|





<!-- Start of picture text -->
= Dijkstex'<br>® Gee<br>mc)<br>by<br>—<br><!-- End of picture text -->



# Qual o menor caminho? 

|de|B<br>|C|D|E|F|G|H<br>|
|---|---|---|---|---|---|---|---|
|A|20<br>de: A<br>~~a~~|inf|80<br>de: A|inf|inf<br>|90<br>de:<br>|A<br>inf<br>b<br>|
|B||inf|80<br>de: A|inf|30<br>de: B<br>~~a~~|90<br>de:<br>|A<br>inf<br> <br>—|
|F||40<br>de: F|70<br>de: F|inf||90<br>de:|A<br>inf|
|C|||50<br>de: C|inf||90<br>de:|A<br>60<br>de: C|
|D||||inf||70<br>de:|D<br>60<br>de: C|
|||~~Já sa~~<br>cust|~~bemos e~~<br>o 60, e é|~~ntão que~~<br>formado|~~o menor~~<br>pelo se|~~cam~~<br>guint|~~inho entre A~~e H é de<br>e caminho: A,B,F,C,H|



# Dijkstra 

- Inicia em H, e verifica as saídas de H – De H não podemos ir para nenhum nó. 

   - Copia a tabela 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Qual o menor caminho? 

|de|B<br>|C|D|E|F|G|H|
|---|---|---|---|---|---|---|---|
|A|20<br>de: A<br>~~—~~|inf|80<br>de: A|inf|inf|90<br>de: A|inf|
|B||inf|80<br>de: A|inf|30<br>de: B<br>~~a~~|90<br>de: A<br>|inf|
|F||40<br>de: F|70<br>de: F|inf||90<br>de: A|inf|
|C|||50<br>de: C|inf||90<br>de: A|60<br>de: C|
|D||||inf||70<br>de: D|60<br>de: C|
|H||||inf||70<br>de: D||





<!-- Start of picture text -->
= Dijkstex'<br>® Gee<br>mc)<br>by<br>—<br><!-- End of picture text -->



# Qual o menor caminho? 

|de|B<br>|C|D|E|F|G|H<br>|
|---|---|---|---|---|---|---|---|
|A|20<br>de: A<br>~~a~~|inf|80<br>de: A|inf|inf<br>|90<br>de:|A<br>inf<br>b<br>|
|B||inf|80<br>de: A|inf|30<br>de: B<br>~~a~~|90<br>de:|A<br>inf<br> <br>—|
|F||40<br>de: F|70<br>de: F|inf||90<br>de:|A<br>inf|
|C|||50<br>de: C|inf||90<br>de:|A<br>60<br>de: C|
|D||||inf||70<br>de:|D<br>60<br>de: C|
|H||||inf||70<br>de:|D|
|||Já sa<br>~~cust~~|bemos e<br>~~o 70, e é~~|ntão que<br>~~formado~~|o meno<br>~~pelo seg~~|r cam<br>~~uinte~~|inho entre A e G é de<br>~~caminho: A,~~B,F,C,D,G|



# Dijkstra 

- Inicia em G, e verifica as saídas de G 

   - De G podemos ir para 

      - A 

   - A é a origem 

   - Basta copiar a tabela 



<!-- Start of picture text -->
0<br>(Q) = aie’<br>S78<br> _—_o”(<br><!-- End of picture text -->

# Qual o menor caminho? 

|de|B|C|D|E|F|G|H|
|---|---|---|---|---|---|---|---|
|A|20<br>de: A<br>~~~~~|inf|80<br>de: A|inf|inf<br>|90<br>de:<br>|A<br>inf<br>~~t~~h|
|B||inf<br>|80<br>de: A<br>|inf|30<br>de: B<br>|90<br>de:<br>|A<br>inf<br><br><br>|
|F||40<br>de: F<br>~~a~~|70<br>de: F<br><br>|inf<br>||90<br>de:|A<br>inf<br>i<br>|
|C|||50<br>de: C<br>~~_~~|inf<br>||90<br>de:|A<br>60<br>de: C<br>|
|D||||inf<br>||70<br>de:<br><br>|D<br>60<br>de: C<br>~~_~~<br><br>|
|H||||inf<br>~~L~~||70<br>de:<br><br>|D<br><br>|
|G||||inf<br>||||
||||Não<br>|há cami<br>|nho para<br>|o vér<br><br>|tice E a partir de A<br><br>~~o~~|







<!-- Start of picture text -->
0<br>(8) = erie’<br>O (A) ms<br>Y CH<br>Se<br>|<br>Se—<br><!-- End of picture text -->



<!-- Start of picture text -->
O Algoritmo de Dijkstra<br>Require: G = (V,E), um grafo orientado ponderado<br>Require: C, uma matriz de custos associados aos vértices E<br>Ensure: D um vetor com as custos minimos entre cada vértice<br>em E eo vertice origem 1<br>1: S— {1}<br>2: fori —2tondo<br>3: Di] — C1,i]<br>4: end for<br>5: fori’ —2tondo<br>6: encontre um vertice w « V — S tal que D[w] € minimo<br>77 S—SuU{w}<br>8: forallv<e V—Sdo<br>9: D[v] — min(D[v], D[w] + C[w,v])<br>10: end for<br>11: end for<br><!-- End of picture text -->

Slide: Gustavo E.A.P.A. Batista - http://www.lcad.icmc.usp.br/~jbatista/sce183/mat/Didatica.pdf 



<!-- Start of picture text -->
O Algoritmo de Dijkstra<br>Require: G = (V,£), um grafo orientado pc = ee<br>Require: C, uma matriz de custos associad(®) i<br>Ensure: D um vetor com as custos minimos (c)<br>S— {1} fo CH)<br>1: em Eeo vertice origem 1 (A) E vad<br>2: fori —2tondo ,<br>3:<br>4:5: endDili] for— Cit.i] (Qto (G)Oe=<br>fori —2tondo —_—<br>6: encontre um vertice w « V — S tal que D[w] € minimo<br>77 S—SuU{w}<br>8: forallv<eV—Sdo<br>9: D[v] — min(D[v], D[w] + C[w,v])<br>10: end for<br>11: end for<br><!-- End of picture text -->

Slide: Gustavo E.A.P.A. Batista - http://www.lcad.icmc.usp.br/~jbatista/sce183/mat/Didatica.pdf 

## **<mark>A B C D E F G H inf 20 inf</mark>** **<u><mark>80</mark></u>** **<mark>inf inf</mark>** **<u><mark>90</mark></u>** **<mark>inf</mark>** 

> • Matriz C                Vetor D 



<!-- Start of picture text -->
A B C D E F G H<br>A 20 80 90<br>B 10<br>C 10 50 20<br>D 20<br>E 50 30<br>F 10 40<br>G 20<br>H<br><!-- End of picture text -->

**<mark>A B C D E F G H inf 20 inf</mark>** **<u><mark>80</mark></u>** **<mark>inf</mark>** **<u><mark>30 90</mark></u>** **<mark>inf A B C D E F G H inf 20 40 70 inf 30 90 inf A B C D E F G H inf 20 40 50 inf 30 90 60 A B C D E F G H inf 20 40 50 inf 30 70 60 A B C D E F G H inf 20 40 50 inf 30 70 60 A B C D E F G H inf 20 40 50 inf 30 70 60</mark>** 



<!-- Start of picture text -->
@ Caso for necessario reconstruir 0 caminho mais curto<br>entre o vértice origem e cada vértice, pode-se manter um<br>vetor P de vertices, tal que P[v] contem o vertice<br>imediatamente anterior ao vértice v no caminho mais<br>curto.<br>@ Para isso, devemos realizar uma modificagao no algoritmo<br>anterior.<br><!-- End of picture text -->

Slide: Gustavo E.A.P.A. Batista - http://www.lcad.icmc.usp.br/~jbatista/sce183/mat/Didatica.pdf 

= 

Slide: Gustavo E.A.P.A. Batista - http://www.lcad.icmc.usp.br/~jbatista/sce183/mat/Didatica.pdf 

Uma modificação no algoritmo de Djikstra para determinar o caminho mais curto entre dois vértices 

void Caminho_mais_Curto(TipoGrafo *grafo, int origem, int destino) { 

int i, vert,k, NovaDist, min; int *M, *L, *A, *caminho; 

M = (int *)malloc(grafo->NumVertices*sizeof(int)); 

L = (int *)malloc(grafo->NumVertices*sizeof(int)); A = (int *)malloc(grafo->NumVertices*sizeof(int)); 

caminho = (int *)malloc(grafo->NumVertices*3*sizeof(int));  vetor auxiliar 

// incializando vairiaveis 

for (i=0; i<grafo->NumVertices; i++) { 

M[i] = 0; //  false -- determina se um vertice ja foi visitado A[i] = -1;  // determina o caminho mais curto entre origem e destino L[i] = 300000; //infinito determina o comprimento do caminho mais curto } 

vert = origem; 

L[vert] = 0; 

while (vert != destino && vert != -1) // não terminou ou caminho inexistente { 

for(i=0;i<grafo->NumVertices; i++) // percorre vertices adjacentes de vert if (grafo->Mat[vert][i] != 0 && M[i]==0)   // se aresta existe e ela  não foi visitada { 

NovaDist = L[vert] + grafo->Mat[vert][i]; if (NovaDist < L[i]) { L[i] = NovaDist;   // atualiza menor distancia 

A[i] = vert;   // atualiza caminho } } 

M[vert] = 1;   // toda a lista de adjacentes de vert já foi analisada min = 300000;   //infinito 

vert = -1;  // valor invalido 

for (i=0; i<grafo->NumVertices; i++)  // encontra proximo vertice do caminho if (M[i]==0 && L[i] < min)  //escolhe o vertice  cuja aresta possui o menor peso { 

min = L[i];   // atualiza min 

vert = i;      //atualiza vert } 

} //fim while 

// listar o caminho mais curto entre origem e destino 

if (vert == destino) // encontrou um caminho { printf("caminho mais curto entre %4d e %4d tem comprimento  %4d: ", origem, destino, L[destino] ); caminho[0] = destino; k = 1; while (vert != origem) { caminho[k]= A[vert]; vert = A[vert]; k++; } for (i=k-1; i>=0; i--) printf("%4d", caminho[i]); } else printf("nao exite caminho entre %4 e %4", origem, destino); } 

Considere o grafo: Execute manualmente o algoritmo dado e determine o caminho mais curto entre os vértices 0 e 3. aLal 

## M L A 

|M<br>L<br>A|
|---|



M L A 



<!-- Start of picture text -->
grafo criado<br>® 1 5 98<br>6 08 6 15<br>6064<br>660 6 28<br>1)09<br>81 5 300000<br>“1 i) °] -1<br>1 1 0 9<br>i) 1 ) 16<br>“1 i) 0 1<br>1119<br>91 5) 9<br>1 i) 0 2<br>caminho mais curto entre Oe 3 tem comprimento 9: 6 2 3<br><!-- End of picture text -->

