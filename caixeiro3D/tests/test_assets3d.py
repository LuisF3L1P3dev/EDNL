import unittest

from panda3d.core import GeomVertexReader, NodePath
from assets3d import Biblioteca, instancia_normalizada


class AssetsTest(unittest.TestCase):
    def setUp(self):
        self.biblioteca = Biblioteca()

    def test_modelos_reais_e_cache(self):
        for kit, nome in [('carro', 'delivery'), ('rua', 'road-straight'),
                          ('cidade', 'building-a'), ('suburbio', 'tree-small')]:
            modelo = self.biblioteca.modelo(kit, nome)
            self.assertFalse(modelo.find('**/+GeomNode').isEmpty())
            self.assertIs(modelo, self.biblioteca.modelo(kit, nome))
        self.assertGreater(len(self.biblioteca.texturas), 0)
        antes = len(self.biblioteca.texturas)
        self.biblioteca.modelo('carro', 'ambulance')
        self.assertEqual(antes, len(self.biblioteca.texturas))

    def test_textura_e_uv_preservados(self):
        modelo = self.biblioteca.modelo('carro', 'delivery')
        malha = modelo.find('**/+GeomNode')
        self.assertIsNotNone(malha.getTexture())
        dados = malha.node().getGeom(0).getVertexData()
        leitor = GeomVertexReader(dados, 'texcoord')
        coords = []
        while not leitor.isAtEnd():
            coords.append(tuple(leitor.getData2()))
        self.assertTrue(any(u != 0 or v != 0 for u, v in coords))
        self.assertGreater(len(set(coords)), 1)

    def test_normalizacao_nao_altera_cache(self):
        modelo = self.biblioteca.modelo('rua', 'road-straight')
        escala = modelo.getScale()
        copia = instancia_normalizada(modelo, 3)
        minimo, maximo = copia.getTightBounds()
        self.assertAlmostEqual(max(maximo[i] - minimo[i] for i in range(3)), 3, places=5)
        self.assertEqual(modelo.getScale(), escala)
        with self.assertRaises(ValueError):
            instancia_normalizada(modelo, 0)

    def test_tabuleiro_da_ponte_preserva_textura_e_exclui_a_pista_inferior(self):
        ponte = self.biblioteca.modelo('rua', 'road-bridge')
        tabuleiro = self.biblioteca.modelo('rua', 'road-bridge', cota_minima=.45)
        self.assertIs(tabuleiro, self.biblioteca.modelo('rua', 'road-bridge', cota_minima=.45))
        self.assertAlmostEqual(tabuleiro.getTightBounds()[0].z, .45)
        self.assertAlmostEqual(tabuleiro.getTightBounds()[1].z, ponte.getTightBounds()[1].z)
        self.assertAlmostEqual(ponte.getTightBounds()[0].z, 0.)
        self.assertEqual(tabuleiro.findAllTextures()[0], ponte.findAllTextures()[0])

    def test_erros_claros(self):
        with self.assertRaisesRegex(ValueError, 'Kit desconhecido'):
            self.biblioteca.modelo('inexistente', 'x')
        with self.assertRaisesRegex(FileNotFoundError, 'Asset ausente'):
            self.biblioteca.modelo('carro', 'inexistente')
        with self.assertRaisesRegex(ValueError, 'Nome de modelo invalido'):
            self.biblioteca.modelo('carro', '../x')


if __name__ == '__main__':
    unittest.main()
