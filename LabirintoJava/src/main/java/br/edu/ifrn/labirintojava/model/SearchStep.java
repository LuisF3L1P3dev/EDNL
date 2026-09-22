package br.edu.ifrn.labirintojava.model;

import java.util.List;
import java.util.Map;

/**
 * Resultado de uma expansão. As mudanças de G/H são enviadas juntas para a interface;
 * computeNanos soma somente o trabalho do algoritmo, sem espera ou desenho da tela.
 */
public record SearchStep(SearchStatus status, Position expanded, Map<Position, NodeScore> scoresChanged,
                         List<Position> path, int explored, int discovered, int frontier,
                         int routeCost, long computeNanos) { }
