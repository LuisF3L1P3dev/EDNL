"""Regressão do descarte de entidades Ursina, sem janela gráfica."""

from ursina import Entity, scene

from tsp_3d_game.graphics.ciclo_vida import destruir_arvore


def finalizar_descarte_do_quadro():
    """Reproduz a coleta que o motor faz em Ursina._update()."""
    marcadas = scene._entities_marked_for_removal
    scene.entities = [e for e in scene.entities if e not in marcadas]
    marcadas.clear()


def test_descarta_filhos_netos_e_entidades_desabilitadas():
    finalizar_descarte_do_quadro()
    quantidade_inicial = len(scene.entities)
    preservada = Entity(name="fora_da_hierarquia")
    raiz = Entity(name="painel_temporario")
    filha = Entity(parent=raiz)
    neta = Entity(parent=filha, enabled=False)
    apenas_visual = Entity(parent=raiz, add_to_scene_entities=False)

    try:
        destruir_arvore(raiz)
        assert all(e.is_empty() for e in (raiz, filha, neta, apenas_visual))
        assert preservada in scene.entities and not preservada.is_empty()
        finalizar_descarte_do_quadro()
        assert len(scene.entities) == quantidade_inicial + 1
    finally:
        destruir_arvore(raiz)
        destruir_arvore(preservada)
        finalizar_descarte_do_quadro()


def test_descarta_filhos_soltos_com_sua_propria_hierarquia():
    finalizar_descarte_do_quadro()
    quantidade_inicial = len(scene.entities)
    raiz = Entity()
    solta = Entity(loose_parent=raiz)
    neta = Entity(parent=solta)

    destruir_arvore(raiz)
    finalizar_descarte_do_quadro()

    assert all(e.is_empty() for e in (raiz, solta, neta))
    assert len(scene.entities) == quantidade_inicial


def test_reconstrucoes_nao_acumulam_entidades_e_descarte_e_repetivel():
    finalizar_descarte_do_quadro()
    quantidade_inicial = len(scene.entities)
    for _ in range(20):
        raiz = Entity()
        filha = Entity(parent=raiz)
        Entity(parent=filha)
        destruir_arvore(raiz)
        destruir_arvore(raiz)
        destruir_arvore(None)
        finalizar_descarte_do_quadro()
        assert len(scene.entities) == quantidade_inicial


def test_respeita_raiz_marcada_como_eternal():
    raiz = Entity(eternal=True)
    filha = Entity(parent=raiz)
    try:
        destruir_arvore(raiz)
        assert not raiz.is_empty() and not filha.is_empty()
    finally:
        raiz.eternal = False
        destruir_arvore(raiz)
        finalizar_descarte_do_quadro()
