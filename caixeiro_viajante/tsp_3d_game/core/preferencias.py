"""Preferências independentes da missão e do motor de otimização."""
from copy import deepcopy
from pathlib import Path
import json
import math

PADROES = {
    "mostrar_nomes": False, "mostrar_rota_computador": True, "dicas": True,
    "unidade": "km", "qualidade": "Alta", "sombras": True, "brilho_rotas": True,
    "audio_ativo": True, "volume": 0.35, "sensibilidade": 1.0,
    "suavizar_camera": True, "inverter_giro": False, "teclas_movimento": "WASD",
}


def caminho_preferencias():
    return Path(__file__).resolve().parents[2] / "config" / "preferencias_usuario.json"


def validar_preferencias(dados):
    resultado = deepcopy(PADROES)
    for chave, padrao in PADROES.items():
        valor = dados.get(chave, padrao)
        if isinstance(padrao, bool):
            if not isinstance(valor, bool):
                raise ValueError(f"Preferência inválida: {chave}.")
        elif isinstance(padrao, float):
            if isinstance(valor, bool) or not isinstance(valor, (float, int)) or not math.isfinite(valor):
                raise ValueError(f"Valor numérico inválido: {chave}.")
            minimo, maximo = (0, 1) if chave == "volume" else (.25, 2.5)
            if not minimo <= valor <= maximo:
                raise ValueError(f"Valor fora do intervalo: {chave}.")
        else:
            opcoes = {"unidade": ("km", "m"), "qualidade": ("Baixa", "Média", "Alta"),
                      "teclas_movimento": ("WASD", "Setas")}
            if valor not in opcoes[chave]:
                raise ValueError(f"Opção inválida: {chave}.")
        resultado[chave] = valor
    return resultado


def carregar_preferencias(caminho=None):
    try:
        dados = json.loads(Path(caminho or caminho_preferencias()).read_text(encoding="utf-8"))
        return validar_preferencias(dados)
    except (OSError, ValueError, TypeError, AttributeError):
        return deepcopy(PADROES)


def salvar_preferencias(dados, caminho=None):
    valores = validar_preferencias(dados)
    alvo = Path(caminho or caminho_preferencias())
    alvo.parent.mkdir(parents=True, exist_ok=True)
    temporario = alvo.with_suffix(".tmp")
    temporario.write_text(json.dumps(valores, ensure_ascii=False, indent=2), encoding="utf-8")
    temporario.replace(alvo)
    return valores
