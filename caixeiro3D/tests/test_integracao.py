import sys
import time
import types
import unittest
from unittest.mock import patch

from geometria3d import posicoes_mundo, ruas_mundo
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


if __name__ == '__main__':
    unittest.main()
