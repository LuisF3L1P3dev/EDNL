"""Interface Tkinter para edição e comparação das buscas."""

from __future__ import annotations

from dataclasses import dataclass, field
import random
import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterator

from .model import Grid, Movement, Position
from .search import (
    Algorithm,
    SearchEvent,
    SearchEventType,
    SearchMetrics,
    search_steps,
)


COLORS = {
    "background": "#f4f6f8",
    "surface": "#ffffff",
    "text": "#182230",
    "muted": "#5d6b7a",
    "grid": "#d8dee7",
    "empty": "#ffffff",
    "wall": "#263238",
    "start": "#43a047",
    "goal": "#e53935",
    "frontier": "#b9e6c4",
    "explored": "#90caf9",
    "path": "#ffd54f",
    "agent": "#fb8c00",
    "primary": "#1565c0",
}

MODE_INDIVIDUAL = "Individual"
MODE_COMPARISON = "Comparação"


@dataclass(slots=True)
class VisualState:
    frontier: set[Position] = field(default_factory=set)
    explored: set[Position] = field(default_factory=set)
    path: set[Position] = field(default_factory=set)
    agent: Position | None = None

    def clear(self, start: Position | None) -> None:
        self.frontier.clear()
        self.explored.clear()
        self.path.clear()
        self.agent = start


