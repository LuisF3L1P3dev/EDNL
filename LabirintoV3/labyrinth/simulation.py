"""Máquina de estados que desacopla a busca do ritmo da interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator

from .model import Grid, Position
from .search import (
    EventKind,
    HeuristicType,
    SearchAlgorithm,
    SearchEvent,
    SearchMetrics,
    search_steps,
)


class SimulationState(str, Enum):
    IDLE = "Pronto"
    SEARCHING = "Planejando"
    PAUSED = "Pausado"
    WALKING = "Caminhando"
    FINISHED = "Concluído"
    NO_PATH = "Sem caminho"


@dataclass(slots=True)
class Simulation:
    algorithm: SearchAlgorithm
    heuristic: HeuristicType = HeuristicType.MANHATTAN
    state: SimulationState = SimulationState.IDLE
    frontier: set[Position] = field(default_factory=set)
    explored: set[Position] = field(default_factory=set)
    path: list[Position] = field(default_factory=list)
    agent_position: Position | None = None
    current: Position | None = None
    metrics: SearchMetrics = field(default_factory=SearchMetrics)
    g_values: dict[Position, int] = field(default_factory=dict)
    h_values: dict[Position, float] = field(default_factory=dict)
    scores: dict[Position, float] = field(default_factory=dict)
    _steps: Iterator[SearchEvent] | None = field(default=None, repr=False)
    _walk_index: int = field(default=0, repr=False)

    def start(
        self,
        grid: Grid,
        heuristic: HeuristicType | None = None,
    ) -> None:
        self.reset(grid)
        if heuristic is not None:
            self.heuristic = heuristic
        self._steps = search_steps(grid.clone(), self.algorithm, self.heuristic)
        self.state = SimulationState.SEARCHING

    def reset(self, grid: Grid) -> None:
        self.state = SimulationState.IDLE
        self.frontier.clear()
        self.explored.clear()
        self.path.clear()
        self.agent_position = grid.start
        self.current = None
        self.metrics = SearchMetrics()
        self.g_values.clear()
        self.h_values.clear()
        self.scores.clear()
        self._steps = None
        self._walk_index = 0

    def pause(self) -> None:
        if self.state in (SimulationState.SEARCHING, SimulationState.WALKING):
            self.state = SimulationState.PAUSED

    def resume(self) -> None:
        if self.state is SimulationState.PAUSED:
            self.state = SimulationState.WALKING if self.path else SimulationState.SEARCHING

    def advance(self) -> None:
        if self.state is SimulationState.SEARCHING and self._steps is not None:
            event = next(self._steps)
            self._consume(event)
        elif self.state is SimulationState.WALKING:
            self._walk_index += 1
            if self._walk_index >= len(self.path):
                self._walk_index = max(0, len(self.path) - 1)
                self.state = SimulationState.FINISHED
            if self.path:
                self.agent_position = self.path[self._walk_index]

    def _consume(self, event: SearchEvent) -> None:
        self.frontier = event.frontier
        self.explored = event.explored
        self.current = event.current
        self.metrics = event.metrics
        self.g_values = event.g_values
        self.h_values = event.h_values
        self.scores = event.scores
        if event.kind is EventKind.FOUND:
            self.path = event.path
            self._walk_index = 0
            self.agent_position = self.path[0]
            self.state = SimulationState.WALKING
        elif event.kind is EventKind.NO_PATH:
            self.state = SimulationState.NO_PATH

    @property
    def active(self) -> bool:
        return self.state in (SimulationState.SEARCHING, SimulationState.WALKING)

    @property
    def terminal(self) -> bool:
        return self.state in (SimulationState.FINISHED, SimulationState.NO_PATH)
