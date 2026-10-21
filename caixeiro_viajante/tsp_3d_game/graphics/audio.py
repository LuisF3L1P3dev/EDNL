"""Sinais curtos originais incluídos no projeto, carregados uma única vez."""
from pathlib import Path
from ursina import Audio


class AudioMissao:
    def __init__(self, preferencias):
        pasta = Path(__file__).resolve().parents[2] / "assets" / "audio"
        self.sons = {nome: Audio(pasta / f"{nome}.wav", autoplay=False, auto_destroy=False)
                     for nome in ("entrega", "conclusao")}
        self.preferencias = preferencias

    def tocar(self, nome):
        if self.preferencias.get("audio_ativo", False):
            som = self.sons[nome]
            som.volume = self.preferencias.get("volume", .35)
            som.play()
