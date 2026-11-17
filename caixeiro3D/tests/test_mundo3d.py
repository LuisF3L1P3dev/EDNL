import unittest
from mundo3d import (Viagem, diferenca_angular, direcao_antecipada,
                     heading_da_direcao, interpolar, posicoes_mundo,
                     ruas_mundo, suavizar_heading)
from tsp_core import Grafo, No, Aresta


def grafo():
    return Grafo('teste', 'Teste', (No(1, 0, 0), No(2, .5, 0), No(3, 1, 1)),
                 (Aresta(1, 2, 2), Aresta(2, 3, 3), Aresta(3, 1, 4)))


class MundoTest(unittest.TestCase):
    def setUp(self):
        self.g = grafo()
        self.v = Viagem()
        self.v.carregar(self.g, (1, 2, 3, 1))

    def test_geometria_e_interpolacao_reversa(self):
        ruas = ruas_mundo(self.g)
        self.assertEqual(ruas[1, 2], tuple(reversed(ruas[2, 1])))
        self.assertEqual(set(posicoes_mundo(self.g)), {1, 2, 3})
        a, _ = interpolar(ruas[1, 2], .3)
        b, _ = interpolar(ruas[2, 1], .7)
        for x, y in zip(a, b):
            self.assertAlmostEqual(x, y)

    def test_chegada_pausa_e_retornar(self):
        self.v.atualizar(2 / (9 / 30))
        self.assertAlmostEqual(self.v.custo_atual, 2)
        self.assertEqual(self.v.visitadas, {1, 2})
        self.assertTrue(self.v.em_chegada)
        self.v.atualizar(.1)
        self.assertEqual(self.v.custo_atual, 2)
        self.v.reproduzindo = False
        self.v.atualizar(20)
        self.assertEqual(self.v.custo_atual, 2)
        self.v.reproduzir()
        self.v.atualizar(100)
        self.assertEqual(self.v.custo_atual, 9)
        self.assertTrue(self.v.concluida)
        self.assertEqual(self.v.visitadas, {1, 2, 3})
        self.assertFalse(self.v.reproduzindo)

    def test_grande_delta_e_velocidade(self):
        outra = Viagem()
        outra.carregar(self.g, (1, 2, 3, 1))
        self.v.velocidade = 4
        self.v.atualizar(2)
        outra.atualizar(8)
        self.assertAlmostEqual(self.v.custo_atual, outra.custo_atual)
        self.assertEqual(self.v.trecho, outra.trecho)
        self.v.atualizar(1000)
        self.assertTrue(self.v.concluida)
        self.assertEqual(self.v.total, 9)
        with self.assertRaises(ValueError):
            self.v.atualizar(-1)

    def test_unico_e_validacao(self):
        self.v.carregar(self.g, (2,), ciclo=False)
        self.assertTrue(self.v.concluida)
        self.assertEqual(self.v.visitadas, {2})
        self.assertFalse(self.v.reproduzindo)
        with self.assertRaises(ValueError):
            self.v.carregar(self.g, (99,), ciclo=False)
        with self.assertRaises(ValueError):
            self.v.carregar(self.g, (1, 1), ciclo=False)
        with self.assertRaises(ValueError):
            self.v.carregar(self.g, (1, 2, 1))

    def test_salto_reinicio(self):
        self.v.saltar(1)
        self.assertEqual(self.v.custo_atual, 2)
        self.assertEqual(self.v.visitadas, {1, 2})
        self.v.saltar(-1)
        self.assertEqual(self.v.custo_atual, 0)
        self.v.reproduzir()
        self.v.atualizar(1)
        self.v.reiniciar()
        self.assertEqual(self.v.custo_atual, 0)
        self.assertFalse(self.v.reproduzindo)
        self.assertEqual(self.v.visitadas, {1})

    def test_heading_cardinal_wrap_e_giro_suave(self):
        self.assertEqual(heading_da_direcao((0, 1, 0)), 0)
        self.assertEqual(heading_da_direcao((1, 0, 0)), -90)
        self.assertEqual(heading_da_direcao((-1, 0, 0)), 90)
        self.assertEqual(abs(heading_da_direcao((0, -1, 0))), 180)
        self.assertEqual(diferenca_angular(170, -170), 20)
        self.assertAlmostEqual(suavizar_heading(170, -170, .05, 180), 179)
        self.assertAlmostEqual(suavizar_heading(179, -179, .1, 180), -179)

    def test_lookahead_antecipa_curva_e_preserva_rampa(self):
        ruas = {
            (1, 2): ((0., 0., 0.), (5., 0., 0.)),
            (2, 3): ((5., 0., 0.), (5., 5., 2.)),
        }
        curva = direcao_antecipada(ruas, (1, 2, 3), 0, .9, 2.)
        self.assertGreater(curva[1], 0)
        rampa = direcao_antecipada({(1, 2): ((0., 0., 0.), (4., 0., 2.))},
                                   (1, 2), 0, .25, 2.)
        self.assertGreater(rampa[2], 0)


if __name__ == '__main__':
    unittest.main()
