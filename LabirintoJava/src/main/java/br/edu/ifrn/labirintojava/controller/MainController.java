package br.edu.ifrn.labirintojava.controller;

import br.edu.ifrn.labirintojava.algorithm.AStarSearch;
import br.edu.ifrn.labirintojava.algorithm.GreedySearch;
import br.edu.ifrn.labirintojava.algorithm.SearchAlgorithm;
import br.edu.ifrn.labirintojava.model.GridMap;
import br.edu.ifrn.labirintojava.model.MovementMode;
import br.edu.ifrn.labirintojava.model.NodeScore;
import br.edu.ifrn.labirintojava.model.Position;
import br.edu.ifrn.labirintojava.model.SearchStatus;
import br.edu.ifrn.labirintojava.model.SearchStep;
import br.edu.ifrn.labirintojava.service.PresetMaps;
import br.edu.ifrn.labirintojava.service.ComparisonService;
import br.edu.ifrn.labirintojava.service.SimulationRunner;
import br.edu.ifrn.labirintojava.view.GridCanvas;
import javafx.animation.KeyFrame;
import javafx.animation.Timeline;
import javafx.beans.property.SimpleStringProperty;
import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.CheckBox;
import javafx.scene.control.ComboBox;
import javafx.scene.control.Label;
import javafx.scene.control.Slider;
import javafx.scene.control.Spinner;
import javafx.scene.control.SpinnerValueFactory;
import javafx.scene.control.TableColumn;
import javafx.scene.control.TableView;
import javafx.scene.layout.HBox;
import javafx.scene.layout.VBox;
import javafx.util.Duration;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.function.Function;

public final class MainController {
    private enum EditTool {
        WALL("Desenhar obstáculo"), ERASE("Apagar obstáculo"), START("Definir A"), GOAL("Definir B");
        private final String label;
        EditTool(String label) { this.label = label; }
        @Override public String toString() { return label; }
    }
    private enum Phase { SEARCH, MOVE, DONE }
    private record ComparisonRow(String algorithm, String time, String explored, String cost) { }

    @FXML private ComboBox<PresetMaps.Preset> presetBox;
    @FXML private ComboBox<EditTool> toolBox;
    @FXML private ComboBox<MovementMode> movementBox;
    @FXML private ComboBox<String> algorithmBox;
    @FXML private Spinner<Integer> widthSpinner;
    @FXML private Spinner<Integer> heightSpinner;
    @FXML private CheckBox compareBox;
    @FXML private Slider speedSlider;
    @FXML private Button startButton;
    @FXML private Button pauseButton;
    @FXML private Button resumeButton;
    @FXML private Button stepButton;
    @FXML private HBox boards;
    @FXML private Label speedLabel;
    @FXML private Label visualLabel;
    @FXML private Label noticeLabel;
    @FXML private Label inspectorLabel;
    @FXML private TableView<ComparisonRow> comparisonTable;

    private final List<RunPanel> panels = new ArrayList<>();
    private final ComparisonService comparisonService = new ComparisonService();
    private GridMap editorMap;
    private GridCanvas editorCanvas;
    private Timeline timeline;
    private boolean settingDimensions;
    private boolean editLocked;
    private boolean running;
    // Muda a cada reinício: callbacks de uma busca anterior não podem desenhar na busca nova.
    private long generation;
    // O tempo visual acumula apenas períodos ativos, inclusive os intervalos da animação.
    private long visualActiveNanos;
    private long visualResumedAt;

    @FXML private void initialize() {
        settingDimensions = true;
        widthSpinner.setValueFactory(new SpinnerValueFactory.IntegerSpinnerValueFactory(5, 50, 20));
        heightSpinner.setValueFactory(new SpinnerValueFactory.IntegerSpinnerValueFactory(5, 50, 15));
        widthSpinner.setEditable(true);
        heightSpinner.setEditable(true);
        configureDimensionSpinner(widthSpinner);
        configureDimensionSpinner(heightSpinner);
        presetBox.getItems().setAll(PresetMaps.Preset.values());
        toolBox.getItems().setAll(EditTool.values());
        movementBox.getItems().setAll(MovementMode.values());
        algorithmBox.getItems().setAll("Busca Gulosa", "A*");
        toolBox.setValue(EditTool.WALL);
        movementBox.setValue(MovementMode.FOUR);
        algorithmBox.setValue("A*");
        compareBox.selectedProperty().addListener((obs, oldValue, newValue) -> updateControls());
        settingDimensions = false;
        widthSpinner.valueProperty().addListener((obs, oldValue, newValue) -> resizeMap());
        heightSpinner.valueProperty().addListener((obs, oldValue, newValue) -> resizeMap());
        speedSlider.valueProperty().addListener((obs, oldValue, newValue) -> {
            speedLabel.setText(Math.round(newValue.doubleValue()) + " passos/s");
            if (running) startTimeline();
        });
        speedLabel.setText(Math.round(speedSlider.getValue()) + " passos/s");
        setupComparisonTable();
        editorMap = new GridMap(20, 15);
        createEditorView();
    }

