"""Relógio de reprodução independente de Pygame e dos algoritmos."""
from dataclasses import dataclass
from tsp_core import Passo


@dataclass
class Reprodutor:
    eventos: tuple[Passo, ...] = ()
    indice: int = -1
    reproduzindo: bool = False
    velocidade: float = 1
    acumulado: float = 0

    @property
    def passo(self):
        return self.eventos[self.indice] if 0 <= self.indice < len(self.eventos) else None

    def carregar(self, eventos):
        self.eventos = tuple(eventos)
        self.indice = -1
        self.reproduzindo = False
        self.acumulado = 0

    def comando(self, chave):
        if not self.eventos:
            return
        self.acumulado = 0
        if chave == "reproduzir":
            if self.indice < 0 or self.indice == len(self.eventos) - 1:
                self.indice = 0
            self.reproduzindo = True
        elif chave == "pausar":
            self.reproduzindo = False
        elif chave in ("proximo", "voltar"):
            self.reproduzindo = False
            self.indice = max(0, min(len(self.eventos) - 1, self.indice + (1 if chave == "proximo" else -1)))
        elif chave == "velocidade":
            velocidades = (.25, .5, 1, 2, 4, 8, 16)
            self.velocidade = velocidades[(velocidades.index(self.velocidade) + 1) % len(velocidades)]
        elif chave == "fim":
            self.indice = -1
            self.reproduzindo = False

    def atualizar(self, dt):
        if not self.reproduzindo:
            return
        self.acumulado += max(0, dt) * self.velocidade
        passos = int(self.acumulado / .6)
        if passos:
            self.acumulado -= passos * .6
            self.indice = min(len(self.eventos) - 1, self.indice + passos)
            if self.indice == len(self.eventos) - 1:
                self.reproduzindo = False
