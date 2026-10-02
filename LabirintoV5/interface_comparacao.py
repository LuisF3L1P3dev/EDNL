"""Interface Tkinter para acompanhar duas buscas no mesmo labirinto."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
import tkinter as tk

from busca_eventos import Celula, SearchEvent


@dataclass
class SearchPanel:
    """Estado visual e estado da animação de um algoritmo."""

    title: str
    route_color: str
    events_factory: Callable[[], Iterator[SearchEvent]]
    canvas: tk.Canvas
    status: tk.StringVar
    cell_items: dict[Celula, int] = field(default_factory=dict)
    frontier: set[Celula] = field(default_factory=set)
    visited: set[Celula] = field(default_factory=set)
    current: Celula | None = None
    path: dict[Celula, Celula] = field(default_factory=dict)
    generator: Iterator[SearchEvent] | None = None
    after_id: str | None = None
    expanded_count: int = 0
    done: bool = False
    found: bool | None = None
    cell_size: float = 0
    offset_x: float = 0
    offset_y: float = 0
    canvas_size: tuple[int, int] = (0, 0)


class ComparisonWindow:
    """Mostra exploração e rota final em dois canvases sincronizados pela UI."""

    DELAY_MS = 10
    GOAL: Celula = (1, 1)
    EMPTY_COLOR = "#ffffff"
    VISITED_COLOR = "#bfdbfe"
    FRONTIER_COLOR = "#fde68a"
    CURRENT_COLOR = "#fb923c"

    def __init__(self, labirinto, guloso_events, astar_events) -> None:
        self.labirinto = labirinto
        self.root = tk.Tk()
        self.root.title("Comparação")
        self.root.configure(bg="#f3f5f7")
        largura = min(1260, self.root.winfo_screenwidth() - 40)
        altura = min(760, self.root.winfo_screenheight() - 80)
        self.root.geometry(f"{largura}x{altura}")
        self.root.minsize(900, 600)
        self.root.protocol("WM_DELETE_WINDOW", self._fechar)

        self.started = False
        self.paused = False
        self.panels: list[SearchPanel] = []
        self._build_widgets(guloso_events, astar_events)
        self.root.update_idletasks()
        for panel in self.panels:
            self._draw_board(panel)

    def _build_widgets(self, guloso_events, astar_events) -> None:
        tk.Label(
            self.root,
            bg="#f3f5f7",
            fg="#17212b",
            font=("Arial", 17, "bold"),
        ).pack(pady=(10, 2))
        tk.Label(
            self.root,
            text=(
                "Exploradas: azul   -   Fronteira: amarelo   -   Atual: laranja   -   "
                "Início: I   -   Objetivo: F"
            ),
            bg="#f3f5f7",
            fg="#425466",
            font=("Arial", 10),
        ).pack(pady=(0, 8))

        controles = tk.Frame(self.root, bg="#f3f5f7")
        controles.pack(pady=(0, 0))
        self.start_button = tk.Button(
            controles, text="Iniciar", width=12, command=self.start
        )
        self.start_button.pack(side=tk.LEFT, padx=4)
        self.pause_button = tk.Button(
            controles,
            text="Pausar",
            width=12,
            state=tk.DISABLED,
            command=self.toggle_pause,
        )
        self.pause_button.pack(side=tk.LEFT, padx=4)
        self.restart_button = tk.Button(
            controles, text="Reiniciar", width=12, command=self.restart
        )
        self.restart_button.pack(side=tk.LEFT, padx=4)

        body = tk.Frame(self.root, bg="#f3f5f7")
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        panels = (
            ("Busca Gulosa (h)", "#dc2626", guloso_events),
            ("A* (g + h)", "#1d4ed8", astar_events),
        )
        for title, route_color, events_factory in panels:
            frame = tk.LabelFrame(
                body,
                text=title,
                bg="white",
                fg="#17212b",
                font=("Arial", 11, "bold"),
                padx=5,
                pady=5,
            )
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            status = tk.StringVar(value="Aguardando início")
            tk.Label(
                frame,
                textvariable=status,
                bg="white",
                fg="#425466",
                font=("Arial", 9),
            ).pack(fill=tk.X, pady=(0, 4))
            canvas = tk.Canvas(
                frame,
                width=560,
                height=520,
                bg="white",
                highlightthickness=0,
            )
            canvas.pack(fill=tk.BOTH, expand=True)

            panel = SearchPanel(
                title=title,
                route_color=route_color,
                events_factory=events_factory,
                canvas=canvas,
                status=status,
            )
            self.panels.append(panel)
            canvas.bind(
                "<Configure>",
                lambda event, current_panel=panel: self._on_canvas_configure(
                    current_panel, event.width, event.height
                ),
            )

    def _on_canvas_configure(
        self, panel: SearchPanel, width: int, height: int
    ) -> None:
        if width <= 1 or height <= 1:
            return
        if panel.canvas_size != (width, height):
            self._draw_board(panel)

    def _draw_board(self, panel: SearchPanel) -> None:
        canvas = panel.canvas
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        canvas.delete("all")
        panel.cell_items.clear()
        margin = 16
        panel.cell_size = min(
            (width - 2 * margin) / self.labirinto.cols,
            (height - 2 * margin) / self.labirinto.rows,
        )
        map_width = panel.cell_size * self.labirinto.cols
        map_height = panel.cell_size * self.labirinto.rows
        panel.offset_x = (width - map_width) / 2
        panel.offset_y = (height - map_height) / 2
        panel.canvas_size = (width, height)

        for cell in self.labirinto.grid:
            x1, y1, x2, y2 = self._cell_bounds(panel, cell)
            panel.cell_items[cell] = canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=self.EMPTY_COLOR,
                outline="",
            )

        for cell, walls in self.labirinto.maze_map.items():
            x1, y1, x2, y2 = self._cell_bounds(panel, cell)
            if walls["N"] == 0:
                canvas.create_line(x1, y1, x2, y1, fill="#263238", width=2)
            if walls["S"] == 0:
                canvas.create_line(x1, y2, x2, y2, fill="#263238", width=2)
            if walls["W"] == 0:
                canvas.create_line(x1, y1, x1, y2, fill="#263238", width=2)
            if walls["E"] == 0:
                canvas.create_line(x2, y1, x2, y2, fill="#263238", width=2)

        self._refresh_cells(panel, set(self.labirinto.grid))
        if panel.done and panel.found:
            self._draw_route(panel)
        self._draw_markers(panel)

    def _cell_bounds(
        self, panel: SearchPanel, cell: Celula
    ) -> tuple[float, float, float, float]:
        row, column = cell
        x1 = panel.offset_x + (column - 1) * panel.cell_size
        y1 = panel.offset_y + (row - 1) * panel.cell_size
        return x1, y1, x1 + panel.cell_size, y1 + panel.cell_size

    def _cell_center(self, panel: SearchPanel, cell: Celula) -> tuple[float, float]:
        x1, y1, x2, y2 = self._cell_bounds(panel, cell)
        return (x1 + x2) / 2, (y1 + y2) / 2

    def _refresh_cells(self, panel: SearchPanel, cells: set[Celula]) -> None:
        for cell in cells:
            item = panel.cell_items.get(cell)
            if item is None:
                continue
            if cell == panel.current:
                color = self.CURRENT_COLOR
            elif cell in panel.frontier:
                color = self.FRONTIER_COLOR
            elif cell in panel.visited:
                color = self.VISITED_COLOR
            else:
                color = self.EMPTY_COLOR
            panel.canvas.itemconfigure(item, fill=color)

    def _draw_route(self, panel: SearchPanel) -> None:
        panel.canvas.delete("route")
        width = max(3, panel.cell_size * 0.2)
        for cell, next_cell in panel.path.items():
            x1, y1 = self._cell_center(panel, cell)
            x2, y2 = self._cell_center(panel, next_cell)
            panel.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill=panel.route_color,
                width=width,
                capstyle=tk.ROUND,
                tags=("route",),
            )

    def _draw_markers(self, panel: SearchPanel) -> None:
        start: Celula = (self.labirinto.rows, self.labirinto.cols)
        for cell, color, label in (
            (start, "#198754", "I"),
            (self.GOAL, "#e89b24", "F"),
        ):
            x, y = self._cell_center(panel, cell)
            radius = panel.cell_size * 0.27
            panel.canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill=color,
                outline="white",
                width=1,
            )
            panel.canvas.create_text(
                x,
                y,
                text=label,
                fill="white",
                font=("Arial", max(8, int(panel.cell_size * 0.32)), "bold"),
            )

    def start(self) -> None:
        if self.started:
            return
        self.started = True
        self.paused = False
        self.start_button.configure(state=tk.DISABLED)
        self.pause_button.configure(state=tk.NORMAL, text="Pausar")
        for panel in self.panels:
            panel.generator = panel.events_factory()
            self._schedule(panel, self.DELAY_MS)

    def toggle_pause(self) -> None:
        if not self.started:
            return
        self.paused = not self.paused
        if self.paused:
            for panel in self.panels:
                self._cancel_pending(panel)
            self.pause_button.configure(text="Continuar")
            return

        self.pause_button.configure(text="Pausar")
        for panel in self.panels:
            if not panel.done:
                self._schedule(panel, 0)

    def restart(self) -> None:
        for panel in self.panels:
            self._cancel_pending(panel)
            panel.generator = None
            panel.frontier.clear()
            panel.visited.clear()
            panel.current = None
            panel.path.clear()
            panel.expanded_count = 0
            panel.done = False
            panel.found = None
            panel.status.set("Aguardando início")
            self._draw_board(panel)

        self.started = False
        self.paused = False
        self.start_button.configure(state=tk.NORMAL)
        self.pause_button.configure(state=tk.DISABLED, text="Pausar")

    def _schedule(self, panel: SearchPanel, delay: int) -> None:
        if self.paused or panel.done or panel.generator is None:
            return
        panel.after_id = self.root.after(delay, lambda: self._advance(panel))

    def _advance(self, panel: SearchPanel) -> None:
        panel.after_id = None
        if self.paused or panel.done or panel.generator is None:
            return
        try:
            event = next(panel.generator)
        except StopIteration:
            event = SearchEvent(
                current=None,
                frontier=frozenset(),
                visited=frozenset(panel.visited),
                expanded_count=panel.expanded_count,
                done=True,
                found=False,
                path={},
            )

        self._apply_event(panel, event)
        if not event.done:
            self._schedule(panel, self.DELAY_MS)
        elif all(current.done for current in self.panels):
            self.pause_button.configure(state=tk.DISABLED)

    def _apply_event(self, panel: SearchPanel, event: SearchEvent) -> None:
        new_frontier = set(event.frontier)
        new_visited = set(event.visited)
        changed = (panel.frontier ^ new_frontier) | (panel.visited ^ new_visited)
        if panel.current is not None:
            changed.add(panel.current)
        if event.current is not None:
            changed.add(event.current)

        panel.frontier = new_frontier
        panel.visited = new_visited
        panel.current = event.current
        panel.expanded_count = event.expanded_count
        self._refresh_cells(panel, changed)

        if event.done:
            panel.done = True
            panel.found = event.found
            panel.path = event.path or {}
            if panel.found:
                self._draw_route(panel)

        if event.done and panel.found is False:
            route_status = "sem rota"
        elif event.done:
            route_status = f"{len(panel.path)} passos"
        else:
            route_status = "buscando"
        panel.status.set(
            f"Expansões: {panel.expanded_count}  |  "
            f"Fronteira: {len(panel.frontier)}  |  Rota: {route_status}"
        )

    def _cancel_pending(self, panel: SearchPanel) -> None:
        if panel.after_id is not None:
            try:
                self.root.after_cancel(panel.after_id)
            except tk.TclError:
                pass
            panel.after_id = None

    def _fechar(self) -> None:
        for panel in self.panels:
            self._cancel_pending(panel)
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
