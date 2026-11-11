from pathlib import Path
import unittest
from identidade_algoritmos import METODOS, garantia_resultado
from busca_limitada import ResultadoBusca
from tsp_core import carregar_mapa, tsp_dijkstra


class IdentidadeAlgoritmosTests(unittest.TestCase):
    def test_catalogo_distingue_caminho_hamiltoniano_e_fecho(self):
        self.assertEqual(set(METODOS), {"dijkstra", "forca", "fecho", "limitada", "comparar"})
        self.assertEqual(METODOS["fecho"].atalho, "T")
        self.assertIn("Passeio", METODOS["fecho"].problema)
        self.assertIn("Hamiltoniano", METODOS["forca"].problema)
        self.assertEqual(METODOS["fecho"].limite_nos, 9)
        self.assertIsNone(METODOS["dijkstra"].limite_nos)

    def test_progresso_informa_as_fases_reais_do_metodo_composto(self):
        mapa = carregar_mapa(Path(__file__).resolve().parents[1] / "data/mapa_05.json")
        fases = []
        resultado = tsp_dijkstra(mapa, 1, ao_progresso=fases.append)
        self.assertEqual(resultado, tsp_dijkstra(mapa, 1))
        self.assertEqual(fases, ["Dijkstra: calculando menores caminhos",
                                 "Caixeiro: buscando a melhor ordem de visitas",
                                 "Expandindo o percurso nas arestas reais"])

    def test_rotulo_nao_chama_busca_cortada_de_otima_ou_inexistente(self):
        sem_rota = ResultadoBusca((), float("inf"), 1, False, "limite_sem_solucao", 1)
        self.assertEqual(garantia_resultado("limitada", sem_rota), "Limite atingido · nenhuma rota encontrada")
        conhecida = ResultadoBusca((1, 2, 1), 4, 2, False, "melhor_conhecida", 1)
        self.assertEqual(garantia_resultado("limitada", conhecida), "Melhor conhecida · sem prova de ótimo")
