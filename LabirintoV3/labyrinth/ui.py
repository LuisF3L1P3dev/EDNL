"""Interface Pygame do laboratório de buscas."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Callable

import pygame

from .model import Grid, Position
from .scenarios import (
    MAX_COLS,
    MAX_ROWS,
    MIN_COLS,
    MIN_ROWS,
    SCENARIOS,
    SCENARIO_LABELS,
    create_empty_grid,
    create_scenario,
)
from .search import HeuristicType, SearchAlgorithm, SearchMetrics
from .simulation import Simulation, SimulationState


WINDOW_MIN = (1180, 820)
WINDOW_INITIAL = (1380, 820)
FPS = 60

BG = (11, 16, 29)
PANEL = (20, 29, 49)
PANEL_LIGHT = (28, 40, 65)
BORDER = (54, 71, 101)
TEXT = (229, 236, 248)
MUTED = (143, 158, 184)
CYAN = (42, 211, 226)
BLUE = (68, 126, 255)
GREEN = (57, 211, 129)
YELLOW = (250, 196, 72)
RED = (245, 91, 104)
PURPLE = (177, 112, 255)
WALL = (43, 55, 76)
GRID_LINE = (42, 56, 80)
CELL = (16, 24, 40)


@dataclass(slots=True)
class Button:
    rect: pygame.Rect
    label: str
    action: str
    active: bool = False
    enabled: bool = True
    accent: tuple[int, int, int] = BLUE


class App:
    def __init__(self) -> None:
        pygame.init()
        self.window = pygame.Window(
            "Labirinto V3 — Busca Gulosa vs. A*",
            size=WINDOW_INITIAL,
            resizable=True,
        )
        self.window.minimum_size = WINDOW_MIN
        self.screen = self.window.get_surface()
        self.clock = pygame.time.Clock()
        self.fonts = {
            "title": pygame.font.SysFont("segoeui", 28, bold=True),
            "subtitle": pygame.font.SysFont("segoeui", 15),
            "heading": pygame.font.SysFont("segoeui", 18, bold=True),
            "body": pygame.font.SysFont("segoeui", 15),
            "small": pygame.font.SysFont("segoeui", 13),
            "metric": pygame.font.SysFont("consolas", 18, bold=True),
            "cell": pygame.font.SysFont("consolas", 11, bold=True),
        }
        self.mode = "Individual"
        self.algorithm = SearchAlgorithm.ASTAR
        self.heuristic = HeuristicType.MANHATTAN
        self.scenario_index = 0
        self.grid = create_scenario(SCENARIOS[self.scenario_index])
        self.simulations = {
            SearchAlgorithm.GREEDY: Simulation(SearchAlgorithm.GREEDY),
            SearchAlgorithm.ASTAR: Simulation(SearchAlgorithm.ASTAR),
        }
        for simulation in self.simulations.values():
            simulation.reset(self.grid)
        self.history: dict[SearchAlgorithm, SearchMetrics] = {}
        self.tool = "Parede"
        self.size_dialog_open = False
        self.size_inputs = {
            "rows": str(self.grid.rows),
            "cols": str(self.grid.cols),
        }
        self.active_size_field = "rows"
        self.replace_size_value = True
        self.size_error = ""
        self.size_field_rects: dict[str, pygame.Rect] = {}
        self.size_apply_rect = pygame.Rect(0, 0, 0, 0)
        self.size_cancel_rect = pygame.Rect(0, 0, 0, 0)
        self.speeds = (2, 5, 10, 20, 40, 80)
        self.speed_index = 3
        self.step_accumulator = 0.0
        self.buttons: list[Button] = []
        self.grid_views: list[tuple[pygame.Rect, SearchAlgorithm]] = []
        self.notice = "Desenhe obstáculos ou escolha um cenário para começar."
        self.running = True

    def run(self) -> None:
        while self.running:
            delta = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(delta)
            self._draw()
            self.window.flip()
        self.window.destroy()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type in (
                pygame.VIDEORESIZE,
                pygame.WINDOWRESIZED,
                pygame.WINDOWSIZECHANGED,
            ):
                self.screen = self.window.get_surface()
            elif self.size_dialog_open:
                if event.type == pygame.KEYDOWN:
                    self._handle_size_key(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_size_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self._click_button(event.pos):
                    continue
                if event.button in (1, 3):
                    self._edit_at(event.pos, erase=event.button == 3)
            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[0]:
                    self._edit_at(event.pos, erase=False)
                elif event.buttons[2]:
                    self._edit_at(event.pos, erase=True)

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_SPACE:
            self._run_or_pause()
        elif key == pygame.K_r:
            self._reset_visualization()
        elif key == pygame.K_c:
            self._clear_grid()
        elif key == pygame.K_TAB:
            self._change_mode()
        elif key == pygame.K_g:
            self._select_algorithm(SearchAlgorithm.GREEDY)
        elif key == pygame.K_a:
            self._select_algorithm(SearchAlgorithm.ASTAR)
        elif key == pygame.K_1:
            self.tool = "Parede"
        elif key == pygame.K_2:
            self.tool = "Ponto A"
        elif key == pygame.K_3:
            self.tool = "Ponto B"
        elif key in (pygame.K_4, pygame.K_e):
            self.tool = "Borracha"

    def _handle_size_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            self.size_dialog_open = False
            self.size_error = ""
        elif event.key == pygame.K_TAB:
            self.active_size_field = (
                "cols" if self.active_size_field == "rows" else "rows"
            )
            self.replace_size_value = True
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._apply_custom_size()
        elif event.key == pygame.K_BACKSPACE:
            value = self.size_inputs[self.active_size_field]
            self.size_inputs[self.active_size_field] = (
                "" if self.replace_size_value else value[:-1]
            )
            self.replace_size_value = False
            self.size_error = ""
        elif event.unicode.isdigit():
            value = "" if self.replace_size_value else self.size_inputs[self.active_size_field]
            if len(value) < 3:
                self.size_inputs[self.active_size_field] = value + event.unicode
                self.replace_size_value = False
                self.size_error = ""

    def _handle_size_click(self, position: tuple[int, int]) -> None:
        for field, rect in self.size_field_rects.items():
            if rect.collidepoint(position):
                self.active_size_field = field
                self.replace_size_value = True
                return
        if self.size_apply_rect.collidepoint(position):
            self._apply_custom_size()
        elif self.size_cancel_rect.collidepoint(position):
            self.size_dialog_open = False
            self.size_error = ""

    def _open_size_dialog(self) -> None:
        if not self._can_edit():
            self.notice = "Reinicie a execução antes de alterar o tamanho."
            return
        self._sync_size_inputs()
        self.active_size_field = "rows"
        self.replace_size_value = True
        self.size_error = ""
        self.size_dialog_open = True

    def _apply_custom_size(self) -> None:
        if not self.size_inputs["rows"] or not self.size_inputs["cols"]:
            self.size_error = "Preencha os dois campos numéricos."
            return
        try:
            rows = int(self.size_inputs["rows"])
            cols = int(self.size_inputs["cols"])
            name = SCENARIOS[self.scenario_index]
            seed = random.randrange(1_000_000) if name == "Aleatório" else None
            grid = create_scenario(name, seed=seed, rows=rows, cols=cols)
        except (TypeError, ValueError) as error:
            self.size_error = str(error) or "Informe linhas e colunas válidas."
            return
        self.grid = grid
        self.size_dialog_open = False
        self._map_changed(
            f"Cenário “{name}” regenerado em {rows} × {cols}."
        )

    def _cycle_heuristic(self) -> None:
        if not self._can_edit():
            self.notice = "Reinicie a execução antes de trocar a heurística."
            return
        self.heuristic = (
            HeuristicType.EUCLIDEAN
            if self.heuristic is HeuristicType.MANHATTAN
            else HeuristicType.MANHATTAN
        )
        for simulation in self.simulations.values():
            simulation.heuristic = self.heuristic
            simulation.reset(self.grid)
        self.history.clear()
        self.notice = f"Heurística {self.heuristic.value} selecionada."

    def _sync_size_inputs(self) -> None:
        self.size_inputs["rows"] = str(self.grid.rows)
        self.size_inputs["cols"] = str(self.grid.cols)

    def _update(self, delta: float) -> None:
        active = self._visible_simulations()
        if not any(simulation.active for simulation in active):
            self._capture_results()
            return

        self.step_accumulator += delta
        interval = 1.0 / self.speeds[self.speed_index]
        iterations = 0
        while self.step_accumulator >= interval and iterations < 12:
            self.step_accumulator -= interval
            iterations += 1
            for simulation in active:
                if simulation.active:
                    simulation.advance()
        self._capture_results()

    def _capture_results(self) -> None:
        for algorithm, simulation in self.simulations.items():
            if simulation.terminal:
                self.history[algorithm] = simulation.metrics
        visible = self._visible_simulations()
        if visible and all(simulation.terminal for simulation in visible):
            if self.mode == "Duelo":
                greedy = self.simulations[SearchAlgorithm.GREEDY].metrics
                astar = self.simulations[SearchAlgorithm.ASTAR].metrics
                if greedy.path_cost is None or astar.path_cost is None:
                    self.notice = "Duelo encerrado: não existe caminho válido até o alvo."
                elif greedy.path_cost == astar.path_cost:
                    self.notice = f"Duelo encerrado: empate em {astar.path_cost} passos."
                else:
                    saved = greedy.path_cost - astar.path_cost
                    self.notice = f"Duelo encerrado: o A* economizou {saved} passo(s)."
            else:
                simulation = visible[0]
                if simulation.metrics.path_cost is None:
                    self.notice = "Busca encerrada: não existe caminho até o ponto B."
                else:
                    self.notice = (
                        f"Rota concluída com custo {simulation.metrics.path_cost} "
                        f"em {simulation.metrics.path_steps} passos."
                    )

    def _visible_simulations(self) -> list[Simulation]:
        if self.mode == "Duelo":
            return [self.simulations[SearchAlgorithm.GREEDY], self.simulations[SearchAlgorithm.ASTAR]]
        return [self.simulations[self.algorithm]]

    def _run_or_pause(self) -> None:
        visible = self._visible_simulations()
        if any(sim.state is SimulationState.PAUSED for sim in visible):
            for simulation in visible:
                simulation.resume()
            self.notice = "Simulação retomada."
        elif any(sim.active for sim in visible):
            for simulation in visible:
                simulation.pause()
            self.notice = "Simulação pausada."
        else:
            algorithms = (
                (SearchAlgorithm.GREEDY, SearchAlgorithm.ASTAR)
                if self.mode == "Duelo" else (self.algorithm,)
            )
            for algorithm in algorithms:
                self.simulations[algorithm].start(self.grid, self.heuristic)
                self.history.pop(algorithm, None)
            self.step_accumulator = 0.0
            self.notice = "Busca em andamento: fronteira e visitados são atualizados em tempo real."

    def _reset_visualization(self) -> None:
        for simulation in self.simulations.values():
            simulation.reset(self.grid)
        self.history.clear()
        self.notice = "Visualização reiniciada; o mapa foi preservado."

    def _clear_grid(self) -> None:
        if not self._can_edit():
            self.notice = "Pause não libera a edição; reinicie a simulação primeiro."
            return
        self.grid = create_empty_grid(self.grid.rows, self.grid.cols)
        self.scenario_index = 0
        self._map_changed("Grade limpa.")

    def _change_mode(self) -> None:
        if not self._can_edit():
            self.notice = "Reinicie a execução antes de trocar o modo."
            return
        self.mode = "Duelo" if self.mode == "Individual" else "Individual"
        self._reset_visualization()
        self.notice = f"Modo {self.mode} selecionado."

    def _select_algorithm(self, algorithm: SearchAlgorithm) -> None:
        if self.mode != "Individual" or not self._can_edit():
            return
        self.algorithm = algorithm
        self.notice = f"{algorithm.value} selecionado."

    def _cycle_scenario(self) -> None:
        if not self._can_edit():
            self.notice = "Reinicie a execução antes de trocar o cenário."
            return
        self.scenario_index = (self.scenario_index + 1) % len(SCENARIOS)
        name = SCENARIOS[self.scenario_index]
        seed = random.randrange(1_000_000) if name == "Aleatório" else None
        self.grid = create_scenario(
            name,
            seed=seed,
            rows=self.grid.rows,
            cols=self.grid.cols,
        )
        self._map_changed(f"Cenário “{name}” carregado.")

    def _map_changed(self, message: str) -> None:
        for simulation in self.simulations.values():
            simulation.reset(self.grid)
        self.history.clear()
        self.step_accumulator = 0.0
        self._sync_size_inputs()
        self.notice = message

    def _can_edit(self) -> bool:
        return all(
            simulation.state not in (
                SimulationState.SEARCHING,
                SimulationState.WALKING,
                SimulationState.PAUSED,
            )
            for simulation in self.simulations.values()
        )

    def _click_button(self, position: tuple[int, int]) -> bool:
        for button in self.buttons:
            if button.enabled and button.rect.collidepoint(position):
                actions: dict[str, Callable[[], None]] = {
                    "mode": self._change_mode,
                    "algorithm": lambda: self._select_algorithm(
                        SearchAlgorithm.GREEDY
                        if self.algorithm is SearchAlgorithm.ASTAR else SearchAlgorithm.ASTAR
                    ),
                    "scenario": self._cycle_scenario,
                    "heuristic": self._cycle_heuristic,
                    "size": self._open_size_dialog,
                    "wall": lambda: setattr(self, "tool", "Parede"),
                    "start": lambda: setattr(self, "tool", "Ponto A"),
                    "goal": lambda: setattr(self, "tool", "Ponto B"),
                    "eraser": lambda: setattr(self, "tool", "Borracha"),
                    "run": self._run_or_pause,
                    "reset": self._reset_visualization,
                    "clear": self._clear_grid,
                    "slower": lambda: setattr(self, "speed_index", max(0, self.speed_index - 1)),
                    "faster": lambda: setattr(
                        self, "speed_index", min(len(self.speeds) - 1, self.speed_index + 1)
                    ),
                }
                actions[button.action]()
                return True
        return False

    def _edit_at(self, mouse: tuple[int, int], erase: bool) -> None:
        if not self._can_edit():
            return
        position = self._position_at(mouse)
        if position is None:
            return
        changed = False
        if erase or self.tool == "Borracha":
            changed = self.grid.set_wall(position, False)
        elif self.tool == "Parede":
            changed = self.grid.set_wall(position, True)
        elif self.tool == "Ponto A":
            changed = self.grid.set_start(position)
        elif self.tool == "Ponto B":
            changed = self.grid.set_goal(position)
        if changed:
            self._map_changed("Mapa alterado; resultados anteriores foram limpos.")

    def _position_at(self, mouse: tuple[int, int]) -> Position | None:
        for rect, _ in self.grid_views:
            if rect.collidepoint(mouse):
                cell_size = min(rect.width // self.grid.cols, rect.height // self.grid.rows)
                col = (mouse[0] - rect.x) // cell_size
                row = (mouse[1] - rect.y) // cell_size
                candidate = int(row), int(col)
                return candidate if self.grid.in_bounds(candidate) else None
        return None

    def _draw(self) -> None:
        self.screen.fill(BG)
        width, height = self.screen.get_size()
        sidebar_width = 330
        sidebar_x = width - sidebar_width - 20
        content = pygame.Rect(20, 92, sidebar_x - 34, height - 118)
        sidebar = pygame.Rect(sidebar_x, 92, sidebar_width, height - 112)
        self._draw_header()
        self.grid_views.clear()
        if self.mode == "Individual":
            self._draw_individual(content)
        else:
            self._draw_duel(content)
        self._draw_sidebar(sidebar)
        if self.size_dialog_open:
            self._draw_size_dialog()
        else:
            self._draw_hover_tooltip()

    def _draw_header(self) -> None:
        self.screen.blit(self.fonts["title"].render("LABIRINTO V3", True, TEXT), (22, 15))
        subtitle = "Laboratório interativo de busca informada  •  Gulosa vs. A*"
        self.screen.blit(self.fonts["subtitle"].render(subtitle, True, MUTED), (23, 54))
        pygame.draw.circle(self.screen, CYAN, (self.screen.get_width() - 38, 33), 8)

    def _draw_individual(self, area: pygame.Rect) -> None:
        simulation = self.simulations[self.algorithm]
        self._panel(area)
        label = f"EXECUÇÃO INDIVIDUAL  /  {self.algorithm.value.upper()}"
        self.screen.blit(self.fonts["small"].render(label, True, CYAN), (area.x + 16, area.y + 13))
        grid_area = pygame.Rect(area.x + 16, area.y + 44, area.width - 32, area.height - 60)
        grid_rect = self._fit_grid(grid_area)
        self.grid_views.append((grid_rect, self.algorithm))
        self._draw_grid(grid_rect, simulation)

    def _draw_duel(self, area: pygame.Rect) -> None:
        self._panel(area)
        gap = 16
        half = (area.width - gap - 32) // 2
        for index, algorithm in enumerate((SearchAlgorithm.GREEDY, SearchAlgorithm.ASTAR)):
            x = area.x + 16 + index * (half + gap)
            title_color = YELLOW if algorithm is SearchAlgorithm.GREEDY else CYAN
            self.screen.blit(
                self.fonts["heading"].render(algorithm.value, True, title_color),
                (x, area.y + 15),
            )
            simulation = self.simulations[algorithm]
            state_text = self.fonts["small"].render(simulation.state.value, True, MUTED)
            self.screen.blit(state_text, (x + half - state_text.get_width(), area.y + 20))
            grid_area = pygame.Rect(x, area.y + 54, half, area.height - 72)
            grid_rect = self._fit_grid(grid_area)
            self.grid_views.append((grid_rect, algorithm))
            self._draw_grid(grid_rect, simulation)

    def _fit_grid(self, area: pygame.Rect) -> pygame.Rect:
        size = max(2, min(area.width // self.grid.cols, area.height // self.grid.rows))
        width, height = size * self.grid.cols, size * self.grid.rows
        return pygame.Rect(
            area.x + (area.width - width) // 2,
            area.y + (area.height - height) // 2,
            width,
            height,
        )

    def _draw_grid(self, rect: pygame.Rect, simulation: Simulation) -> None:
        cell_size = rect.width // self.grid.cols
        path_cells = set(simulation.path)
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                position = row, col
                cell_rect = pygame.Rect(
                    rect.x + col * cell_size,
                    rect.y + row * cell_size,
                    cell_size,
                    cell_size,
                )
                color = CELL
                if position in self.grid.walls:
                    color = WALL
                elif position in simulation.explored:
                    color = (37, 74, 102)
                elif position in simulation.frontier:
                    color = (56, 49, 105)
                if position in path_cells:
                    color = (42, 112, 94)
                pygame.draw.rect(self.screen, color, cell_rect)
                pygame.draw.rect(self.screen, GRID_LINE, cell_rect, 1)

        if simulation.current is not None and simulation.state is SimulationState.SEARCHING:
            self._cell_outline(rect, simulation.current, YELLOW, 2)
        self._draw_marker(rect, self.grid.start, "A", GREEN)
        self._draw_marker(rect, self.grid.goal, "B", RED)
        if simulation.agent_position not in (None, self.grid.start):
            self._draw_agent(rect, simulation.agent_position)
        pygame.draw.rect(self.screen, BORDER, rect, 2, border_radius=3)

    def _cell_outline(
        self, rect: pygame.Rect, position: Position, color: tuple[int, int, int], width: int
    ) -> None:
        size = rect.width // self.grid.cols
        row, col = position
        target = pygame.Rect(rect.x + col * size, rect.y + row * size, size, size)
        pygame.draw.rect(self.screen, color, target, width)

    def _draw_marker(
        self, rect: pygame.Rect, position: Position, label: str, color: tuple[int, int, int]
    ) -> None:
        size = rect.width // self.grid.cols
        row, col = position
        center = rect.x + col * size + size // 2, rect.y + row * size + size // 2
        pygame.draw.circle(self.screen, color, center, max(4, size // 2 - 2))
        if size >= 14:
            text = self.fonts["cell"].render(label, True, BG)
            self.screen.blit(text, text.get_rect(center=center))

    def _draw_agent(self, rect: pygame.Rect, position: Position) -> None:
        size = rect.width // self.grid.cols
        row, col = position
        center = rect.x + col * size + size // 2, rect.y + row * size + size // 2
        radius = max(4, size // 2 - 2)
        if position == self.grid.goal:
            pygame.draw.circle(self.screen, GREEN, center, radius, 2)
        else:
            pygame.draw.circle(self.screen, GREEN, center, radius)
            pygame.draw.circle(self.screen, TEXT, center, radius, 2)

    def _draw_sidebar(self, rect: pygame.Rect) -> None:
        self._panel(rect)
        self.buttons.clear()
        x, y = rect.x + 16, rect.y + 14
        inner_width = rect.width - 32

        self._section_label("CONFIGURAÇÃO", x, y)
        y += 27
        half_width = (inner_width - 6) // 2
        self._add_button(
            x,
            y,
            half_width,
            f"Modo: {self.mode}",
            "mode",
            active=True,
            enabled=self._can_edit(),
        )
        self._add_button(
            x + half_width + 6,
            y,
            inner_width - half_width - 6,
            f"H: {self.heuristic.value}",
            "heuristic",
            active=True,
            enabled=self._can_edit(),
            accent=PURPLE,
        )
        y += 39
        algorithm_enabled = self.mode == "Individual"
        self._add_button(
            x, y, inner_width, f"Estratégia: {self.algorithm.value}", "algorithm",
            active=algorithm_enabled, enabled=algorithm_enabled,
            accent=CYAN if self.algorithm is SearchAlgorithm.ASTAR else YELLOW,
        )
        y += 39
        scenario = SCENARIOS[self.scenario_index]
        scenario_width = 186
        self._add_button(
            x,
            y,
            scenario_width,
            f"Cenário: {SCENARIO_LABELS[scenario]}",
            "scenario",
            enabled=self._can_edit(),
        )
        self._add_button(
            x + scenario_width + 6,
            y,
            inner_width - scenario_width - 6,
            f"{self.grid.rows} × {self.grid.cols}",
            "size",
            enabled=self._can_edit(),
            accent=CYAN,
        )
        y += 49

        self._section_label("FERRAMENTAS DE EDIÇÃO", x, y)
        y += 27
        tool_width = (inner_width - 18) // 4
        for index, (label, action) in enumerate(
            (
                ("Parede", "wall"),
                ("Ponto A", "start"),
                ("Ponto B", "goal"),
                ("Borracha", "eraser"),
            )
        ):
            self._add_button(
                x + index * (tool_width + 6), y, tool_width, label, action,
                active=self.tool == label, enabled=self._can_edit(), accent=PURPLE,
            )
        y += 49

        self._section_label("SIMULAÇÃO", x, y)
        y += 27
        visible = self._visible_simulations()
        paused = any(sim.state is SimulationState.PAUSED for sim in visible)
        active = any(sim.active for sim in visible)
        run_label = "Continuar" if paused else "Pausar" if active else "Executar"
        self._add_button(x, y, 142, run_label, "run", active=True, accent=GREEN)
        self._add_button(x + 150, y, inner_width - 150, "Reiniciar", "reset")
        y += 39
        self._add_button(x, y, 42, "−", "slower", enabled=self.speed_index > 0)
        speed_text = f"{self.speeds[self.speed_index]} passos/s"
        speed_surface = self.fonts["body"].render(speed_text, True, TEXT)
        self.screen.blit(speed_surface, speed_surface.get_rect(center=(x + inner_width // 2, y + 16)))
        self._add_button(x + inner_width - 42, y, 42, "+", "faster", enabled=self.speed_index < len(self.speeds) - 1)
        y += 42
        self._add_button(x, y, inner_width, "Limpar mapa", "clear", enabled=self._can_edit())
        y += 49

        self._section_label("TELEMETRIA", x, y)
        y += 24
        if self.mode == "Individual":
            y = self._draw_metrics_card(x, y, inner_width, self.algorithm, self.simulations[self.algorithm])
            y += 8
            self._draw_history(x, y, inner_width)
        else:
            y = self._draw_metrics_card(x, y, inner_width, SearchAlgorithm.GREEDY, self.simulations[SearchAlgorithm.GREEDY], compact=True)
            y += 7
            y = self._draw_metrics_card(x, y, inner_width, SearchAlgorithm.ASTAR, self.simulations[SearchAlgorithm.ASTAR], compact=True)

        self._draw_notice(rect)

    def _draw_metrics_card(
        self,
        x: int,
        y: int,
        width: int,
        algorithm: SearchAlgorithm,
        simulation: Simulation,
        compact: bool = False,
    ) -> int:
        height = 91 if compact else 112
        card = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, PANEL_LIGHT, card, border_radius=8)
        accent = YELLOW if algorithm is SearchAlgorithm.GREEDY else CYAN
        pygame.draw.rect(self.screen, accent, (x, y, 4, height), border_radius=3)
        title = f"{algorithm.value}  •  {simulation.state.value}"
        self.screen.blit(self.fonts["small"].render(title, True, accent), (x + 12, y + 9))
        metrics = simulation.metrics
        values = (
            ("Tempo", f"{metrics.elapsed_ms:.3f} ms"),
            ("Explorados", str(metrics.nodes_explored)),
            ("Fronteira", str(metrics.frontier_size)),
            (
                "Custo/passos",
                "—" if metrics.path_cost is None else f"{metrics.path_cost}/{metrics.path_steps}",
            ),
        )
        columns = 2
        for index, (label, value) in enumerate(values):
            row, col = divmod(index, columns)
            item_x = x + 12 + col * (width // 2)
            item_y = y + 34 + row * 30
            label_surface = self.fonts["small"].render(label, True, MUTED)
            self.screen.blit(label_surface, (item_x, item_y))
            value_surface = self.fonts["metric"].render(value, True, TEXT)
            self.screen.blit(value_surface, (item_x + label_surface.get_width() + 7, item_y - 3))
        return y + height

    def _draw_history(self, x: int, y: int, width: int) -> None:
        self.screen.blit(self.fonts["small"].render("ÚLTIMOS RESULTADOS NO MAPA", True, MUTED), (x, y))
        y += 22
        for algorithm in (SearchAlgorithm.GREEDY, SearchAlgorithm.ASTAR):
            metrics = self.history.get(algorithm)
            name = "Gulosa" if algorithm is SearchAlgorithm.GREEDY else "A*"
            value = "sem execução"
            if metrics is not None:
                cost = "—" if metrics.path_cost is None else str(metrics.path_cost)
                value = f"custo {cost}  •  {metrics.nodes_explored} nós"
            self.screen.blit(self.fonts["small"].render(name, True, TEXT), (x, y))
            rendered = self.fonts["small"].render(value, True, MUTED)
            self.screen.blit(rendered, (x + width - rendered.get_width(), y))
            y += 21

    def _draw_notice(self, sidebar: pygame.Rect) -> None:
        box = pygame.Rect(sidebar.x + 16, sidebar.bottom - 79, sidebar.width - 32, 62)
        pygame.draw.rect(self.screen, (15, 23, 39), box, border_radius=7)
        lines = self._wrap_text(self.notice, box.width - 18, self.fonts["small"])
        for index, line in enumerate(lines[:3]):
            self.screen.blit(
                self.fonts["small"].render(line, True, MUTED),
                (box.x + 9, box.y + 8 + index * 16),
            )

    def _draw_hover_tooltip(self) -> None:
        mouse = pygame.mouse.get_pos()
        position = self._position_at(mouse)
        if position is None:
            return
        simulation: Simulation | None = None
        for rect, algorithm in self.grid_views:
            if rect.collidepoint(mouse):
                simulation = self.simulations[algorithm]
                break
        if simulation is None:
            return
        g = simulation.g_values.get(position)
        h = simulation.h_values.get(position)
        score = simulation.scores.get(position)
        values = f"({position[0]}, {position[1]})"
        if g is not None:
            symbol = "h" if simulation.algorithm is SearchAlgorithm.GREEDY else "f"
            values += (
                f"   g={g}  h={self._format_search_value(h)}"
                f"  {symbol}={self._format_search_value(score)}"
            )
        rendered = self.fonts["small"].render(values, True, TEXT)
        box = rendered.get_rect()
        box.inflate_ip(16, 10)
        box.x = min(mouse[0] + 14, self.screen.get_width() - box.width - 6)
        box.y = min(mouse[1] + 14, self.screen.get_height() - box.height - 6)
        pygame.draw.rect(self.screen, (7, 12, 22), box, border_radius=5)
        pygame.draw.rect(self.screen, BORDER, box, 1, border_radius=5)
        self.screen.blit(rendered, (box.x + 8, box.y + 5))

    def _draw_size_dialog(self) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((3, 7, 15, 190))
        self.screen.blit(overlay, (0, 0))

        dialog = pygame.Rect(0, 0, 440, 270)
        dialog.center = self.screen.get_rect().center
        pygame.draw.rect(self.screen, PANEL, dialog, border_radius=12)
        pygame.draw.rect(self.screen, CYAN, dialog, 1, border_radius=12)

        self.screen.blit(
            self.fonts["heading"].render("Tamanho personalizado", True, TEXT),
            (dialog.x + 24, dialog.y + 20),
        )
        help_text = "O cenário atual será regenerado no novo tamanho."
        self.screen.blit(
            self.fonts["small"].render(help_text, True, MUTED),
            (dialog.x + 24, dialog.y + 49),
        )

        field_width = 184
        field_y = dialog.y + 98
        self.size_field_rects = {
            "rows": pygame.Rect(dialog.x + 24, field_y, field_width, 42),
            "cols": pygame.Rect(dialog.x + 232, field_y, field_width, 42),
        }
        labels = {
            "rows": f"Linhas ({MIN_ROWS}–{MAX_ROWS})",
            "cols": f"Colunas ({MIN_COLS}–{MAX_COLS})",
        }
        for field, field_rect in self.size_field_rects.items():
            active = field == self.active_size_field
            self.screen.blit(
                self.fonts["small"].render(labels[field], True, MUTED),
                (field_rect.x, field_rect.y - 20),
            )
            pygame.draw.rect(self.screen, (12, 20, 35), field_rect, border_radius=6)
            pygame.draw.rect(
                self.screen,
                CYAN if active else BORDER,
                field_rect,
                2 if active else 1,
                border_radius=6,
            )
            value = self.size_inputs[field]
            value_surface = self.fonts["metric"].render(value, True, TEXT)
            self.screen.blit(
                value_surface,
                value_surface.get_rect(midleft=(field_rect.x + 12, field_rect.centery)),
            )
            if active and pygame.time.get_ticks() % 1000 < 550:
                cursor_x = field_rect.x + 13 + value_surface.get_width()
                pygame.draw.line(
                    self.screen,
                    CYAN,
                    (cursor_x, field_rect.y + 10),
                    (cursor_x, field_rect.bottom - 10),
                    2,
                )

        message = self.size_error or "Tab alterna os campos • Enter aplica • Esc cancela"
        message_color = RED if self.size_error else MUTED
        self.screen.blit(
            self.fonts["small"].render(message, True, message_color),
            (dialog.x + 24, dialog.y + 154),
        )

        self.size_cancel_rect = pygame.Rect(dialog.x + 160, dialog.bottom - 54, 116, 34)
        self.size_apply_rect = pygame.Rect(dialog.x + 284, dialog.bottom - 54, 132, 34)
        self._draw_dialog_button(self.size_cancel_rect, "Cancelar", BORDER)
        self._draw_dialog_button(self.size_apply_rect, "Aplicar", GREEN)

    def _draw_dialog_button(
        self,
        rect: pygame.Rect,
        label: str,
        accent: tuple[int, int, int],
    ) -> None:
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = PANEL_LIGHT if not hovered else tuple(
            min(255, channel + 14) for channel in PANEL_LIGHT
        )
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, accent, rect, 1, border_radius=6)
        rendered = self.fonts["small"].render(label, True, TEXT)
        self.screen.blit(rendered, rendered.get_rect(center=rect.center))

    def _add_button(
        self,
        x: int,
        y: int,
        width: int,
        label: str,
        action: str,
        active: bool = False,
        enabled: bool = True,
        accent: tuple[int, int, int] = BLUE,
    ) -> None:
        button = Button(pygame.Rect(x, y, width, 32), label, action, active, enabled, accent)
        self.buttons.append(button)
        mouse_over = button.rect.collidepoint(pygame.mouse.get_pos())
        color = PANEL_LIGHT
        if active:
            color = tuple(max(0, channel // 3) for channel in accent)
        if mouse_over and enabled:
            color = tuple(min(255, channel + 12) for channel in color)
        pygame.draw.rect(self.screen, color, button.rect, border_radius=6)
        border_color = accent if active else BORDER
        pygame.draw.rect(self.screen, border_color, button.rect, 1, border_radius=6)
        text_color = TEXT if enabled else (83, 95, 116)
        text = self.fonts["small"].render(label, True, text_color)
        self.screen.blit(text, text.get_rect(center=button.rect.center))

    def _section_label(self, label: str, x: int, y: int) -> None:
        self.screen.blit(self.fonts["small"].render(label, True, MUTED), (x, y))

    def _panel(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=12)
        pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=12)

    @staticmethod
    def _wrap_text(text: str, width: int, font: pygame.font.Font) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    @staticmethod
    def _format_search_value(value: float | None) -> str:
        if value is None:
            return "—"
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.2f}"


def run() -> None:
    App().run()
