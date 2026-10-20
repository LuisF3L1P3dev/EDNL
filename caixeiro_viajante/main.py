"""Entrada do jogo e modo de terminal para verificar o motor matemático."""

import argparse
from dataclasses import asdict
import json
import multiprocessing
from pathlib import Path
import sys

def argumentos():
    parser = argparse.ArgumentParser(description="TSP 3D — O Desafio da Rota Perfeita")
    parser.add_argument("--cidades", type=int, help="Número de cidades, incluindo o depósito (3–100).")
    parser.add_argument("--semente", type=int, help="Semente reproduzível do cenário.")
    parser.add_argument("--tempo", type=float, help="Limite de busca em segundos.")
    parser.add_argument("--sem-interface", action="store_true", help="Executar os cálculos no terminal.")
    parser.add_argument("--comparar", action="store_true", help="Comparar os cinco métodos no terminal.")
    parser.add_argument("--algoritmo", default="OR-Tools + GLS", help="Nome do algoritmo no modo terminal.")
    parser.add_argument("--euclidiano", action="store_true", help="Usar distâncias diretas entre destinos.")
    parser.add_argument("--carregar", type=Path, help="Reabrir um cenário exportado em JSON.")
    parser.add_argument("--teste-grafico", action="store_true", help="Verificação automatizada da janela, com captura e encerramento.")
    parser.add_argument("--captura", type=Path, default=Path("resultados/verificacao_3d.png"))
    return parser.parse_args()


def executar_terminal(config, opcoes, cenario):
    from tsp_3d_game.algorithms.registro import ALGORITMOS, resolver_matriz
    from tsp_3d_game.core.distance_matrix import CacheDistancias
    from tsp_3d_game.core.route_validator import validar_resultado
    from tsp_3d_game.core.persistencia import salvar_sessao
    modo = "euclidiano" if opcoes.euclidiano else "rodoviario"
    matriz = CacheDistancias().calcular(cenario, modo=modo, metros_por_unidade=config["metros_por_unidade"])
    resultados = []
    for nome in ALGORITMOS if opcoes.comparar else [opcoes.algoritmo]:
        if nome == "Held–Karp (exato)" and len(cenario.cidades) > config["limite_held_karp"] and opcoes.comparar:
            print(f"{nome}: ignorado (limite de {config['limite_held_karp']} cidades).")
            continue
        resultado = resolver_matriz(nome, matriz, cenario.deposito,
                                     tempo_limite=config["tempo_otimizacao_segundos"],
                                     limite_held_karp=config["limite_held_karp"])
        validar_resultado(resultado, matriz, cenario)
        resultados.append(resultado)
        print(f"{nome}: {resultado.distancia / 1000:.3f} km | custo {resultado.custo:.3f} | "
              f"{resultado.tempo_segundos:.4f}s | " + ("ótimo comprovado" if resultado.otima_comprovada else "sem prova de ótimo"))
        print(" → ".join(cenario.nome(no) for no in resultado.ordem))
    caminho = salvar_sessao(cenario, resultados, configuracoes=config | {"modalidade": modo})
    print(f"Resultados: {caminho}")


def executar_janela(config, opcoes, cenario):
    from panda3d.core import loadPrcFileData
    loadPrcFileData("", "framebuffer-multisample 1\nmultisamples 4\naudio-library-name null\nsync-video 1\nmodel-cache-dir")
    if sys.platform == "win32":
        # O NTFS não diferencia maiúsculas; o VFS do Panda pode rejeitar caminhos
        # válidos quando a grafia retornada pelo Windows difere da do ambiente.
        loadPrcFileData("", "vfs-case-sensitive #f")
    from ursina import Ursina, application, window
    from tsp_3d_game.app import JogoTSP
    app = Ursina(title=config["titulo"], borderless=False, fullscreen=False,
                 size=tuple(config["tamanho_janela"]), forced_aspect_ratio=16 / 9,
                 development_mode=False, show_ursina_splash=False, vsync=True)
    window.exit_button.visible = False
    window.fps_counter.enabled = False
    jogo = JogoTSP(config, cenario)
    if opcoes.euclidiano:
        jogo.trocar_modalidade()
    if opcoes.teste_grafico:
        from tsp_3d_game.verificacao_grafica import instalar_verificacao
        instalar_verificacao(app, jogo, opcoes.captura)
    try:
        app.run()
    finally:
        jogo.fechar()


def main():
    for saida in (sys.stdout, sys.stderr):
        if hasattr(saida, "reconfigure"):
            saida.reconfigure(encoding="utf-8", errors="replace")
    opcoes = argumentos()
    from tsp_3d_game.core.persistencia import carregar_cenario, carregar_configuracoes
    from tsp_3d_game.core.scenario_generator import gerar_cenario
    config = carregar_configuracoes()
    for argumento, chave in (("cidades", "quantidade_cidades"), ("semente", "semente"),
                            ("tempo", "tempo_otimizacao_segundos")):
        valor = getattr(opcoes, argumento)
        if valor is not None:
            config[chave] = valor
    if not .01 <= config["tempo_otimizacao_segundos"] <= 120:
        raise ValueError("O tempo de processamento deve estar entre 0,01 e 120 segundos.")
    cenario = carregar_cenario(opcoes.carregar) if opcoes.carregar else gerar_cenario(
        config["quantidade_cidades"], config["semente"], config["metros_por_unidade"])
    if opcoes.sem_interface:
        executar_terminal(config, opcoes, cenario)
    else:
        executar_janela(config, opcoes, cenario)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        main()
    except (ValueError, ImportError, TimeoutError) as erro:
        print(f"Não foi possível iniciar: {erro}", file=sys.stderr)
        if isinstance(erro, ImportError):
            print("Instale as dependências com: python -m pip install -r requirements.txt", file=sys.stderr)
        raise SystemExit(1)


