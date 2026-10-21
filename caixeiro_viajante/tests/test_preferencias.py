"""Preferências persistidas sem depender da interface gráfica."""

import json

import pytest

from tsp_3d_game.core.preferencias import (
    PADROES,
    carregar_preferencias,
    salvar_preferencias,
    validar_preferencias,
)


@pytest.mark.parametrize(
    "chave, valor",
    [
        ("volume", 0), ("volume", 1), ("volume", 0.65),
        ("sensibilidade", 0.25), ("sensibilidade", 2.5),
        ("sensibilidade", 2),
        ("unidade", "km"), ("unidade", "m"),
        ("qualidade", "Baixa"), ("qualidade", "Média"),
        ("qualidade", "Alta"),
        ("teclas_movimento", "WASD"), ("teclas_movimento", "Setas"),
    ],
)
def test_aceita_opcoes_e_limites_inclusivos(chave, valor):
    resultado = validar_preferencias({chave: valor})
    assert resultado[chave] == valor
    assert set(resultado) == set(PADROES)
    assert all(resultado[k] == v for k, v in PADROES.items() if k != chave)


@pytest.mark.parametrize(
    "chave",
    [chave for chave, valor in PADROES.items() if isinstance(valor, bool)],
)
def test_campos_booleanos_exigem_bool_e_aceitam_as_duas_opcoes(chave):
    for valor in (True, False):
        assert validar_preferencias({chave: valor})[chave] is valor
    for valor in (0, 1, "false", None, []):
        with pytest.raises(ValueError, match=chave):
            validar_preferencias({chave: valor})


@pytest.mark.parametrize(
    "chave, valor",
    [
        ("volume", -0.001), ("volume", 1.001),
        ("sensibilidade", 0.249), ("sensibilidade", 2.501),
        ("volume", True), ("sensibilidade", False),
        ("volume", "0.5"), ("sensibilidade", None),
        ("volume", float("nan")), ("volume", float("inf")),
        ("sensibilidade", float("-inf")),
        ("unidade", "milhas"), ("unidade", None),
        ("qualidade", "Ultra"), ("qualidade", 1),
        ("teclas_movimento", "AZERTY"), ("teclas_movimento", []),
    ],
)
def test_rejeita_tipos_opcoes_e_valores_fora_dos_limites(chave, valor):
    with pytest.raises(ValueError, match=chave):
        validar_preferencias({chave: valor})


def test_configuracao_parcial_nao_carrega_chaves_desconhecidas():
    resultado = validar_preferencias({"unidade": "m", "campo_antigo": 123})
    assert resultado == {**PADROES, "unidade": "m"}
    assert "campo_antigo" not in resultado


@pytest.mark.parametrize(
    "conteudo",
    ["{", "null", "[]", '"texto"', "123", '{"volume": 2}'],
)
def test_arquivo_invalido_restaura_padrao_sem_sobrescrever_original(tmp_path, conteudo):
    caminho = tmp_path / "preferencias.json"
    caminho.write_text(conteudo, encoding="utf-8")

    assert carregar_preferencias(caminho) == PADROES
    assert caminho.read_text(encoding="utf-8") == conteudo


def test_arquivo_inexistente_retorna_padrao_sem_criar_arquivo(tmp_path):
    caminho = tmp_path / "ainda_nao_existe.json"
    assert carregar_preferencias(caminho) == PADROES
    assert not caminho.exists()


def test_salvar_e_carregar_em_pasta_nova_preserva_preferencias(tmp_path):
    caminho = tmp_path / "usuario" / "preferencias.json"
    escolhidas = {
        "mostrar_nomes": True,
        "qualidade": "Média",
        "volume": 0,
        "sensibilidade": 2.5,
        "teclas_movimento": "Setas",
    }
    esperado = {**PADROES, **escolhidas}

    assert salvar_preferencias(escolhidas, caminho) == esperado
    assert carregar_preferencias(caminho) == esperado
    assert json.loads(caminho.read_text(encoding="utf-8")) == esperado
    assert "Média" in caminho.read_text(encoding="utf-8")
    assert not caminho.with_suffix(".tmp").exists()


def test_salvar_configuracao_invalida_preserva_arquivo_existente(tmp_path):
    caminho = tmp_path / "preferencias.json"
    salvar_preferencias({"volume": 0.8}, caminho)
    original = caminho.read_bytes()

    with pytest.raises(ValueError, match="volume"):
        salvar_preferencias({"volume": -1}, caminho)

    assert caminho.read_bytes() == original
    assert not caminho.with_suffix(".tmp").exists()


def test_restauracao_e_validacao_nao_compartilham_dicionarios_mutaveis(tmp_path):
    caminho = tmp_path / "inexistente.json"
    primeira = carregar_preferencias(caminho)
    segunda = carregar_preferencias(caminho)
    origem = {"qualidade": "Baixa"}
    validada = validar_preferencias(origem)

    assert primeira is not segunda
    assert primeira is not PADROES
    assert validada is not origem
    primeira["qualidade"] = "valor alterado pelo chamador"
    validada["qualidade"] = "outro valor"
    assert segunda["qualidade"] == PADROES["qualidade"] == "Alta"
    assert origem == {"qualidade": "Baixa"}
    assert carregar_preferencias(caminho) == PADROES


def test_salvar_padrao_restaura_preferencias_persistidas(tmp_path):
    caminho = tmp_path / "preferencias.json"
    salvar_preferencias({"volume": 0, "unidade": "m"}, caminho)
    salvar_preferencias({}, caminho)
    assert carregar_preferencias(caminho) == PADROES
