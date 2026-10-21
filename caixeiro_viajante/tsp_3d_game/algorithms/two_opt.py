"""2-opt: remover duas conexões e inverter o segmento entre elas."""

from time import perf_counter

import numpy as np

from ..core.modelos import EtapaAlgoritmo, ResultadoRota, custo_rota, verificar_cancelamento
from .nearest_neighbor import VizinhoMaisProximo


class DoisOpt:
    nome = "2-opt"

    def resolver(self, custos, inicio=0, fim=None, tempo_limite=3.0,
                 cancelado=lambda: False, rota_inicial=None):
        instante = perf_counter()
        ordem = list(rota_inicial) if rota_inicial is not None else VizinhoMaisProximo().resolver(
            custos, inicio, fim, cancelado=cancelado).ordem
        custo = custo_rota(custos, ordem)
        etapas = [EtapaAlgoritmo("Rota inicial para as trocas 2-opt.", ordem.copy(), custo)]
        simetrica = np.allclose(custos, custos.T)
        melhorias = 0
        houve_melhoria = True
        while houve_melhoria and perf_counter() - instante < tempo_limite:
            houve_melhoria = False
            for i in range(1, len(ordem) - 2):
                verificar_cancelamento(cancelado)
                if perf_counter() - instante >= tempo_limite:
                    break
                for j in range(i + 1, len(ordem) - 1):
                    a, b, c, d = ordem[i - 1], ordem[i], ordem[j], ordem[j + 1]
                    if simetrica:
                        novo_custo = custo - custos[a, b] - custos[c, d] + custos[a, c] + custos[b, d]
                    else:
                        candidata = ordem[:i] + ordem[i:j + 1][::-1] + ordem[j + 1:]
                        novo_custo = custo_rota(custos, candidata)
                    if novo_custo < custo - 1e-7:
                        antes = custo
                        ordem[i:j + 1] = reversed(ordem[i:j + 1])
                        custo = custo_rota(custos, ordem)
                        melhorias += 1
                        etapas.append(EtapaAlgoritmo(
                            f"Troca {melhorias}: duas conexões removidas e duas adicionadas.",
                            ordem.copy(), custo, [(a, b), (c, d)], [(a, c), (b, d)], antes))
                        houve_melhoria = True
                        break
                if houve_melhoria:
                    break
        return ResultadoRota(self.nome, ordem, custo, custo, perf_counter() - instante,
                             melhorias=melhorias, etapas=etapas,
                             observacao="Busca local 2-opt; um mínimo local não prova o ótimo global.")

