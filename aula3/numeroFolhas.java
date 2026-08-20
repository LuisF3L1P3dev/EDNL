package aula3;

// Classe utilitaria responsavel por contar as folhas da arvore.
final class numeroFolhas {

    private numeroFolhas() {
        // Impede a criacao de objetos, pois o metodo e estatico.
    }

    static int contar(arvoreBinaria.No atual) {
        // Caso-base: uma posicao vazia nao possui folhas.
        if (atual == null) {
            return 0;
        }

        // Um no sem filhos e uma folha.
        if (atual.esquerda == null && atual.direita == null) {
            return 1;
        }

        // Conta separadamente as folhas das duas subarvores.
        int folhasEsquerda = contar(atual.esquerda);
        int folhasDireita = contar(atual.direita);

        return folhasEsquerda + folhasDireita;
    }
}
