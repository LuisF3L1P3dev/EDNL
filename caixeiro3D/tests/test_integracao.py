import sys
import time
import types
import unittest
from math import dist
from unittest.mock import patch

from geometria3d import medir_rua, posicoes_mundo, ruas_mundo
from mundo3d import diferenca_angular, heading_da_direcao
from tsp_3d import Aplicacao3D


class CenaTeste:
    def __init__(self, app, grafo, biblioteca):
        self.raiz = app.render.attachNewNode('cena-teste')
        self.rota = self.raiz.attachNewNode('rota')
        self.posicoes = posicoes_mundo(grafo)
        self.ruas = ruas_mundo(grafo)
        self.caminho = ()
        self.trechos = []

    def mostrar_rota(self, caminho):
        self.caminho = tuple(caminho)
        for a, b in zip(caminho, caminho[1:]):
            assert (a, b) in self.ruas

    def mostrar_trecho(self, origem, destino):
        self.trechos.append((origem, destino))
        self.mostrar_rota((origem, destino))
        return True

    def limpar_rota(self):
        self.caminho = ()

    def destruir(self):
        self.raiz.removeNode()


class HUDTeste:
    def __init__(self, app):
        self.app = app
        self.config_aberta = False
        self.animar_busca = True
        self.botoes, self.posicoes_tela = {}, {}

    def desenhar(self):
        pass

    def tratar_acao(self, acao):
        if acao == 'config':
            self.config_aberta = not self.config_aberta
            return True
        return False


class IntegracaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch = patch.dict(sys.modules, {'render3d': types.SimpleNamespace(Cena3D=CenaTeste),
                                             'hud': types.SimpleNamespace(HUD=HUDTeste)})
        cls.patch.start()
        cls.app = Aplicacao3D(offscreen=True)

    @classmethod
    def tearDownClass(cls):
        cls.app.fechar()
        cls.patch.stop()

    def setUp(self):
        self.app.acao('mapa0')
        self.app.ui.animar_busca = True

    def test_acompanhamento_pausa_reinicio_arrasto_e_reset(self):
        from panda3d.core import Vec3
        app = self.app
        app.camera_iso.mudar_zoom(3)
        app.viagem.carregar(app.mapa, (1, 2, 3), ciclo=False)
        app.acao('acompanhar')
        app.atualizar(.1)
        self.assertTrue(app.acompanhando)
        app.acao('pausa')
        pan = Vec3(app.camera_iso.pan)
        app.atualizar(.5)
        self.assertEqual(app.camera_iso.pan, pan)
        app.acao('reiniciar')
        app.atualizar(.1)
        self.assertTrue(app.acompanhando)
        self.assertEqual(app.camera_iso.zoom, 3.)
        antigo = app.mouse_pixel
        try:
            ponto = app.camera_iso.viewport.center
            app.mouse_pixel = lambda: ponto
            app._iniciar_arraste()
            app.atualizar(.01)
            self.assertTrue(app.acompanhando)
            app.mouse_pixel = lambda: (ponto[0] + 10, ponto[1])
            app.atualizar(.01)
            self.assertFalse(app.acompanhando)
            app._terminar_arraste()
        finally:
            app.mouse_pixel = antigo
        app.acao('acompanhar')
        app.acao('reset')
        self.assertFalse(app.acompanhando)
        self.assertEqual(app.camera_iso.zoom, 1.)

    def aguardar_calculo(self):
        fim = time.monotonic() + 5
        while self.app.futuro and time.monotonic() < fim:
            self.app.atualizar(0)
            time.sleep(.001)
        self.assertIsNone(self.app.futuro)

    def test_busca_pausa_replay_e_viagem(self):
        app = self.app
        app.acao('iniciar')
        app.acao('pausa')
        self.aguardar_calculo()
        app.atualizar(20)
        self.assertIsNone(app.resultado)
        app.acao('pausa')
        app.atualizar(20)
        self.assertEqual(app.resultado.custo, 15)
        self.assertTrue(app.viagem.caminho)
        app.atualizar(100)
        self.assertTrue(app.viagem.concluida)
        self.assertEqual(app.viagem.visitadas, set(app.mapa.ids))
        self.assertGreater(app.distancia_percorrida, 0)

    def test_mapa_cancelamento_e_rota_unitaria(self):
        app = self.app
        app.acao('iniciar')
        app.acao('mapa1')
        self.assertEqual(len(app.mapa.ids), 18)
        self.assertIsNone(app.resultado)
        app.acao('selecionar_dijkstra')
        app.destino = app.origem
        app.ui.animar_busca = False
        app.acao('iniciar')
        self.aguardar_calculo()
        app.atualizar(0)
        self.assertEqual(app.viagem.caminho, (app.origem,))
        self.assertTrue(app.viagem.concluida)
        self.assertEqual(app.viagem.visitadas, {app.origem})
        app.acao('iniciar')
        app.acao('cancelar')
        app.atualizar(1)
        self.assertIsNone(app.resultado)
        self.assertFalse(app.ocupado)

    def test_destaque_mostra_somente_trecho_durante_viagem_e_rota_no_fim(self):
        app = self.app
        app.ui.animar_busca = False
        app.acao('iniciar')
        self.aguardar_calculo()
        atual = app.viagem.caminho[:2]
        self.assertEqual(app.cena.caminho, atual)
        self.assertEqual(app.cena.trechos, [atual])
        # Sem trocar de aresta, o frame seguinte não redesenha a rota.
        app.atualizar(.01)
        self.assertEqual(app.cena.trechos, [atual])
        app.atualizar(100)
        self.assertTrue(app.viagem.concluida)
        self.assertEqual(app.cena.caminho, app.viagem.caminho)

    def test_modal_bloqueia_acao(self):
        app = self.app
        app.acao('config')
        app.acao('mapa1')
        self.assertEqual(app.indice_mapa, 0)
        app._escape()
        self.assertFalse(app.ui.config_aberta)
        app.acao('velocidade')
        self.assertEqual(app.viagem.velocidade, 2)

    def test_disponibilidade_de_algoritmos_respeita_tamanho_do_mapa(self):
        app = self.app
        self.assertEqual(app.metodo, 'forca')
        app.acao('selecionar_heuristica')
        self.assertEqual(app.metodo, 'forca')
        self.assertIn('indisponivel', app.status.casefold())
        app.acao('selecionar_dijkstra')
        self.assertEqual(app.metodo, 'dijkstra')
        app.acao('mapa1')
        self.assertEqual(app.metodo, 'heuristica')
        app.acao('selecionar_forca')
        self.assertEqual(app.metodo, 'heuristica')
        self.assertIn('indisponivel', app.status.casefold())
        app.acao('selecionar_dijkstra')
        self.assertEqual(app.metodo, 'dijkstra')

    def test_modelo_da_van_tem_correcao_fixa_de_frente(self):
        self.assertEqual(self.app.modelo_carro.getH(), 180)

    def test_pausa_no_meio_do_giro_preserva_heading_da_van(self):
        """Frame pausado nao pode reposicionar abruptamente o modelo."""
        app = self.app
        aresta = app.mapa.arestas[0]
        a, b = aresta.origem, aresta.destino
        app.viagem.carregar(app.mapa, (a, b), ciclo=False)
        app.cena.ruas[a, b] = ((0., 0., 0.), (0., 5., 0.))
        app.viagem.atualizar(.2)
        app._heading_carro = 47.  # estado intermediario de uma curva suave
        app._posicionar_carro(0.)
        self.assertEqual(app._heading_carro, 47.)
        self.assertEqual(app.carro.getH(), 47.)

    def test_progresso_visual_usa_comprimento_em_vez_do_peso(self):
        app = self.app
        app.viagem.velocidade = 1
        app.viagem.carregar(app.mapa, (1, 2, 3), ciclo=False)
        trecho_longo = ((0., 0., 0.), (10., 0., 0.))
        trecho_curto = ((10., 0., 0.), (11., 0., 0.))
        peso_leve, peso_alto = app.viagem.pesos
        self.assertLess(peso_leve, peso_alto)
        with patch.dict(app.cena.ruas, {(1, 2): trecho_longo, (2, 3): trecho_curto}):
            app.atualizar(30 * peso_leve / app.viagem.total + 1e-8)
            self.assertEqual(app.viagem.custo_atual, peso_leve)
            self.assertEqual(app.distancia_percorrida, 10.)
            self.assertAlmostEqual(app.progresso_visual, 10 / 11)
            app.atualizar(40.)
            self.assertEqual(app.distancia_percorrida, 11.)
            self.assertEqual(app.progresso_visual, 1.)

    def test_retorno_gira_parado_e_sai_alinhado_em_1x_e_4x(self):
        app = self.app
        for velocidade in (1, 4):
            with self.subTest(velocidade=velocidade):
                app.acao('mapa1')
                app.viagem.velocidade = velocidade
                app.viagem.carregar(app.mapa, (13, 12, 13), ciclo=False)
                entrada = medir_rua(app.cena.ruas[13, 12]).amostrar(1.)
                saida = medir_rua(app.cena.ruas[12, 13]).amostrar(0.)
                rumo_entrada = heading_da_direcao(entrada.tangente)
                rumo_saida = heading_da_direcao(saida.tangente)
                tempo_ate_parada = 30 * app.viagem.pesos[0] / app.viagem.total / velocidade
                app.atualizar(tempo_ate_parada - .01 / velocidade)
                self.assertAlmostEqual(diferenca_angular(app.carro.getH(), rumo_entrada), 0.)
                app.atualizar(.01 / velocidade + 1e-8)
                self.assertLess(dist(tuple(app.carro.getPos()), entrada.ponto), 1e-5)
                self.assertAlmostEqual(diferenca_angular(app.carro.getH(), rumo_entrada), 0., places=3)

                app.atualizar(app.viagem.PAUSA_CHEGADA / (2 * velocidade))
                meio_giro = app.carro.getH()
                self.assertAlmostEqual(abs(diferenca_angular(rumo_entrada, meio_giro)), 90., places=3)
                app.acao('pausa')
                app.atualizar(10.)
                self.assertEqual(meio_giro, app.carro.getH())
                self.assertLess(dist(tuple(app.carro.getPos()), entrada.ponto), 1e-5)

                app.acao('pausa')
                app.atualizar(.17 / velocidade)
                self.assertFalse(app.viagem.em_chegada)
                self.assertAlmostEqual(diferenca_angular(app.carro.getH(), rumo_saida), 0.)
                app.atualizar(40.)
                fim = medir_rua(app.cena.ruas[12, 13]).amostrar(1.)
                self.assertLess(dist(tuple(app.carro.getPos()), fim.ponto), 1e-5)
                self.assertAlmostEqual(diferenca_angular(app.carro.getH(), heading_da_direcao(fim.tangente)), 0.)


if __name__ == '__main__':
    unittest.main()
