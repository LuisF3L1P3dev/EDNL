"""Verificação com OpenGL real, componentes reais e capturas dos dois mapas.

Executar da raiz: python scripts/smoke_3d.py. Não controla o desktop.
"""
import argparse
import json
from math import dist
from pathlib import Path
import statistics
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from panda3d.core import PNMImage, StringStream
from tsp_3d import Aplicacao3D

DESTINO = ROOT / 'tmp' / '3d-review'


def capturar(app, nome):
    app.ui.desenhar()
    for _ in range(3):
        app.graphicsEngine.renderFrame()
    imagem, fluxo = PNMImage(), StringStream()
    assert app.win.getScreenshot(imagem)
    assert imagem.write(fluxo, 'captura.png')
    (DESTINO / nome).write_bytes(fluxo.getData())


def calcular(app):
    app.acao('iniciar')
    assert app.futuro is not None, app.status
    app.futuro.result(timeout=10)
    app.atualizar(0)
    if app.ocupado:
        app.acao('pausa')
        etapa = app.etapa
        app.atualizar(1)
        assert app.etapa == etapa
        assert app.resultado is None
        app.acao('pausa')
        app.ui.animar_busca = False
        app.atualizar(0)
        app.ui.animar_busca = True
    assert app.resultado is not None
    assert app.resultado.termino == 'concluido'
    assert app.mapa.custo(app.viagem.caminho) == app.resultado.custo


def verificar(tamanho):
    sufixo = f'{tamanho[0]}x{tamanho[1]}'
    app = Aplicacao3D(tamanho=tamanho, offscreen=True)
    resultados = []
    try:
        for indice, n in enumerate((5, 18)):
            app.acao(f'mapa{indice}')
            app.ui.desenhar()
            assert len(app.ui.posicoes_tela) == n
            for p in app.ui.posicoes_tela.values():
                assert app.camera_iso.viewport.collidepoint(p), p
            for rect, _ in app.ui.botoes.values():
                assert app.ui.canvas.get_rect().contains(rect), rect
            calcular(app)
            assert app.resultado.custo == (15 if n == 5 else 340)
            assert set(app.viagem.caminho) == set(app.mapa.ids)
            assert app.viagem.caminho[0] == app.viagem.caminho[-1]
            app.atualizar(8)
            assert 0 < app.viagem.custo_atual < app.viagem.total
            capturar(app, f'mapa{n}-viagem-{sufixo}.png')
            custo = app.viagem.custo_atual
            app.acao('pausa')
            app.atualizar(2)
            assert app.viagem.custo_atual == custo
            app.acao('velocidade')
            assert app.viagem.velocidade == 2
            app.acao('velocidade')
            assert app.viagem.velocidade == 4
            app.acao('pausa')
            app.atualizar(120)
            assert app.viagem.concluida
            assert app.viagem.visitadas == set(app.mapa.ids)
            assert dist(tuple(app.carro.getPos()), app.cena.posicoes[app.origem]) < 1e-4
            assert app.fase == 'Concluido'
            capturar(app, f'mapa{n}-final-{sufixo}.png')
            resultados.append({'resolucao': sufixo, 'mapa': n, 'algoritmo': app.metodo,
                               'custo': app.resultado.custo, 'rota': app.viagem.caminho,
                               'visitados': len(app.viagem.visitadas), 'retorno_origem': True})
            app.acao('reiniciar')
            assert app.viagem.custo_atual == 0
            assert not app.viagem.reproduzindo
            app.camera_iso.mudar_zoom(100)
            assert app.camera_iso.zoom == 3
            app.camera_iso.arrastar(10000, 10000)
            app.acao('reset')
            assert app.camera_iso.zoom == 1
            assert app.camera_iso.pan.length() == 0
            app.viagem.velocidade = 1

        # Seleção pelos mesmos alvos de clique usados pela interface real.
        app.acao('selecionar_dijkstra')
        app.ui.desenhar()
        mouse_original = app.mouse_pixel
        app.acao('origem')
        app.mouse_pixel = lambda: app.ui.posicoes_tela[14]
        app.clicar()
        app.acao('destino')
        app.mouse_pixel = lambda: app.ui.posicoes_tela[9]
        app.clicar()
        app.mouse_pixel = mouse_original
        assert (app.origem, app.destino) == (14, 9)
        calcular(app)
        assert app.resultado.caminho == (14, 9)
        assert app.resultado.custo == 1
        app.acao('distancias')
        app.ui.desenhar()
        assert app.ui.config_aberta
        assert set(app.ui.botoes) == {'fechar_config'}
        app.acao('mapa0')
        assert app.indice_mapa == 1
        capturar(app, f'dijkstra-distancias-{sufixo}.png')
        app._escape()
        app.acao('config')
        app.ui.desenhar()
        assert set(app.ui.botoes) == {'pesos', 'legendas', 'animacao', 'fechar_config'}
        capturar(app, f'configuracoes-{sufixo}.png')
        app._escape()

        app.acao('iniciar')
        app.acao('mapa0')
        app.atualizar(1)
        assert not app.ocupado and app.resultado is None
        assert len(app.render.findAllMatches('**/veiculo')) == 1
        app.acao('selecionar_dijkstra')
        app.destino = app.origem
        calcular(app)
        assert app.resultado.custo == 0
        assert app.viagem.concluida and app.viagem.visitadas == {app.origem}
        app.acao('mapa1')
        app.acao('selecionar_forca')
        assert app.metodo == 'heuristica'
        app.acao('iniciar')
        app.acao('cancelar')
        app.atualizar(1)
        assert not app.ocupado and not app.viagem.caminho

        tempos = []
        for _ in range(30):
            inicio = perf_counter()
            app.ui.desenhar()
            app.graphicsEngine.renderFrame()
            tempos.append((perf_counter() - inicio) * 1000)
        resultados.append({'resolucao': sufixo, 'frame_com_hud_mediana_ms': round(statistics.median(tempos), 2),
                           'modelos_em_cache': len(app.biblioteca.modelos),
                           'texturas_em_cache': len(app.biblioteca.texturas),
                           'selecao_pelo_mapa': True, 'cancelamento': True,
                           'dialogos': True, 'troca_durante_busca': True})
        return resultados
    finally:
        app.fechar()
        app.fechar()


