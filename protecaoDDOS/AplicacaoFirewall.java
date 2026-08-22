package protecaoDDOS;

/**
 * Programa de demonstracao do filtro de firewall.
 *
 * Execute a partir da raiz do projeto com:
 *   javac protecaoDDOS/*.java
 *   java protecaoDDOS.AplicacaoFirewall
 */
public class AplicacaoFirewall {

    public static void main(String[] args) {
        // Criamos uma blacklist inicialmente vazia.
        ArvoreBlacklist blacklist = new ArvoreBlacklist();

        /*
         * O sufixo L informa ao Java que os numeros sao do tipo long.
         * Isso e necessario porque esses valores ultrapassam o limite de int.
         *
         * A ordem foi escolhida para formar nos a esquerda e a direita,
         * permitindo observar diferentes caminhos dentro da BST.
         */
        long[] ipsRecebidos = {
            192168001100L,
            172016000010L,
            203000113020L,
            10000000005L,
            180100050025L,
            198051100042L,
            220010010010L,
            198051100050L,
            203000113020L
        };

        System.out.println("=== REGISTRO DAS TENTATIVAS ===");
        for (long ip : ipsRecebidos) {
            // Cada valor do vetor e inserido na arvore.
            blacklist.inserir(ip);
        }
        System.out.println("Tentativas registradas.\n");

        System.out.println("=== CONSULTA AO FIREWALL ===");

        // Este IP foi inserido duas vezes, portanto seu contador deve ser 2.
        blacklist.buscar(203000113020L);

        // Este IP nao foi inserido e deve ser informado como liberado.
        blacklist.buscar(8008008008L);

        System.out.println("\n=== RELATORIO INICIAL ===");
        blacklist.relatorioOrdenado();

        System.out.println("\n=== FIM DA PENALIDADE ===");

        /*
         * CASO 1 - NO COM DOIS FILHOS:
         * Este no possui os filhos 10000000005 e 180100050025.
         * A remocao usara o sucessor para manter a ordenacao da BST.
         */
        blacklist.remover(172016000010L);

        /*
         * CASO 2 - NO FOLHA:
         * Este IP nao possui filhos e pode ser retirado diretamente.
         */
        blacklist.remover(10000000005L);

        /*
         * CASO 3 - NO COM UM FILHO:
         * Este IP possui somente o filho direito 198051100050.
         * Esse filho assumira a posicao do no removido.
         */
        blacklist.remover(198051100042L);

        /*
         * CASO 4 - REMOCAO DA RAIZ:
         * Mostra por que o metodo publico sempre atualiza a variavel raiz.
         */
        blacklist.remover(192168001100L);

        // Tentamos remover um IP ausente para demonstrar esse caso com seguranca.
        blacklist.remover(123456789L);

        System.out.println("\n=== RELATORIO APOS A REMOCAO ===");
        blacklist.relatorioOrdenado();
    }
}
