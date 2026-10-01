from pyamaze import agent, maze

from astar import astar


def main() -> None:
    labirinto = maze(50,50)
    labirinto.CreateMaze()

    agente = agent(labirinto, filled=True, footprints=True)
    caminho = astar(labirinto)
    if caminho:
        labirinto.tracePath({agente: caminho}, delay=10)
    labirinto.run()


if __name__ == "__main__":
    main()
