"""Contrato das estratégias que configuram o motor de busca."""

from abc import ABC, abstractmethod

from .contracts import Algorithm


class SearchStrategy(ABC):
    """Define as decisões específicas de um algoritmo de busca informada."""

    algorithm: Algorithm

    @abstractmethod
    def priority(self, path_cost: int, estimate: int) -> int:
        """Calcula a prioridade de um nó na fronteira."""

    @abstractmethod
    def should_update(
        self,
        known_cost: int | None,
        tentative_cost: int,
    ) -> bool:
        """Informa se a rota candidata deve substituir a rota conhecida."""
