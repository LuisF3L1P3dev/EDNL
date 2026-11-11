# TSP-020 — Busca segura até 18 nós

Foi implementado `tsp_branch_bound()` em `busca_limitada.py`, acessível pelo botão **B Busca limitada**. Resolve o TSP Hamiltoniano sobre as ligações existentes. Dijkstra A→B continua disponível em qualquer mapa validado, independentemente do limite didático de 9 nós dos enumeradores.

## Escolha e limites

Branch-and-bound foi escolhido por aproveitar a malha esparsa sem instalar um solver externo. Ordena vizinhos por custo e usa limite inferior admissível: árvore geradora mínima dos vértices restantes mais as ligações mínimas das duas pontas do percurso. Uma conclusão necessariamente contém essas conexões e uma árvore entre os restantes; portanto essa poda não descarta uma solução melhor.

Orçamento padrão: **2 segundos ou 200 mil estados**, o que ocorrer primeiro. Cache de árvores limitado a 8192 subconjuntos; profundidade máxima de 18 cidades. Verifica o orçamento a cada expansão; há pequeno custo adicional para terminar a expansão em curso. Não há garantia polinomial: em instâncias difíceis o algoritmo pode terminar sem achar uma rota, e isso não prova inexistência.

O resultado informa explicitamente:

| Estado | Interpretação |
|---|---|
| `otimo_comprovado` | Busca esgotada/podada com solução; ótimo provado |
| `sem_ciclo_comprovado` | Busca esgotada sem ciclo Hamiltoniano |
| `melhor_conhecida` | Limite atingido com rota viável; ótimo não provado |
| `limite_sem_solucao` | Limite atingido sem rota encontrada; não prova inexistência |

Os estados expandidos não são permutações completas; a interface os identifica separadamente. O solver roda no worker e não bloqueia o loop Pygame.

## Validação executada e limitação real

Os testes comparam o resultado ao enumerador exato em todas as origens do mapa 5. Uma instância **sintética** de 18 nós em anel é resolvida com custo 18 e prova de ótimo dentro do orçamento. Também são testados cortes com/sem solução e ausência comprovada de ciclo.

**A TSP-020 continua parcialmente pendente quanto ao mapa real de 18 nós.** Não é possível medir sua solução sem o custo de 9–14. O usuário confirmou que essa ligação não tem peso informado. Ela permanece com `null`; não foi removida, tratada como zero ou completada por distância visual. O solver recusa esse mapa antes de pesquisar. Os resultados sintéticos não são apresentados como resultados do mapa da aula.

Quando houver definição acadêmica do custo e a TSP-004 for concluída, executar `tsp_branch_bound(carregar_mapa('data/mapa_18.json'), 1)` e registrar custo, tempo, estados e classificação antes de fechar o aceite da TSP-020. Força bruta ingênua permanece limitada a 9 nós.
