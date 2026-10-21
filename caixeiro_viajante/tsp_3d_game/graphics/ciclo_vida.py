"""Descarte das hierarquias temporárias criadas pelo jogo."""

from ursina import destroy


def destruir_arvore(entidade):
    """Destrói filhos antes do pai e libera seus registros no Ursina.

    Em Ursina 8.3, ``destroy(pai)`` remove o NodePath do pai, mas deixa
    entidades filhas em ``scene.entities``. Percorrer a hierarquia antes
    da remoção evita acumular textos, botões, malhas e colisores a cada
    reconstrução de painel ou cenário. A remoção da lista de entidades
    continua sendo feita pelo motor, ao final do quadro.
    """
    visitadas = set()

    def descartar(atual):
        if atual is None or not atual or id(atual) in visitadas:
            return
        visitadas.add(id(atual))
        if getattr(atual, "eternal", False):
            return
        for filha in tuple(atual.children) + tuple(atual.loose_children):
            descartar(filha)
        destroy(atual)

    descartar(entidade)