    private void setupComparisonTable() {
        comparisonTable.getColumns().setAll(
                column("Algoritmo", ComparisonRow::algorithm, 160),
                column("Tempo computacional", ComparisonRow::time, 190),
                column("Nós explorados", ComparisonRow::explored, 155),
                column("Custo da rota", ComparisonRow::cost, 150));
        comparisonTable.setColumnResizePolicy(TableView.CONSTRAINED_RESIZE_POLICY);
    }

    private TableColumn<ComparisonRow, String> column(String title, Function<ComparisonRow, String> getter, int width) {
        TableColumn<ComparisonRow, String> column = new TableColumn<>(title);
        column.setCellValueFactory(data -> new SimpleStringProperty(getter.apply(data.getValue())));
        column.setPrefWidth(width);
        return column;
    }

    @FXML private void loadPreset() {
        if (settingDimensions || editLocked || presetBox.getValue() == null) return;
        editorMap = PresetMaps.load(presetBox.getValue());
        settingDimensions = true;
        widthSpinner.getValueFactory().setValue(editorMap.width());
        heightSpinner.getValueFactory().setValue(editorMap.height());
        settingDimensions = false;
        createEditorView();
    }

    private void resizeMap() {
        if (settingDimensions || editLocked || editorMap == null) return;
        Integer width = widthSpinner.getValue();
        Integer height = heightSpinner.getValue();
        if (width == null || height == null || width < 5 || height < 5 || width > 50 || height > 50) return;
        editorMap = new GridMap(width, height);
        presetBox.setValue(null);
        createEditorView();
    }

    private void configureDimensionSpinner(Spinner<Integer> spinner) {
        spinner.getEditor().setOnAction(event -> commitDimension(spinner));
        spinner.getEditor().focusedProperty().addListener((obs, wasFocused, isFocused) -> {
            if (!isFocused) commitDimension(spinner);
        });
    }

    private void commitDimension(Spinner<Integer> spinner) {
        try {
            int value = Integer.parseInt(spinner.getEditor().getText().trim());
            spinner.getValueFactory().setValue(Math.max(5, Math.min(50, value)));
        } catch (NumberFormatException exception) {
            spinner.getEditor().setText(spinner.getValue().toString());
        }
    }

    private void createEditorView() {
        // Voltar ao editor fecha as sessões anteriores e limpa apenas as marcas visuais.
        cancelRuns();
        editLocked = false;
        boards.getChildren().clear();
        editorCanvas = new GridCanvas(editorMap, 29);
        editorCanvas.setEditable(true);
        editorCanvas.setOnEdit(this::editCell);
        editorCanvas.setOnInspect(position -> inspect(editorCanvas, position, algorithmBox.getValue()));
        VBox card = new VBox(8, heading("Mapa editável"), editorCanvas);
        card.getStyleClass().add("board-card");
        boards.getChildren().add(card);
        comparisonTable.setVisible(false);
        comparisonTable.setManaged(false);
        visualActiveNanos = 0;
        visualLabel.setText("Tempo visual: 0,00 s");
        updateControls();
    }

    private void editCell(Position position) {
        if (editLocked) return;
        switch (toolBox.getValue()) {
            case WALL -> editorMap.setWall(position, true);
            case ERASE -> editorMap.setWall(position, false);
            case START -> editorMap.setStart(position);
            case GOAL -> editorMap.setGoal(position);
        }
        editorCanvas.draw();
    }

    @FXML private void start() {
        if (editLocked) return;
        cancelRuns();
        editLocked = true;
        boards.getChildren().clear();
        // O destino e os obstáculos usados na busca ficam congelados nesta cópia.
        GridMap snapshot = editorMap.copy();
        MovementMode movement = movementBox.getValue();
        SearchAlgorithm selected = "Busca Gulosa".equals(algorithmBox.getValue()) ? new GreedySearch() : new AStarSearch();
        for (ComparisonService.RunPlan plan : comparisonService.prepare(snapshot, movement, selected, compareBox.isSelected())) {
            addPanel(plan.algorithm(), plan.map(), plan.movement(), compareBox.isSelected() ? 25 : 29);
        }
        comparisonTable.setVisible(compareBox.isSelected());
        comparisonTable.setManaged(compareBox.isSelected());
        updateComparisonTable();
        visualActiveNanos = 0;
        visualResumedAt = System.nanoTime();
        running = true;
        noticeLabel.setText("Busca em andamento. Um passo expande um nó válido; o destino permanece fixo.");
        startTimeline();
        updateControls();
    }

