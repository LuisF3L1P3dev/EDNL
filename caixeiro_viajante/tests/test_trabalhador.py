"""Integração do processo Windows/spawn, sem importar o motor 3D."""

from time import monotonic, sleep

from tsp_3d_game.core.scenario_generator import gerar_cenario
from tsp_3d_game.core.servico_otimizacao import ServicoOtimizacao


def aguardar(servico, limite=15):
    mensagens = []
    prazo = monotonic() + limite
    while monotonic() < prazo:
        lote = servico.receber()
        mensagens.extend(lote)
        if any(tipo in ("concluido", "erro") for tipo, _ in lote):
            return mensagens
        sleep(.01)
    raise AssertionError("O trabalhador não respondeu no tempo esperado.")


def test_processo_compara_e_reutiliza_mesma_matriz():
    servico = ServicoOtimizacao()
    try:
        cenario = gerar_cenario(7)
        servico.enviar("comparar", cenario=cenario, tempo_limite=.1)
        mensagens = aguardar(servico)
        assert not [m for m in mensagens if m[0] == "erro"]
        assert len([m for m in mensagens if m[0] == "matriz"]) == 1
        resultados = [valor for tipo, valor in mensagens if tipo == "resultado"]
        assert len(resultados) == 5
        assert all(set(r.ordem) == set(cenario.cidades) for r in resultados)
        assert next(r for r in resultados if r.otima_comprovada).custo <= min(r.custo for r in resultados) + 1e-6
    finally:
        servico.fechar()
    assert not servico.processo.is_alive()


def test_resposta_antiga_e_descartada_apos_nova_missao():
    servico = ServicoOtimizacao()
    try:
        servico.enviar("resolver", cenario=gerar_cenario(50, 1), tempo_limite=.3)
        sleep(.04)
        novo = gerar_cenario(8, 99)
        servico.enviar("preparar", cenario=novo)
        mensagens = aguardar(servico)
        assert not [m for m in mensagens if m[0] == "erro"]
        assert not [m for m in mensagens if m[0] == "resultado"]
        matriz = next(valor for tipo, valor in mensagens if tipo == "matriz")
        assert matriz.destinos == novo.cidades
    finally:
        servico.fechar()

