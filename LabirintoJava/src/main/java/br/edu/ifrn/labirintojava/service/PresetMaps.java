package br.edu.ifrn.labirintojava.service;

import br.edu.ifrn.labirintojava.model.GridMap;
import br.edu.ifrn.labirintojava.model.Position;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;

public final class PresetMaps {
    public enum Preset {
        SIMPLE("Simples", "simple.txt"),
        MAZE("Labirinto", "maze.txt"),
        GREEDY_TRAP("Gulosa mais cara", "greedy-trap.txt");

        private final String label;
        private final String file;
        Preset(String label, String file) { this.label = label; this.file = file; }
        @Override public String toString() { return label; }
    }

    private PresetMaps() { }

    public static GridMap load(Preset preset) {
        String path = "/br/edu/ifrn/labirintojava/maps/" + preset.file;
        try (InputStream stream = PresetMaps.class.getResourceAsStream(path)) {
            if (stream == null) throw new IllegalStateException("Mapa não encontrado: " + path);
            return parse(new String(stream.readAllBytes(), StandardCharsets.UTF_8));
        } catch (IOException exception) {
            throw new IllegalStateException("Falha ao carregar " + path, exception);
        }
    }

    public static GridMap parse(String text) {
        List<String> rows = Arrays.stream(text.strip().split("\\R")).map(String::strip).toList();
        if (rows.isEmpty()) throw new IllegalArgumentException("Mapa vazio");
        int width = rows.getFirst().length();
        GridMap map = new GridMap(width, rows.size());
        Position start = null;
        Position goal = null;
        java.util.List<Position> walls = new java.util.ArrayList<>();
        for (int y = 0; y < rows.size(); y++) {
            String row = rows.get(y);
            if (row.length() != width) throw new IllegalArgumentException("Linhas com larguras diferentes");
            for (int x = 0; x < width; x++) {
                Position position = new Position(x, y);
                switch (row.charAt(x)) {
                    case '#' -> walls.add(position);
                    case 'A' -> { if (start != null) throw new IllegalArgumentException("Mais de um início"); start = position; }
                    case 'B' -> { if (goal != null) throw new IllegalArgumentException("Mais de um destino"); goal = position; }
                    case '.' -> { }
                    default -> throw new IllegalArgumentException("Caractere inválido no mapa");
                }
            }
        }
        if (start == null || goal == null) throw new IllegalArgumentException("Mapa exige A e B");
        map.setStart(start);
        map.setGoal(goal);
        for (Position wall : walls) map.setWall(wall, true);
        return map;
    }
}
