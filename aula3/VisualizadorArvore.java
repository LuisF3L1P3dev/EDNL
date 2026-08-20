package aula3;

// Classe utilitaria responsavel apenas pela exibicao visual da arvore.
final class VisualizadorArvore {

    private VisualizadorArvore() {
        // Impede a criacao de objetos, pois todos os metodos sao estaticos.
    }

    static void mostrar(arvoreBinaria.No raiz) {
        if (raiz == null) {
            System.out.println("Arvore vazia");
            return;
        }

        int altura = calcularAltura(raiz);

        // Evita criar uma linha gigantesca para uma arvore muito alta.
        if (altura > 10) {
            System.out.println("Arvore muito alta para a exibicao em piramide.");
            return;
        }

        int larguraDoValor = maiorLargura(raiz);
        int unidade = Math.max(2, larguraDoValor);
        int posicoes = (1 << (altura + 1)) - 1;
        int colunas = posicoes * unidade;
        int linhas = altura * 2 + 1;

        // A matriz funciona como uma tela onde a arvore sera desenhada.
        char[][] tela = new char[linhas][colunas];
        for (char[] linha : tela) {
            java.util.Arrays.fill(linha, ' ');
        }

        int posicaoDaRaiz = (1 << altura) - 1;
        desenharNo(raiz, 0, posicaoDaRaiz, altura, unidade, tela);

        System.out.println("Arvore binaria de busca:");
        for (char[] linha : tela) {
            System.out.println(removerEspacosFinais(new String(linha)));
        }
    }

    private static void desenharNo(
        arvoreBinaria.No atual,
        int profundidade,
        int posicao,
        int altura,
        int unidade,
        char[][] tela
    ) {
        if (atual == null) {
            return;
        }

        int linhaDoNo = profundidade * 2;
        int colunaDoNo = posicao * unidade + unidade / 2;
        String valor = String.valueOf(atual.valor);

        // Centraliza o valor na posicao reservada para o no.
        escrever(tela[linhaDoNo], colunaDoNo - valor.length() / 2, valor);

        if (profundidade == altura) {
            return;
        }

        int deslocamento = 1 << (altura - profundidade - 1);
        int linhaDasLigacoes = linhaDoNo + 1;

        if (atual.esquerda != null) {
            int posicaoEsquerda = posicao - deslocamento;
            int colunaEsquerda = posicaoEsquerda * unidade + unidade / 2;

            // Coloca a barra entre o pai e o filho esquerdo.
            tela[linhaDasLigacoes][(colunaDoNo + colunaEsquerda) / 2] = '/';
            desenharNo(
                atual.esquerda,
                profundidade + 1,
                posicaoEsquerda,
                altura,
                unidade,
                tela
            );
        }

        if (atual.direita != null) {
            int posicaoDireita = posicao + deslocamento;
            int colunaDireita = posicaoDireita * unidade + unidade / 2;

            // Coloca a barra entre o pai e o filho direito.
            tela[linhaDasLigacoes][(colunaDoNo + colunaDireita) / 2] = '\\';
            desenharNo(
                atual.direita,
                profundidade + 1,
                posicaoDireita,
                altura,
                unidade,
                tela
            );
        }
    }

    private static int calcularAltura(arvoreBinaria.No atual) {
        if (atual == null) {
            return -1;
        }

        return 1 + Math.max(
            calcularAltura(atual.esquerda),
            calcularAltura(atual.direita)
        );
    }

    private static int maiorLargura(arvoreBinaria.No atual) {
        if (atual == null) {
            return 0;
        }

        return Math.max(
            String.valueOf(atual.valor).length(),
            Math.max(maiorLargura(atual.esquerda), maiorLargura(atual.direita))
        );
    }

    private static void escrever(char[] linha, int coluna, String texto) {
        for (int i = 0; i < texto.length(); i++) {
            linha[coluna + i] = texto.charAt(i);
        }
    }

    private static String removerEspacosFinais(String texto) {
        int fim = texto.length();

        while (fim > 0 && texto.charAt(fim - 1) == ' ') {
            fim--;
        }

        return texto.substring(0, fim);
    }
}
