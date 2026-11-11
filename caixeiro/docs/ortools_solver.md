# OR-Tools opcional — TSP-031

Instalação: `python -m pip install -r requirements-ortools.txt`. Foi validado
OR-Tools **9.15.6755**, wheel `cp314-cp314-win_amd64`, no Python 3.14.0 deste
projeto. A dependência não é importada ao iniciar a interface. Se ausente, o
registro informa indisponibilidade e os outros solvers continuam funcionando.

O Routing Solver usa um veículo com origem/retorno fixos, primeira solução
`PATH_CHEAPEST_ARC` e `GUIDED_LOCAL_SEARCH` (ou `GREEDY_DESCENT` configurável).
Todo uso recebe orçamento positivo pelo contrato, inclusive por padrão.
O tempo nativo recebe o saldo após preparação/importação. Um `CustomLimit`
monitora cancelamento, tempo e ramificações; snapshots registram incumbentes.
Status, versão, estratégias, escala e limites ficam no resultado.

No modo original, arcos ausentes são **removidos de NextVar**, inclusive o
retorno à origem; nenhum peso artificial torna um arco ausente válido. No
fecho, o resultado é expandido. A validação comum confere cada aresta física.

Custos decimais são convertidos com frações de sua representação decimal e
MMC dos denominadores. Não há arredondamento silencioso: se a escala exceder
int64 seguro, a entrada é recusada. O custo exibido é recalculado nos pesos
originais, na unidade do mapa. Sucesso do Routing Solver recebe garantia de
rota viável **sem certificado de ótimo**. Até status `OPTIMAL` é apenas
registrado; o adaptador não o promove a certificado do problema original.

Validação: dependência ausente simulada, custos fracionários/overflow, ambos
os mapas nos dois modelos, mapa 5 contra Held–Karp, origem arbitrária,
arcos proibidos, timeout sem solução, cancelamento real e cidade única.
A suíte chegou a 122 testes aprovados com a dependência instalada.

Referências oficiais: [TSP](https://developers.google.com/optimization/routing/tsp),
[opções e limites](https://developers.google.com/optimization/routing/routing_options).
