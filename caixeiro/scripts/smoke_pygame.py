"""Roteiro reproduzível de integração SDL com capturas da superfície Pygame.

Não injeta eventos no Windows. --janela permite acompanhar a execução ao vivo.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--janela", action="store_true")
    args = parser.parse_args()
    if not args.janela:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    import pygame
    from tsp_ui import Aplicacao
    app = Aplicacao()
    pasta = ROOT / "docs" / "capturas"
    pasta.mkdir(parents=True, exist_ok=True)
    passos = []

    def evento(tipo, **campos):
        pygame.event.post(pygame.event.Event(tipo, **campos))
        for e in pygame.event.get():
            app.processar_evento(e)
        app.atualizar(0)
        app.desenhar()

    def clicar(chave):
        app.desenhar()
        rect, ativo = app.botoes[chave]
        assert ativo, chave
        evento(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)

    def tecla(key):
        evento(pygame.KEYDOWN, key=key)

    def aguardar():
        if app.futuro is not None:
            app.futuro.result(timeout=15)
        app.atualizar(0)
        assert app.resultados, app.status
        app.desenhar()

    def registrar(nome, captura=None):
        passos.append({"caso": nome, "resultado": "passou"})
        if captura:
            pygame.image.save(app.tela, str(pasta / captura))

    try:
        app.desenhar()
        clicar("dijkstra")
        aguardar()
        assert app.resultados["dijkstra"].caminho == (1, 2, 3)
        registrar("Dijkstra por botão: 1-2-3, custo 6", "dijkstra.png")
        tecla(pygame.K_l)
        for no in (2, 5):
            evento(pygame.MOUSEBUTTONDOWN, button=1, pos=app.posicoes()[no])
        assert (app.origem, app.destino) == (2, 5)
        registrar("Clique nos nós alterna origem e destino")
        clicar("forca")
        aguardar()
        assert app.resultados["forca"].custo == 15
        registrar("Força bruta por botão: custo 15", "forca_bruta.png")
        app.processar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_t))
        app.desenhar()
        assert app.identidade_visual()["estado"] == "Em execução"
        registrar("Primeiro frame identifica o método em execução", "algoritmo_em_execucao.png")
        aguardar()
        assert set(app.resultados) == {"fecho"} and app.resultados["fecho"].custo == 15
        registrar("T executa Dijkstra + TSP separadamente", "tsp_dijkstra.png")
        while app.player.passo is None or app.player.passo.tipo != "relaxamento":
            clicar("proximo")
        assert app.identidade_visual()["metodo"] == "fecho"
        assert "Dijkstra" in app.identidade_visual()["fase"]
        registrar("Etapa de Dijkstra preserva identidade do TSP composto", "tsp_dijkstra_etapa_dijkstra.png")
        clicar("fim")
        clicar("limitada")
        aguardar()
        assert app.resultados["limitada"].custo == 15 and app.resultados["limitada"].otimo
        registrar("Busca limitada por botão: ótimo comprovado 15", "busca_limitada.png")
        tecla(pygame.K_1)
        tecla(pygame.K_c)
        aguardar()
        assert app.resultados["fecho"].custo == app.resultados["forca"].custo == 15
        registrar("Comparação por teclado: ambos custam 15", "comparacao.png")
        for chave in ("fecho", "forca"):
            clicar(f"rota_{chave}")
            assert app.resultado_focado == chave and len(app.rotas_exibidas()) == 1
            registrar(f"Resultado {chave} destaca somente a própria rota", f"comparacao_foco_{chave}.png")
        clicar("rota_forca")
        assert app.resultado_focado is None
        for chave in ("reproduzir", "pausar", "proximo", "voltar", "velocidade"):
            clicar(chave)
        clicar("reproduzir")
        app.atualizar(.7)
        clicar("pausar")
        assert app.player.passo is not None
        registrar("Play, pausa, avançar, voltar e velocidade", "animacao.png")
        clicar("fim")
        assert app.player.passo is None
        for _ in range(3):
            clicar("pesos")
        assert app.pesos
        clicar("original")
        assert app.original
        registrar("Referência original do mapa 5", "referencia_05.png")
        tecla(pygame.K_o)
        tecla(pygame.K_2)
        assert len(app.mapa.nos) == 18
        clicar("dijkstra")
        aguardar()
        assert app.resultados["dijkstra"].custo == 45
        registrar("Mapa 18 validado: Dijkstra 1–3 com custo 45", "mapa_18.png")
        for no in (9, 14):
            evento(pygame.MOUSEBUTTONDOWN, button=1, pos=app.posicoes()[no])
        clicar("dijkstra")
        aguardar()
        assert app.resultados["dijkstra"].caminho == (9, 14)
        assert app.resultados["dijkstra"].custo == 1
        registrar("Mapa 18: aresta 9–14 com peso 1", "mapa_18_dijkstra_9_14.png")
        tecla(pygame.K_2)
        clicar("limitada")
        aguardar()
        assert app.resultados["limitada"].custo == 391 and app.resultados["limitada"].otimo
        registrar("Mapa 18 real: ciclo de custo 391, ótimo comprovado", "mapa_18_busca_limitada.png")
        clicar("forca")
        assert app.futuro is None and "9 nós" in app.status and not app.resultados
        clicar("comparar")
        assert app.futuro is None and "9 nós" in app.status
        registrar("Mapa 18 recusa enumeradores acima de 9 nós", "mapa_18_limite.png")
        clicar("zoom_mais")
        assert app.zoom > 1
        clicar("zoom_menos")
        evento(pygame.MOUSEBUTTONDOWN, button=3, pos=app.viewport.center)
        evento(pygame.MOUSEMOTION, rel=(30, 20), pos=app.viewport.center)
        evento(pygame.MOUSEBUTTONUP, button=3, pos=app.viewport.center)
        assert app.pan.length() > 0
        tecla(pygame.K_z)
        assert app.pan.length() == 0 and app.zoom == 1
        registrar("Zoom por botão, pan e reset por teclado")
        clicar("original")
        registrar("Referência original do mapa 18", "referencia_18.png")
        clicar("original")
        evento(pygame.VIDEORESIZE, w=1000, h=760)
        assert app.tela.get_size() == (1000, 760)
        registrar("Redimensionamento mínimo", "janela_minima.png")
        evento(pygame.VIDEORESIZE, w=1360, h=940)
        tecla(pygame.K_1)
        app.acao("pagina_metodos")
        app.desenhar()
        for nome, key, custo in (("nearest_neighbor", pygame.K_n, 17), ("two_opt", pygame.K_i, 15),
                                  ("held_karp", pygame.K_h, 15), ("christofides", pygame.K_a, 15),
                                  ("ortools_solver", pygame.K_r, 15)):
            tecla(key)
            if app.futuro is None:
                assert nome == "ortools_solver" and "opcional ausente" in app.status
                registrar("OR-Tools ausente é identificado sem interromper a UI")
                continue
            aguardar()
            r = app.resultados[nome]
            assert r.custo == custo and r.variante == "fecho", (nome, r.custo)
            assert app.identidade_visual()["metodo"] == nome
            registrar(f"Novo método {nome}: custo {custo}, modelo e garantia visíveis", f"novo_{nome}.png")
            clicar("proximo")
            assert app.identidade_visual()["metodo"] == nome
            clicar("fim")
        tecla(pygame.K_g)
        aguardar()
        assert app.comparacao_info["otimo"] == 15
        assert len(app.resultados) == 6 and all(r.variante == "fecho" for r in app.resultados.values())
        for _ in range(3):
            clicar("resultado_next")
        assert app.pagina_resultados == 0
        registrar("Comparação de seis métodos, paginação e ótimo certificado do mesmo fecho", "novos_comparacao.png")
        tecla(pygame.K_m)
        tecla(pygame.K_2)
        tecla(pygame.K_h)
        aguardar()
        assert app.resultados["held_karp"].custo == 391 and app.resultados["held_karp"].otimo
        registrar("Held–Karp mapa 18 original: ciclo ótimo 391", "novo_held_karp_18.png")
        app.limite_segundos = 1e-12
        tecla(pygame.K_h)
        aguardar()
        assert app.estado_execucao == "limitado" and not app.resultados["held_karp"].otimo
        registrar("Orçamento esgotado aparece como limite, sem prova", "novo_limite.png")
        app.limite_segundos = 5.0
        tecla(pygame.K_r)
        if app.futuro is not None:
            clicar("cancelar")
            aguardar()
            assert app.estado_execucao == "cancelado"
            registrar("Cancelamento pelo botão mantém a janela responsiva", "novo_cancelado.png")
        from unittest.mock import patch
        with patch("solvers.importlib.util.find_spec", return_value=None):
            tecla(pygame.K_r)
            assert app.futuro is None and app.estado_execucao == "bloqueado"
            registrar("Dependência OR-Tools ausente simulada: indisponibilidade explícita", "novo_indisponivel.png")
        from dataclasses import replace
        mapas = app.mapas
        app.mapas = tuple(replace(g, validado=False, pendencias=("fixture smoke",)) for g in mapas)
        tecla(pygame.K_n)
        assert app.futuro is None and app.estado_execucao == "bloqueado"
        registrar("Mapa não validado continua bloqueando os novos métodos")
        app.mapas = mapas
        tecla(pygame.K_ESCAPE)
        assert not app.rodando
        registrar("Escape encerra o loop")
        relatorio = {"modo": "janela" if args.janela else "SDL dummy", "python": platform.python_version(),
                     "pygame": pygame.version.ver, "plataforma": platform.platform(), "casos": passos}
        (ROOT / "docs" / "smoke_resultados.json").write_text(
            json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{len(passos)} casos passaram; capturas em docs/capturas.")
    finally:
        app.fechar()


if __name__ == "__main__":
    main()
