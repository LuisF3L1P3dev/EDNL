package br.edu.ifrn.labirintojava.model;

import java.util.List;
import java.util.Map;

public record SearchStep(SearchStatus status, Position expanded, Map<Position, NodeScore> scoresChanged,
                         List<Position> path, int explored, int discovered, int frontier,
                         int routeCost, long computeNanos) { }
