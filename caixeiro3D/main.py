"""Entrada do jogo, com modo offscreen para verificacao automatizada."""
import argparse
from pathlib import Path
from panda3d.core import PNMImage, StringStream
from tsp_3d import Aplicacao3D


def main():
    parser = argparse.ArgumentParser(description='Caixeiro viajante 3D')
    parser.add_argument('--offscreen', action='store_true')
    parser.add_argument('--frames', type=int, default=0)
    parser.add_argument('--screenshot', type=Path)
    parser.add_argument('--mapa', choices=('5', '18'), default='5')
    parser.add_argument('--algoritmo', choices=('forca', 'dijkstra', 'heuristica'))
    parser.add_argument('--iniciar', action='store_true')
    args = parser.parse_args()
    app = Aplicacao3D(offscreen=args.offscreen)
    try:
        if args.mapa == '18':
            app.acao('mapa1')
        if args.algoritmo:
            app.acao('selecionar_' + args.algoritmo)
        if args.iniciar:
            app.acao('iniciar')
        frames = args.frames or (120 if args.offscreen else 0)
        if frames > 0:
            for _ in range(frames):
                app.taskMgr.step()
            if args.screenshot:
                imagem = PNMImage()
                if not app.win.getScreenshot(imagem):
                    raise RuntimeError('Falha ao capturar a janela')
                fluxo = StringStream()
                if not imagem.write(fluxo, 'captura.png'):
                    raise RuntimeError('Falha ao codificar a captura PNG')
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                args.screenshot.write_bytes(fluxo.getData())
        else:
            app.executar()
    finally:
        app.fechar()


if __name__ == '__main__':
    main()
