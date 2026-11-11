"""Contrato dos dados fixos do mapa 5, conferido contra a figura da aula.

Estes testes validam a transcrição, sem implementar o carregador de grafos
ou os algoritmos das próximas tarefas. Não dependem de Pygame.
"""

import json
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Transcrição independente da imagem: alterações exigem nova conferência visual.
EXPECTED_WEIGHTS = {
    (1, 2): 2,
    (1, 4): 3,
    (1, 5): 6,
    (2, 3): 4,
    (2, 4): 3,
    (3, 4): 7,
    (3, 5): 3,
    (4, 5): 3,
}


class Mapa05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (PROJECT_ROOT / "data" / "mapa_05.json").open(encoding="utf-8") as source:
            cls.mapa = json.load(source)

    def test_metadata_e_referencia_original(self):
        self.assertEqual(self.mapa["id"], "mapa_05")
        self.assertIs(self.mapa["direcionado"], False)
        self.assertIs(self.mapa["validado"], True)
        self.assertEqual(
            self.mapa["referencia"], "assets/referencias/mapa_05_original.png"
        )
        self.assertTrue((PROJECT_ROOT / self.mapa["referencia"]).is_file())

    def test_cinco_ids_unicos_preservados(self):
        ids = [node["id"] for node in self.mapa["nos"]]
        self.assertEqual(len(ids), 5)
        self.assertTrue(all(type(node_id) is int for node_id in ids))
        self.assertEqual(set(ids), {1, 2, 3, 4, 5})

    def test_coordenadas_normalizadas_preservam_disposicao_da_figura(self):
        self.assertEqual(self.mapa["sistema_coordenadas"], "normalizadas_0_1")
        nodes = {node["id"]: node for node in self.mapa["nos"]}
        for node in nodes.values():
            for axis in ("x", "y"):
                with self.subTest(node=node["id"], axis=axis):
                    self.assertGreaterEqual(node[axis], 0)
                    self.assertLessEqual(node[axis], 1)
        self.assertLess(nodes[1]["x"], nodes[2]["x"])
        self.assertLess(nodes[2]["x"], nodes[3]["x"])
        self.assertLess(nodes[4]["x"], nodes[5]["x"])
        self.assertLess(nodes[2]["y"], nodes[1]["y"])
        self.assertLess(nodes[1]["y"], nodes[4]["y"])
        self.assertLess(nodes[3]["y"], nodes[5]["y"])

    def test_oito_arestas_com_todos_os_pesos_da_figura(self):
        edges = self.mapa["arestas"]
        self.assertEqual(len(edges), 8)
        weights = {}
        for edge in edges:
            a, b, weight = edge["origem"], edge["destino"], edge["peso"]
            with self.subTest(edge=(a, b)):
                self.assertIn(a, {1, 2, 3, 4, 5})
                self.assertIn(b, {1, 2, 3, 4, 5})
                self.assertNotEqual(a, b)
                self.assertIs(type(weight), int)
                self.assertGreater(weight, 0)
                pair = tuple(sorted((a, b)))
                self.assertNotIn(pair, weights, "Aresta não direcionada duplicada")
                weights[pair] = weight
        self.assertEqual(weights, EXPECTED_WEIGHTS)

    def test_ligacoes_ausentes_nao_completam_o_grafo(self):
        pairs = {
            frozenset((edge["origem"], edge["destino"]))
            for edge in self.mapa["arestas"]
        }
        self.assertNotIn(frozenset((1, 3)), pairs)
        self.assertNotIn(frozenset((2, 5)), pairs)

    def test_ciclo_de_referencia_e_inverso_custam_15(self):
        weights = {
            frozenset((edge["origem"], edge["destino"])): edge["peso"]
            for edge in self.mapa["arestas"]
        }
        for route in ((1, 2, 3, 5, 4, 1), (1, 4, 5, 3, 2, 1)):
            with self.subTest(route=route):
                self.assertEqual(route[0], route[-1])
                self.assertEqual(set(route[:-1]), {1, 2, 3, 4, 5})
                self.assertEqual(len(route[:-1]), 5)
                cost = sum(weights[frozenset((a, b))] for a, b in zip(route, route[1:]))
                self.assertEqual(cost, 15)


if __name__ == "__main__":
    unittest.main()
