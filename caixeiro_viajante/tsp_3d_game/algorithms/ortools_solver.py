"""Um veículo, custos inteiros e Guided Local Search com limite de tempo."""

from time import perf_counter

import numpy as np

from ..core.modelos import EtapaAlgoritmo, ResultadoRota, custo_rota, verificar_cancelamento


class SolucionadorORTools:
    nome = "OR-Tools + GLS"

    def resolver(self, custos, inicio=0, fim=None, tempo_limite=3.0,
                 cancelado=lambda: False):
        # Importação tardia mantém os algoritmos didáticos utilizáveis sem OR-Tools.
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2

        instante = perf_counter()
        verificar_cancelamento(cancelado)
        fim = inicio if fim is None else fim
        inteiros = np.rint(custos * 1000).astype(np.int64)
        gerenciador = pywrapcp.RoutingIndexManager(len(custos), 1, [inicio], [fim])
        modelo = pywrapcp.RoutingModel(gerenciador)

        def custo_trecho(indice_a, indice_b):
            return int(inteiros[gerenciador.IndexToNode(indice_a), gerenciador.IndexToNode(indice_b)])

        retorno = modelo.RegisterTransitCallback(custo_trecho)
        modelo.SetArcCostEvaluatorOfAllVehicles(retorno)
        parametros = pywrapcp.DefaultRoutingSearchParameters()
        parametros.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        parametros.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        parametros.time_limit.FromMilliseconds(max(1, int(tempo_limite * 1000)))
        parametros.log_search = False
        etapas, melhor = [], [float("inf")]
        contagem = [0]

        def ao_encontrar_solucao():
            if cancelado():
                modelo.solver().FinishCurrentSearch()
                return
            objetivo = modelo.CostVar().Value()
            if objetivo >= melhor[0]:
                return
            melhor[0] = objetivo
            indice, ordem = modelo.Start(0), []
            while not modelo.IsEnd(indice):
                ordem.append(gerenciador.IndexToNode(indice))
                indice = modelo.NextVar(indice).Value()
            ordem.append(gerenciador.IndexToNode(indice))
            contagem[0] += 1
            if len(etapas) < 160:
                etapas.append(EtapaAlgoritmo(
                    f"Solução incumbente {contagem[0]} observada no OR-Tools.", ordem,
                    custo_rota(custos, ordem)))

        modelo.AddAtSolutionCallback(ao_encontrar_solucao)
        solucao = modelo.SolveWithParameters(parametros)
        verificar_cancelamento(cancelado)
        if solucao is None:
            raise ValueError(f"OR-Tools não encontrou uma rota no tempo disponível (estado {modelo.status()}).")
        indice, ordem = modelo.Start(0), []
        while not modelo.IsEnd(indice):
            ordem.append(gerenciador.IndexToNode(indice))
            indice = solucao.Value(modelo.NextVar(indice))
        ordem.append(gerenciador.IndexToNode(indice))
        valor = custo_rota(custos, ordem)
        return ResultadoRota(self.nome, ordem, valor, valor, perf_counter() - instante,
                             melhorias=max(0, contagem[0] - 1), etapas=etapas,
                             observacao="Melhor solução encontrada no limite de tempo; sem prova de ótimo. Custos do solver arredondados a 0,001 unidade de custo.")

