from concurrent.futures import Future
from unittest.mock import patch
import unittest
from test_ui import pygame, Aplicacao
from solvers import executar, Orcamento


@unittest.skipIf(pygame is None, "Pygame opcional para testes do núcleo")
class InterfaceSolversTests(unittest.TestCase):
    def setUp(self):
        self.app = Aplicacao()
        self.app.limite_segundos = 0.5
        self.addCleanup(self.app.fechar)

    def concluir(self):
        self.app.futuro.result(timeout=10)
        self.app.atualizar(0)
        self.app.desenhar()

    def test_cinco_metodos_botoes_atalhos_e_historico(self):
        a = self.app
        a.acao("pagina_metodos")
        a.desenhar()
        metodos = ("nearest_neighbor", "two_opt", "held_karp", "christofides", "ortools_solver")
        for nome in metodos:
            a.desenhar()
            rect, ativo = a.botoes[nome]
            self.assertTrue(ativo)
            a.processar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))
            if a.futuro is None:  # dependência opcional ausente
                self.assertEqual(nome, "ortools_solver")
                self.assertEqual(a.estado_execucao, "bloqueado")
                continue
            self.concluir()
            self.assertEqual(set(a.resultados), {nome})
            self.assertTrue(a.resultados[nome].caminho)
            self.assertEqual(a.identidade_visual()["metodo"], nome)
            self.assertEqual({e.metodo_origem for e in a.historico}, {nome})
            a.acao("proximo")
            self.assertEqual(a.identidade_visual()["metodo"], nome)
            self.assertNotIn("Caixeiro exato", a.identidade_visual()["fase"])
            a.acao("fim")

    def test_comparacao_paginas_mesmo_problema_e_modelo_estavel(self):
        a = self.app
        a.acao("comparar_todos")
        variante = a.variante
        a.acao("modelo")
        self.assertEqual(a.variante, variante)
        self.concluir()
        self.assertEqual(len(a.resultados), 6)
        self.assertEqual(a.comparacao_info["otimo"], 15)
        self.assertEqual({r.variante for r in a.resultados.values()}, {variante})
        a.estado_execucao = "limitado"  # outro método do grupo atingiu seu orçamento
        a.resultado_focado = "held_karp"
        self.assertEqual(a.identidade_visual()["estado"], "Concluído")
        for _ in range(3):
            a.desenhar()
            self.assertEqual(sum(k.startswith("rota_") for k in a.botoes), 2)
            a.acao("resultado_next")
        self.assertEqual(a.pagina_resultados, 0)
        a.acao("modelo")
        a.acao("held_karp")
        self.concluir()
        self.assertEqual(a.resultados["held_karp"].variante, "original")

    def test_cancelamento_limite_dependencia_e_layout_minimo(self):
        a = self.app
        a.acao("pagina_metodos")
        a.processar_evento(pygame.event.Event(pygame.VIDEORESIZE, w=1000, h=760))
        a.desenhar()
        for chave, (rect, _) in a.botoes.items():
            if chave in ("nearest_neighbor", "two_opt", "held_karp", "christofides", "ortools_solver", "modelo", "orcamento", "comparar_todos"):
                self.assertTrue(a.lateral.contains(rect), chave)
        with patch("solvers.importlib.util.find_spec", return_value=None):
            a.acao("ortools_solver")
            self.assertIsNone(a.futuro)
            self.assertIn("opcional ausente", a.status)
        a.metodo_selecionado = "held_karp"
        r = executar("held_karp", a.mapa, 1, orcamento=Orcamento(memoria_bytes=1))
        a.futuro = Future()
        a.futuro.set_result(({"held_karp": r}, {"held_karp": 1}, []))
        a.atualizar(0)
        self.assertEqual(a.identidade_visual()["estado"], "Limite atingido")
        a.futuro = Future()
        a.acao("cancelar")
        self.assertTrue(a.cancelar.is_set())
        a.futuro.set_result(({}, {}, []))
        a.atualizar(0)
        self.assertEqual(a.identidade_visual()["estado"], "Cancelado")
