"""Câmeras de apresentação e navegação do cenário."""

import math

from ursina import Entity, Vec3, camera, held_keys, lerp, mouse, time
from ..ui.tema import (ALTURA_REFERENCIA, LARGURA_DIREITA,
                       LARGURA_ESQUERDA, MARGEM)


class CameraMissao:
    def __init__(self, tamanho, preferencias=None):
        self.preferencias = preferencias or {}
        self.alvo = Vec3(0, 0, 0)
        self.yaw = -40.0
        self.inclinacao = 48.0
        self.distancia = tamanho * 1.55
        self.escala = tamanho * 1.18
        self.escala_desejada = self.escala
        self.alvo_suave = Vec3(0, 0, 0)
        self.yaw_suave = self.yaw
        self.inclinacao_suave = self.inclinacao
        self.tamanho = tamanho
        self.modo = "Isométrica"
        self.escala_inicial = self.escala
        self.fator_enquadramento = 1.0
        self.ajustar_enquadramento(camera.aspect_ratio)
        camera.orthographic = True
        camera.fov = self.escala
        self.atualizar(0, None)

    def escolher(self, modo):
        self.modo = modo
        camera.orthographic = modo != "Perspectiva"
        if modo in ("Aérea", "Superior"):
            self.inclinacao = 89
        elif modo == "Isométrica":
            self.inclinacao = 48
        elif modo == "Perspectiva":
            self.inclinacao = 42
        else:
            self.inclinacao = 40

    def centralizar(self):
        """Retorna o alvo ao centro do mapa e recupera o zoom inicial."""
        if self.modo == "Seguir veículo":
            self.escolher("Isométrica")
        self.alvo = Vec3(0, 0, 0)
        self.yaw = -40.0
        self.inclinacao = 89 if self.modo in ("Aérea", "Superior") else 48 if self.modo == "Isométrica" else 42
        self.escala_desejada = self.escala_inicial

    def ajustar_enquadramento(self, aspecto):
        """Dá espaço ao mapa quando a HUD reduz a largura central disponível."""
        faixa_lateral = (LARGURA_ESQUERDA + LARGURA_DIREITA + 2 * MARGEM) / ALTURA_REFERENCIA
        largura_referencia = 16 / 9 - faixa_lateral
        largura_util = max(.35, aspecto - faixa_lateral)
        self.fator_enquadramento = max(1.0, largura_referencia / largura_util)
        self._atualizar_fov()

    def _atualizar_fov(self):
        if camera.orthographic:
            camera.fov = self.escala * self.fator_enquadramento * (.42 if self.modo == "Seguir veículo" else 1)
        else:
            semiangulo = math.radians(24) * self.fator_enquadramento
            camera.fov = min(82, math.degrees(2 * math.atan(math.tan(semiangulo))))

    def entrada(self, tecla, sobre_mapa=True):
        if sobre_mapa and tecla in ("scroll up", "scroll down"):
            fator = .9 if tecla == "scroll up" else 1.1
            self.zoom(fator)

    def zoom(self, fator):
        self.escala_desejada = max(9, min(self.tamanho * 2.5, self.escala_desejada * fator))

    def atualizar(self, dt, posicao_veiculo, interagir=True):
        if interagir and self.modo != "Seguir veículo":
            sensibilidade = self.preferencias.get("sensibilidade", 1.)
            if held_keys["right mouse"]:
                sinal = -1 if self.preferencias.get("inverter_giro") else 1
                self.yaw += mouse.velocity.x * 160 * sensibilidade * sinal
                if self.modo not in ("Aérea", "Superior"):
                    self.inclinacao = max(25, min(80, self.inclinacao - mouse.velocity.y * 110 * sensibilidade))
            velocidade = self.escala * .6 * dt * sensibilidade
            direita, esquerda, cima, baixo = ("right arrow", "left arrow", "up arrow", "down arrow") if self.preferencias.get("teclas_movimento") == "Setas" else ("d", "a", "w", "s")
            direcao = Vec3(held_keys[direita] - held_keys[esquerda], 0, held_keys[cima] - held_keys[baixo])
            angulo = math.radians(self.yaw)
            self.alvo += Vec3(direcao.x * math.cos(angulo) + direcao.z * math.sin(angulo), 0,
                              -direcao.x * math.sin(angulo) + direcao.z * math.cos(angulo)) * velocidade
            if held_keys["middle mouse"]:
                self.alvo += Vec3(-mouse.velocity.x, 0, -mouse.velocity.y) * self.escala * 1.4 * sensibilidade
            self.alvo.x = max(-self.tamanho * .6, min(self.tamanho * .6, self.alvo.x))
            self.alvo.z = max(-self.tamanho * .6, min(self.tamanho * .6, self.alvo.z))
        if self.modo == "Seguir veículo" and posicao_veiculo is not None:
            self.alvo = lerp(self.alvo, Vec3(*posicao_veiculo), min(1, dt * 4))
        fator = 1 - math.exp(-dt * 12) if dt and self.preferencias.get("suavizar_camera", True) else 1
        self.alvo_suave = lerp(self.alvo_suave, self.alvo, fator)
        self.escala = lerp(self.escala, self.escala_desejada, fator)
        self.yaw_suave = lerp(self.yaw_suave, self.yaw, fator)
        self.inclinacao_suave = lerp(self.inclinacao_suave, self.inclinacao, fator)
        inclinacao, angulo = math.radians(self.inclinacao_suave), math.radians(self.yaw_suave)
        deslocamento = Vec3(math.sin(angulo) * math.cos(inclinacao), math.sin(inclinacao),
                            -math.cos(angulo) * math.cos(inclinacao)) * self.distancia
        if self.modo == "Perspectiva":
            deslocamento *= self.escala / self.escala_inicial
        camera.position = self.alvo_suave + deslocamento
        camera.look_at(self.alvo_suave)
        self._atualizar_fov()

