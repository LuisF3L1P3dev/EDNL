"""Integração com SDL dummy; o teste visual real está documentado em docs/."""
import os
import unittest
from concurrent.futures import Future

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
try:
    import pygame
    from tsp_ui import Aplicacao
except ModuleNotFoundError as error:
    if error.name != "pygame":
        raise
    pygame = None


@unittest.skipIf(pygame is None, "Instale requirements.txt para testar Pygame")
class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacao()
        self.addCleanup(self.app.fechar)

    def test_zoom_ancorado_reset_e_custos_preservados(self):
        a = self.app
        a.acao("mapa2")
        antes = a.mapa.arestas
        ponto = a.posicoes()[9]
        a.mudar_zoom(2, ponto)
        self.assertLess(a.posicoes()[9].distance_to(ponto), .001)
        a.pan += pygame.Vector2(20, 30)
        a.acao("reset")
        self.assertEqual(a.zoom, 1)
        self.assertEqual(a.pan, pygame.Vector2())
        self.assertEqual(antes, a.mapa.arestas)
        a.desenhar()

    def test_pesos_referencia_e_resize(self):
        a = self.app
        for esperado in (1, 2, 0):
            a.acao("pesos")
            self.assertEqual(a.modo_pesos, esperado)
            a.desenhar()
        a.acao("original")
        a.desenhar()
        a.processar_evento(pygame.event.Event(pygame.VIDEORESIZE, w=1000, h=760))
        a.desenhar()
        self.assertEqual(a.tela.get_size(), (1000, 760))

    def test_cliques_teclado_worker_e_bloqueio(self):
        a = self.app
        a.desenhar()
        for node_id in (2, 5):
            a.processar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=a.posicoes()[node_id]))
        self.assertEqual((a.origem, a.destino), (2, 5))
        a.processar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c))
        a.futuro.result(timeout=10)
        a.atualizar(0)
        self.assertEqual(a.resultados["forca"].custo, 15)
        self.assertEqual(a.resultados["fecho"].custo, 15)
        a.acao("reproduzir")
        a.atualizar(1)
        self.assertIsNotNone(a.player.passo)
        a.acao("limitada")
        a.futuro.result(timeout=10)
        a.atualizar(0)
        self.assertEqual(a.resultados["limitada"].estado, "otimo_comprovado")
        a.acao("mapa2")
        self.assertEqual(a.historico, [])
        a.acao("dijkstra")
        a.futuro.result(timeout=10)
        a.atualizar(0)
        self.assertIsNone(a.futuro)
        self.assertEqual(a.resultados["dijkstra"].custo, 45)
        a.acao("forca")
        self.assertIsNone(a.futuro)
        self.assertIn("9 nós", a.status)
        a.desenhar()

    def test_selecoes_estaveis_durante_trabalho_e_erro_recuperavel(self):
        a = self.app
        futuro = Future()
        a.futuro = futuro
        a.acao("mapa2")
        a.selecionar_no(5)
        self.assertEqual((a.indice_mapa, a.origem), (0, 1))
        futuro.set_exception(ValueError("erro simulado"))
        a.atualizar(0)
        self.assertIsNone(a.futuro)
        self.assertIn("erro simulado", a.status)
        a.desenhar()
