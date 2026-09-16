package dev.java.abb.model;

import java.util.List;

/** Fotografia imutavel da arvore usada pelas camadas service e controller. */
public record EstadoArvore(
        No raiz,
        int altura,
        int numeroNos,
        int numeroFolhas,
        List<Valor> emOrdem
) {

    public record No(int valor, int quantidade, No esquerda, No direita) {
    }

    public record Valor(int valor, int quantidade) {
    }
}
