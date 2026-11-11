# TSP-019 — Comparação formal

Medições desta máquina: mediana de 7 execuções, sem histórico no cronômetro. Contadores são coletados em execução separada. Não são um benchmark universal.

## Malha original: problemas distintos

Dijkstra sozinho resolve A→B. O TSP direto exige ciclo Hamiltoniano nas arestas existentes. O TSP no fecho métrico escolhe a ordem de entregas e permite repetir cidades de passagem. Igualdade de custo no mapa 5 não demonstra equivalência dos problemas ou que Dijkstra sozinho resolva TSP.

| Método / problema | Custo | Tempo mediano (ms) | Ordens TSP | Nós finalizados em Dijkstra | Chamadas Dijkstra |
|---|---:|---:|---:|---:|---:|
| dijkstra_A_B | 6 | 0.0204 | 0 | 4 | 1 |
| hamiltoniano_direto | 15 | 0.0468 | 24 | 0 | 0 |
| passeio_no_fecho | 15 | 0.2994 | 24 | 75 | 25 |

Nós finalizados contam retiradas definitivas da fila (somados entre todas as chamadas), não ordens de visitas. Ordens TSP contam permutações examinadas. O tempo do método composto inclui construir o fecho e expandir o percurso.

## Controle para o mesmo TSP

Construímos uma instância de controle completa com os menores custos do mapa 5. Ambos os métodos recebem exatamente esse mesmo grafo métrico. A preparação inicial dessa instância fica fora do tempo para ambos. A segunda abordagem inclui sua própria reconstrução do fecho no cronômetro. Os dados fixos da aula não são alterados; essa instância é somente um controle experimental.

| Método na mesma instância métrica | Custo | Tempo mediano (ms) | Ordens TSP |
|---|---:|---:|---:|
| forca_bruta | 15 | 0.0221 | 24 |
| dijkstra_mais_busca_exata | 15 | 0.2131 | 24 |

No controle métrico, atalhar um trecho não reduz sua distância abaixo do peso direto (desigualdade triangular). Assim os dois métodos resolvem o mesmo TSP em termos de ordem e custo mínimo. Este controle não autoriza tratar os dois problemas da malha original como iguais.

## Contraexemplo verificado nos testes

Triângulo com pesos 1–2=1, 2–3=1 e 1–3=10: o ciclo Hamiltoniano custa 12; o passeio 1–2–3–2–1 custa 4. A estrela 1–2, 1–3, 1–4 não tem ciclo Hamiltoniano, mas tem passeio fechado que visita todos os nós. Esses testes impedem confundir ausência de aresta direta com ausência de caminho.

Reproduzir: `python scripts/comparar_metodos.py`. Dados completos e rotas: [comparacao.json](comparacao.json). A TSP-017 ainda requer inspeção manual nativa; as medições acima são do núcleo, independentes dela. O mapa 18 foi validado com 9–14=1 informado pelo usuário; sua busca limitada e o controle independente estão em [resultados_mapa_18.json](resultados_mapa_18.json). Os enumeradores didáticos continuam limitados a 9 nós.
