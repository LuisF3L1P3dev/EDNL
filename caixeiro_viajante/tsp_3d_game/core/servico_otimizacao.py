"""Processo trabalhador persistente: nunca importa nem manipula Ursina."""

from __future__ import annotations

import multiprocessing as mp
from queue import Empty

from ..algorithms.registro import ALGORITMOS, resolver_matriz
from .distance_matrix import CacheDistancias
from .route_validator import validar_resultado


def executar_trabalhador(pedidos, respostas, cancelar, encerrar):
    cache = CacheDistancias()
    while not encerrar.is_set():
        try:
            pedido = pedidos.get(timeout=.15)
        except Empty:
            continue
        if pedido is None:
            return
        identificador, acao, dados = pedido
        cancelar.clear()
        try:
            cenario = dados["cenario"]
            inicio = dados.get("inicio", cenario.deposito)
            fim = cenario.deposito
            destinos = dados.get("destinos", cenario.cidades)
            matriz = cache.calcular(cenario, destinos, dados.get("modalidade", "rodoviario"),
                                     dados.get("escala", 100.0), cancelar.is_set)
            respostas.put((identificador, "matriz", matriz))
            if acao == "preparar":
                respostas.put((identificador, "concluido", None))
                continue
            nomes = [dados.get("algoritmo", ALGORITMOS[0])] if acao != "comparar" else ALGORITMOS
            for nome in nomes:
                if cancelar.is_set():
                    raise InterruptedError("Cálculo cancelado.")
                if nome == "Held–Karp (exato)" and len(destinos) > dados.get("limite_held_karp", 12) and acao == "comparar":
                    respostas.put((identificador, "aviso", f"Held–Karp ignorado: limite de {dados.get('limite_held_karp', 12)} cidades."))
                    continue
                respostas.put((identificador, "status", f"Calculando {nome}…"))
                try:
                    resultado = resolver_matriz(nome, matriz, inicio, fim,
                                                 dados.get("tempo_limite", 3.0),
                                                 dados.get("limite_held_karp", 12), cancelar.is_set)
                    validar_resultado(resultado, matriz, cenario, inicio, fim)
                    respostas.put((identificador, "resultado", resultado))
                except (ValueError, TimeoutError) as erro:
                    if acao != "comparar":
                        raise
                    respostas.put((identificador, "aviso", str(erro)))
            respostas.put((identificador, "concluido", None))
        except InterruptedError:
            respostas.put((identificador, "cancelado", None))
        except Exception as erro:
            respostas.put((identificador, "erro", f"{type(erro).__name__}: {erro}"))


class ServicoOtimizacao:
    def __init__(self):
        contexto = mp.get_context("spawn")
        self.pedidos = contexto.Queue()
        self.respostas = contexto.Queue()
        self.cancelar_evento = contexto.Event()
        self.encerrar_evento = contexto.Event()
        self.processo = contexto.Process(target=executar_trabalhador,
            args=(self.pedidos, self.respostas, self.cancelar_evento, self.encerrar_evento),
            name="NEXUS-Otimizacao", daemon=True)
        self.processo.start()
        self.identificador = 0

    def enviar(self, acao, **dados):
        self.cancelar_evento.set()
        # Descarta pedidos que ainda não começaram; a interface só usa o mais recente.
        while True:
            try:
                self.pedidos.get_nowait()
            except Empty:
                break
        self.identificador += 1
        self.pedidos.put((self.identificador, acao, dados))
        return self.identificador

    def receber(self):
        mensagens = []
        while True:
            try:
                mensagem = self.respostas.get_nowait()
            except Empty:
                break
            if mensagem[0] == self.identificador:
                mensagens.append(mensagem[1:])
        return mensagens

    def fechar(self):
        self.cancelar_evento.set()
        self.encerrar_evento.set()
        self.processo.join(timeout=.6)
        if self.processo.is_alive():
            self.processo.terminate()
            self.processo.join(timeout=.5)
        self.pedidos.close()
        self.respostas.close()

