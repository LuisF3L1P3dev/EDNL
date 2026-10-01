from pyamaze import agent, maze

from guloso import busca_gulosa


def main() -> None:
    labirinto = maze(25,25)
    labirinto.CreateMaze()

    agente = agent(labirinto, filled=True, footprints=True)
    caminho = busca_gulosa(labirinto)
    if caminho:
        labirinto.tracePath({agente: caminho}, delay=10)
    labirinto.run()


if __name__ == "__main__":
    main()
