"""Regressão: 44 pesos conferidos nas imagens e 9-14=1 definido pelo usuário."""

import hashlib
import json
from pathlib import Path
import struct
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Conferência visual de pcv-exemplo.png e pcv-grafo.png, do próprio autor.
# 9-14 complementado explicitamente pelo usuário; não foi lido da imagem.
EXPECTED_WEIGHTS = {
    (1, 2): 20, (1, 8): 29, (1, 12): 29, (1, 13): 37,
    (2, 3): 25, (2, 8): 28, (2, 12): 39,
    (3, 4): 25, (3, 8): 30, (3, 13): 54,
    (4, 5): 39, (4, 6): 32, (4, 7): 42, (4, 9): 23,
    (4, 10): 33, (4, 14): 56,
    (5, 6): 12, (5, 7): 26, (5, 10): 19,
    (6, 7): 17, (6, 10): 35, (6, 11): 30, (7, 11): 38,
    (8, 12): 25, (8, 13): 22,
    (9, 10): 26, (9, 13): 34, (9, 14): 1, (9, 16): 43,
    (10, 11): 24, (10, 14): 30, (10, 15): 19,
    (11, 15): 26, (11, 18): 36,
    (12, 13): 27, (12, 16): 43, (13, 14): 24, (13, 16): 19,
    (14, 15): 20, (14, 16): 19, (14, 17): 17,
    (15, 17): 18, (15, 18): 21, (16, 17): 26, (17, 18): 15,
}


class Mapa18Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (PROJECT_ROOT / "data" / "mapa_18.json").open(encoding="utf-8") as source:
            cls.mapa = json.load(source)

    def test_cadastro_validado_com_referencia(self):
        self.assertEqual(self.mapa["id"], "mapa_18")
        self.assertIs(self.mapa["validado"], True)
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

    def test_ligacoes_sem_duplicatas_ou_extremos_invalidos(self):
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
        self.assertEqual(known_weights, 45)

    def test_peso_9_14_definido_pelo_usuario_com_proveniencia(self):
        unknown = [edge for edge in self.mapa["arestas"] if edge["peso"] is None]
        self.assertEqual(unknown, [])
        edge = next(a for a in self.mapa["arestas"] if (a["origem"], a["destino"]) == (9, 14))
        self.assertEqual(edge["peso"], 1)
        self.assertIn("usuário", edge["observacao"])
        complemento = self.mapa["auditoria"]["complemento_usuario"]
        self.assertEqual((complemento["origem"], complemento["destino"], complemento["peso"]), (9, 14, 1))
        self.assertEqual(complemento["tipo"], "definicao_explicita_usuario")
        self.assertEqual(complemento["mensagem"], "o peso da aresta 9 - 14 é 1")
        self.assertEqual(self.mapa["pendencias"], [])

    def test_rotulo_56_confirmado_em_4_14(self):
        edge = next(
            edge for edge in self.mapa["arestas"]
            if (edge["origem"], edge["destino"]) == (4, 14)
        )
        self.assertEqual(edge["peso"], 56)
        self.assertIn("confirmado", edge["observacao"])
        self.assertEqual(len(self.mapa["pendencias"]), 0)

    def test_todos_os_pesos_e_ligacoes_conferidos(self):
        actual = {
            tuple(sorted((edge["origem"], edge["destino"]))): edge["peso"]
            for edge in self.mapa["arestas"]
        }
        self.assertEqual(len(EXPECTED_WEIGHTS), 45)
        self.assertEqual(actual, EXPECTED_WEIGHTS)

    def test_fontes_da_auditoria_preservadas_com_hash_e_resolucao(self):
        audit = self.mapa["auditoria"]
        self.assertEqual(audit["estado"], "validado_com_definicao_usuario")
        self.assertTrue((PROJECT_ROOT / audit["relatorio"]).is_file())
        self.assertEqual(len(audit["fontes"]), 2)
        for source in audit["fontes"]:
            with self.subTest(source=source["arquivo"]):
                raw = (PROJECT_ROOT / source["arquivo"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), source["sha256"])
                self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(
                    struct.unpack(">II", raw[16:24]),
                    (source["largura"], source["altura"]),
                )


if __name__ == "__main__":
    unittest.main()
