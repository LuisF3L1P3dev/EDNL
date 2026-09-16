package dev.java.abb.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Arvore binaria de busca de inteiros.
 * Valores repetidos compartilham o mesmo no e incrementam sua quantidade.
 */
public final class ArvoreBinaria {

    private NoArvore raiz;

    public void inserir(int valor) {
        raiz = inserir(raiz, valor);
    }

    public void inserirTodos(List<Integer> valores) {
        if (valores == null || valores.isEmpty() || valores.stream().anyMatch(valor -> valor == null)) {
            throw new IllegalArgumentException("A lista deve conter ao menos um numero inteiro.");
        }

        for (int valor : valores) {
            inserir(valor);
        }
    }

    public boolean remover(int valor) {
        if (!contem(raiz, valor)) {
            return false;
        }

        raiz = remover(raiz, valor);
        return true;
    }

    public EstadoArvore consultarEstado() {
        List<EstadoArvore.Valor> valoresEmOrdem = new ArrayList<>();
        preencherEmOrdem(raiz, valoresEmOrdem);

        return new EstadoArvore(
                copiar(raiz),
                calcularAltura(raiz),
                contarNos(raiz),
                contarFolhas(raiz),
                List.copyOf(valoresEmOrdem)
        );
    }

    private NoArvore inserir(NoArvore atual, int valor) {
        if (atual == null) {
            return new NoArvore(valor);
        }

        if (valor < atual.valor) {
            atual.esquerda = inserir(atual.esquerda, valor);
        } else if (valor > atual.valor) {
            atual.direita = inserir(atual.direita, valor);
        } else {
            atual.quantidade++;
        }

        return atual;
    }

    private boolean contem(NoArvore atual, int valor) {
        while (atual != null) {
            if (valor == atual.valor) {
                return true;
            }
            atual = valor < atual.valor ? atual.esquerda : atual.direita;
        }
        return false;
    }

    private NoArvore remover(NoArvore atual, int valor) {
        if (valor < atual.valor) {
            atual.esquerda = remover(atual.esquerda, valor);
        } else if (valor > atual.valor) {
            atual.direita = remover(atual.direita, valor);
        } else {
            if (atual.quantidade > 1) {
                atual.quantidade--;
                return atual;
            }
            if (atual.esquerda == null) {
                return atual.direita;
            }
            if (atual.direita == null) {
                return atual.esquerda;
            }

            NoArvore sucessor = encontrarMenor(atual.direita);
            atual.valor = sucessor.valor;
            atual.quantidade = sucessor.quantidade;
            atual.direita = removerMenor(atual.direita);
        }
        return atual;
    }

    private NoArvore encontrarMenor(NoArvore atual) {
        while (atual.esquerda != null) {
            atual = atual.esquerda;
        }
        return atual;
    }

    private NoArvore removerMenor(NoArvore atual) {
        if (atual.esquerda == null) {
            return atual.direita;
        }
        atual.esquerda = removerMenor(atual.esquerda);
        return atual;
    }

    private int calcularAltura(NoArvore atual) {
        if (atual == null) {
            return -1;
        }
        return 1 + Math.max(calcularAltura(atual.esquerda), calcularAltura(atual.direita));
    }

    private int contarNos(NoArvore atual) {
        if (atual == null) {
            return 0;
        }
        return 1 + contarNos(atual.esquerda) + contarNos(atual.direita);
    }

    private int contarFolhas(NoArvore atual) {
        if (atual == null) {
            return 0;
        }
        if (atual.esquerda == null && atual.direita == null) {
            return 1;
        }
        return contarFolhas(atual.esquerda) + contarFolhas(atual.direita);
    }

    private void preencherEmOrdem(NoArvore atual, List<EstadoArvore.Valor> destino) {
        if (atual == null) {
            return;
        }
        preencherEmOrdem(atual.esquerda, destino);
        destino.add(new EstadoArvore.Valor(atual.valor, atual.quantidade));
        preencherEmOrdem(atual.direita, destino);
    }

    private EstadoArvore.No copiar(NoArvore atual) {
        if (atual == null) {
            return null;
        }
        return new EstadoArvore.No(
                atual.valor,
                atual.quantidade,
                copiar(atual.esquerda),
                copiar(atual.direita)
        );
    }
}
