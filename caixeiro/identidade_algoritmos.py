"""Identificação dos métodos disponíveis; sem dependência de Pygame."""
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class MetodoVisual:
    titulo: str
    curto: str
    descricao: str
    problema: str
    garantia: str
    cor: tuple[int, int, int]
    atalho: str
    limite_nos: int | None = None


METODOS = MappingProxyType({
    "dijkstra": MetodoVisual(
        "Dijkstra", "Dijkstra", "Menor caminho da origem ao destino",
        "Caminho mínimo A → B", "Exato · pesos não negativos", (45, 97, 169), "D"),
    "forca": MetodoVisual(
        "Caixeiro viajante · Força bruta", "Força bruta", "Enumeração exata das ordens de visita",
        "Ciclo Hamiltoniano na malha original", "Exato · até 9 cidades", (26, 107, 75), "F", 9),
    "fecho": MetodoVisual(
        "Caixeiro viajante + Dijkstra", "Dijkstra + TSP", "Menores caminhos + busca exata de visitas",
        "Passeio fechado no fecho métrico", "Exato · até 9 cidades · permite repetir passagens", (116, 65, 159), "T", 9),
    "limitada": MetodoVisual(
        "Caixeiro viajante · Branch-and-bound", "Branch-and-bound", "Busca com limite de tempo e estados",
        "Ciclo Hamiltoniano na malha original", "Até 18 cidades · prova ou limite informado", (172, 83, 38), "B", 18),
    "comparar": MetodoVisual(
        "Comparação dos métodos TSP", "Comparar TSP", "Força bruta e Dijkstra + TSP",
        "Hamiltoniano × passeio no fecho", "Problemas distintos na malha original", (55, 91, 103), "C", 9),
})


def garantia_resultado(metodo, resultado):
    if metodo == "dijkstra":
        return "Caminho mínimo exato" if resultado.caminho else "Destino inalcançável"
    estado = getattr(resultado, "estado", "")
    if estado == "limite_sem_solucao":
        return "Limite atingido · nenhuma rota encontrada"
    if not resultado.caminho:
        return "Ausência de ciclo comprovada" if resultado.otimo else "Nenhuma rota encontrada"
    return "Ótimo comprovado" if resultado.otimo else "Melhor conhecida · sem prova de ótimo"
