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
        // Envia a raiz e o vetor para a classe responsavel pelo preenchimento.
        raiz = inserirNumero.preencher(raiz, numeros);
    }

    public void inserirNumero(int numero) {
        /*
         * Atualiza a raiz porque, se a arvore estiver vazia,
         * o novo no criado devera se tornar a raiz.
         */
        raiz = inserirNumero.inserir(raiz, numero);
    }

    public void deletarNumero(int numero) {
        /*
         * Atualiza a raiz porque ela tambem pode ser removida
         * ou substituida durante a operacao.
         */
        raiz = deletarNo.remover(raiz, numero);
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

    public int calcularAltura() {
        // Envia a raiz para a classe responsavel pelo calculo da altura.
        return alturaArvore.calcular(raiz);
    }

    public int contarNos() {
        // Envia a raiz para a classe responsavel pela contagem dos nos.
        return numeroNos.contar(raiz);
    }

    public int contarFolhas() {
        // Envia a raiz para a classe responsavel pela contagem das folhas.
        return numeroFolhas.contar(raiz);
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

        arvore.mostrarArvore();
        
        // Insere um unico numero depois do preenchimento inicial.
        arvore.inserirNumero(65);

        // Remove o 70, que possui dois filhos: 60 e 80.
        arvore.deletarNumero(70);

        // Desenha a arvore com a raiz no topo.
        arvore.mostrarArvore();

        // Calcula a altura considerando o numero de arestas.
        System.out.println("\nAltura da arvore: " + arvore.calcularAltura());

        // Conta somente os nos fisicos; repeticoes ficam em quantidade.
        System.out.println("Numero de nos: " + arvore.contarNos());

        // Conta somente os nos que nao possuem filhos.
        System.out.println("Numero de folhas: " + arvore.contarFolhas());

        System.out.println("\nPercurso em ordem:");

        // Exibe os valores em ordem crescente.
        arvore.mostrarEmOrdem();
    }
}
