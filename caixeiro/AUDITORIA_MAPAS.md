# Auditoria da transcrição dos dois grafos

## Regras

**Estado dos artefatos:** as referências em `assets/referencias/` foram conferidas contra `docs/ativ/` por SHA-256 (TSP-001). O mapa 5 tem cadastro JSON e testes (TSP-002). O mapa 18 tem 45 conexões e 44 pesos revisados nas figuras do próprio autor; a TSP-004 permanece aberta pela ausência do peso de `9–14` na fonte. Ver [relatório completo](docs/auditoria_mapa_18.md).

Os arquivos PNG anexados pelo professor/usuário são a **fonte de verdade**. A transcrição para JSON não altera pesos, conectividade ou número de nós. Coordenadas normalizadas têm finalidade apenas visual; **não** representam distância.

## Mapa 1 — 5 nós

- **Estado:** conferido a partir da figura recebida.
- **Nós:** `1, 2, 3, 4, 5`.
- **8 arestas:** `1-2:2`, `1-4:3`, `1-5:6`, `2-3:4`, `2-4:3`, `3-4:7`, `3-5:3`, `4-5:3`.
- **Não há aresta direta:** `1-3` nem `2-5`.
- **Verificação:** o ciclo `1-2-3-5-4-1` custa `15`.
- **Cadastro:** `data/mapa_05.json`, com coordenadas normalizadas exclusivamente para desenho e `validado: true`.
- **Validação automatizada:** 6 testes aprovados em `tests/test_mapa_05.py`; incluem todos os pesos, a ausência de `1-3` e `2-5` e o ciclo de referência/inverso. Comando: `python -B -m unittest discover -s tests -v`.

## Mapa 2 — 18 nós

- **Estado:** auditoria parcial, **não aprovado para cálculos** por faltar o peso de `9–14`.
- **Cadastro:** `data/mapa_18.json`, com `validado: false`, coordenadas normalizadas e pendências explícitas. Não usar como instância validada de algoritmos.
- **Bloqueio implementado (TSP-006):** `carregar_mapa()` preserva os nós, arestas e o peso desconhecido para inspeção/desenho; `Grafo.exigir_validado()` e `Grafo.adjacencia()` levantam `MapaNaoValidadoError` citando `9-14`. Não há conversão de `null` em custo numérico nem exclusão silenciosa da ligação.
- **Nós:** inteiros de `1` a `18` (18 no total).
- **Arestas registradas:** 45, sendo 44 com pesos visíveis e uma com `null`.
- **Ponto pendente:** existência de `9-14` confirmada nas figuras originais do autor, mas **não há peso indicado para essa linha**. O rótulo `56` foi confirmado em `4-14`; `43` pertence a `9-16`.
- **Conduta:** não adivinhar, não atribuir média de pesos, não substituir pela distância euclidiana.
- **Demais arestas:** as 44 arestas ponderadas foram cotejadas visualmente com `mapa_18_pardini_pesos.png`; as 45 ligações também foram cotejadas com `mapa_18_pardini_ligacoes.png`. A tabela completa está no relatório.
- **Testes:** 8 testes em `tests/test_mapa_18.py` verificam estrutura, todos os pesos conferidos, o custo ausente, metadados e integridade das fontes. Com os 6 testes do mapa 5, são 14 testes. Comando: `python -B -m unittest discover -s tests -v`.

## Checklist de validação obrigatória

- [x] Obter figuras do autor em maior resolução para verificar as ligações.
- [x] Confirmar que `9–14` é realmente uma aresta.
- [ ] Obter o peso de `9–14`, ausente inclusive na figura original do autor.
- [x] Confirmar se `4–14` tem peso `56`.
- [x] Verificar as 44 arestas ponderadas já listadas em `data/mapa_18.json`.
- [x] Conferir os cruzamentos e as conexões nas duas figuras do autor; 45 ligações identificadas.
- [x] Confirmar representação não direcionada: não há setas nas figuras.
- [x] Criar testes para as 45 arestas e todos os 44 pesos conferidos, preservando o único custo ausente.
- [ ] Somente após aprovação, atualizar `validado` para `true` em `data/mapa_18.json`.
- [ ] Não habilitar solução do TSP por força bruta para 18 nós; usar método adequado à escala.

## Registro de mudanças

| Data | Grafo | Alteração | Evidência |
|---|---|---|---|
| 2026-11-11 | Mapa 5 | Transcrito com 5 nós e 8 pesos | `assets/referencias/mapa_05_original.png` |
| 2026-11-11 | Mapa 18 | 18 nós, 45 ligações provisórias, 1 peso não legível | `assets/referencias/mapa_18_original.png` |
| 2026-11-11 | Mapa 18 | 45 ligações e 44 pesos conferidos; `4–14:56` confirmado; custo de `9–14` ausente também na fonte | Figuras do autor e `docs/auditoria_mapa_18.md` |
