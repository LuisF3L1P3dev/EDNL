"""Verificação com OpenGL real, componentes reais e capturas dos dois mapas.

Executar da raiz: python scripts/smoke_3d.py. Não controla o desktop.
"""
import argparse
from itertools import combinations
import json
from math import ceil, dist
from pathlib import Path
import statistics
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from direct.showbase.MessengerGlobal import messenger
from panda3d.core import PNMImage, StringStream
from geometria3d import medir_rua
from mundo3d import diferenca_angular, heading_da_direcao
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


def clicar(app, acao):
    """Usa o alvo que o HUD acabou de desenhar."""
    app.ui.desenhar()
    rect, ativo = app.ui.botoes[acao]
    assert ativo, acao
    mouse = app.mouse_pixel
    try:
        app.mouse_pixel = lambda: rect.center
        app.clicar()
    finally:
        app.mouse_pixel = mouse


def verificar_posicionamento(app):
    app.ui.desenhar()
    cena, hud, camera = app.cena, app.ui, app.camera_iso
    nos = cena.mapa_visual.nos
    assert len(set(cena.marcadores_no.values())) == len(nos)
    assert len(hud.etiquetas_tela) == len(nos)
    assert len(hud.pesos_tela) == len(app.mapa.arestas)
    if cena.cidades:
        cobertos = [no for no, r in hud.etiquetas_tela.items() if r.collidelist(hud._edificios_tela) >= 0]
        assert not cobertos, (camera.viewport.size, camera.zoom, cobertos)
    for no in nos:
        ancora = cena.marcadores_no[no.id]
        assert hud.ancoras_tela[no.id] == camera.projetar(ancora)
        if cena.cidades:
            cidade = cena.cidades[no.id]
            assert cidade.ancora_rua == ancora
            assert set(cidade.via_acesso) <= {no.id, *no.conexoes}
        else:
            assert no.id in cena.construcoes_no
            assert no.acesso == (no.ancora_rua, no.entrada)
        for vizinho in no.conexoes:
            assert cena.ruas[no.id, vizinho][0] == ancora
    etiquetas = list(hud.etiquetas_tela.values()) + list(hud.pesos_tela.values())
    assert not any(a.colliderect(b) for a, b in combinations(etiquetas, 2))
    assert not any(r.colliderect(hud._area_controles()) for r in etiquetas)


def verificar_acompanhamento(app, sufixo, n):
    camera, v = app.camera_iso, app.viagem
    clicar(app, 'zoom+')
    assert camera.zoom > 1.
    zoom = camera.zoom
    messenger.send('wheel_up')
    assert camera.zoom > zoom
    clicar(app, 'zoom-')
    assert abs(camera.zoom - zoom) < 1e-9
    clicar(app, 'reset')
    assert camera.zoom == 1. and not camera.pan.length()

    camera.mudar_zoom(100)
    clicar(app, 'acompanhar')
    assert app.acompanhando
    clicar(app, 'velocidade')
    clicar(app, 'velocidade')
    clicar(app, 'pausa')
    for _ in range(90):
        app.atualizar(1/60)
    capturar(app, f'mapa{n}-acompanhamento-{sufixo}.png')
    clicar(app, 'pausa')
    posicao, pan = tuple(app.carro.getPos()), tuple(camera.pan)
    app.atualizar(.25)
    assert tuple(app.carro.getPos()) == posicao and tuple(camera.pan) == pan
    clicar(app, 'reiniciar')
    assert dist(app.carro.getPos(), app.cena.posicoes[app.origem]) < 1e-4
    assert tuple(camera.pan) == pan and app.acompanhando
    for _ in range(90):
        app.atualizar(1/60)
    clicar(app, 'pausa')
    chegadas = set()
    limite_quadros = ceil((sum(v.duracoes) + len(v.pesos) * v.PAUSA_CHEGADA) * 60 / v.velocidade) + 2
    chegada_rotatorias = {r.no: r for r in app.cena.rotatorias}
    for frames in range(1, limite_quadros):
        app.atualizar(1/60)
        i, fracao = v.trecho
        par = v.caminho[i:i + 2]
        amostra = medir_rua(app.cena.ruas[par]).amostrar(app.cena.fracao_percurso(par, fracao))
        assert dist(app.carro.getPos(), amostra.ponto) < 1e-4
        for no in par:
            if no in chegada_rotatorias:
                r = chegada_rotatorias[no]
                assert dist(amostra.ponto[:2], r.centro[:2]) >= r.raio_interno
        if not v.em_chegada:
            heading = heading_da_direcao(amostra.tangente)
            assert abs(diferenca_angular(heading, app.carro.getH())) <= 45.001
        p = camera.projetar(app.carro.getPos(app.render))
        assert p is not None and camera.viewport.collidepoint(p), (n, frames, par, p)
        if v.em_chegada:
            chegadas.add(v.caminho[i])
            assert amostra.ponto == app.cena.posicoes[v.caminho[i]]
        if v.concluida:
            break
    assert v.concluida and chegadas | {app.origem} == set(app.mapa.ids)
    pan = tuple(camera.pan)
    app.atualizar(.25)
    assert tuple(camera.pan) == pan and camera.zoom == 3.
    clicar(app, 'acompanhar')
    assert not app.acompanhando and tuple(camera.pan) == pan
    clicar(app, 'reset')
    v.velocidade = 1
    return frames


