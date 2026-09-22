package br.edu.ifrn.labirintojava.model;

public final class GridMap {
    private final int width;
    private final int height;
    private final boolean[][] walls;
    private Position start;
    private Position goal;

    public GridMap(int width, int height) {
        if (width < 2 || height < 2) throw new IllegalArgumentException("Grade muito pequena");
        this.width = width;
        this.height = height;
        this.walls = new boolean[height][width];
        this.start = new Position(0, 0);
        this.goal = new Position(width - 1, height - 1);
    }

    public int width() { return width; }
    public int height() { return height; }
    public Position start() { return start; }
    public Position goal() { return goal; }
    public boolean contains(int x, int y) { return x >= 0 && x < width && y >= 0 && y < height; }
    public boolean isWall(int x, int y) { return contains(x, y) && walls[y][x]; }
    public boolean isFree(int x, int y) { return contains(x, y) && !walls[y][x]; }

    public void setWall(Position position, boolean wall) {
        requireInside(position);
        if (wall && (position.equals(start) || position.equals(goal))) return;
        walls[position.y()][position.x()] = wall;
    }

    public void setStart(Position position) {
        requireInside(position);
        walls[position.y()][position.x()] = false;
        start = position;
    }

    public void setGoal(Position position) {
        requireInside(position);
        walls[position.y()][position.x()] = false;
        goal = position;
    }

    public void clearWalls() {
        for (boolean[] row : walls) java.util.Arrays.fill(row, false);
    }

    public GridMap copy() {
        GridMap copy = new GridMap(width, height);
        for (int y = 0; y < height; y++) System.arraycopy(walls[y], 0, copy.walls[y], 0, width);
        copy.start = start;
        copy.goal = goal;
        return copy;
    }

    private void requireInside(Position position) {
        if (!contains(position.x(), position.y())) throw new IllegalArgumentException("Posição fora da grade");
    }
}
