"""Camera isometrica ortografica e projecao para pixels do Pygame.

O chamador deve chamar ajustar() quando a janela for redimensionada. Pontos
sao coordenadas do mundo (iteravel de sequencias XYZ ou dicionario de pontos).
Zoom maior aproxima; arrastar recebe deslocamentos do mouse em pixels.
"""
import math

import pygame
from panda3d.core import OrthographicLens, Point2, Point3, Vec3, WindowProperties


class CameraIsometrica:
    ESQUERDA, DIREITA, TOPO, BAIXO = 244, 250, 90, 132
    MIN_LARGURA, MIN_ALTURA = 1100, 760
    ZOOM_MIN, ZOOM_MAX = 0.65, 3.0
    MARGEM = 3.0

    def __init__(self, base, pontos):
        self.base = base
        self.lente = OrthographicLens()
        self.lente.setNearFar(1, 2000)
        self.base.cam.node().setLens(self.lente)
        self.zoom = 1.0
        self.pan = Vec3(0, 0, 0)
        self.azimute = 45.0
        self.elevacao = math.degrees(math.atan(1 / math.sqrt(2)))
        self._definir_pontos(pontos)
        self.ajustar()

    def _definir_pontos(self, pontos):
        if hasattr(pontos, 'values'):
            pontos = pontos.values()
        novos = [Point3(*p) if len(p) == 3 else Point3(p[0], p[1], 0) for p in pontos]
        if not novos:
            raise ValueError('A camera precisa de pelo menos um ponto')
        self.pontos = novos

    def _eixos(self):
        a = math.radians(self.azimute)
        e = math.radians(self.elevacao)
        # Azimute 45 coloca a camera em (+X, -Y), olhando para o mapa.
        direita = Vec3(math.cos(a), math.sin(a), 0)
        cima = Vec3(-math.sin(a) * math.sin(e), math.cos(a) * math.sin(e), math.cos(e))
        direcao = Vec3(math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))
        return direita, cima, direcao

    def ajustar(self, tamanho=None):
        """Atualiza viewport e enquadramento; tamanho e (largura, altura) em pixels."""
        w, h = tamanho if tamanho is not None else (self.base.win.getXSize(), self.base.win.getYSize())
        if w <= self.ESQUERDA + self.DIREITA or h <= self.TOPO + self.BAIXO:
            raise ValueError('Janela pequena demais para o viewport')
        if (w < self.MIN_LARGURA or h < self.MIN_ALTURA) and hasattr(self.base.win, 'requestProperties'):
            propriedades = WindowProperties()
            propriedades.setSize(max(w, self.MIN_LARGURA), max(h, self.MIN_ALTURA))
            self.base.win.requestProperties(propriedades)
        self.viewport = pygame.Rect(self.ESQUERDA, self.TOPO,
                                    w - self.ESQUERDA - self.DIREITA,
                                    h - self.TOPO - self.BAIXO)
        self.base.cam.node().getDisplayRegion(0).setDimensions(
            self.viewport.left / w, self.viewport.right / w,
            1 - self.viewport.bottom / h, 1 - self.viewport.top / h)
        direita, cima, direcao = self._eixos()
        xs = [p.dot(direita) for p in self.pontos]
        ys = [p.dot(cima) for p in self.pontos]
        # A altura media permite centralizar os limites projetados mesmo com pontos 3D.
        z = sum(p.z for p in self.pontos) / len(self.pontos)
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        a = math.radians(self.azimute)
        horizontal = (cy - z * cima.z) / math.sin(math.radians(self.elevacao))
        centro = Vec3(cx * math.cos(a) - horizontal * math.sin(a),
                      cx * math.sin(a) + horizontal * math.cos(a), z)
        aspecto = self.viewport.w / self.viewport.h
        largura = max(xs) - min(xs) + 2 * self.MARGEM
        altura = max(ys) - min(ys) + 2 * self.MARGEM
        film_altura = max(altura, largura / aspecto) / self.zoom
        self.lente.setFilmSize(film_altura * aspecto, film_altura)
        self._limite_pan = max(largura, altura, 1.0)
        self._limitar_pan()
        alvo = centro + self.pan
        self.base.camera.setPos(alvo + direcao * 500)
        self.base.camera.lookAt(alvo)

    def _limitar_pan(self):
        self.pan.z = 0
        comprimento = self.pan.length()
        if comprimento > self._limite_pan:
            self.pan *= self._limite_pan / comprimento

    def centralizar(self, pontos=None):
        if pontos is not None:
            self._definir_pontos(pontos)
        self.pan = Vec3(0, 0, 0)
        self.zoom = 1.0
        self.ajustar()

    def mudar_zoom(self, fator):
        if not math.isfinite(fator) or fator <= 0:
            raise ValueError('Fator de zoom deve ser positivo e finito')
        self.zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, self.zoom * fator))
        self.ajustar()

    def arrastar(self, dx, dy):
        direita, _, _ = self._eixos()
        # A componente vertical do mouse movimenta o plano horizontal do mapa.
        a = math.radians(self.azimute)
        norte = Vec3(-math.sin(a), math.cos(a), 0)
        unidade = self.lente.getFilmSize().x / self.viewport.w
        self.pan += -direita * (dx * unidade) + norte * (dy * unidade / math.sin(math.radians(self.elevacao)))
        self.ajustar()

    def girar(self, delta):
        self.azimute = (self.azimute + delta) % 360
        self.ajustar()

    def projetar(self, ponto):
        """Retorna (x, y) em pixels da janela, ou None se fora do volume da lente."""
        p = Point3(*ponto) if len(ponto) == 3 else Point3(ponto[0], ponto[1], 0)
        camera_ponto = self.base.cam.getRelativePoint(self.base.render, p)
        tela = Point2()
        if not self.lente.project(camera_ponto, tela):
            return None
        return (self.viewport.left + (tela.x + 1) * self.viewport.w / 2,
                self.viewport.top + (1 - tela.y) * self.viewport.h / 2)
