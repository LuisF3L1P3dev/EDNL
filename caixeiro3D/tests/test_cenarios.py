import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tsp_core import carregar_cenarios

ROOT = Path(__file__).resolve().parents[1]


class CenariosTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pasta = Path(self.tmp.name)
        for nome in ('mapa_05.json', 'mapa_18.json'):
            (self.pasta / nome).write_bytes((ROOT / 'data' / nome).read_bytes())

    def modificar(self, arquivo, funcao):
        caminho = self.pasta / arquivo
        dados = json.loads(caminho.read_text(encoding='utf-8'))
        funcao(dados)
        caminho.write_text(json.dumps(dados), encoding='utf-8')

    def test_registro_e_correcoes(self):
        pequeno, grande = carregar_cenarios(self.pasta)
        self.assertEqual((pequeno.id, grande.id), ('mapa_05', 'mapa_18'))
        self.assertEqual((len(pequeno.arestas), len(grande.arestas)), (8, 45))
        adj = grande.adjacencia()
        self.assertEqual((adj[1][3], adj[9][13], adj[9][14]), (37, 34, 1))
        self.assertNotIn(13, adj[1])

    def test_rejeita_registro_identidade_e_pendencia(self):
        self.modificar('mapa_05.json', lambda d: d.update(id='outro'))
        with self.assertRaisesRegex(ValueError, 'identificador'):
            carregar_cenarios(self.pasta)
        self.modificar('mapa_05.json', lambda d: d.update(id='mapa_05', pendencias=['confirmar']))
        with self.assertRaisesRegex(ValueError, 'pendencias'):
            carregar_cenarios(self.pasta)

    def test_rejeita_ids_incompletos(self):
        def alterar(d):
            d['nos'].append({'id': 6, 'x': .5, 'y': .5})
        self.modificar('mapa_05.json', alterar)
        with self.assertRaisesRegex(ValueError, 'nos de 1 a 5'):
            carregar_cenarios(self.pasta)

    def test_rejeita_desconexao_e_contagem(self):
        self.modificar('mapa_05.json', lambda d: d.update(arestas=[a for a in d['arestas'] if 5 not in a[:2]]))
        with self.assertRaisesRegex(ValueError, 'desconectado'):
            carregar_cenarios(self.pasta)
        dados = json.loads((ROOT / 'data/mapa_05.json').read_text(encoding='utf-8'))
        dados['arestas'].pop()
        (self.pasta / 'mapa_05.json').write_text(json.dumps(dados), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '8 arestas'):
            carregar_cenarios(self.pasta)

    def test_arquivo_ausente(self):
        (self.pasta / 'mapa_18.json').unlink()
        with self.assertRaises(FileNotFoundError):
            carregar_cenarios(self.pasta)


if __name__ == '__main__':
    unittest.main()
