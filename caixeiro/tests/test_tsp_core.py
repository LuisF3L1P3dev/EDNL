"""Validação da representação do grafo (TSP-006), sem Pygame."""

import copy
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import tempfile
import unittest

from tsp_core import Aresta, GrafoInvalidoError, MapaNaoValidadoError, No, carregar_mapa


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = object()


class GrafoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "mapa.json"
        self.dados = {
            "id": "exemplo", "nome": "Exemplo", "direcionado": False,
            "validado": True, "referencia": "referencia.png",
            "sistema_coordenadas": "normalizadas_0_1",
            "nos": [
                {"id": 1, "x": 0, "y": 0},
                {"id": 2, "x": 1, "y": 1},
                {"id": 7, "x": 0.5, "y": 0.5},
            ],
            "arestas": [{"origem": 1, "destino": 2, "peso": 4}],
        }

    def carregar(self, dados=DEFAULT_DATA):
        self.path.write_text(json.dumps(self.dados if dados is DEFAULT_DATA else dados), encoding="utf-8")
        return carregar_mapa(self.path)

    def test_mapa_05_adjacencia_completa_nos_dois_sentidos(self):
        grafo = carregar_mapa(PROJECT_ROOT / "data" / "mapa_05.json")
        self.assertEqual(grafo.ids, (1, 2, 3, 4, 5))
        self.assertEqual(len(grafo.arestas), 8)
        self.assertEqual(grafo.adjacencia(), {
            1: {2: 2, 4: 3, 5: 6}, 2: {1: 2, 3: 4, 4: 3},
            3: {2: 4, 4: 7, 5: 3}, 4: {1: 3, 2: 3, 3: 7, 5: 3},
            5: {1: 6, 3: 3, 4: 3},
        })

    def test_mapa_18_pode_ser_inspecionado_mas_bloqueia_calculos(self):
        grafo = carregar_mapa(PROJECT_ROOT / "data" / "mapa_18.json")
        self.assertEqual(len(grafo.nos), 18)
        self.assertEqual(len(grafo.arestas), 45)
        unknown = [a for a in grafo.arestas if a.peso is None]
        self.assertEqual([(a.origem, a.destino) for a in unknown], [(9, 14)])
        self.assertIn("peso ausente", unknown[0].observacao)
        for operacao in (grafo.exigir_validado, grafo.adjacencia):
            with self.subTest(operacao=operacao.__name__):
                with self.assertRaisesRegex(MapaNaoValidadoError, "9-14"):
                    operacao()

    def test_nao_validado_bloqueia_mesmo_com_todos_os_pesos_conhecidos(self):
        self.dados["validado"] = False
        self.dados["pendencias"] = ["Aguardar conferência da fonte."]
        grafo = self.carregar()
        with self.assertRaisesRegex(MapaNaoValidadoError, "Aguardar conferência"):
            grafo.adjacencia()

    def test_pendente_sem_descricao_ainda_bloqueia(self):
        self.dados["validado"] = False
        with self.assertRaisesRegex(MapaNaoValidadoError, "Auditoria ainda não concluída"):
            self.carregar().adjacencia()

    def test_validado_com_peso_desconhecido_ou_pendencias_e_invalido(self):
        for modificacao in ("peso", "pendencias"):
            dados = copy.deepcopy(self.dados)
            if modificacao == "peso":
                dados["arestas"][0]["peso"] = None
            else:
                dados["pendencias"] = ["Não auditado."]
            with self.subTest(caso=modificacao):
                with self.assertRaisesRegex(GrafoInvalidoError, "marcado como validado"):
                    self.carregar(dados)

    def test_pesos_zero_e_fracionario_preservados_e_no_isolado(self):
        for peso in (0, 1.25):
            self.dados["arestas"][0]["peso"] = peso
            with self.subTest(peso=peso):
                grafo = self.carregar()
                self.assertEqual(grafo.adjacencia(), {1: {2: peso}, 2: {1: peso}, 7: {}})
                self.assertIs(type(grafo.arestas[0].peso), type(peso))

    def test_coordenadas_nao_alteram_peso_ou_criam_ligacoes(self):
        antes = self.carregar().adjacencia()
        self.dados["nos"][0].update(x=1, y=1)
        self.dados["nos"][1].update(x=0, y=0)
        depois = self.carregar().adjacencia()
        self.assertEqual(antes, depois)
        self.assertNotIn(7, depois[1])
        self.assertNotIn(1, depois[1])

    def test_grafo_sem_arestas_e_nos_isolados_sao_representaveis(self):
        self.dados["arestas"] = []
        self.assertEqual(self.carregar().adjacencia(), {1: {}, 2: {}, 7: {}})

    def test_dados_e_adjacencia_nao_podem_ser_mutados(self):
        grafo = self.carregar()
        with self.assertRaises(FrozenInstanceError):
            grafo.validado = False
        with self.assertRaises(FrozenInstanceError):
            grafo.nos[0].x = 0.7
        with self.assertRaises(FrozenInstanceError):
            grafo.arestas[0].peso = 999
        adj = grafo.adjacencia()
        with self.assertRaises(TypeError):
            adj[1] = {}
        with self.assertRaises(TypeError):
            adj[1][2] = 999
        self.assertEqual(grafo.adjacencia()[1][2], 4)

    def test_rejeita_ids_invalidos_e_duplicados(self):
        for node_id in (True, "1", 1.0, 0, -1, None, 2):
            dados = copy.deepcopy(self.dados)
            dados["nos"][0]["id"] = node_id
            with self.subTest(id=node_id):
                with self.assertRaises(GrafoInvalidoError):
                    self.carregar(dados)

    def test_rejeita_extremos_invalidos_e_lacos(self):
        for destino in (99, True, "2", 2.0, 0, None, 1):
            dados = copy.deepcopy(self.dados)
            dados["arestas"][0]["destino"] = destino
            with self.subTest(destino=destino):
                with self.assertRaises(GrafoInvalidoError):
                    self.carregar(dados)

    def test_rejeita_arestas_duplicadas_inclusive_invertidas(self):
        for a, b in ((1, 2), (2, 1)):
            dados = copy.deepcopy(self.dados)
            dados["arestas"].append({"origem": a, "destino": b, "peso": 99})
            with self.subTest(aresta=(a, b)):
                with self.assertRaisesRegex(GrafoInvalidoError, "duplicada"):
                    self.carregar(dados)

    def test_rejeita_pesos_negativos_booleanos_textos_e_nao_finitos(self):
        for peso in (-1, -0.25, True, "4", [], {}, float("nan"), float("inf"), -float("inf")):
            dados = copy.deepcopy(self.dados)
            dados["arestas"][0]["peso"] = peso
            with self.subTest(peso=peso):
                with self.assertRaisesRegex(GrafoInvalidoError, "peso deve ser"):
                    self.carregar(dados)

    def test_rejeita_coordenadas_invalidas(self):
        for eixo in ("x", "y"):
            for valor in (-0.01, 1.01, True, None, "0.5", float("nan"), float("inf")):
                dados = copy.deepcopy(self.dados)
                dados["nos"][0][eixo] = valor
                with self.subTest(eixo=eixo, valor=valor):
                    with self.assertRaisesRegex(GrafoInvalidoError, "coordenada"):
                        self.carregar(dados)

    def test_rejeita_metadados_invalidos(self):
        for campo, valores in {
            "direcionado": (True, 0, None, "false"),
            "validado": (1, None, "true"),
            "id": ("", "  ", None), "nome": ("", 18), "referencia": (None, ""),
            "sistema_coordenadas": ("pixels", None), "observacoes": (None,),
            "pendencias": (None, "aguardar", [None], [""]),
        }.items():
            for valor in valores:
                dados = copy.deepcopy(self.dados)
                dados[campo] = valor
                with self.subTest(campo=campo, valor=valor):
                    with self.assertRaises(GrafoInvalidoError):
                        self.carregar(dados)

    def test_rejeita_campos_obrigatorios_ausentes_e_estruturas_invalidas(self):
        casos = [[], "mapa", None, {**self.dados, "nos": []}]
        for campo in self.dados:
            dados = copy.deepcopy(self.dados)
            del dados[campo]
            casos.append(dados)
        for campo in ("nos", "arestas"):
            for valor in ({}, None, "lista", [None], [{}]):
                casos.append({**self.dados, campo: valor})
        for indice, dados in enumerate(casos):
            with self.subTest(caso=indice):
                with self.assertRaises(GrafoInvalidoError):
                    self.carregar(dados)

    def test_rejeita_json_quebrado_chaves_duplicadas_e_utf8_invalido(self):
        for conteudo in (b'{"id":', b'{"validado": false, "validado": true}', b'\xff'):
            self.path.write_bytes(conteudo)
            with self.subTest(conteudo=conteudo):
                with self.assertRaises(GrafoInvalidoError):
                    carregar_mapa(self.path)

    def test_arquivo_inexistente_produz_erro_claro(self):
        with self.assertRaisesRegex(GrafoInvalidoError, "Não foi possível ler"):
            carregar_mapa(self.path)

    def test_construcao_direta_e_replace_tambem_validam_invariantes(self):
        with self.assertRaises(GrafoInvalidoError):
            No(True, 0, 0)
        with self.assertRaises(GrafoInvalidoError):
            Aresta(1, 2, -1)
        grafo = self.carregar()
        with self.assertRaises(GrafoInvalidoError):
            replace(grafo, arestas=(Aresta(1, 99, 1),))
        with self.assertRaises(GrafoInvalidoError):
            replace(grafo, arestas=(Aresta(1, 2, None),))
        with self.assertRaises(GrafoInvalidoError):
            replace(grafo, nos=list(grafo.nos))


if __name__ == "__main__":
    unittest.main()
