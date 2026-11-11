# Auditoria da transcrição dos dois grafos

## Regras

**Estado dos artefatos:** as referências em `assets/referencias/` foram conferidas contra `docs/ativ/` por SHA-256 (TSP-001). O mapa 5 tem cadastro JSON e testes (TSP-002). O mapa 18 tem cadastro provisório e testes estruturais (TSP-003); sua auditoria integral permanece pendente (TSP-004).

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

- **Estado:** transcrição provisória, **não aprovada**.
- **Cadastro:** `data/mapa_18.json`, com `validado: false`, coordenadas normalizadas e pendências explícitas. Não usar como instância validada de algoritmos.
- **Nós:** inteiros de `1` a `18` (18 no total).
- **Arestas registradas:** 45, sendo 44 com pesos visíveis e uma com `null`.
- **Ponto pendente:** ligação aparente `9-14` existe no desenho, mas **não foi possível ler seu peso**. A anotação `56` mais próxima parece pertencer a `4-14`; esse mapeamento exige conferência com uma versão mais nítida da figura.
- **Conduta:** não adivinhar, não atribuir média de pesos, não substituir pela distância euclidiana.
- **Demais arestas:** ainda precisam de uma auditoria independente por comparação lado a lado com a imagem de alta qualidade; não considerar a transcrição inteira definitiva.
- **Testes do cadastro:** 6 testes em `tests/test_mapa_18.py` verificam IDs, coordenadas, extremos, duplicatas, 44 pesos numéricos e preservação das dúvidas. Não certificam os pesos da figura. Junto dos testes do mapa 5, 12 testes passaram com `python -B -m unittest discover -s tests -v`.

## Checklist de validação obrigatória

- [ ] Obter a figura original do mapa 18 em resolução que permita verificar todas as ligações.
- [ ] Confirmar se `9–14` é realmente uma aresta e identificar seu peso.
- [ ] Confirmar se `4–14` tem peso `56`.
- [ ] Verificar as 44 arestas ponderadas já listadas em `data/mapa_18.json`.
- [ ] Confirmar que não existe qualquer outra aresta que ficou oculta por cruzamentos.
- [ ] Confirmar se o grafo é não direcionado, como as figuras sugerem (não há setas).
- [ ] Criar testes para o número final de arestas e todos os pesos conferidos.
- [ ] Somente após aprovação, atualizar `validado` para `true` em `data/mapa_18.json`.
- [ ] Não habilitar solução do TSP por força bruta para 18 nós; usar método adequado à escala.

## Registro de mudanças

| Data | Grafo | Alteração | Evidência |
|---|---|---|---|
| 2026-11-11 | Mapa 5 | Transcrito com 5 nós e 8 pesos | `assets/referencias/mapa_05_original.png` |
| 2026-11-11 | Mapa 18 | 18 nós, 45 ligações provisórias, 1 peso não legível | `assets/referencias/mapa_18_original.png` |
