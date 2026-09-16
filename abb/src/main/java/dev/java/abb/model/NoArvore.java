package dev.java.abb.model;

/** Representa um valor distinto armazenado na arvore. */
final class NoArvore {

    int valor;
    int quantidade = 1;
    NoArvore esquerda;
    NoArvore direita;

    NoArvore(int valor) {
        this.valor = valor;
    }
}
