# Transcrição dos grafos

## Fontes e decisões

- Mapa 5: lista explícita de `tasks.md` (8 arestas).
- O mapa de 18 cidades segue `Captura de tela 2026-11-11 135747.png` e a tabela de `tasks_correcao_sequencia.md`. Os campos `x` e `y` registram os centros de `ref/Mapa Isométrico da Rota Mais Curta.png`. A coluna e a linha da `grade` no mesmo arquivo posicionam os centros na cena 3D.
- A imagem liga **1–13** com peso **37**. O cadastro anterior atribuía esse peso a 1–3.
- Os pesos de 9–10, 10–14, 12–13 e 13–14 são **26**, **30**, **27** e **24**, respectivamente.
- A ligação 9–13 pesa **34** e a ligação 9–14 pesa **1**, conforme o enunciado.
- Os grafos são não direcionados. Sobreposições sem nó não são adjacências.

## Mapa 18 — lista de arestas confirmadas

| Origem | Destino | Peso |
| --- | --- | --- |
| 1 | 2 | 20 |
| 1 | 8 | 29 |
| 1 | 12 | 29 |
| 1 | 13 | 37 |
| 2 | 3 | 25 |
| 2 | 8 | 28 |
| 2 | 12 | 39 |
| 3 | 4 | 25 |
| 3 | 8 | 30 |
| 3 | 13 | 54 |
| 4 | 5 | 39 |
| 4 | 6 | 32 |
| 4 | 7 | 42 |
| 4 | 9 | 23 |
| 4 | 10 | 33 |
| 4 | 14 | 56 |
| 5 | 6 | 12 |
| 5 | 7 | 26 |
| 5 | 10 | 19 |
| 6 | 7 | 17 |
| 6 | 10 | 35 |
| 6 | 11 | 30 |
| 7 | 11 | 38 |
| 8 | 12 | 25 |
| 8 | 13 | 22 |
| 9 | 10 | 26 |
| 9 | 13 | 34 |
| 9 | 14 | 1 |
| 9 | 16 | 43 |
| 10 | 11 | 24 |
| 10 | 14 | 30 |
| 10 | 15 | 19 |
| 11 | 15 | 26 |
| 11 | 18 | 36 |
| 12 | 13 | 27 |
| 12 | 16 | 43 |
| 13 | 14 | 24 |
| 13 | 16 | 19 |
| 14 | 15 | 20 |
| 14 | 16 | 19 |
| 14 | 17 | 17 |
| 15 | 17 | 18 |
| 15 | 18 | 21 |
| 16 | 17 | 26 |
| 17 | 18 | 15 |

Total validado de **18 nós e 45 arestas** em um grafo conectado. O jogo carrega os nós, as conexões e os pesos de [`data/mapa_18.json`](../data/mapa_18.json).

## Mapa 5

| Origem | Destino | Peso |
| --- | --- | --- |
| 1 | 2 | 2 |
| 1 | 4 | 3 |
| 1 | 5 | 6 |
| 2 | 3 | 4 |
| 2 | 4 | 3 |
| 3 | 4 | 7 |
| 3 | 5 | 3 |
| 4 | 5 | 3 |
