package br.edu.ifrn.labirintojava.service;

import br.edu.ifrn.labirintojava.algorithm.AStarSearch;
import br.edu.ifrn.labirintojava.algorithm.GreedySearch;
import br.edu.ifrn.labirintojava.algorithm.SearchAlgorithm;
import br.edu.ifrn.labirintojava.model.GridMap;
import br.edu.ifrn.labirintojava.model.MovementMode;

import java.util.List;

public final class ComparisonService {
    public record RunPlan(SearchAlgorithm algorithm, GridMap map, MovementMode movement) { }

    public List<RunPlan> prepare(GridMap source, MovementMode movement,
                                 SearchAlgorithm selected, boolean compare) {
        if (compare) return List.of(
                new RunPlan(new GreedySearch(), source.copy(), movement),
                new RunPlan(new AStarSearch(), source.copy(), movement));
        return List.of(new RunPlan(selected, source.copy(), movement));
    }
}
