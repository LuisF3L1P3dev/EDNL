"""Verifica o cadastro provisório; não certifica os pesos da TSP-004."""

import json
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Mapa18Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (PROJECT_ROOT / "data" / "mapa_18.json").open(encoding="utf-8") as source:
            cls.mapa = json.load(source)

    def test_cadastro_permanece_nao_validado_com_referencia(self):
        self.assertEqual(self.mapa["id"], "mapa_18")
        self.assertIs(self.mapa["validado"], False)
        self.assertIs(self.mapa["direcionado"], False)
        self.assertEqual(
            self.mapa["referencia"], "assets/referencias/mapa_18_original.png"
        )
        self.assertTrue((PROJECT_ROOT / self.mapa["referencia"]).is_file())
        self.assertIn("auditoria", self.mapa["observacoes"])

    def test_dezoito_ids_unicos_preservados(self):
        ids = [node["id"] for node in self.mapa["nos"]]
        self.assertEqual(len(ids), 18)
        self.assertTrue(all(type(node_id) is int for node_id in ids))
        self.assertEqual(set(ids), set(range(1, 19)))

    def test_coordenadas_normalizadas_para_desenho(self):
        self.assertEqual(self.mapa["sistema_coordenadas"], "normalizadas_0_1")
        for node in self.mapa["nos"]:
            for axis in ("x", "y"):
                with self.subTest(node=node["id"], axis=axis):
                    self.assertIsInstance(node[axis], (int, float))
                    self.assertGreaterEqual(node[axis], 0)
                    self.assertLessEqual(node[axis], 1)
        positions = {(node["x"], node["y"]) for node in self.mapa["nos"]}
        self.assertEqual(len(positions), 18)

    def test_ligacoes_provisorias_sem_duplicatas_ou_extremos_invalidos(self):
        self.assertEqual(len(self.mapa["arestas"]), 45)
        pairs = set()
        known_weights = 0
        for edge in self.mapa["arestas"]:
            a, b = edge["origem"], edge["destino"]
            with self.subTest(edge=(a, b)):
                self.assertIs(type(a), int)
                self.assertIs(type(b), int)
                self.assertIn(a, range(1, 19))
                self.assertIn(b, range(1, 19))
                self.assertNotEqual(a, b)
                pair = tuple(sorted((a, b)))
                self.assertNotIn(pair, pairs)
                pairs.add(pair)
                if edge["peso"] is not None:
                    self.assertIs(type(edge["peso"]), int)
                    self.assertGreater(edge["peso"], 0)
                    known_weights += 1
        self.assertEqual(known_weights, 44)

    def test_peso_desconhecido_9_14_nao_recebe_valor_inventado(self):
        unknown = [edge for edge in self.mapa["arestas"] if edge["peso"] is None]
        self.assertEqual(len(unknown), 1)
        self.assertEqual((unknown[0]["origem"], unknown[0]["destino"]), (9, 14))
        self.assertIn("existência e peso a confirmar", unknown[0]["observacao"])
        self.assertTrue(any("9-14" in item for item in self.mapa["pendencias"]))

    def test_associacao_do_rotulo_56_explicitamente_provisoria(self):
        edge = next(
            edge for edge in self.mapa["arestas"]
            if (edge["origem"], edge["destino"]) == (4, 14)
        )
        self.assertEqual(edge["peso"], 56)
        self.assertIn("provisória", edge["observacao"])
        self.assertTrue(any("4-14" in item for item in self.mapa["pendencias"]))


if __name__ == "__main__":
    unittest.main()