    private void addPanel(SearchAlgorithm algorithm, GridMap snapshot, MovementMode movement, int cell) {
        RunPanel panel = new RunPanel(algorithm, snapshot, movement, cell);
        panels.add(panel);
        boards.getChildren().add(panel.card);
    }

    private void startTimeline() {
        // O Timeline determina a cadência visual; o cálculo do algoritmo fica no executor.
        if (timeline != null) timeline.stop();
        timeline = new Timeline(new KeyFrame(Duration.millis(1000.0 / Math.round(speedSlider.getValue())), event -> tick()));
        timeline.setCycleCount(Timeline.INDEFINITE);
        timeline.play();
    }

    private void tick() {
        if (!running) return;
        advanceOne();
        updateVisualTime();
    }

    private void advanceOne() {
        // O mesmo método atende ao relógio automático e ao botão de avanço manual.
        long runGeneration = generation;
        for (RunPanel panel : panels) {
            if (panel.phase == Phase.SEARCH) {
                panel.runner.requestStep(step -> {
                    // Um resultado tardio pertence à execução antiga e não altera a tela atual.
                    if (generation != runGeneration) return;
                    panel.accept(step);
                    updateComparisonTable();
                    finishIfDone();
                    updateControls();
                }, error -> {
                    if (generation != runGeneration) return;
                    noticeLabel.setText("Erro na busca: " + error.getMessage());
                    pause();
                });
            } else if (panel.phase == Phase.MOVE) {
                panel.move();
            }
        }
        finishIfDone();
        updateControls();
    }

    @FXML private void pause() {
        if (!running) return;
        running = false;
        if (timeline != null) timeline.stop();
        // Pausas ficam fora do tempo visual; o tempo computacional já é medido na busca.
        visualActiveNanos += System.nanoTime() - visualResumedAt;
        updateVisualTime();
        noticeLabel.setText("Pausado. Avançar expande um nó válido ou move o agente uma célula.");
        updateControls();
    }

    @FXML private void resume() {
        if (!editLocked || running || allDone()) return;
        running = true;
        visualResumedAt = System.nanoTime();
        noticeLabel.setText("Simulação em andamento.");
        startTimeline();
        updateControls();
    }

    @FXML private void stepOnce() {
        // Espera o passo pendente: cada clique avança uma expansão ou movimento por painel ativo.
        if (!editLocked || running || allDone() || panels.stream().anyMatch(p -> p.runner.isBusy())) return;
        advanceOne();
    }

    @FXML private void reset() {
        boolean cancelled = editLocked && !allDone();
        String summary = cancelled ? cancellationSummary() : "";
        createEditorView();
        noticeLabel.setText(cancelled ? summary + " Mapa pronto para nova busca."
                : "Simulação reiniciada. Mapa pronto para edição.");
    }

    @FXML private void clearMap() {
        boolean cancelled = editLocked && !allDone();
        String summary = cancelled ? cancellationSummary() : "";
        editorMap.clearWalls();
        createEditorView();
        presetBox.setValue(null);
        noticeLabel.setText(cancelled ? summary + " Obstáculos removidos."
                : "Obstáculos removidos. A e B foram mantidos.");
    }

    private String cancellationSummary() {
        List<String> rows = new ArrayList<>();
        for (RunPanel panel : panels) {
            int explored = panel.last == null ? 0 : panel.last.explored();
            long time = panel.last == null ? 0 : panel.last.computeNanos();
            rows.add(panel.algorithm.name() + ": execução cancelada, explorados=" + explored
                    + ", CPU=" + formatNanos(time));
        }
        return String.join(" | ", rows) + ".";
    }

    private void cancelRuns() {
        // Invalidar primeiro os callbacks impede que uma sessão fechada contamine a próxima.
        generation++;
        if (timeline != null) timeline.stop();
        for (RunPanel panel : panels) panel.runner.close();
        panels.clear();
        running = false;
    }

    private boolean allDone() {
        return !panels.isEmpty() && panels.stream().allMatch(panel -> panel.phase == Phase.DONE);
    }

    private void finishIfDone() {
        if (!allDone()) return;
        if (running) {
            visualActiveNanos += System.nanoTime() - visualResumedAt;
            running = false;
        }
        if (timeline != null) timeline.stop();
        updateVisualTime();
        noticeLabel.setText("Execução concluída. Reinicie para editar o mapa. Busca Gulosa não garante custo mínimo.");
    }

    private void updateControls() {
        startButton.setDisable(editLocked);
        pauseButton.setDisable(!running);
        resumeButton.setDisable(!editLocked || running || allDone());
        stepButton.setDisable(!editLocked || running || allDone() || panels.stream().anyMatch(p -> p.runner.isBusy()));
        presetBox.setDisable(editLocked);
        widthSpinner.setDisable(editLocked);
        heightSpinner.setDisable(editLocked);
        toolBox.setDisable(editLocked);
        movementBox.setDisable(editLocked);
        algorithmBox.setDisable(editLocked || compareBox.isSelected());
        compareBox.setDisable(editLocked);
    }

