package br.edu.ifrn.labirintojava.model;

public record NodeScore(int g, int h) {
    public int f() { return g + h; }
}
