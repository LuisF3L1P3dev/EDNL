"""Entrada do aplicativo 2D. Execute: python main.py."""
from tsp_ui import Aplicacao


def main():
    app = Aplicacao()
    try:
        app.executar()
    finally:
        app.fechar()


if __name__ == "__main__":
    main()
