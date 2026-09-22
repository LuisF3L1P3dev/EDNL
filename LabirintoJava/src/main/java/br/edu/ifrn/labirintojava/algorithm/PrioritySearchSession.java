package br.edu.ifrn.labirintojava.algorithm;

import br.edu.ifrn.labirintojava.model.GridMap;
import br.edu.ifrn.labirintojava.model.MovementMode;
import br.edu.ifrn.labirintojava.model.NodeScore;
import br.edu.ifrn.labirintojava.model.Position;
import br.edu.ifrn.labirintojava.model.SearchStatus;
import br.edu.ifrn.labirintojava.model.SearchStep;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;

final class PrioritySearchSession implements SearchSession {
    // A versão distingue a entrada atual das entradas antigas da mesma célula na fila.
    private record Entry(Position position, int priority, int h, int version, long order) { }

    private final GridMap map;
    private final MovementMode movement;
    private final boolean astar;
    // Depois da prioridade principal, H, coordenadas e ordem de inserção resolvem empates.
    private final PriorityQueue<Entry> queue = new PriorityQueue<>(Comparator
            .comparingInt(Entry::priority).thenComparingInt(Entry::h)
            .thenComparingInt(e -> e.position().y()).thenComparingInt(e -> e.position().x())
            .thenComparingLong(Entry::order));
    private final int[][] g;
    private final int[][] versions;
    // Estas matrizes contam células únicas, mesmo quando a fila contém entradas repetidas.
    private final boolean[][] discoveredCells;
    private final boolean[][] frontierCells;
    private final boolean[][] closed;
    private final Position[][] parent;
    private SearchStatus status = SearchStatus.RUNNING;
    private int explored;
    private int discovered;
    private int frontier;
    private int routeCost = -1;
    private long elapsedNanos;
    private long insertionOrder;
    private List<Position> path = List.of();
    private boolean startScoreSent;

    PrioritySearchSession(GridMap map, MovementMode movement, boolean astar) {
        this.map = map;
        this.movement = movement;
        this.astar = astar;
        int width = map.width();
        int height = map.height();
        g = new int[height][width];
        versions = new int[height][width];
        discoveredCells = new boolean[height][width];
        frontierCells = new boolean[height][width];
        closed = new boolean[height][width];
        parent = new Position[height][width];
        for (int[] row : g) Arrays.fill(row, Integer.MAX_VALUE);
        Position start = map.start();
        g[start.y()][start.x()] = 0;
        discoveredCells[start.y()][start.x()] = true;
        frontierCells[start.y()][start.x()] = true;
        discovered = frontier = 1;
        enqueue(start);
    }

    @Override public SearchStatus status() { return status; }

    @Override public SearchStep step() {
        if (status != SearchStatus.RUNNING) return snapshot(null, Map.of());
        // O cronômetro cobre apenas a expansão; pausas e renderização ocorrem fora daqui.
        long begin = System.nanoTime();
        Map<Position, NodeScore> changed = new HashMap<>();
        if (!startScoreSent) {
            Position start = map.start();
            changed.put(start, score(start));
            startScoreSent = true;
        }
        Entry current = nextValid();
        Position expanded = null;
        if (current == null) {
            status = SearchStatus.NO_PATH;
        } else {
            expanded = current.position();
            frontierCells[expanded.y()][expanded.x()] = false;
            frontier--;
            closed[expanded.y()][expanded.x()] = true;
            explored++;
            // Com H consistente, o A* encontra o custo ótimo quando B sai da fila válida.
            // A Busca Gulosa também só termina ao expandir B, mas não garante custo mínimo.
            if (expanded.equals(map.goal())) {
                status = SearchStatus.FOUND;
                routeCost = g[expanded.y()][expanded.x()];
                path = reconstruct(expanded);
            } else {
                for (Position neighbor : movement.neighbors(map, expanded)) {
                    int x = neighbor.x();
                    int y = neighbor.y();
                    if (closed[y][x]) continue;
                    int candidate = g[expanded.y()][expanded.x()] + movement.cost(expanded, neighbor);
                    // A* substitui G e pai se achou rota melhor; a Gulosa mantém a primeira descoberta.
                    if (astar ? candidate < g[y][x] : !discoveredCells[y][x]) {
                        g[y][x] = candidate;
                        parent[y][x] = expanded;
                        if (!discoveredCells[y][x]) {
                            discoveredCells[y][x] = true;
                            discovered++;
                        }
                        if (!frontierCells[y][x]) {
                            frontierCells[y][x] = true;
                            frontier++;
                        }
                        enqueue(neighbor);
                        changed.put(neighbor, score(neighbor));
                    }
                }
                if (frontier == 0) status = SearchStatus.NO_PATH;
            }
        }
        elapsedNanos += System.nanoTime() - begin;
        return snapshot(expanded, changed);
    }

    private void enqueue(Position position) {
        int x = position.x();
        int y = position.y();
        int h = movement.heuristic(position, map.goal());
        // A única prioridade da Gulosa é H; o A* soma o custo já percorrido G.
        int priority = astar ? g[y][x] + h : h;
        queue.add(new Entry(position, priority, h, ++versions[y][x], insertionOrder++));
    }

    private Entry nextValid() {
        // PriorityQueue não remove uma entrada antiga quando G melhora; ignoramos sua versão.
        while (!queue.isEmpty()) {
            Entry entry = queue.remove();
            Position p = entry.position();
            if (!closed[p.y()][p.x()] && frontierCells[p.y()][p.x()]
                    && versions[p.y()][p.x()] == entry.version()) return entry;
        }
        return null;
    }

    private NodeScore score(Position p) {
        return new NodeScore(g[p.y()][p.x()], movement.heuristic(p, map.goal()));
    }

    private List<Position> reconstruct(Position goal) {
        // Os pais apontam para A; percorremos B -> A e invertemos para animar A -> B.
        List<Position> reversed = new ArrayList<>();
        Position p = goal;
        while (p != null) {
            reversed.add(p);
            p = parent[p.y()][p.x()];
        }
        java.util.Collections.reverse(reversed);
        return List.copyOf(reversed);
    }

    private SearchStep snapshot(Position expanded, Map<Position, NodeScore> changed) {
        return new SearchStep(status, expanded, Map.copyOf(changed), path,
                explored, discovered, frontier, routeCost, elapsedNanos);
    }
}