def tempo_para_posicao(app, indice, fracao_fisica):
    viagem = app.viagem
    par = viagem.caminho[indice:indice + 2]
    esquerda, direita = 0., 1.
    for _ in range(40):
        meio = (esquerda + direita) / 2
        if app.cena.fracao_percurso(par, meio) < fracao_fisica:
            esquerda = meio
        else:
            direita = meio
    return (sum(viagem.duracoes[:indice]) + direita * viagem.duracoes[indice]
            + indice * viagem.PAUSA_CHEGADA)


def capturar_ponte(app):
    """Captura uma ponte do circuito heurístico com a van sobre o tabuleiro."""
    viagem = app.viagem
    for i, par in enumerate(zip(viagem.caminho, viagem.caminho[1:])):
        ponte = next((p for p in app.cena.mapa_visual.pontes
                      if set(p.aresta) == set(par)), None)
        if ponte:
            break
    else:
        raise AssertionError('O circuito não percorreu uma ponte elevada.')
    rua = medir_rua(app.cena.ruas[par])
    for j, (a, b) in enumerate(rua.segmentos):
        if a[2] != ponte.centro[2] or b[2] != a[2]:
            continue
        if dist(a, ponte.centro) + dist(b, ponte.centro) <= dist(a, b) + 1e-7:
            fracao = (rua.acumulados[j] + dist(a, ponte.centro)) / rua.comprimento
            break
    else:
        raise AssertionError('O centro da ponte não pertence ao tabuleiro.')
    app.acao('reiniciar')
    viagem.velocidade = 1
    app.acao('pausa')
    app.atualizar(tempo_para_posicao(app, i, fracao))
    assert dist(app.carro.getPos(), ponte.centro) < 1e-4
    ponto = app.camera_iso.projetar(ponte.centro)
    cx, cy = app.camera_iso.viewport.center
    app.camera_iso.arrastar(cx - ponto[0], cy - ponto[1])
    app.camera_iso.mudar_zoom(3)
    capturar(app, 'travessia-ponte-1440x960.png')
    app.acao('reset')


