# Atividade Prática: Filtro de Firewall com Árvore Binária de Busca (BST)

## 1. O Contexto Real
Um servidor web recebe milhares de requisições por segundo. Cada requisição vem de um endereço IP de 32 bits (representado aqui como um número inteiro para simplificar, por exemplo, `192168001001`). O firewall precisa verificar rapidamente se o IP de origem está na **Lista Negra (Blacklist)** para bloquear a requisição.

Sua missão é implementar um protótipo desse filtro usando uma **Árvore Binária de Busca (BST)** para garantir buscas eficientes $O(\log n)$ em vez de uma busca linear $O(n)$ em vetor.

---

## 2. Requisitos da Estrutura
Você deve construir uma estrutura de dados de Árvore Binária onde cada nó armazena:
* `ip`: chave numérica de ordenação (`long long` ou `unsigned int`).
* `contador_tentativas`: inteiro que registra quantas vezes o IP tentou acessar a rede.
* `ponteiro_esquerdo` e `ponteiro_direito`: referências para os nós filhos.

---

## 3. Funcionalidades a Implementar
1. **`inserir(IP)`**: Adiciona um IP à árvore. Se o IP já existir, apenas incremente o `contador_tentativas`.
2. **`buscar(IP)`**: Retorna se o IP está bloqueado e exibe o número de tentativas registradas.
3. **`relatorio_ordenado()`**: Exibe todos os IPs bloqueados em ordem crescente (*dica: qual percurso em árvore faz isso?*).
4. **`remover(IP)`**: Remove um IP da lista negra quando ele cumprir o tempo de penalidade.