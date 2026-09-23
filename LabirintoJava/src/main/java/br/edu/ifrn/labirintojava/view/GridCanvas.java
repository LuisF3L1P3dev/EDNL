package br.edu.ifrn.labirintojava.view;

import br.edu.ifrn.labirintojava.model.GridMap;
import br.edu.ifrn.labirintojava.model.NodeScore;
import br.edu.ifrn.labirintojava.model.Position;
import br.edu.ifrn.labirintojava.model.SearchStep;
import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.input.MouseEvent;
import javafx.scene.paint.Color;
import javafx.scene.text.Font;
import javafx.scene.text.TextAlignment;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;

public final class GridCanvas extends Canvas {
    private static final Color EMPTY = Color.web("#f4f7fb");
    private static final Color WALL = Color.web("#27364a");
    private static final Color FRONTIER = Color.web("#f6c453");
    private static final Color EXPLORED = Color.web("#8ac7e7");
    private static final Color PATH = Color.web("#89ce8f");
    private static final Color START = Color.web("#27865d");
    private static final Color GOAL = Color.web("#d45359");
    private static final Color AGENT = Color.web("#794dc7");
    private static final Color GRID = Color.web("#cbd5e1");

    private final GridMap map;
    private final int cell;
    private final Set<Position> explored = new HashSet<>();
    private final Set<Position> frontier = new HashSet<>();
    private final Set<Position> path = new HashSet<>();
    private final Map<Position, NodeScore> scores = new HashMap<>();
    private Position agent;
    private Consumer<Position> onEdit = ignored -> { };
    private Consumer<Position> onInspect = ignored -> { };
    private boolean editable;

    public GridCanvas(GridMap map, int cell) {
        super(map.width() * cell, map.height() * cell);
        this.map = map;
        this.cell = cell;
        addEventHandler(MouseEvent.MOUSE_PRESSED, event -> {
            Position position = at(event);
            if (position != null && editable) onEdit.accept(position);
            if (position != null) onInspect.accept(position);
        });
        addEventHandler(MouseEvent.MOUSE_DRAGGED, event -> {
            Position position = at(event);
            if (position != null && editable) onEdit.accept(position);
        });
        addEventHandler(MouseEvent.MOUSE_MOVED, event -> {
            Position position = at(event);
            if (position != null) onInspect.accept(position);
        });
        draw();
    }

    public void setOnEdit(Consumer<Position> handler) { onEdit = handler; }
    public void setOnInspect(Consumer<Position> handler) { onInspect = handler; }
    public void setEditable(boolean editable) { this.editable = editable; }
    public NodeScore score(Position position) { return scores.get(position); }

    public void apply(SearchStep step) {
        // Cada expansão chega como um conjunto de alterações, seguido de um único redesenho.
        scores.putAll(step.scoresChanged());
        for (Position position : step.scoresChanged().keySet()) {
            if (!explored.contains(position)) frontier.add(position);
        }
        if (step.expanded() != null) {
            frontier.remove(step.expanded());
            explored.add(step.expanded());
        }
        if (!step.path().isEmpty()) path.addAll(step.path());
        draw();
    }

    public void setAgent(Position position) { agent = position; draw(); }

    public void draw() {
        GraphicsContext g = getGraphicsContext2D();
        g.setFont(Font.font(Math.max(11, cell * .46)));
        g.setTextAlign(TextAlignment.CENTER);
        for (int y = 0; y < map.height(); y++) {
            for (int x = 0; x < map.width(); x++) {
                Position p = new Position(x, y);
                Color color = EMPTY;
                // As últimas atribuições têm precedência: A, B e agente continuam visíveis.
                if (explored.contains(p)) color = EXPLORED;
                if (frontier.contains(p)) color = FRONTIER;
                if (path.contains(p)) color = PATH;
                if (map.isWall(x, y)) color = WALL;
                if (p.equals(map.start())) color = START;
                if (p.equals(map.goal())) color = GOAL;
                if (p.equals(agent)) color = AGENT;
                g.setFill(color);
                g.fillRect(x * cell, y * cell, cell, cell);
                g.setStroke(GRID);
                g.strokeRect(x * cell + .5, y * cell + .5, cell, cell);
                String symbol = "";
                if (p.equals(agent)) symbol = "●";
                else if (p.equals(map.start()) && p.equals(map.goal())) symbol = "A/B";
                else if (p.equals(map.start())) symbol = "A";
                else if (p.equals(map.goal())) symbol = "B";
                if (!symbol.isEmpty()) {
                    g.setFill(Color.WHITE);
                    g.fillText(symbol, x * cell + cell / 2.0, y * cell + cell * .69);
                }
            }
        }
    }

    private Position at(MouseEvent event) {
        if (event.getX() < 0 || event.getY() < 0) return null;
        int x = (int) (event.getX() / cell);
        int y = (int) (event.getY() / cell);
        return map.contains(x, y) ? new Position(x, y) : null;
    }
}