def verificar_janela():
    """Abre uma janela por cerca de 1,2 s para verificar eventos nativos."""
    from panda3d.core import WindowProperties
    app = Aplicacao3D()
    observado = {}

    def redimensionar(task):
        props = WindowProperties()
        # Exercitar a restauração assíncrona do mínimo após um resize extremo.
        props.setSize(300, 120)
        app.win.requestProperties(props)
        return task.done

    def fechar_janela(task):
        observado['tamanho'] = [app.win.getXSize(), app.win.getYSize()]
        observado['hud'] = list(app.ui.canvas.get_size())
        assert observado['tamanho'] == observado['hud'] == [1100, 760]
        props = WindowProperties()
        props.setOpen(False)
        app.win.requestProperties(props)
        return task.done

    try:
        app.taskMgr.doMethodLater(.5, redimensionar, 'verificar-resize')
        app.taskMgr.doMethodLater(1.2, fechar_janela, 'verificar-fechar-janela')
        app.executar()
        assert app._fechada
        observado['abertura_resize_fechamento'] = True
        return observado
    finally:
        app.fechar()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--janela', action='store_true', help='verificar abertura, resize e fechamento em janela nativa')
    args = parser.parse_args()
    DESTINO.mkdir(parents=True, exist_ok=True)
    if args.janela:
        resultados = verificar_janela()
        (DESTINO / 'janela.json').write_text(json.dumps(resultados, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(resultados, ensure_ascii=False, indent=2))
        return
    resultados = verificar((1440, 960)) + verificar((1100, 760))
    (DESTINO / 'resultados.json').write_text(json.dumps(resultados, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(resultados, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
