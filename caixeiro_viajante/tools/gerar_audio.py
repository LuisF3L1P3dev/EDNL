"""Gera dois sinais musicais originais; não utiliza áudio de terceiros."""
from pathlib import Path
import math
import struct
import wave

PASTA = Path(__file__).resolve().parents[1] / "assets" / "audio"


def gerar(nome, notas):
    PASTA.mkdir(parents=True, exist_ok=True)
    amostras = bytearray()
    taxa = 22050
    for frequencia in notas:
        for i in range(int(taxa * .12)):
            t = i / taxa
            envelope = min(1, t / .008) * max(0, 1 - t / .12) ** 2
            onda = math.sin(math.tau * frequencia * t) + .18 * math.sin(math.tau * frequencia * 2 * t)
            amostras += struct.pack("<h", int(onda * envelope * 11000))
    with wave.open(str(PASTA / f"{nome}.wav"), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(taxa)
        arquivo.writeframes(amostras)


if __name__ == "__main__":
    gerar("entrega", [659.25, 880])
    gerar("conclusao", [523.25, 659.25, 783.99, 1046.5])
