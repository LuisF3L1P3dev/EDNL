"""Órbita isométrica, vista aérea e acompanhamento do caminhão."""

import math

from ursina import Entity, Vec3, camera, held_keys, lerp, mouse, time


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
        camera.orthographic = True
        camera.fov = self.escala
        self.atualizar(0, None)

    def escolher(self, modo):
        self.modo = modo
        if modo == "Aérea":
            self.inclinacao = 89
        elif modo == "Isométrica":
            self.inclinacao = 48
        else:
            self.inclinacao = 40

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
                if self.modo != "Aérea":
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
        camera.position = self.alvo_suave + deslocamento
        camera.look_at(self.alvo_suave)
        camera.fov = self.escala * (.42 if self.modo == "Seguir veículo" else 1)

