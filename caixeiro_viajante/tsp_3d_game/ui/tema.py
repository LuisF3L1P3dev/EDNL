"""Tokens visuais compartilhados pela HUD e pelos modais."""

from pathlib import Path

from ursina import Text, application

from ..graphics.estilo import (BORDA, CIANO, FUNDO, LARANJA, PAINEL, ROSA,
                               ROXO, SUAVE, SUPERFICIE, TEXTO, VERDE)


ALTURA_REFERENCIA = 900
MARGEM = 10
ALTURA_TOPO = 64
LARGURA_ESQUERDA = 280
LARGURA_DIREITA = 290
ALTURA_RODAPE = 64

SOMBRA = "#080D18"
BORDA_CLARA = "#31415E"
AMARELO = "#FFD34E"

PALETA = {
    "fundo": FUNDO,
    "painel": PAINEL,
    "superficie": SUPERFICIE,
    "borda": BORDA,
    "borda_clara": BORDA_CLARA,
    "texto": TEXTO,
    "suave": SUAVE,
    "ciano": CIANO,
    "verde": VERDE,
    "laranja": LARANJA,
    "amarelo": AMARELO,
    "roxo": ROXO,
    "rosa": ROSA,
    "sombra": SOMBRA,
}

_FONTES_CARREGADAS = False
FONTE_TITULO = "OpenSans-Regular.ttf"
FONTE_TEXTO = "OpenSans-Regular.ttf"


def carregar_fontes():
    """Seleciona as fontes locais uma vez, com fallback para a fonte Ursina."""
    global _FONTES_CARREGADAS, FONTE_TITULO, FONTE_TEXTO
    if _FONTES_CARREGADAS:
        return FONTE_TITULO, FONTE_TEXTO
    _FONTES_CARREGADAS = True
    raiz = Path(application.asset_folder)
    titulo = raiz / "assets" / "fonts" / "Fredoka-Medium.ttf"
    texto = raiz / "assets" / "fonts" / "NunitoSans-Regular.ttf"
    if titulo.is_file():
        FONTE_TITULO = titulo.name
    if texto.is_file():
        FONTE_TEXTO = texto.name
        Text.default_font = FONTE_TEXTO
    return FONTE_TITULO, FONTE_TEXTO


carregar_fontes()
