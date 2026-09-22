package br.edu.ifrn.labirintojava.algorithm;

import br.edu.ifrn.labirintojava.model.SearchStatus;
import br.edu.ifrn.labirintojava.model.SearchStep;

public interface SearchSession {
    SearchStep step();
    SearchStatus status();
}