class GridCanvas(tk.Canvas):
    """Canvas responsivo que desenha uma grade editável."""

    def __init__(
        self,
        master: tk.Misc,
        grid: Grid,
        visual: VisualState,
        edit_callback: Callable[[Position, bool], None],
    ) -> None:
        super().__init__(
            master,
            background=COLORS["surface"],
            highlightthickness=0,
            cursor="crosshair",
        )
        self.grid_model = grid
        self.visual = visual
        self.edit_callback = edit_callback
        self._cell_items: dict[Position, int] = {}
        self._cell_size = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._start_text: int | None = None
        self._goal_text: int | None = None
        self._agent_text: int | None = None
        self._last_dragged: Position | None = None

        self.bind("<Configure>", self._on_resize)
        self.bind("<Button-1>", self._on_primary_click)
        self.bind("<B1-Motion>", self._on_primary_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Button-3>", self._on_secondary_click)
        self.after_idle(self._rebuild_items)

    def _on_resize(self, _event: tk.Event[tk.Misc]) -> None:
        self._rebuild_items()

    def _rebuild_items(self) -> None:
        width = max(self.winfo_width(), 50)
        height = max(self.winfo_height(), 50)
        self._cell_size = max(
            3.0,
            min(
                (width - 4) / self.grid_model.columns,
                (height - 4) / self.grid_model.rows,
            ),
        )
        grid_width = self._cell_size * self.grid_model.columns
        grid_height = self._cell_size * self.grid_model.rows
        self._offset_x = (width - grid_width) / 2
        self._offset_y = (height - grid_height) / 2

        self.delete("all")
        self._cell_items.clear()
        for row in range(self.grid_model.rows):
            for column in range(self.grid_model.columns):
                position = (row, column)
                x1 = self._offset_x + column * self._cell_size
                y1 = self._offset_y + row * self._cell_size
                item = self.create_rectangle(
                    x1,
                    y1,
                    x1 + self._cell_size,
                    y1 + self._cell_size,
                    width=1,
                    outline=COLORS["grid"],
                    fill=COLORS["empty"],
                )
                self._cell_items[position] = item

        font_size = max(8, min(15, int(self._cell_size * 0.47)))
        marker_font = ("TkDefaultFont", font_size, "bold")
        self._start_text = self.create_text(0, 0, text="A", font=marker_font)
        self._goal_text = self.create_text(0, 0, text="B", font=marker_font)
        self._agent_text = self.create_text(
            0,
            0,
            text="●",
            font=marker_font,
            fill="#ffffff",
        )
        self.redraw()

    def redraw(self) -> None:
        if not self._cell_items:
            return
        for position, item in self._cell_items.items():
            self.itemconfigure(item, fill=self._color_for(position))

        assert self.grid_model.start is not None
        assert self.grid_model.goal is not None
        self._place_text(self._start_text, self.grid_model.start, "A")
        self._place_text(self._goal_text, self.grid_model.goal, "B")

        agent = self.visual.agent
        if agent is not None and agent != self.grid_model.start:
            self._place_text(self._agent_text, agent, "●")
        elif self._agent_text is not None:
            self.itemconfigure(self._agent_text, state="hidden")

    def _color_for(self, position: Position) -> str:
        if position in self.grid_model.walls:
            return COLORS["wall"]
        if position == self.visual.agent:
            return COLORS["agent"]
        if position == self.grid_model.start:
            return COLORS["start"]
        if position == self.grid_model.goal:
            return COLORS["goal"]
        if position in self.visual.path:
            return COLORS["path"]
        if position in self.visual.explored:
            return COLORS["explored"]
        if position in self.visual.frontier:
            return COLORS["frontier"]
        return COLORS["empty"]

    def _place_text(
        self,
        item: int | None,
        position: Position,
        text: str,
    ) -> None:
        if item is None:
            return
        row, column = position
        x = self._offset_x + (column + 0.5) * self._cell_size
        y = self._offset_y + (row + 0.5) * self._cell_size
        self.coords(item, x, y)
        self.itemconfigure(item, text=text, state="normal")
        self.tag_raise(item)

    def _position_from_event(self, event: tk.Event[tk.Misc]) -> Position | None:
        column = int((event.x - self._offset_x) // self._cell_size)
        row = int((event.y - self._offset_y) // self._cell_size)
        position = (row, column)
        if self.grid_model.in_bounds(position):
            return position
        return None

    def _on_primary_click(self, event: tk.Event[tk.Misc]) -> None:
        self._last_dragged = None
        self._edit_from_event(event, erase=False)

    def _on_primary_drag(self, event: tk.Event[tk.Misc]) -> None:
        self._edit_from_event(event, erase=False)

    def _on_secondary_click(self, event: tk.Event[tk.Misc]) -> None:
        self._last_dragged = None
        self._edit_from_event(event, erase=True)

    def _on_release(self, _event: tk.Event[tk.Misc]) -> None:
        self._last_dragged = None

    def _edit_from_event(
        self,
        event: tk.Event[tk.Misc],
        *,
        erase: bool,
    ) -> None:
        position = self._position_from_event(event)
        if position is None or position == self._last_dragged:
            return
        self._last_dragged = position
        self.edit_callback(position, erase)


class MetricsBar(ttk.Frame):
    """Resumo numérico de uma execução."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, style="Metrics.TFrame", padding=(8, 7))
        self.status_var = tk.StringVar(value="Pronto")
        self.time_var = tk.StringVar(value="0,000 ms")
        self.explored_var = tk.StringVar(value="0")
        self.frontier_var = tk.StringVar(value="0")
        self.cost_var = tk.StringVar(value="—")
        self.length_var = tk.StringVar(value="—")

        fields = (
            ("Estado", self.status_var, 18),
            ("Tempo", self.time_var, 13),
            ("Explorados", self.explored_var, 9),
            ("Fronteira", self.frontier_var, 8),
            ("Custo", self.cost_var, 7),
            ("Passos", self.length_var, 7),
        )
        for column, (title, variable, width) in enumerate(fields):
            self.columnconfigure(column, weight=2 if column == 0 else 1)
            block = ttk.Frame(self, style="Metrics.TFrame")
            block.grid(row=0, column=column, sticky="ew", padx=4)
            ttk.Label(
                block,
                text=title,
                style="MetricTitle.TLabel",
            ).pack(anchor="w")
            ttk.Label(
                block,
                textvariable=variable,
                width=width,
                style="MetricValue.TLabel",
            ).pack(anchor="w")

    def reset(self) -> None:
        self.status_var.set("Pronto")
        self.update_metrics(SearchMetrics())

    def update_metrics(self, metrics: SearchMetrics) -> None:
        self.time_var.set(_format_milliseconds(metrics.elapsed_ms))
        self.explored_var.set(str(metrics.nodes_explored))
        self.frontier_var.set(str(metrics.frontier_size))
        self.cost_var.set("—" if metrics.path_cost is None else str(metrics.path_cost))
        self.length_var.set(
            "—" if metrics.path_length is None else str(metrics.path_length)
        )


class SearchPanel(ttk.Frame):
    """Um painel de visualização com grade e métricas próprias."""

    def __init__(
        self,
        master: tk.Misc,
        grid: Grid,
        title: str,
        edit_callback: Callable[[Position, bool], None],
    ) -> None:
        super().__init__(master, style="Panel.TFrame", padding=1)
        self.grid_model = grid
        self.visual = VisualState(agent=grid.start)
        self.title_var = tk.StringVar(value=title)

        ttk.Label(
            self,
            textvariable=self.title_var,
            style="PanelTitle.TLabel",
            anchor="center",
            padding=(8, 8),
        ).pack(fill="x")
        self.canvas = GridCanvas(self, grid, self.visual, edit_callback)
        self.canvas.pack(fill="both", expand=True, padx=1)
        self.metrics = MetricsBar(self)
        self.metrics.pack(fill="x", padx=1, pady=(1, 0))

    def reset(self) -> None:
        self.visual.clear(self.grid_model.start)
        self.metrics.reset()
        self.canvas.redraw()

    def apply_event(self, event: SearchEvent) -> None:
        if event.current is not None:
            self.visual.frontier.discard(event.current)
            if event.current not in (self.grid_model.start, self.grid_model.goal):
                self.visual.explored.add(event.current)

        for position in event.opened:
            if position not in self.visual.explored:
                self.visual.frontier.add(position)

        self.metrics.update_metrics(event.metrics)
        if event.kind is SearchEventType.EXPANDED:
            self.metrics.status_var.set("Buscando")
        elif event.kind is SearchEventType.FOUND:
            self.visual.path = set(event.path)
            self.metrics.status_var.set("Rota encontrada")
        else:
            self.metrics.status_var.set("Sem caminho")
        self.canvas.redraw()

    def move_agent(self, position: Position) -> None:
        self.visual.agent = position
        self.canvas.redraw()


@dataclass(slots=True)
class AnimationRunner:
    algorithm: Algorithm
    panel: SearchPanel
    events: Iterator[SearchEvent]
    phase: str = "search"
    path: tuple[Position, ...] = ()
    path_index: int = 1
    final_event: SearchEvent | None = None
    done: bool = False


class PathfindingApp(tk.Tk):
    """Janela principal da aplicação."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Laboratório de Busca em Labirintos")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = max(800, min(1360, screen_width - 80))
        window_height = max(600, min(850, screen_height - 100))
        self.geometry(f"{window_width}x{window_height}")
        self.minsize(min(1020, window_width), min(680, window_height))
        self.configure(background=COLORS["background"])
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.grid_model = Grid()
        self.mode_var = tk.StringVar(value=MODE_INDIVIDUAL)
        self.algorithm_var = tk.StringVar(value=Algorithm.ASTAR.value)
        self.movement_var = tk.StringVar(value=Movement.FOUR.value)
        self.tool_var = tk.StringVar(value="wall")
        self.speed_var = tk.DoubleVar(value=75)
        self.speed_label_var = tk.StringVar(value="75%")
        self.density_var = tk.DoubleVar(value=28)
        self.density_label_var = tk.StringVar(value="28%")
        self.status_var = tk.StringVar(
            value="Edite o labirinto e clique em Executar."
        )
        self.pause_text_var = tk.StringVar(value="Pausar")

        self._panels: list[SearchPanel] = []
        self._runners: list[AnimationRunner] = []
        self._running = False
        self._paused = False
        self._run_token = 0
        self._after_id: str | None = None

        self._configure_styles()
        self._build_interface()
        self._rebuild_panels()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("App.TFrame", background=COLORS["background"])
        style.configure("Surface.TFrame", background=COLORS["surface"])
        style.configure("Panel.TFrame", background=COLORS["grid"])
        style.configure("Metrics.TFrame", background="#eef2f6")
        style.configure(
            "Title.TLabel",
            background=COLORS["background"],
            foreground=COLORS["text"],
            font=("TkDefaultFont", 18, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=COLORS["background"],
            foreground=COLORS["muted"],
            font=("TkDefaultFont", 10),
        )
        style.configure(
            "PanelTitle.TLabel",
            background="#e8eef5",
            foreground=COLORS["text"],
            font=("TkDefaultFont", 11, "bold"),
        )
        style.configure(
            "MetricTitle.TLabel",
            background="#eef2f6",
            foreground=COLORS["muted"],
            font=("TkDefaultFont", 8),
        )
        style.configure(
            "MetricValue.TLabel",
            background="#eef2f6",
            foreground=COLORS["text"],
            font=("TkDefaultFont", 9, "bold"),
        )
        style.configure(
            "Status.TLabel",
            background="#e8eef5",
            foreground=COLORS["text"],
            padding=(10, 7),
        )
        style.configure(
            "Accent.TButton",
            background=COLORS["primary"],
            foreground="#ffffff",
            font=("TkDefaultFont", 9, "bold"),
            padding=(12, 7),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#0d47a1"), ("disabled", "#9eabb8")],
            foreground=[("disabled", "#eef2f6")],
        )

    def _build_interface(self) -> None:
        outer = ttk.Frame(self, style="App.TFrame", padding=(14, 12, 14, 10))
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer, style="App.TFrame")
        header.pack(fill="x", pady=(0, 10))
        title_block = ttk.Frame(header, style="App.TFrame")
        title_block.pack(side="left")
        ttk.Label(
            title_block,
            text="Laboratório de Busca em Labirintos",
            style="Title.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            title_block,
            text="Compare Busca Gulosa e A* em um ambiente interativo",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        controls = ttk.Frame(outer, style="Surface.TFrame", padding=10)
        controls.pack(fill="x", pady=(0, 9))
        self._build_selection_controls(controls)
        ttk.Separator(controls, orient="horizontal").pack(fill="x", pady=8)
        self._build_action_controls(controls)

        self.panel_host = ttk.Frame(outer, style="App.TFrame")
        self.panel_host.pack(fill="both", expand=True)

        footer = ttk.Frame(outer, style="App.TFrame")
        footer.pack(fill="x", pady=(9, 0))
        self._build_legend(footer)
        ttk.Label(
            footer,
            textvariable=self.status_var,
            style="Status.TLabel",
            anchor="w",
        ).pack(side="right", fill="x", expand=True, padx=(12, 0))

    def _build_selection_controls(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent, style="Surface.TFrame")
        row.pack(fill="x")

        ttk.Label(row, text="Visualização:").pack(side="left")
        mode = ttk.Combobox(
            row,
            textvariable=self.mode_var,
            values=(MODE_INDIVIDUAL, MODE_COMPARISON),
            state="readonly",
            width=14,
        )
        mode.pack(side="left", padx=(5, 14))
        mode.bind("<<ComboboxSelected>>", self._on_mode_changed)

        ttk.Label(row, text="Estratégia:").pack(side="left")
        self.algorithm_combo = ttk.Combobox(
            row,
            textvariable=self.algorithm_var,
            values=(Algorithm.GREEDY.value, Algorithm.ASTAR.value),
            state="readonly",
            width=15,
        )
        self.algorithm_combo.pack(side="left", padx=(5, 14))
        self.algorithm_combo.bind("<<ComboboxSelected>>", self._on_algorithm_changed)

        ttk.Label(row, text="Movimento:").pack(side="left")
        movement = ttk.Combobox(
            row,
            textvariable=self.movement_var,
            values=(Movement.FOUR.value, Movement.EIGHT.value),
            state="readonly",
            width=13,
        )
        movement.pack(side="left", padx=(5, 16))
        movement.bind("<<ComboboxSelected>>", self._on_movement_changed)

        ttk.Label(row, text="Velocidade:").pack(side="left")
        ttk.Scale(
            row,
            from_=1,
            to=100,
            variable=self.speed_var,
            command=self._on_speed_changed,
            length=115,
        ).pack(side="left", padx=(5, 4))
        ttk.Label(row, textvariable=self.speed_label_var, width=5).pack(side="left")

        ttk.Label(row, text="Obstáculos:").pack(side="left", padx=(12, 0))
        ttk.Scale(
            row,
            from_=5,
            to=55,
            variable=self.density_var,
            command=self._on_density_changed,
            length=100,
        ).pack(side="left", padx=(5, 4))
        ttk.Label(row, textvariable=self.density_label_var, width=5).pack(side="left")

    def _build_action_controls(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent, style="Surface.TFrame")
        row.pack(fill="x")

        ttk.Label(row, text="Ferramenta:").pack(side="left")
        tools = (
            ("Parede", "wall"),
            ("Borracha", "erase"),
            ("Ponto A", "start"),
            ("Ponto B", "goal"),
        )
        for label, value in tools:
            ttk.Radiobutton(
                row,
                text=label,
                value=value,
                variable=self.tool_var,
            ).pack(side="left", padx=(5, 2))

        ttk.Button(row, text="Gerar labirinto", command=self._generate_maze).pack(
            side="left", padx=(15, 3)
        )
        ttk.Button(row, text="Limpar paredes", command=self._clear_walls).pack(
            side="left", padx=3
        )
        ttk.Button(row, text="Limpar busca", command=self._clear_search).pack(
            side="left", padx=3
        )
        ttk.Button(row, text="Restaurar", command=self._restore_grid).pack(
            side="left", padx=3
        )

        self.stop_button = ttk.Button(row, text="Parar", command=self._stop_clicked)
        self.stop_button.pack(side="right", padx=(3, 0))
        self.pause_button = ttk.Button(
            row,
            textvariable=self.pause_text_var,
            command=self._toggle_pause,
        )
        self.pause_button.pack(side="right", padx=3)
        self.start_button = ttk.Button(
            row,
            text="Executar",
            command=self._start_execution,
            style="Accent.TButton",
        )
        self.start_button.pack(side="right", padx=3)
        self._set_running_controls(False)

    def _build_legend(self, parent: ttk.Frame) -> None:
        legend = ttk.Frame(parent, style="App.TFrame")
        legend.pack(side="left")
        items = (
            ("A", COLORS["start"]),
            ("B", COLORS["goal"]),
            ("Fronteira", COLORS["frontier"]),
            ("Explorado", COLORS["explored"]),
            ("Caminho", COLORS["path"]),
            ("Agente", COLORS["agent"]),
            ("Parede", COLORS["wall"]),
        )
        for label, color in items:
            item = ttk.Frame(legend, style="App.TFrame")
            item.pack(side="left", padx=(0, 9))
            swatch = tk.Canvas(
                item,
                width=12,
                height=12,
                highlightthickness=1,
                highlightbackground=COLORS["grid"],
            )
            swatch.create_rectangle(0, 0, 13, 13, fill=color, outline=color)
            swatch.pack(side="left", padx=(0, 3))
            ttk.Label(item, text=label, style="Subtitle.TLabel").pack(side="left")

    def _rebuild_panels(self) -> None:
        self._cancel_execution()
        for child in self.panel_host.winfo_children():
            child.destroy()
        self._panels.clear()
        # Remove pesos que possam ter permanecido do modo comparativo.
        for column in range(2):
            self.panel_host.columnconfigure(column, weight=0, uniform="")

        if self.mode_var.get() == MODE_COMPARISON:
            algorithms = (Algorithm.GREEDY, Algorithm.ASTAR)
            self.algorithm_combo.configure(state="disabled")
        else:
            algorithms = (Algorithm(self.algorithm_var.get()),)
            self.algorithm_combo.configure(state="readonly")

        for column, algorithm in enumerate(algorithms):
            self.panel_host.columnconfigure(column, weight=1, uniform="panels")
            panel = SearchPanel(
                self.panel_host,
                self.grid_model,
                algorithm.value,
                self._edit_grid,
            )
            panel.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else 4, 4 if column == 0 else 0),
            )
            self._panels.append(panel)
        self.panel_host.rowconfigure(0, weight=1)
        self.status_var.set("Modo alterado. O labirinto foi preservado.")

    def _edit_grid(self, position: Position, erase_override: bool) -> None:
        if self._running:
            self.status_var.set("Interrompa a execução antes de editar a grade.")
            return

        tool = "erase" if erase_override else self.tool_var.get()
        changed = False
        if tool == "wall":
            changed = self.grid_model.set_wall(position, True)
        elif tool == "erase":
            changed = self.grid_model.set_wall(position, False)
        elif tool == "start":
            changed = self.grid_model.set_start(position)
            if not changed and position == self.grid_model.goal:
                self.status_var.set("O ponto A não pode ocupar a célula de B.")
        elif tool == "goal":
            changed = self.grid_model.set_goal(position)
            if not changed and position == self.grid_model.start:
                self.status_var.set("O ponto B não pode ocupar a célula de A.")

        if changed:
            self._reset_panels()
            self.status_var.set("Labirinto atualizado.")

    def _start_execution(self) -> None:
        self._cancel_execution()
        self._reset_panels()
        movement = Movement(self.movement_var.get())

        if self.mode_var.get() == MODE_COMPARISON:
            algorithms = (Algorithm.GREEDY, Algorithm.ASTAR)
        else:
            algorithms = (Algorithm(self.algorithm_var.get()),)

        self._runners = []
        for algorithm, panel in zip(algorithms, self._panels, strict=True):
            panel.title_var.set(algorithm.value)
            snapshot = self.grid_model.clone()
            self._runners.append(
                AnimationRunner(
                    algorithm=algorithm,
                    panel=panel,
                    events=search_steps(snapshot, algorithm, movement),
                )
            )

        self._running = True
        self._paused = False
        self._run_token += 1
        self.pause_text_var.set("Pausar")
        self._set_running_controls(True)
        self.status_var.set("Busca em andamento...")
        token = self._run_token
        self._after_id = self.after(0, lambda: self._tick(token))

    def _tick(self, token: int) -> None:
        self._after_id = None
        if token != self._run_token or not self._running or self._paused:
            return

        for runner in self._runners:
            if runner.done:
                continue
            if runner.phase == "search":
                self._advance_search(runner)
            elif runner.phase == "walk":
                self._advance_agent(runner)

        if all(runner.done for runner in self._runners):
            self._finish_execution()
            return

        self._after_id = self.after(
            self._animation_delay(),
            lambda: self._tick(token),
        )

    def _advance_search(self, runner: AnimationRunner) -> None:
        try:
            event = next(runner.events)
        except StopIteration:
            runner.done = True
            runner.panel.metrics.status_var.set("Finalizado")
            return

        runner.panel.apply_event(event)
        if event.kind is SearchEventType.FOUND:
            runner.final_event = event
            runner.path = event.path
            runner.path_index = 1
            runner.phase = "walk"
            runner.panel.metrics.status_var.set("Caminhando")
        elif event.kind is SearchEventType.NO_PATH:
            runner.final_event = event
            runner.done = True

    def _advance_agent(self, runner: AnimationRunner) -> None:
        if runner.path_index < len(runner.path):
            runner.panel.move_agent(runner.path[runner.path_index])
            runner.path_index += 1
        if runner.path_index >= len(runner.path):
            runner.done = True
            runner.panel.metrics.status_var.set("Concluído")

    def _finish_execution(self) -> None:
        self._running = False
        self._paused = False
        self._after_id = None
        self._set_running_controls(False)

        found = [
            runner
            for runner in self._runners
            if runner.final_event is not None
            and runner.final_event.kind is SearchEventType.FOUND
        ]
        if not found:
            self.status_var.set("Nenhum caminho foi encontrado.")
        elif len(self._runners) == 1:
            self.status_var.set("Execução concluída. O agente chegou ao ponto B.")
        elif len(found) == 2:
            greedy_cost = found[0].final_event.metrics.path_cost
            astar_cost = found[1].final_event.metrics.path_cost
            if greedy_cost == astar_cost:
                message = "Comparação concluída: os caminhos têm o mesmo custo."
            else:
                message = (
                    "Comparação concluída: A* encontrou o caminho de menor custo."
                )
            self.status_var.set(message)
        else:
            self.status_var.set("Comparação concluída; apenas um algoritmo achou rota.")

    def _toggle_pause(self) -> None:
        if not self._running:
            return
        if self._paused:
            self._paused = False
            self.pause_text_var.set("Pausar")
            self.status_var.set("Execução retomada.")
            token = self._run_token
            self._after_id = self.after(0, lambda: self._tick(token))
        else:
            self._paused = True
            self.pause_text_var.set("Continuar")
            self._cancel_scheduled_tick()
            self.status_var.set("Execução pausada.")

    def _stop_clicked(self) -> None:
        if not self._running:
            return
        active_runners = [runner for runner in self._runners if not runner.done]
        self._cancel_execution()
        for runner in active_runners:
            runner.panel.metrics.status_var.set("Interrompido")
        self.status_var.set("Execução interrompida; o resultado parcial foi mantido.")

    def _cancel_execution(self) -> None:
        self._cancel_scheduled_tick()
        self._run_token += 1
        self._running = False
        self._paused = False
        self._runners.clear()
        self.pause_text_var.set("Pausar")
        if hasattr(self, "start_button"):
            self._set_running_controls(False)

    def _cancel_scheduled_tick(self) -> None:
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _set_running_controls(self, running: bool) -> None:
        self.start_button.configure(state="disabled" if running else "normal")
        self.pause_button.configure(state="normal" if running else "disabled")
        self.stop_button.configure(state="normal" if running else "disabled")

    def _clear_search(self) -> None:
        self._cancel_execution()
        self._reset_panels()
        self.status_var.set("Visualização da busca removida; paredes preservadas.")

    def _clear_walls(self) -> None:
        self._cancel_execution()
        self.grid_model.clear_walls()
        self._reset_panels()
        self.status_var.set("Todas as paredes foram removidas.")

    def _restore_grid(self) -> None:
        self._cancel_execution()
        self.grid_model = Grid(
            rows=self.grid_model.rows,
            columns=self.grid_model.columns,
        )
        self._rebuild_panels()
        self.status_var.set("Grade restaurada para o estado inicial.")

    def _generate_maze(self) -> None:
        self._cancel_execution()
        self.grid_model.randomize(
            density=self.density_var.get() / 100,
            rng=random.Random(),
        )
        self._reset_panels()
        self.status_var.set("Labirinto aleatório solucionável gerado.")

    def _reset_panels(self) -> None:
        for panel in self._panels:
            panel.reset()

    def _on_mode_changed(self, _event: tk.Event[tk.Misc]) -> None:
        self._rebuild_panels()

    def _on_algorithm_changed(self, _event: tk.Event[tk.Misc]) -> None:
        self._clear_search()
        if self._panels:
            self._panels[0].title_var.set(self.algorithm_var.get())
        self.status_var.set("Estratégia individual alterada.")

    def _on_movement_changed(self, _event: tk.Event[tk.Misc]) -> None:
        self._clear_search()
        self.status_var.set(
            f"Modelo alterado para {self.movement_var.get().lower()}."
        )

    def _on_speed_changed(self, value: str) -> None:
        self.speed_label_var.set(f"{round(float(value))}%")

    def _on_density_changed(self, value: str) -> None:
        self.density_label_var.set(f"{round(float(value))}%")

    def _animation_delay(self) -> int:
        return max(5, round(205 - self.speed_var.get() * 2))

    def _on_close(self) -> None:
        self._cancel_execution()
        self.destroy()


def _format_milliseconds(value: float) -> str:
    if value < 1:
        return f"{value:.3f} ms".replace(".", ",")
    if value < 1000:
        return f"{value:.2f} ms".replace(".", ",")
    return f"{value / 1000:.2f} s".replace(".", ",")


def run() -> None:
    app = PathfindingApp()
    app.mainloop()
