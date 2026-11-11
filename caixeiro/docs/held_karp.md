# Held–Karp com reconstrução — TSP-029

`executar("held_karp", grafo, origem, variante="original")` resolve o TSP por
programação dinâmica de subconjuntos/última cidade, em O(n² 2ⁿ). Também aceita
`fecho`, com preparação Dijkstra e expansão física. O limite didático é 18 nós.

Custos são mantidos por camadas e os predecessores por estado permitem
reconstruir o ciclo. Progresso e snapshots identificam cada camada. Tempo,
estados e memória interrompem cooperativamente a busca, sem certificado.
A memória DP é contabilizada com `sys.getsizeof` dos dicionários, chaves,
custos e predecessores; o pico é registrado em bytes. A contagem conservadora
repete objetos compartilhados, inclui a camada anterior durante a construção
da próxima e pode exceder o limite por uma inserção antes de interromper.
Não é a memória total do processo/UI.

Testes aleatórios determinísticos comparam os dois modelos à força bruta;
o mapa 18 original retorna ciclo de custo **391**, com predecessores e memória
medida. O verificador independente de custo em `scripts/validar_mapa_18.py`
continua separado para auditoria. Seu resultado não é presumido para o fecho.
