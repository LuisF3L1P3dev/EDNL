package aula3;

// Classe utilitaria responsavel por remover numeros da arvore.
final class deletarNo {

    private deletarNo() {
        // Impede a criacao de objetos, pois os metodos sao estaticos.
    }

    static arvoreBinaria.No remover(arvoreBinaria.No atual, int numero) {
        // Caso-base: o numero nao foi encontrado.
        if (atual == null) {
            return null;
        }

        if (numero < atual.valor) {
            // Procura o numero na subarvore esquerda.
            atual.esquerda = remover(atual.esquerda, numero);
        } else if (numero > atual.valor) {
            // Procura o numero na subarvore direita.
            atual.direita = remover(atual.direita, numero);
        } else {
            // Encontramos o numero que deve ser removido.
            if (atual.quantidade > 1) {
                // Ainda existem outras ocorrencias desse valor.
                atual.quantidade--;
                return atual;
            }

            if (atual.esquerda == null) {
                /*
                 * Sem filhos: retorna null.
                 * Somente com filho direito: retorna esse filho.
                 */
                return atual.direita;
            }

            if (atual.direita == null) {
                // O no possui somente o filho esquerdo.
                return atual.esquerda;
            }

            // Com dois filhos, usa o menor no da subarvore direita.
            arvoreBinaria.No sucessor = encontrarMenor(atual.direita);

            // Transfere o valor e todas as ocorrencias do sucessor.
            atual.valor = sucessor.valor;
            atual.quantidade = sucessor.quantidade;

            // Remove fisicamente o sucessor de sua antiga posicao.
            atual.direita = removerMenor(atual.direita);
        }

        return atual;
    }

    private static arvoreBinaria.No encontrarMenor(arvoreBinaria.No atual) {
        // O menor valor fica o mais a esquerda possivel.
        while (atual.esquerda != null) {
            atual = atual.esquerda;
        }

        return atual;
    }

    private static arvoreBinaria.No removerMenor(arvoreBinaria.No atual) {
        // Encontramos o menor no desta subarvore.
        if (atual.esquerda == null) {
            return atual.direita;
        }

        atual.esquerda = removerMenor(atual.esquerda);
        return atual;
    }
}
