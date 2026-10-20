"""Vizinho mais próximo: escolher a entrega restante de menor custo."""

from time import perf_counter

from ..core.modelos import EtapaAlgoritmo, ResultadoRota, custo_rota, verificar_cancelamento


class VizinhoMaisProximo:
    nome = "Vizinho mais próximo"

    def resolver(self, custos, inicio=0, fim=None, tempo_limite=3.0,
                 cancelado=lambda: False):
        instante = perf_counter()
        fim = inicio if fim is None else fim
        restantes = set(range(len(custos))) - {inicio, fim}
        ordem, etapas = [inicio], []
        while restantes:
            verificar_cancelamento(cancelado)
            atual = ordem[-1]
            proximo = min(restantes, key=lambda cidade: (custos[atual, cidade], cidade))
            ordem.append(proximo)
            restantes.remove(proximo)
            etapas.append(EtapaAlgoritmo(
                "Escolher o destino restante mais próximo.", ordem.copy(), custo_rota(custos, ordem),
                adicionadas=[(atual, proximo)]))
        ordem.append(fim)
        custo = custo_rota(custos, ordem)
        etapas.append(EtapaAlgoritmo("Retorno ao depósito e fechamento da rota.", ordem.copy(), custo))
        return ResultadoRota(self.nome, ordem, custo, custo, perf_counter() - instante,
                             etapas=etapas)

