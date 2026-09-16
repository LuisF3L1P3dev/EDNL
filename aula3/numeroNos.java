package aula3;

// Classe utilitaria responsavel por contar os nos fisicos da arvore.
final class numeroNos {

    private numeroNos() {
        // Impede a criacao de objetos, pois o metodo e estatico.
    }

    static int contar(arvoreBinaria.No atual) {
        // Caso-base: uma posicao vazia nao possui nenhum no.
        if (atual == null) {
            return 0;
        }

        // Conta separadamente os nos das duas subarvores.
        int nosEsquerda = contar(atual.esquerda);
        int nosDireita = contar(atual.direita);

        // Soma o no atual aos nos encontrados nos dois lados.
        return 1 + nosEsquerda + nosDireita;
    }
}
