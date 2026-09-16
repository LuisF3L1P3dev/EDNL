package protecaoDDOS;

/*
 * Esta classe representa um unico no da arvore.
 *
 * Ela nao precisa ser public, pois sera usada somente pela
 * ArvoreBlacklist, que esta no mesmo pacote.
 */
final class NoIP {

    // Chave usada para decidir a posicao do no na arvore.
    long ip;

    // Quantas vezes este mesmo IP foi inserido na blacklist.
    int contadorTentativas;

    // IPs menores ficam na subarvore esquerda.
    NoIP esquerdo;

    // IPs maiores ficam na subarvore direita.
    NoIP direito;

    NoIP(long ip) {
        this.ip = ip;

        // O no e criado durante a primeira tentativa deste IP.
        this.contadorTentativas = 1;

        /*
         * Todo novo no comeca como uma folha: ele ainda nao possui filhos.
         * Em Java, esses campos ja seriam null por padrao, mas deixa-los
         * explicitos torna o estado inicial mais facil de compreender.
         */
        this.esquerdo = null;
        this.direito = null;
    }
}
