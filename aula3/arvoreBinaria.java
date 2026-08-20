package aula3;

public class arvoreBinaria {

    // Representa cada no da arvore.
    static class No {
        int valor;
        int quantidade;
        No esquerda;
        No direita;

        No(int valor) {
            this.valor = valor;

            // O valor apareceu pela primeira vez.
            this.quantidade = 1;

            // Inicialmente, o no nao possui filhos.
            this.esquerda = null;
            this.direita = null;
        }
    }

    // Primeiro no da arvore.
    private No raiz;

    public void preencher(int[] numeros) {
        // Percorre todos os numeros do vetor.
        for (int numero : numeros) {
            // Insere o numero e atualiza a raiz, se necessario.
            raiz = inserir(raiz, numero);
        }
    }

    private No inserir(No atual, int numero) {
        // Encontramos uma posicao vazia.
        if (atual == null) {
            return new No(numero);
        }

        if (numero < atual.valor) {
            // Numeros menores pertencem a subarvore esquerda.
            atual.esquerda = inserir(atual.esquerda, numero);
        } else if (numero > atual.valor) {
            // Numeros maiores pertencem a subarvore direita.
            atual.direita = inserir(atual.direita, numero);
        } else {
            // O numero ja existe: nao criamos outro no.
            atual.quantidade++;
        }

        // Devolve o no com suas possiveis alteracoes.
        return atual;
    }

    public void mostrarEmOrdem() {
        mostrarEmOrdem(raiz);
    }

    private void mostrarEmOrdem(No atual) {
        if (atual == null) {
            return;
        }

        // Visita os nos na ordem: esquerda, no atual e direita.
        mostrarEmOrdem(atual.esquerda);
        System.out.println(
            atual.valor + " (quantidade: " + atual.quantidade + ")"
        );
        mostrarEmOrdem(atual.direita);
    }

    public void mostrarArvore() {
        // Envia a raiz para a classe responsavel somente pelo desenho.
        VisualizadorArvore.mostrar(raiz);
    }

    public static void main(String[] args) {
        arvoreBinaria arvore = new arvoreBinaria();

        int[] numeros = {50,30,70,20,40,60,80,80,20};

        // Preenche a arvore com todos os valores.
        arvore.preencher(numeros);

        // Desenha a arvore com a raiz no topo.
        arvore.mostrarArvore();

        System.out.println("\nPercurso em ordem:");

        // Exibe os valores em ordem crescente.
        arvore.mostrarEmOrdem();
    }
}
