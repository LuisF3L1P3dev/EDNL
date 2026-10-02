"""Ponto de entrada da comparação animada entre Gulosa e A*."""

import random

from astar import eventos_astar
from guloso import eventos_gulosa
from interface_comparacao import ComparisonWindow
from pyamaze import maze


def main() -> None:
    random.seed(50)
    labirinto = maze(25, 25)
    labirinto.CreateMaze(loopPercent=15)

    # A interface própria reutiliza maze_map e desenha os dois canvases.
    labirinto._win.destroy()

    janela = ComparisonWindow(
        labirinto,
        guloso_events=lambda: eventos_gulosa(labirinto),
        astar_events=lambda: eventos_astar(labirinto),
    )
    janela.run()


if __name__ == "__main__":
    main()
