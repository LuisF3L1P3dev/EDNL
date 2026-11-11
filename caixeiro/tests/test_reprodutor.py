import unittest
from reprodutor import Reprodutor
from tsp_core import Passo


class ReprodutorTests(unittest.TestCase):
    def test_play_pause_passos_velocidade_e_retorno(self):
        p = Reprodutor()
        p.comando("reproduzir")
        self.assertIsNone(p.passo)
        p.carregar(Passo("teste", str(i)) for i in range(5))
        p.comando("reproduzir")
        p.atualizar(.6)
        self.assertEqual(p.indice, 1)
        p.comando("pausar")
        p.atualizar(10)
        self.assertEqual(p.indice, 1)
        p.comando("proximo")
        p.comando("voltar")
        self.assertEqual(p.indice, 1)
        p.comando("velocidade")
        self.assertEqual(p.velocidade, 2)
        p.comando("reproduzir")
        p.atualizar(10)
        self.assertEqual(p.indice, 4)
        self.assertFalse(p.reproduzindo)
        p.comando("fim")
        self.assertIsNone(p.passo)

    def test_limites_e_limpeza(self):
        p = Reprodutor()
        p.carregar([Passo("teste", "unico")])
        p.comando("voltar")
        p.comando("proximo")
        self.assertEqual(p.indice, 0)
        p.carregar([])
        self.assertIsNone(p.passo)
