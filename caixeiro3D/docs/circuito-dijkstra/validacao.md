# Circuito completo com Dijkstra

Selecione **Circuito completo** ou pressione `H`, escolha um ponto de origem e use **Iniciar entrega**. O painel mostra as entregas programadas e o percurso físico, incluindo as passagens intermediárias. Em **Caminho entre dois pontos**, escolher o mesmo ponto como origem e destino produz custo zero e mantém a van nesse ponto.

Dijkstra calcula os caminhos entre as paradas. A heurística usa vizinho mais próximo e 2-opt para escolher a sequência, depois expande cada trecho pelas ruas do grafo. Nos mapas do jogo, a origem fica reservada para a chegada final. A contagem de entregas usa as paradas programadas, incluindo a origem na partida. O retorno encerra a viagem.

| Origem na região | Entregas | Custo | Destino final |
| --- | ---: | ---: | --- |
| 01 | 18 | 388 | Ponto 01 |
| 14 | 18 | 398 | Ponto 14 |

Com origem no ponto 1, a rota física usa 19 trechos. O ponto 14 é entregue na primeira visita. A passagem 9 → 14 → 16 usa ruas do mapa e continua a viagem para o ponto 16. Com origem no próprio ponto 14, a van só volta a ele depois de passar pelas outras 17 cidades.

## Evidências

[Vídeo da van da partida à chegada, a 4×](van-circuito-heuristico-18.mp4) · [Captura da viagem em andamento](em-viagem.png) · [Painel final com custo 388 e 18 entregas](chegada.png)

O teste de integração com OpenGL seguiu o trajeto quadro a quadro nas resoluções 1440 × 960 e 1100 × 760. Conferiu pausa, retomada, reinício, orientação da van, posição sobre a via e retorno físico à origem. A suíte passou com 121 testes. Os testes do algoritmo verificaram as 18 origens, a expansão de cada trecho, os pesos usados na soma e a chegada à origem após as entregas.
