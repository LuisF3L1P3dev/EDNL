"""Cadastros pendentes sintéticos para preservar testes das guardas."""
from dataclasses import replace
from pathlib import Path
from tsp_core import carregar_mapa


def mapa_18_pendente():
    """Cópia em memória; não altera o mapa real validado nem seu peso 1."""
    mapa = carregar_mapa(Path(__file__).resolve().parents[1] / "data/mapa_18.json")
    return replace(
        mapa, validado=False,
        arestas=tuple(replace(a, peso=None, observacao="Fixture: peso ausente.")
                      if (a.origem, a.destino) == (9, 14) else a for a in mapa.arestas),
        pendencias=("Fixture de teste: custo 9-14 desconhecido.",),
    )
