"""Programação dinâmica exata por subconjuntos (Held–Karp)."""

from itertools import combinations
from time import perf_counter

from ..core.modelos import EtapaAlgoritmo, ResultadoRota, custo_rota, verificar_cancelamento


class HeldKarp:
    nome = "Held–Karp (exato)"

    def __init__(self, limite_cidades=12):
        self.limite_cidades = limite_cidades

    def resolver(self, custos, inicio=0, fim=None, tempo_limite=3.0,
                 cancelado=lambda: False):
        if len(custos) > self.limite_cidades:
            raise ValueError(f"Held–Karp está limitado a {self.limite_cidades} cidades. Reduza o mapa ou ajuste a configuração.")
        instante = perf_counter()
        fim = inicio if fim is None else fim
        intermediarios = [i for i in range(len(custos)) if i not in {inicio, fim}]
        quantidade = len(intermediarios)
        if not quantidade:
            ordem = [inicio, fim]
            valor = custo_rota(custos, ordem)
            return ResultadoRota(self.nome, ordem, valor, valor, perf_counter() - instante,
                                 True, observacao="Ótimo comprovado por programação dinâmica.")
        # (máscara dos visitados, último destino) -> (menor custo, predecessor).
        memoria = {}
        for j, cidade in enumerate(intermediarios):
            memoria[1 << j, j] = (float(custos[inicio, cidade]), -1)
        etapas = []
        for tamanho in range(2, quantidade + 1):
            verificar_cancelamento(cancelado)
            if perf_counter() - instante > tempo_limite:
                raise TimeoutError("Held–Karp atingiu o limite de tempo sem concluir a prova de ótimo.")
            for numero, subconjunto in enumerate(combinations(range(quantidade), tamanho)):
                if numero % 256 == 0:
                    verificar_cancelamento(cancelado)
                    if perf_counter() - instante > tempo_limite:
                        raise TimeoutError("Held–Karp atingiu o limite de tempo sem concluir a prova de ótimo.")
                mascara = sum(1 << j for j in subconjunto)
                for ultimo in subconjunto:
                    anteriores = mascara ^ (1 << ultimo)
                    memoria[mascara, ultimo] = min(
                        (memoria[anteriores, anterior][0] + custos[intermediarios[anterior], intermediarios[ultimo]], anterior)
                        for anterior in subconjunto if anterior != ultimo)
            etapas.append(EtapaAlgoritmo(f"Programação dinâmica: subconjuntos de {tamanho} destinos resolvidos."))
        completa = (1 << quantidade) - 1
        _, ultimo = min((memoria[completa, j][0] + custos[cidade, fim], j)
                        for j, cidade in enumerate(intermediarios))
        reversa = []
        mascara = completa
        while ultimo != -1:
            reversa.append(intermediarios[ultimo])
            predecessor = memoria[mascara, ultimo][1]
            mascara ^= 1 << ultimo
            ultimo = predecessor
        ordem = [inicio] + reversa[::-1] + [fim]
        valor = custo_rota(custos, ordem)
        etapas.append(EtapaAlgoritmo("Reconstrução da solução exata a partir dos predecessores.", ordem.copy(), valor))
        return ResultadoRota(self.nome, ordem, valor, valor, perf_counter() - instante, True,
                             etapas=etapas, observacao="Ótimo comprovado por programação dinâmica, para esta matriz de custos.")

