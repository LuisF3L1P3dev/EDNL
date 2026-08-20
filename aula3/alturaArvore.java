package aula3;

// Classe utilitaria responsavel apenas por calcular a altura da arvore.
final class alturaArvore {

    private alturaArvore() {
        // Impede a criacao de objetos, pois o metodo e estatico.
    }

    static int calcular(arvoreBinaria.No atual) {
        // Caso-base: uma arvore vazia possui altura -1.
        if (atual == null) {
            return -1;
        }

        // Calcula separadamente a altura de cada subarvore.
        int alturaEsquerda = calcular(atual.esquerda);
        int alturaDireita = calcular(atual.direita);

        // Escolhe o maior caminho e conta a aresta ate ele.
        return 1 + Math.max(alturaEsquerda, alturaDireita);
    }
}
