package br.edu.ifrn.labirintojava.service;

import br.edu.ifrn.labirintojava.algorithm.SearchAlgorithm;
import br.edu.ifrn.labirintojava.algorithm.SearchSession;
import br.edu.ifrn.labirintojava.model.GridMap;
import br.edu.ifrn.labirintojava.model.MovementMode;
import br.edu.ifrn.labirintojava.model.SearchStep;
import javafx.application.Platform;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;

public final class SimulationRunner implements AutoCloseable {
    private final SearchSession session;
    // Cada simulação tem um executor próprio; o cálculo nunca bloqueia a thread gráfica.
    private final ExecutorService executor;
    private final AtomicBoolean busy = new AtomicBoolean();
    private volatile boolean cancelled;

    public SimulationRunner(SearchAlgorithm algorithm, GridMap snapshot, MovementMode movement) {
        session = algorithm.createSession(snapshot, movement);
        executor = Executors.newSingleThreadExecutor(task -> {
            Thread thread = new Thread(task, "labirinto-" + algorithm.name());
            thread.setDaemon(true);
            return thread;
        });
    }

    public boolean isBusy() { return busy.get(); }

    public boolean requestStep(Consumer<SearchStep> onStep, Consumer<Throwable> onError) {
        // Impede que vários ticks agendem expansões simultâneas para a mesma sessão.
        if (cancelled || !busy.compareAndSet(false, true)) return false;
        try {
            executor.execute(() -> {
                try {
                    SearchStep step = session.step();
                    // Controles e Canvas só podem ser atualizados na JavaFX Application Thread.
                    // A segunda checagem evita entregar resultados de uma execução já cancelada.
                    if (!cancelled) Platform.runLater(() -> {
                        busy.set(false);
                        if (!cancelled) onStep.accept(step);
                    });
                } catch (Throwable error) {
                    if (!cancelled) Platform.runLater(() -> {
                        busy.set(false);
                        if (!cancelled) onError.accept(error);
                    });
                }
            });
            return true;
        } catch (RejectedExecutionException exception) {
            busy.set(false);
            return false;
        }
    }

    @Override public void close() {
        // A interrupção encerra o executor; um passo que terminar depois será descartado.
        cancelled = true;
        executor.shutdownNow();
    }
}
