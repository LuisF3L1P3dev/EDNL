package br.edu.ifrn.labirintojava.algorithm;

import br.edu.ifrn.labirintojava.model.GridMap;
import br.edu.ifrn.labirintojava.model.MovementMode;

public final class AStarSearch implements SearchAlgorithm {
    @Override public String name() { return "A*"; }
    @Override public SearchSession createSession(GridMap map, MovementMode movement) {
        return new PrioritySearchSession(map.copy(), movement, true);
    }
}
