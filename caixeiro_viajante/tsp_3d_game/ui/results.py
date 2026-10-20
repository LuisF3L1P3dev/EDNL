"""Ranking interativo e exportação de gráficos reais com Matplotlib."""

from datetime import datetime
from pathlib import Path

from ursina import Entity, Text, camera, color, destroy

from ..core.game_state import economia_percentual
from ..core.persistencia import RAIZ
from ..graphics.estilo import CIANO, FUNDO, LARANJA, PAINEL, ROXO, SUAVE, VERDE
from .dashboard import botao, km, painel, texto


class JanelaResultados:
    def __init__(self, jogo, ajuda=False):
        self.jogo = jogo
        self.raiz = Entity(parent=camera.ui, z=-1)
        # O fundo intercepta cliques antes que alcancem a cidade.
        cor_fundo = color.rgba32(6, 12, 24, 235)
        bloqueador = botao(self.raiz, "", 0, 0, camera.aspect_ratio, 1, lambda: None, cor_fundo)
        bloqueador.z = .08
        bloqueador.highlight_color = bloqueador.pressed_color = cor_fundo
        painel(self.raiz, 0, .01, 1.13, .81, PAINEL)
        texto(self.raiz, "MANUAL DO OPERADOR" if ajuda else "BATALHA DE ALGORITMOS", -.51, .374, .96, CIANO)
        botao(self.raiz, "FECHAR", .449, .358, .15, .035, self.fechar)
        if ajuda:
            self._ajuda()
        else:
            self._ranking()

    def _ranking(self):
        j = self.jogo
        resultados = list(j.estado.resultados.values())
        if j.estado.manual:
            resultados.append(j.estado.manual)
        resultados = sorted(resultados, key=lambda r: (r.custo, r.tempo_segundos))
        texto(self.raiz, "Mesma semente, mesmos destinos e mesma matriz de custos.", -.51, .315, .57, SUAVE)
        for x, rotulo in ((-.51, "ALGORITMO"), (-.102, "DISTÂNCIA / CUSTO"), (.12, "TEMPO"), (.31, "GARANTIA")):
            texto(self.raiz, rotulo, x, .263, .48, SUAVE)
        if not resultados:
            texto(self.raiz, "Planeje uma rota ou execute uma comparação para preencher o ranking.", -.51, .15, .61)
        pior = max((r.custo for r in resultados), default=1)
        for i, resultado in enumerate(resultados[:7]):
            y = .209 - i * .063
            cor = LARANJA if resultado.algoritmo == "Rota do jogador" else VERDE if i == 0 else CIANO
            botao(self.raiz, f"{i + 1}. {resultado.algoritmo}", -.325, y, .37, .035,
                  lambda r=resultado: self.mostrar_rota(r), color.hex("#3C3224") if resultado.algoritmo == "Rota do jogador" else color.hex("#194139") if i == 0 else color.hex("#203044"))
            texto(self.raiz, km(resultado.distancia), -.102, y + .01, .57)
            economia = economia_percentual(j.estado.manual.custo if j.estado.manual else j.custo_inicial, resultado.custo)
            texto(self.raiz, f"{resultado.custo:.0f} u.c. · {economia:+.1f}%" if economia is not None else f"{resultado.custo:.0f} u.c.",
                  -.102, y - .01, .39, SUAVE)
            texto(self.raiz, f"{resultado.tempo_segundos:.3f} s", .12, y + .01, .55, SUAVE)
            texto(self.raiz, f"{resultado.melhorias} melhorias" if resultado.melhorias is not None else "melhorias: n/d",
                  .12, y - .01, .37, SUAVE)
            texto(self.raiz, "Exato" if resultado.otima_comprovada else "≤ 1,5×" if resultado.algoritmo == "Christofides" else "Aproximado",
                  .31, y + .01, .52, VERDE if resultado.otima_comprovada else SUAVE)
            largura = .99 * resultado.custo / pior if pior else .001
            painel(self.raiz, -.51 + largura / 2, y - .024, largura, .005, cor, z=-.02)
        texto(self.raiz, "Clique no algoritmo para exibir sua rota no mapa.", -.51, -.265, .53, SUAVE)
        texto(self.raiz, "Economia sobre a rota manual ou inicial. Ótimo exige prova exata.", -.51, -.294, .51, SUAVE)
        botao(self.raiz, "Exportar gráfico PNG", -.335, -.348, .34, .04, self.exportar_grafico)
        botao(self.raiz, "Salvar resultados JSON", .075, -.348, .34, .04, j.exportar)
        self.resultados = resultados

    def _ajuda(self):
        linhas = [
            "01  Escolha o modo, o número de cidades e uma semente. Gere o mapa.",
            "02  Desafio Humano: clique nas cidades na ordem das entregas.",
            "      A base abre a rota; o retorno é incluído após a última seleção.",
            "03  Otimizar calcula uma solução; comparar executa os cinco métodos.",
            "04  Iniciar simulação faz o caminhão percorrer as ruas da rota ativa.",
            "05  G mostra o grafo. C alterna a câmera. Espaço pausa a viagem.",
            "06  Botão direito gira, roda aproxima e WASD desloca a câmera.",
            "07  Rever etapas reproduz decisões realmente registradas no cálculo.",
            "08  Bloqueios e obras aguardam o próximo cruzamento e recalculam",
            "      somente as entregas restantes, terminando no depósito.",
            "09  Modo euclidiano é uma abstração: o veículo representa um drone.",
            "      Os segmentos diretos não representam ruas ou passagens físicas.",
            "10  Held–Karp prova o ótimo até o limite configurado (12 por padrão).",
            "      GLS e 2-opt não provam o ótimo. Christofides exige TSP métrico.",
            "Futuros: Concorde, LKH, genéticos, formigas e recozimento simulado.",
        ]
        texto(self.raiz, "\n".join(linhas), -.51, .292, .64, SUAVE, line_height=1.5)

    def mostrar_rota(self, resultado):
        self.jogo.exibir_resultado(resultado, animar=False)
        self.fechar()

    def exportar_grafico(self):
        if not self.resultados:
            return
        # Este trabalho de exportação ocorre sob demanda, com a simulação pausada.
        import os
        pasta_cache = RAIZ / ".cache" / "matplotlib"
        pasta_cache.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", str(pasta_cache))
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        with plt.style.context("dark_background"):
            figura, eixos = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
            nomes = [r.algoritmo for r in self.resultados]
            cores = ["#FFB020" if r.algoritmo == "Rota do jogador" else "#40E39B" for r in self.resultados]
            eixos[0].barh(nomes, [r.distancia / 1000 for r in self.resultados], color=cores)
            eixos[0].set_xlabel("Distância (km)")
            eixos[0].invert_yaxis()
            eixos[1].barh(nomes, [r.tempo_segundos for r in self.resultados], color="#00D1FF")
            eixos[1].set_xlabel("Tempo de execução (s)")
            eixos[1].invert_yaxis()
            figura.suptitle(f"NEXUS LOGISTICS · Semente {self.jogo.cenario.semente} · {len(self.jogo.cenario.cidades)} cidades")
            pasta = RAIZ / "resultados"
            pasta.mkdir(exist_ok=True)
            caminho = pasta / f"comparacao_{datetime.now():%Y%m%d_%H%M%S}.png"
            figura.savefig(caminho, dpi=160)
            plt.close(figura)
        self.jogo.notificar("GRÁFICO SALVO", caminho.name)

    def fechar(self):
        destroy(self.raiz)
        self.jogo.janela_resultados = None