def capturar_rotatoria(app, n):
    viagem = app.viagem
    rotatoria = next(r for r in app.cena.rotatorias if r.no == (4 if n == 5 else 17))
    i = viagem.caminho.index(rotatoria.no)
    par = viagem.caminho[i:i + 2]
    rua = medir_rua(app.cena.ruas[par])
    anel = [s for p, s in zip(rua.pontos, rua.acumulados)
            if abs(dist(p[:2], rotatoria.centro[:2]) - rotatoria.raio_pista) < .001]
    alvo = anel[len(anel) // 2] / rua.comprimento
    app.acao('reiniciar')
    viagem.velocidade = 1
    app.acao('pausa')
    app.atualizar(tempo_para_posicao(app, i, alvo))
    assert abs(dist(tuple(app.carro.getPos())[:2], rotatoria.centro[:2]) - rotatoria.raio_pista) < .01
    x, y = app.camera_iso.projetar(rotatoria.centro)
    cx, cy = app.camera_iso.viewport.center
    app.camera_iso.arrastar(cx - x, cy - y)
    app.camera_iso.mudar_zoom(3)
    capturar(app, f'rotatoria-mapa{n}.png')
    app.acao('reset')


def gravar_curva():
    """Grava a chegada e a saída reais da van no nó 4, em 1×."""
    app = Aplicacao3D(offscreen=True)
    destino = DESTINO / 'van-na-rotatoria.mp4'
    try:
        calcular(app)
        viagem = app.viagem
        rotatoria = next(r for r in app.cena.rotatorias if r.no == 4)
        i = viagem.caminho.index(rotatoria.no)
        entrada, saida = viagem.caminho[i - 1:i + 1], viagem.caminho[i:i + 2]
        chegada = medir_rua(app.cena.ruas[entrada])
        partida = medir_rua(app.cena.ruas[saida])
        _, n_chegada = app.cena.mapa_visual.zonas_rotatorias[entrada]
        n_partida, _ = app.cena.mapa_visual.zonas_rotatorias[saida]
        a = (chegada.acumulados[-1 - n_chegada] - 2.) / chegada.comprimento
        b = (partida.acumulados[n_partida] + 2.) / partida.comprimento
        inicio = tempo_para_posicao(app, i - 1, a)
        fim = tempo_para_posicao(app, i, b)
        x, y = app.camera_iso.projetar(rotatoria.centro)
        cx, cy = app.camera_iso.viewport.center
        app.camera_iso.arrastar(cx - x, cy - y)
        app.camera_iso.mudar_zoom(3)
        app.atualizar(inicio)
        fps = 24
        with TemporaryDirectory(dir=DESTINO) as quadros:
            pasta = Path(quadros)
            for i in range(ceil((fim - inicio) * fps)):
                app.ui.desenhar()
                app.graphicsEngine.renderFrame()
                imagem, fluxo = PNMImage(), StringStream()
                assert app.win.getScreenshot(imagem) and imagem.write(fluxo, 'captura.png')
                (pasta / f'{i:04}.png').write_bytes(fluxo.getData())
                app.atualizar(1 / fps)
            subprocess.run(
                ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps),
                 '-i', str(pasta / '%04d.png'), '-pix_fmt', 'yuv420p', '-c:v', 'libx264',
                 '-movflags', '+faststart', str(destino)],
                check=True,
            )
        return destino
    finally:
        app.fechar()


def capturar_cidade(app):
    capturar(app, 'regiao-18-cidades.png')
    app.ui.mostrar_pesos = False
    camera = app.camera_iso
    for no in (1, 5, 18):
        cidade = app.cena.cidades[no]
        centro = tuple((a + b) / 2 for a, b in zip(cidade.centro, cidade.ancora_rua))
        x, y = camera.projetar((*centro, cidade.entrada[2]))
        cx, cy = camera.viewport.center
        camera.arrastar(cx - x, cy - y)
        camera.mudar_zoom(3)
        capturar(app, f'cidade-{no:02}.png')
        assert no in app.ui.etiquetas_tela
        assert app.ui.etiquetas_tela[no].collidelist(app.ui._edificios_tela) < 0
        app.acao('reset')
    app.ui.mostrar_pesos = True


def verificar(tamanho):
    sufixo = f'{tamanho[0]}x{tamanho[1]}'
    app = Aplicacao3D(tamanho=tamanho, offscreen=True)
    resultados = []
    try:
        for indice, n in enumerate((5, 18)):
            app.acao(f'mapa{indice}')
            verificar_posicionamento(app)
            if tamanho == (1440, 960):
                capturar(app, f'ruas-mapa{n}.png')
            if n == 18 and tamanho == (1440, 960):
                capturar_cidade(app)
            if n == 18:
                app.camera_iso.mudar_zoom(.65)
                verificar_posicionamento(app)
                app.acao('reset')
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
            resultado = {'resolucao': sufixo, 'mapa': n, 'algoritmo': app.metodo,
                         'custo': app.resultado.custo, 'rota': app.viagem.caminho,
                         'visitados': len(app.viagem.visitadas), 'retorno_origem': True}
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
            resultado['quadros_acompanhados_em_4x'] = verificar_acompanhamento(app, sufixo, n)
            resultados.append(resultado)
            if tamanho == (1440, 960):
                capturar_rotatoria(app, n)
                if n == 18:
                    capturar_ponte(app)

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
        tempos_arraste = []
        app.camera_iso.mudar_zoom(1.5)
        for passo in range(16):
            inicio = perf_counter()
            app.camera_iso.arrastar(7 if passo < 8 else -7, 2)
            app.ui.desenhar()
            app.graphicsEngine.renderFrame()
            tempos_arraste.append((perf_counter() - inicio) * 1000)
        resultados.append({'resolucao': sufixo, 'frame_com_hud_mediana_ms': round(statistics.median(tempos), 2),
                           'frame_arraste_mediana_ms': round(statistics.median(tempos_arraste), 2),
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
    parser.add_argument('--demo', action='store_true', help='gravar demonstração MP4 com FFmpeg')
    args = parser.parse_args()
    DESTINO.mkdir(parents=True, exist_ok=True)
    if args.demo:
        print(gravar_curva())
        return
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
