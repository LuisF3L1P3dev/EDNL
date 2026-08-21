package aula3;

// Classe utilitaria responsavel por preencher e inserir na arvore.
final class inserirNumero {

    private inserirNumero() {
        // Impede a criacao de objetos, pois os metodos sao estaticos.
    }

    static arvoreBinaria.No preencher(
        arvoreBinaria.No raiz,
        int[] numeros
    ) {
        // Insere cada numero e guarda a raiz atualizada.
        for (int numero : numeros) {
            raiz = inserir(raiz, numero);
        }

        return raiz;
    }

    static arvoreBinaria.No inserir(
        arvoreBinaria.No atual,
        int numero
    ) {
        // Encontrou uma posicao vazia: cria um novo no.
        if (atual == null) {
            return new arvoreBinaria.No(numero);
        }

        if (numero < atual.valor) {
            // Numeros menores pertencem a subarvore esquerda.
            atual.esquerda = inserir(atual.esquerda, numero);
        } else if (numero > atual.valor) {
            // Numeros maiores pertencem a subarvore direita.
            atual.direita = inserir(atual.direita, numero);
        } else {
            // O numero ja existe: aumenta o contador do no.
            atual.quantidade++;
        }

        return atual;
    }
}
