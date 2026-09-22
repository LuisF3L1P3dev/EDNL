package br.edu.ifrn.labirintojava.model;

import java.util.ArrayList;
import java.util.List;

public enum MovementMode {
    FOUR("4 direções"), EIGHT("8 direções");

    private static final int[][] CARDINAL = {{0, -1}, {-1, 0}, {1, 0}, {0, 1}};
    private static final int[][] DIAGONAL = {{-1, -1}, {1, -1}, {-1, 1}, {1, 1}};
    private final String label;

    MovementMode(String label) { this.label = label; }
    @Override public String toString() { return label; }

    public int heuristic(Position from, Position goal) {
        int dx = Math.abs(from.x() - goal.x());
        int dy = Math.abs(from.y() - goal.y());
        return this == FOUR ? 10 * (dx + dy) : 10 * Math.max(dx, dy) + 4 * Math.min(dx, dy);
    }

    public int cost(Position from, Position to) {
        int dx = Math.abs(from.x() - to.x());
        int dy = Math.abs(from.y() - to.y());
        if (dx == 0 && dy == 0 || dx > 1 || dy > 1 || this == FOUR && dx + dy != 1) {
            throw new IllegalArgumentException("Movimento inválido: " + from + " -> " + to);
        }
        return dx + dy == 2 ? 14 : 10;
    }

    public List<Position> neighbors(GridMap map, Position from) {
        List<Position> result = new ArrayList<>(this == FOUR ? 4 : 8);
        addNeighbors(map, from, CARDINAL, result);
        if (this == EIGHT) addNeighbors(map, from, DIAGONAL, result);
        return result;
    }

    private static void addNeighbors(GridMap map, Position from, int[][] directions, List<Position> result) {
        for (int[] direction : directions) {
            int x = from.x() + direction[0];
            int y = from.y() + direction[1];
            if (!map.isFree(x, y)) continue;
            if (direction[0] != 0 && direction[1] != 0
                    && (!map.isFree(x, from.y()) || !map.isFree(from.x(), y))) continue;
            result.add(new Position(x, y));
        }
    }
}
