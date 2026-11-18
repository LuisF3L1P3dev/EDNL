import unittest
from types import SimpleNamespace

from panda3d.core import Camera, NodePath, Vec3
from camera3d import CameraIsometrica


class Regiao:
    def setDimensions(self, *args):
        self.dimensoes = args


class Cam:
    def __init__(self, no):
        self.no = no
        self.regiao = Regiao()

    def node(self):
        return self

    def setLens(self, lente):
        self.no.node().setLens(lente)

    def getDisplayRegion(self, indice):
        return self.regiao

    def getRelativePoint(self, *args):
        return self.no.getRelativePoint(*args)


def base_falsa():
    render = NodePath('render')
    camera = render.attachNewNode('camera')
    cam = Cam(camera.attachNewNode(Camera('cam')))
    win = SimpleNamespace(getXSize=lambda: 1100, getYSize=lambda: 760)
    return SimpleNamespace(render=render, camera=camera, cam=cam, win=win)


class CameraTest(unittest.TestCase):
    def setUp(self):
        self.base = base_falsa()
        self.pontos = [(-30, -20, 0), (30, 20, 0), (-30, 20, 4), (30, -20, 1)]
        self.camera = CameraIsometrica(self.base, self.pontos)

    def assert_enquadrado(self):
        r = self.camera.viewport
        for ponto in self.pontos:
            projetado = self.camera.projetar(ponto)
            self.assertIsNotNone(projetado)
            x, y = projetado
            self.assertTrue(r.left < x < r.right, (ponto, x, y))
            self.assertTrue(r.top < y < r.bottom, (ponto, x, y))

    def test_viewport_e_enquadramento(self):
        self.assertEqual(tuple(self.camera.viewport), (244, 90, 606, 538))
        self.assert_enquadrado()
        self.camera.ajustar((1600, 900))
        self.assert_enquadrado()
        self.camera.girar(90)
        self.assert_enquadrado()

    def test_zoom_limites_e_centralizacao(self):
        self.camera.mudar_zoom(100)
        self.assertEqual(self.camera.zoom, 3.0)
        self.camera.mudar_zoom(.0001)
        self.assertEqual(self.camera.zoom, .65)
        with self.assertRaises(ValueError):
            self.camera.mudar_zoom(0)
        self.camera.arrastar(100000, 100000)
        self.assertEqual(self.camera.pan.z, 0)
        self.camera.centralizar()
        self.assertEqual(self.camera.zoom, 1)
        self.assertEqual(self.camera.pan, Vec3(0))
        self.assert_enquadrado()

    def test_pan_extremo_mantem_intersecao_do_mapa(self):
        for zoom in (.65, 1, 3):
            for dx, dy in ((100000, 100000), (-100000, -100000),
                           (100000, -100000), (-100000, 100000)):
                self.camera.centralizar()
                self.camera.mudar_zoom(zoom)
                self.camera.arrastar(dx, dy)
                direita, cima, _ = self.camera._eixos()
                alvo = self.base.camera.getPos(self.base.render) - self.camera._eixos()[2] * 500
                film = self.camera.lente.getFilmSize()
                for eixo, dimensao in ((direita, film.x), (cima, film.y)):
                    coordenadas = [Vec3(*p).dot(eixo) for p in self.pontos]
                    centro = alvo.dot(eixo)
                    intersecao = min(max(coordenadas), centro + dimensao / 2) - max(min(coordenadas), centro - dimensao / 2)
                    self.assertGreater(intersecao, 2.99, (zoom, dx, dy, intersecao))
                self.assertEqual(self.camera.pan.z, 0)

    def test_arrasto_move_projecao(self):
        antes = self.camera.projetar((0, 0, 0))
        self.camera.arrastar(25, 10)
        depois = self.camera.projetar((0, 0, 0))
        self.assertAlmostEqual(depois[0] - antes[0], 25, places=2)
        self.assertAlmostEqual(depois[1] - antes[1], 10, places=2)

    def test_acompanhar_preserva_lente_e_mantem_veiculo_visivel(self):
        self.camera.mudar_zoom(3)
        filme = self.camera.lente.getFilmSize()
        orientacao = (self.camera.azimute, self.camera.elevacao)
        alvo = (25, 15, 0)
        self.camera.acompanhar(alvo, 1 / 60, veiculo=alvo)
        self.assertTrue(self.camera.viewport.collidepoint(self.camera.projetar(alvo)))
        self.assertEqual(self.camera.lente.getFilmSize(), filme)
        self.assertEqual((self.camera.azimute, self.camera.elevacao), orientacao)
        anterior = Vec3(self.camera.pan)
        self.camera.acompanhar(alvo, 0, veiculo=alvo)
        self.assertEqual(self.camera.pan, anterior)

    def test_pontos_e_janela_invalidos(self):
        with self.assertRaises(ValueError):
            self.camera.centralizar([])
        with self.assertRaises(ValueError):
            CameraIsometrica(base_falsa(), [])
        with self.assertRaises(ValueError):
            self.camera.ajustar((400, 100))

    def test_resize_nativo_extremo_solicita_minimo_e_preserva_lente(self):
        pedidos = []
        self.base.win.requestProperties = pedidos.append
        viewport = self.camera.viewport.copy()
        lente = self.camera.lente.getFilmSize()
        self.camera.ajustar((300, 120))
        self.assertEqual(len(pedidos), 1)
        self.assertEqual((pedidos[0].getXSize(), pedidos[0].getYSize()), (1100, 760))
        self.assertEqual(self.camera.viewport, viewport)
        self.assertEqual(self.camera.lente.getFilmSize(), lente)
        self.camera.ajustar((1100, 760))
        self.assert_enquadrado()


if __name__ == '__main__':
    unittest.main()
