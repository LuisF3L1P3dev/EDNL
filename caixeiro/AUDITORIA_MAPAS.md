# Auditoria da transcrição dos dois grafos

## Regras

**Estado dos artefatos:** referências preservadas por SHA-256. Mapa 5 validado; mapa 18 validado com 44 pesos conferidos nas figuras e o peso `9–14 = 1` fornecido explicitamente pelo usuário. A proveniência consta no JSON e no [relatório completo](docs/auditoria_mapa_18.md).

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

- **Estado:** validado com complemento do usuário; TSP-004 concluída.
- **Cadastro:** `data/mapa_18.json`, com `validado: true`, pesos conhecidos e nenhuma pendência.
- **Guardas preservadas:** instâncias não validadas continuam recusadas pelo núcleo, com testes em cópia sintética. O mapa real validado pode ser usado por Dijkstra e branch-and-bound; força bruta mantém o limite de 9 nós.
- **Nós:** inteiros de `1` a `18` (18 no total).
- **Arestas registradas:** 45, todas com peso: 44 valores nas imagens e `9–14:1` informado pelo usuário.
- **Complemento:** a mensagem “o peso da aresta 9 - 14 é 1” define esse custo. A imagem continua sem rótulo nessa ligação. `4–14:56` e `9–16:43` foram preservados.
- **Conduta:** não adivinhar, não atribuir média de pesos, não substituir pela distância euclidiana.
- **Demais arestas:** as 44 arestas ponderadas foram cotejadas visualmente com `mapa_18_pardini_pesos.png`; as 45 ligações também foram cotejadas com `mapa_18_pardini_ligacoes.png`. A tabela completa está no relatório.
- **Testes:** `tests/test_mapa_18.py` cobre todos os 45 pesos e proveniência; os testes do núcleo e de Dijkstra conferem o novo custo em ambos os sentidos. Comando: `python -B -m unittest discover -s tests -v`.

## Checklist de validação obrigatória

- [x] Obter figuras do autor em maior resolução para verificar as ligações.
- [x] Confirmar que `9–14` é realmente uma aresta.
- [x] Obter o peso de `9–14`: 1, definido pelo usuário.
- [x] Confirmar se `4–14` tem peso `56`.
- [x] Verificar as 44 arestas ponderadas já listadas em `data/mapa_18.json`.
- [x] Conferir os cruzamentos e as conexões nas duas figuras do autor; 45 ligações identificadas.
- [x] Confirmar representação não direcionada: não há setas nas figuras.
- [x] Criar testes para as 45 arestas e pesos, incluindo a origem do complemento de 9–14.
- [x] Atualizar `validado` para `true` após completar os dados e testes.
- [x] Manter força bruta limitada a 9 nós e disponibilizar busca com orçamento para 18.

## Registro de mudanças

| Data | Grafo | Alteração | Evidência |
|---|---|---|---|
| 2026-11-11 | Mapa 5 | Transcrito com 5 nós e 8 pesos | `assets/referencias/mapa_05_original.png` |
| 2026-11-11 | Mapa 18 | 18 nós, 45 ligações provisórias, 1 peso não legível | `assets/referencias/mapa_18_original.png` |
| 2026-11-11 | Mapa 18 | 45 ligações e 44 pesos conferidos; `4–14:56` confirmado; custo de `9–14` ausente também na fonte | Figuras do autor e `docs/auditoria_mapa_18.md` |
| Complemento posterior | Mapa 18 | `9–14 = 1`, pendências encerradas e cadastro validado | Mensagem explícita do usuário, registrada em `auditoria.complemento_usuario` |
