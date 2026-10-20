1 O 

## **Estrutura de Dados Não Linear** 



**Aula 06** 

- Problema do Caixeiro viajante 



**Prof. Aluisio Igor Rêgo Fontes** 



# Problema Caixeiro Viajante 



- É um problema que tenta determinar a menor rota para percorrer uma série de cidades, retornando à cidade de origem. Ele é um problema de otimização NP-Completo 

- Inspirado na necessidade dos vendedores em realizar entregas em diversos locais percorrendo o menor caminho possível 



Tipo de grafo 



<!-- Start of picture text -->
oun<br>EB<br>@ B88 INSTITUTORio Grande do Norte FEDERAL | CampusPau dos Ferros<br><!-- End of picture text -->



<!-- Start of picture text -->
Tn<br><!-- End of picture text -->



<!-- Start of picture text -->
i 1<br>aoa - 3 ? : 2<br>. ei : @) (3)<br>4<br>ey Ree Grafo Incompleto<br><!-- End of picture text -->



os BE NocundedoNone | <u>peu dec Feros</u> 





<!-- Start of picture text -->
6<br>@ (v1) vl-v2-v3-v4-vl - custo = 12<br>vl-v2-v4-v3-vl - custo = 11<br>vl-v3-v2-v4-vl - custo =15<br>3 1 vl-v3-v4-v2-vl - custo =11<br>vl-v4-v2-v3-vl - custo =15<br>vl-v4-v3-v2-vl - custo = 12<br>(v3) (2)<br><!-- End of picture text -->

~~reer~~ 

oun EB 88@B INSTITUTORio Grande do Norte FEDERAL | CampusPau dos Ferros 

~~Tn~~ 



<!-- Start of picture text -->
a ;<br>Heaths ts Rome om<br>EueseaDePamsive Vi q ps<br>wh f ae<br>SB yn Sao Paulo oa 3<br>Mans se ; : rs a ia weneeotem<br>{ TPlneems Aner ined<br>cate j > sae ore<br>rsocue —<br>sn ybrog :<br>. crate<br>4 2 oS 4 octane<br>dee tibe Z Se vnene — Guay Mibation<br>satel<br><!-- End of picture text -->





<!-- Start of picture text -->
se<br>@88 INSTITUTO FEDERAL | Campus<br>© Rio Grandedo Norte Pau dos Ferros<br><!-- End of picture text -->





<!-- Start of picture text -->
— PA<br>perl ee SURINAME le<br>‘SSolele ey<br>Ls oo<br>a S *Rranotp Recife<br>Ge MINAS GERAIS<br>5 Campo: Vion<br>G Rio de —<br>LI Neteller Tose<br>ch 3 #4 iS ASo| dancito] Tropicode Capricérnio<br>aw bh sal a Fa<br>He uN<br>a 4 rooney<br><!-- End of picture text -->



Brasil 



<!-- Start of picture text -->
x<br>@ B88 INSTITUTORio Grande do Norte FEDERAL | CampusPau dos Ferros<br><!-- End of picture text -->



<!-- Start of picture text -->
Tn<br><!-- End of picture text -->



<!-- Start of picture text -->
2 A<br>©<br>(3)<br>3 [> 3<br>a Ns<br><!-- End of picture text -->



<!-- Start of picture text -->
25<br>= — 9<br>Q * 33 33 fa \s0\/ ||,*<br>/ \<br>20<br>/ 28 30, 35. » (6) |<br>39 se OC} 26 7 |<br>@ \ 29 34 56 19 6 ©<br>a\ | ~~ e Y 43 ly 1) |<br>@) i. ©- 24 (aX vy ~P \ |<br>8 a @ 1s<br><!-- End of picture text -->



Problema – Força Bruta 

Criar a figura 



<!-- Start of picture text -->
oun<br>an<br>@ B88 INSTITUTORio Grande do Norte FEDERAL | CampusPau dos Ferros<br><!-- End of picture text -->



<!-- Start of picture text -->
i<br><!-- End of picture text -->



<!-- Start of picture text -->
21: # Generating a graph of 3 nodes<br>n=3<br>num_qubits =n **<br>ns = tsp.random_tsp(n, seed=123)<br>print ('distance\n', ins.w)<br>G = nx.Graph()<br>G.add_nodes_from(np.arange(0, ins.dim, 1))<br>colors = ['r! for node in G.nodes()]<br>for i in range(0, ins.dim):<br>for j in range (itl, ins.dim):<br>G.add_edge(i, 3, weighteins.wli,3])<br>pos = {k: v for k, v dm enumerate (ins.coord) }<br>draw_graph(G, colors, pos)<br>distance<br>[{ 0. 48. 91.]<br>(48. 0. 63.)<br>(91. 63. 0.3)<br>\<br>B<br>°<br>ee eee<br><!-- End of picture text -->



