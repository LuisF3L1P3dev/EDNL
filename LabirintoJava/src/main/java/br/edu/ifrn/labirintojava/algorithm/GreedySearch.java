package br.edu.ifrn.labirintojava.algorithm;

import br.edu.ifrn.labirintojava.model.GridMap;
import br.edu.ifrn.labirintojava.model.MovementMode;

public final class GreedySearch implements SearchAlgorithm {
    @Override public String name() { return "Busca Gulosa"; }
    @Override public SearchSession createSession(GridMap map, MovementMode movement) {
        return new PrioritySearchSession(map.copy(), movement, false);
    }
}
