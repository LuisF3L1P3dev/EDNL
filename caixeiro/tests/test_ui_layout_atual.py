import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
from tsp_ui import Aplicacao
from solvers import executar


class LayoutAtualTests(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacao((1000, 760))

    def tearDown(self):
        self.app.fechar()

    def test_layout_e_controles_de_reproducao(self):
        app = self.app
        r = executar("dijkstra", app.mapa, 1, destino=3)
        app.resultados = {"dijkstra": r}
        app.historico = list(r.eventos)
        app.player.carregar(app.historico)
        app.desenhar()
        self.assertGreaterEqual(app.viewport.w, 638)
        self.assertGreaterEqual(app.viewport.h, 370)
        for nome in ("reproduzir", "pausar", "voltar", "proximo", "velocidade", "fim", "rota_dijkstra"):
            self.assertTrue(app.resultados_rect.contains(app.botoes[nome][0]), nome)
        for nome in ("selecao_origem", "selecao_destino", "mapa1", "mapa2", "dijkstra", "forca", "limpar"):
            self.assertTrue(app.lateral.contains(app.botoes[nome][0]), nome)

    def test_selecao_igualdade_e_bloqueio(self):
        app = self.app
        app.acao("selecao_destino")
        app.selecionar_no(app.origem)
        self.assertEqual(app.origem, app.destino)
        self.assertEqual(app.selecao, "origem")
        self.assertEqual(app.variante_metodo("dijkstra"), app.variante)
        app.futuro = object()
        app.acao("selecao_destino")
        app.selecionar_no(2)
        self.assertEqual((app.origem, app.destino, app.selecao), (1, 1, "origem"))
        app.desenhar()
        self.assertFalse(app.botoes["selecao_origem"][1])
        app.futuro = None

    def test_metodos_disponiveis_e_indisponiveis(self):
        app = self.app
        app.desenhar()
        self.assertTrue(app.botoes["dijkstra"][1])
        self.assertTrue(app.botoes["forca"][1])
        app.trocar_mapa(1)
        app.desenhar()
        self.assertTrue(app.botoes["dijkstra"][1])
        self.assertFalse(app.botoes["forca"][1])
        self.assertTrue(app.motivo_indisponivel("forca"))
        app.acao("forca")
        self.assertIsNone(app.futuro)


if __name__ == "__main__":
    unittest.main()
