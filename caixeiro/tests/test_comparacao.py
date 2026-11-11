import unittest
from pathlib import Path
from comparacao import comparar, medir
from tsp_core import carregar_mapa, tsp_forca_bruta


class ComparacaoTests(unittest.TestCase):
    def test_metricas_distintas_e_controle_equivalente(self):
        mapa = carregar_mapa(Path(__file__).resolve().parents[1] / "data/mapa_05.json")
        r = comparar(mapa, 1, 3, repeticoes=2)
        self.assertFalse(r["comparacao_original_mesmo_problema"])
        original = r["malha_original"]
        self.assertEqual(original["dijkstra_A_B"]["custo"], 6)
        self.assertEqual(original["hamiltoniano_direto"]["ordens_testadas"], 24)
        self.assertEqual(original["hamiltoniano_direto"]["nos_finalizados_dijkstra"], 0)
        self.assertEqual(original["passeio_no_fecho"]["execucoes_dijkstra"], 25)
        controle = r["controle_mesma_instancia_metrica"]
        self.assertEqual(controle["forca_bruta"]["custo"], controle["dijkstra_mais_busca_exata"]["custo"])
        self.assertGreaterEqual(controle["forca_bruta"]["tempo_ms_mediana"], 0)

    def test_repeticoes_invalidas(self):
        for valor in (0, -1, True):
            with self.assertRaises(ValueError):
                medir(tsp_forca_bruta, None, 1, repeticoes=valor)
