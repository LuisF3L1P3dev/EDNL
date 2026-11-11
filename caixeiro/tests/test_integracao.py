"""Contratos entre cadastro, algoritmos, eventos e percurso físico."""
import math
from pathlib import Path
import unittest
from fixtures import mapa_18_pendente
from test_tsp import exemplo
from tsp_core import carregar_mapa, tsp_forca_bruta, tsp_dijkstra, dijkstra, MapaNaoValidadoError

ROOT = Path(__file__).resolve().parents[1]


class IntegracaoTests(unittest.TestCase):
    def test_execucoes_nao_modificam_os_arquivos_de_dados(self):
        arquivos = [ROOT / "data" / nome for nome in ("mapa_05.json", "mapa_18.json")]
        antes = [p.read_bytes() for p in arquivos]
        mapa = carregar_mapa(arquivos[0])
        for origem in mapa.ids:
            self.assertEqual(tsp_forca_bruta(mapa, origem).custo, 15)
            self.assertEqual(tsp_dijkstra(mapa, origem).custo, 15)
        self.assertEqual(antes, [p.read_bytes() for p in arquivos])

    def test_passeio_no_fecho_nao_e_mesmo_problema_que_hamiltoniano(self):
        mapa = exemplo((1, 2, 3), ((1, 2, 1), (2, 3, 1), (1, 3, 10)))
        self.assertEqual(tsp_forca_bruta(mapa, 1).custo, 12)
        r = tsp_dijkstra(mapa, 1)
        self.assertEqual(r.custo, 4)
        self.assertEqual(r.caminho, (1, 2, 3, 2, 1))

    def test_eventos_do_fecho_sao_expandidos_somente_em_arestas_reais(self):
        mapa = exemplo((1, 2, 3, 4), ((1, 2, 1), (1, 3, 1), (1, 4, 1)))
        eventos = []
        tsp_dijkstra(mapa, 1, eventos=eventos)
        adj = mapa.adjacencia()
        candidatos = [p for p in eventos if p.algoritmo == "tsp_fecho"]
        self.assertTrue(candidatos)
        for p in candidatos:
            self.assertEqual(sum(adj[a][b] for a, b in zip(p.caminho, p.caminho[1:])), p.custo)

    def test_todos_os_algoritmos_recusam_instancia_pendente(self):
        mapa = mapa_18_pendente()
        for funcao, args in ((dijkstra, (1, 3)), (tsp_forca_bruta, (1,)), (tsp_dijkstra, (1,))):
            with self.subTest(algoritmo=funcao.__name__), self.assertRaises(MapaNaoValidadoError):
                funcao(mapa, *args)
