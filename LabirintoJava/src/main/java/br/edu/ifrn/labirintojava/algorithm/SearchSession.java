package br.edu.ifrn.labirintojava.algorithm;

import br.edu.ifrn.labirintojava.model.SearchStatus;
import br.edu.ifrn.labirintojava.model.SearchStep;

/** Permite animar, pausar e avançar a busca sem depender de JavaFX. */
public interface SearchSession {
    /** Expande exatamente um nó válido enquanto a busca estiver em andamento. */
    SearchStep step();
    SearchStatus status();
}
