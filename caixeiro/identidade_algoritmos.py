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
        "Contraste dos modelos TSP", "Contrastar modelos", "Força bruta e Dijkstra + TSP",
        "Hamiltoniano × passeio no fecho", "Problemas distintos na malha original", (55, 91, 103), "C", 9),
    "nearest_neighbor": MetodoVisual(
        "Caixeiro viajante · Vizinho mais próximo", "Vizinho mais próximo", "Escolha gulosa com desempate por ID",
        "Modelo TSP selecionado", "Heurística · sem prova de ótimo", (34, 119, 125), "N"),
    "two_opt": MetodoVisual(
        "Caixeiro viajante · nearest_neighbor + two_opt", "Vizinho + 2-opt", "Construção gulosa e melhoria de rota",
        "Modelo TSP selecionado", "Melhoria local · sem prova global", (160, 91, 41), "I"),
    "held_karp": MetodoVisual(
        "Caixeiro viajante · Held–Karp", "Held–Karp", "DP por subconjuntos com reconstrução do ciclo",
        "Modelo TSP selecionado", "Exato se concluído · O(n² 2ⁿ)", (62, 82, 153), "H", 18),
    "christofides": MetodoVisual(
        "Caixeiro viajante + Dijkstra · Christofides", "Christofides", "MST, matching mínimo e atalhamento",
        "Passeio fechado no fecho métrico", "Aproximação 1,5 · TSP métrico", (137, 62, 115), "A", 18),
    "ortools_solver": MetodoVisual(
        "Caixeiro viajante · OR-Tools", "OR-Tools", "Routing Solver opcional com orçamento",
        "Modelo TSP selecionado", "Rota viável · sem certificado de ótimo", (94, 103, 52), "R", 18),
    "comparar_todos": MetodoVisual(
        "Comparação · mesmo problema TSP", "Comparar métodos", "Mesma matriz, origem e regras",
        "Modelo TSP selecionado", "Gap somente com ótimo certificado", (55, 91, 103), "G"),
})


def garantia_resultado(metodo, resultado):
    if hasattr(resultado, "garantia"):
        return resultado.garantia
    if metodo == "dijkstra":
        return "Caminho mínimo exato" if resultado.caminho else "Destino inalcançável"
    estado = getattr(resultado, "estado", "")
    if estado == "limite_sem_solucao":
        return "Limite atingido · nenhuma rota encontrada"
    if not resultado.caminho:
        return "Ausência de ciclo comprovada" if resultado.otimo else "Nenhuma rota encontrada"
    return "Ótimo comprovado" if resultado.otimo else "Melhor conhecida · sem prova de ótimo"
