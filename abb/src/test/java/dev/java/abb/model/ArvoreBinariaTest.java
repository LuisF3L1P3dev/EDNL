package dev.java.abb.model;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatIllegalArgumentException;

class ArvoreBinariaTest {

    @Test
    void deveRepresentarArvoreVazia() {
        EstadoArvore estado = new ArvoreBinaria().consultarEstado();

        assertThat(estado.raiz()).isNull();
        assertThat(estado.altura()).isEqualTo(-1);
        assertThat(estado.numeroNos()).isZero();
        assertThat(estado.numeroFolhas()).isZero();
        assertThat(estado.emOrdem()).isEmpty();
    }

    @Test
    void deveInserirOrdenarEContarSemDuplicarNos() {
        ArvoreBinaria arvore = arvoreCom(50, 30, 70, 20, 40, 60, 80, 80, 20);

        EstadoArvore estado = arvore.consultarEstado();

        assertThat(estado.altura()).isEqualTo(2);
        assertThat(estado.numeroNos()).isEqualTo(7);
        assertThat(estado.numeroFolhas()).isEqualTo(4);
        assertThat(estado.emOrdem()).extracting(EstadoArvore.Valor::valor)
                .containsExactly(20, 30, 40, 50, 60, 70, 80);
        assertThat(quantidadeDe(estado, 20)).isEqualTo(2);
        assertThat(quantidadeDe(estado, 80)).isEqualTo(2);
    }

    @Test
    void deveInserirListaNaOrdemInformada() {
        ArvoreBinaria arvore = new ArvoreBinaria();

        arvore.inserirTodos(List.of(10, 20, 40, 60, 20));

        EstadoArvore estado = arvore.consultarEstado();
        assertThat(estado.raiz().valor()).isEqualTo(10);
        assertThat(estado.altura()).isEqualTo(3);
        assertThat(estado.numeroNos()).isEqualTo(4);
        assertThat(quantidadeDe(estado, 20)).isEqualTo(2);
    }

    @Test
    void naoDeveInserirParcialmenteUmaListaInvalida() {
        ArvoreBinaria arvore = arvoreCom(5);

        assertThatIllegalArgumentException()
                .isThrownBy(() -> arvore.inserirTodos(java.util.Arrays.asList(10, null, 20)));
        assertThat(arvore.consultarEstado().emOrdem())
                .extracting(EstadoArvore.Valor::valor)
                .containsExactly(5);
    }

    @Test
    void deveRemoverSomenteUmaOcorrenciaRepetida() {
        ArvoreBinaria arvore = arvoreCom(10, 10);

        assertThat(arvore.remover(10)).isTrue();

        EstadoArvore estado = arvore.consultarEstado();
        assertThat(estado.numeroNos()).isOne();
        assertThat(quantidadeDe(estado, 10)).isOne();
    }

    @Test
    void deveRemoverFolhaENoComUmFilho() {
        ArvoreBinaria arvore = arvoreCom(50, 30, 70, 60, 65);

        assertThat(arvore.remover(30)).isTrue();
        assertThat(arvore.remover(60)).isTrue();

        assertThat(arvore.consultarEstado().emOrdem())
                .extracting(EstadoArvore.Valor::valor)
                .containsExactly(50, 65, 70);
    }

    @Test
    void deveRemoverRaizComDoisFilhosETransferirQuantidadeDoSucessor() {
        ArvoreBinaria arvore = arvoreCom(50, 30, 70, 60, 60, 80);

        assertThat(arvore.remover(50)).isTrue();

        EstadoArvore estado = arvore.consultarEstado();
        assertThat(estado.raiz().valor()).isEqualTo(60);
        assertThat(estado.raiz().quantidade()).isEqualTo(2);
        assertThat(estado.numeroNos()).isEqualTo(4);
        assertThat(estado.emOrdem()).extracting(EstadoArvore.Valor::valor)
                .containsExactly(30, 60, 70, 80);
    }

    @Test
    void naoDeveAlterarArvoreQuandoValorNaoExiste() {
        ArvoreBinaria arvore = arvoreCom(5, 3, 8);
        List<EstadoArvore.Valor> antes = arvore.consultarEstado().emOrdem();

        assertThat(arvore.remover(99)).isFalse();
        assertThat(arvore.consultarEstado().emOrdem()).isEqualTo(antes);
    }

    @Test
    void deveCalcularAlturaEmArestasParaArvoreDegenerada() {
        ArvoreBinaria arvore = arvoreCom(1, 2, 3, 4);

        assertThat(arvore.consultarEstado().altura()).isEqualTo(3);
    }

    private ArvoreBinaria arvoreCom(int... valores) {
        ArvoreBinaria arvore = new ArvoreBinaria();
        for (int valor : valores) {
            arvore.inserir(valor);
        }
        return arvore;
    }

    private int quantidadeDe(EstadoArvore estado, int valor) {
        return estado.emOrdem().stream()
                .filter(item -> item.valor() == valor)
                .findFirst()
                .orElseThrow()
                .quantidade();
    }
}
