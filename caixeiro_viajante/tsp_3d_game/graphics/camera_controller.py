"""Órbita isométrica, vista aérea e acompanhamento do caminhão."""

import math

from ursina import Entity, Vec3, camera, held_keys, lerp, mouse, time


class CameraMissao:
    def __init__(self, tamanho):
        self.alvo = Vec3(0, 0, 0)
        self.yaw = -40.0
        self.inclinacao = 53.0
        self.distancia = tamanho * 1.55
        self.escala = tamanho * 1.42
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
            self.inclinacao = 53
        else:
            self.inclinacao = 40

    def entrada(self, tecla, sobre_mapa=True):
        if sobre_mapa and tecla in ("scroll up", "scroll down"):
            fator = .9 if tecla == "scroll up" else 1.1
            self.escala = max(9, min(self.tamanho * 3, self.escala * fator))

    def atualizar(self, dt, posicao_veiculo, interagir=True):
        if interagir and self.modo != "Seguir veículo":
            if held_keys["right mouse"]:
                self.yaw += mouse.velocity.x * 160
                if self.modo != "Aérea":
                    self.inclinacao = max(20, min(80, self.inclinacao - mouse.velocity.y * 110))
            velocidade = self.escala * .6 * dt
            direcao = Vec3(held_keys["d"] - held_keys["a"], 0, held_keys["w"] - held_keys["s"])
            angulo = math.radians(self.yaw)
            self.alvo += Vec3(direcao.x * math.cos(angulo) + direcao.z * math.sin(angulo), 0,
                              -direcao.x * math.sin(angulo) + direcao.z * math.cos(angulo)) * velocidade
            if held_keys["middle mouse"]:
                self.alvo += Vec3(-mouse.velocity.x, 0, -mouse.velocity.y) * self.escala * 1.4
        if self.modo == "Seguir veículo" and posicao_veiculo is not None:
            self.alvo = lerp(self.alvo, Vec3(*posicao_veiculo), min(1, dt * 4))
        inclinacao, angulo = math.radians(self.inclinacao), math.radians(self.yaw)
        deslocamento = Vec3(math.sin(angulo) * math.cos(inclinacao), math.sin(inclinacao),
                            -math.cos(angulo) * math.cos(inclinacao)) * self.distancia
        camera.position = self.alvo + deslocamento
        camera.look_at(self.alvo)
        camera.fov = self.escala * (.42 if self.modo == "Seguir veículo" else 1)

