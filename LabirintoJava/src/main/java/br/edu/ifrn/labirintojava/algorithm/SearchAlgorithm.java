package br.edu.ifrn.labirintojava.algorithm;

import br.edu.ifrn.labirintojava.model.GridMap;
import br.edu.ifrn.labirintojava.model.MovementMode;

/** Cria uma sessão isolada para executar uma busca sobre uma cópia do mapa. */
public interface SearchAlgorithm {
    String name();
    SearchSession createSession(GridMap map, MovementMode movement);
}
