package br.edu.ifrn.labirintojava.algorithm;

import br.edu.ifrn.labirintojava.model.GridMap;
import br.edu.ifrn.labirintojava.model.MovementMode;

public interface SearchAlgorithm {
    String name();
    SearchSession createSession(GridMap map, MovementMode movement);
}
