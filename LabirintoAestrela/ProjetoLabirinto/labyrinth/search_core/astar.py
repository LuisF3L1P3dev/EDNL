"""Estratégia do algoritmo A*."""

from .base import SearchStrategy
from .contracts import Algorithm


class AStarStrategy(SearchStrategy):
    """Prioriza ``g(n) + h(n)`` e preserva a rota de menor custo."""

    algorithm = Algorithm.ASTAR

    def priority(self, path_cost: int, estimate: int) -> int:
        return path_cost + estimate

    def should_update(
        self,
        known_cost: int | None,
        tentative_cost: int,
    ) -> bool:
        return known_cost is None or tentative_cost < known_cost
