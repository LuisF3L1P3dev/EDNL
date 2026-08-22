package protecaoDDOS;

/**
 * Arvore Binaria de Busca (BST) usada como uma blacklist de IPs.
 *
 * Regra da BST:
 * - todo IP menor que o IP de um no fica a esquerda;
 * - todo IP maior fica a direita;
 * - um IP igual nao cria outro no: incrementa o contador.
 */
public class ArvoreBlacklist {

    // A raiz e a porta de entrada da arvore inteira.
    private NoIP raiz;

    /**
     * Insere uma tentativa de acesso na blacklist.
     *
     * @param ip IP representado como um numero do tipo long
     */
    public void inserir(long ip) {
        /*
         * E necessario receber a raiz devolvida pelo metodo recursivo.
         * Quando a arvore esta vazia, o novo no passa a ser a raiz.
         */
        raiz = inserir(raiz, ip);
    }

    private NoIP inserir(NoIP atual, long ip) {
        // Caso-base: encontramos o lugar vazio onde o novo no deve entrar.
        if (atual == null) {
            return new NoIP(ip);
        }

        if (ip < atual.ip) {
            // Um valor menor deve ser procurado/inserido do lado esquerdo.
            atual.esquerdo = inserir(atual.esquerdo, ip);
        } else if (ip > atual.ip) {
            // Um valor maior deve ser procurado/inserido do lado direito.
            atual.direito = inserir(atual.direito, ip);
        } else {
            // O IP ja esta na arvore; registramos mais uma tentativa.
            atual.contadorTentativas++;
        }

        /*
         * Cada chamada devolve sua subarvore atualizada ao no pai.
         * Isso reconecta corretamente todos os nos durante a volta da recursao.
         */
        return atual;
    }

    /**
     * Procura um IP e informa seu estado no terminal.
     *
     * @return true se o IP estiver bloqueado; false caso contrario
     */
    public boolean buscar(long ip) {
        NoIP encontrado = localizar(ip);

        if (encontrado == null) {
            System.out.println(
                "IP " + ip + " nao esta bloqueado."
            );
            return false;
        }

        System.out.println(
            "IP " + ip + " esta bloqueado. Tentativas registradas: "
                + encontrado.contadorTentativas
        );
        return true;
    }

    private NoIP localizar(long ip) {
        NoIP atual = raiz;

        /*
         * A cada comparacao descartamos um dos lados da arvore.
         * Por isso nao precisamos visitar todos os nos para fazer uma busca.
         */
        while (atual != null) {
            if (ip < atual.ip) {
                atual = atual.esquerdo;
            } else if (ip > atual.ip) {
                atual = atual.direito;
            } else {
                // Nem menor nem maior: encontramos exatamente o IP procurado.
                return atual;
            }
        }

        // Chegar a null significa que o IP nao existe na arvore.
        return null;
    }

    /**
     * Exibe os IPs bloqueados em ordem numerica crescente.
     */
    public void relatorioOrdenado() {
        if (raiz == null) {
            System.out.println("A blacklist esta vazia.");
            return;
        }

        System.out.println("IPs bloqueados em ordem crescente:");
        relatorioOrdenado(raiz);
    }

    private void relatorioOrdenado(NoIP atual) {
        // Caso-base da recursao: nao ha no para visitar.
        if (atual == null) {
            return;
        }

        /*
         * Percurso em ordem: esquerda, no atual, direita.
         * Como a BST guarda menores a esquerda e maiores a direita,
         * este percurso produz automaticamente uma lista crescente.
         */
        relatorioOrdenado(atual.esquerdo);
        System.out.println(
            "- IP " + atual.ip
                + " | tentativas: " + atual.contadorTentativas
        );
        relatorioOrdenado(atual.direito);
    }

    /**
     * Remove completamente um IP da blacklist, mesmo que seu contador seja
     * maior que um. O fim da penalidade libera o IP, nao apenas uma tentativa.
     *
     * @return true se o IP foi removido; false se ele nao estava na arvore
     */
    public boolean remover(long ip) {
        // A verificacao permite informar ao chamador se havia algo para remover.
        if (localizar(ip) == null) {
            System.out.println(
                "IP " + ip + " nao foi removido porque nao esta na blacklist."
            );
            return false;
        }

        /*
         * A raiz precisa ser atualizada: o IP removido pode ser a propria raiz
         * ou a operacao pode trocar a raiz de alguma subarvore.
         */
        raiz = remover(raiz, ip);
        System.out.println("IP " + ip + " removido da blacklist.");
        return true;
    }

    private NoIP remover(NoIP atual, long ip) {
        // Protege a recursao caso ela alcance uma subarvore vazia.
        if (atual == null) {
            return null;
        }

        if (ip < atual.ip) {
            atual.esquerdo = remover(atual.esquerdo, ip);
        } else if (ip > atual.ip) {
            atual.direito = remover(atual.direito, ip);
        } else {
            // Encontramos o no. Agora precisamos analisar seus filhos.

            /*
             * CASO 1: nenhum filho.
             * Como os dois filhos sao null, devolver atual.direito devolve null.
             *
             * CASO 2: somente filho direito.
             * Devolver o filho direito liga esse filho diretamente ao no pai.
             */
            if (atual.esquerdo == null) {
                return atual.direito;
            }

            // CASO 2: somente filho esquerdo; ele assume o lugar do no removido.
            if (atual.direito == null) {
                return atual.esquerdo;
            }

            /*
             * CASO 3: dois filhos.
             * Escolhemos o sucessor: o menor no da subarvore direita.
             * Ele e maior que toda a esquerda e continua respeitando a BST.
             */
            NoIP sucessor = encontrarMenor(atual.direito);

            // Copiamos para o no atual todos os dados pertencentes ao sucessor.
            atual.ip = sucessor.ip;
            atual.contadorTentativas = sucessor.contadorTentativas;

            /*
             * O sucessor original ainda existe na direita e precisa ser
             * retirado fisicamente para nao deixar dois nos com o mesmo IP.
             */
            atual.direito = removerMenor(atual.direito);
        }

        return atual;
    }

    private NoIP encontrarMenor(NoIP atual) {
        // Em uma BST, o menor valor e o no mais a esquerda.
        while (atual.esquerdo != null) {
            atual = atual.esquerdo;
        }

        return atual;
    }

    private NoIP removerMenor(NoIP atual) {
        if (atual.esquerdo == null) {
            /*
             * Encontramos o menor. Ele nao possui filho esquerdo, mas pode
             * possuir filho direito, que assume sua antiga posicao.
             */
            return atual.direito;
        }

        atual.esquerdo = removerMenor(atual.esquerdo);
        return atual;
    }
}
