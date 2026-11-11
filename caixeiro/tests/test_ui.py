"""Integração com SDL dummy; o teste visual real está documentado em docs/."""
import os
import unittest

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