    private void inspect(GridCanvas canvas, Position position, String algorithm) {
        NodeScore score = canvas.score(position);
        int h = movementBox.getValue().heuristic(position, editorMap.goal());
        String g = score == null ? "não descoberto" : Integer.toString(score.g());
        String f = score == null ? "não descoberto" : Integer.toString(score.f());
        String priority = "Busca Gulosa".equals(algorithm) ? " • prioridade: somente H" : " • prioridade: F = G + H";
        inspectorLabel.setText("(" + position.x() + ", " + position.y() + ")  G=" + g + "  H=" + h + "  F=" + f + priority);
    }

    private void updateVisualTime() {
        long nanos = visualActiveNanos + (running ? System.nanoTime() - visualResumedAt : 0);
        visualLabel.setText(String.format(Locale.forLanguageTag("pt-BR"), "Tempo visual: %.2f s", nanos / 1_000_000_000.0));
    }

    private void updateComparisonTable() {
        if (!compareBox.isSelected()) return;
        comparisonTable.getItems().setAll(panels.stream().map(panel -> new ComparisonRow(
                panel.algorithm.name(), formatNanos(panel.last == null ? 0 : panel.last.computeNanos()),
                Integer.toString(panel.last == null ? 0 : panel.last.explored()),
                panel.last == null || panel.last.status() != SearchStatus.FOUND ? "—" : Integer.toString(panel.last.routeCost())
        )).toList());
    }

    private static String formatNanos(long nanos) {
        return String.format(Locale.forLanguageTag("pt-BR"), "%.3f ms", nanos / 1_000_000.0);
    }

    private static Label heading(String text) {
        Label label = new Label(text);
        label.getStyleClass().add("board-heading");
        return label;
    }

    public void shutdown() { cancelRuns(); }

    private final class RunPanel {
        private final SearchAlgorithm algorithm;
        private final MovementMode movement;
        private final GridCanvas canvas;
        private final VBox card;
        private final Label metrics = new Label();
        private final SimulationRunner runner;
        private SearchStep last;
        private Phase phase = Phase.SEARCH;
        private int agentIndex;
        private int walkedCost;

        private RunPanel(SearchAlgorithm algorithm, GridMap map, MovementMode movement, int cell) {
            this.algorithm = algorithm;
            this.movement = movement;
            this.canvas = new GridCanvas(map, cell);
            this.runner = new SimulationRunner(algorithm, map.copy(), movement);
            canvas.setOnInspect(position -> inspect(canvas, position, algorithm.name()));
            metrics.getStyleClass().add("board-metrics");
            metrics.setWrapText(true);
            metrics.setText("Aguardando primeira expansão...");
            card = new VBox(8, heading(algorithm.name()), metrics, canvas);
            card.getStyleClass().add("board-card");
        }

        private void accept(SearchStep step) {
            last = step;
            canvas.apply(step);
            // Depois da busca, os ticks passam a mover o agente pelo caminho reconstruído.
            if (step.status() == SearchStatus.FOUND) {
                canvas.setAgent(step.path().getFirst());
                phase = step.path().size() == 1 ? Phase.DONE : Phase.MOVE;
            } else if (step.status() == SearchStatus.NO_PATH) {
                phase = Phase.DONE;
            }
            renderMetrics();
        }

        private void move() {
            if (last == null || phase != Phase.MOVE) return;
            Position previous = last.path().get(agentIndex);
            agentIndex++;
            Position next = last.path().get(agentIndex);
            // O custo percorrido usa as mesmas regras de movimento usadas no planejamento.
            walkedCost += movement.cost(previous, next);
            canvas.setAgent(next);
            if (agentIndex == last.path().size() - 1) phase = Phase.DONE;
            renderMetrics();
        }

        private void renderMetrics() {
            if (last == null) return;
            String state = switch (last.status()) {
                case RUNNING -> "buscando";
                case FOUND -> phase == Phase.DONE ? "caminho encontrado" : "agente em movimento";
                case NO_PATH -> "sem caminho";
                case CANCELLED -> "execução cancelada";
            };
            String route = last.status() == SearchStatus.FOUND
                    ? " | Custo: " + last.routeCost() + " | Movimentos: " + (last.path().size() - 1)
                    : " | Custo: — | Movimentos: —";
            metrics.setText("Estado: " + state + " | Explorados: " + last.explored()
                    + " | Descobertos: " + last.discovered() + " | Fronteira: " + last.frontier()
                    + route + " | Percorrido: " + walkedCost + " | CPU busca: " + formatNanos(last.computeNanos()));
        }
    }
}
