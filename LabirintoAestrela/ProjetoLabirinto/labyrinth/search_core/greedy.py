"""Estratégia da Busca Gulosa."""

from .base import SearchStrategy
from .contracts import Algorithm


class GreedyStrategy(SearchStrategy):
    """Prioriza somente ``h(n)`` e mantém a primeira rota descoberta."""

    algorithm = Algorithm.GREEDY

    def priority(self, path_cost: int, estimate: int) -> int:
        return estimate

    def should_update(
        self,
        known_cost: int | None,
        tentative_cost: int,
    ) -> bool:
        return known_cost is None
