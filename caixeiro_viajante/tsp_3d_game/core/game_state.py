"""Estado do jogo e movimento físico testável sem abrir uma janela."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

from .graph_manager import pontos_estrada
from .modelos import Cenario, MatrizDistancias, Posicao, ResultadoRota


@dataclass
class EstadoJogo:
    modo: str = "Desafio Humano"
    modalidade: str = "rodoviario"
    algoritmo: str = "OR-Tools + GLS"
    status: str = "Preparando missão"
    ordem_manual: list[int] = field(default_factory=list)
    manual: ResultadoRota | None = None
    ativa: ResultadoRota | None = None
    resultados: dict[str, ResultadoRota] = field(default_factory=dict)
    ocupada: bool = False
    velocidade: float = 1.0
    pagina_destinos: int = 0

    @property
    def referencia(self) -> ResultadoRota | None:
        candidatas = [r for r in self.resultados.values() if not r.reotimizacao]
        return min(candidatas, key=lambda r: r.custo) if candidatas else None


@dataclass
class Segmento:
    inicio: Posicao
    fim: Posicao
    no_chegada: int | None
    entrega: int | None = None

    @property
    def comprimento(self) -> float:
        return math.dist(self.inicio, self.fim)


class SimulacaoPercurso:
    """Avança pela geometria das ruas e entrega apenas no fim de cada perna.

    Eventos dinâmicos aguardam o próximo cruzamento. Assim, o veículo nunca
    é teleportado para o início da rua durante uma reotimização.
    """

    def __init__(self, cenario: Cenario, matriz: MatrizDistancias, ordem: list[int],
                 metros_por_unidade: float = 100.0, entregar_origem: bool = False):
        self.segmentos: list[Segmento] = []
        self.escala = metros_por_unidade
        self.cenario = cenario
        self.deposito = cenario.deposito
        for a, b in zip(ordem, ordem[1:]):
            if matriz.modo == "euclidiano":
                self.segmentos.append(Segmento(cenario.posicao(a), cenario.posicao(b), b, b))
                continue
            caminho = matriz.caminhos[a, b]
            for indice, (u, v) in enumerate(zip(caminho, caminho[1:])):
                if cenario.grafo[u][v]["bloqueada"]:
                    raise ValueError("A rota contém uma rua bloqueada; recalcule antes de iniciar.")
                pontos = pontos_estrada(cenario, u, v)
                for j, (p, q) in enumerate(zip(pontos, pontos[1:])):
                    ultimo = j == len(pontos) - 2
                    entrega = b if ultimo and indice == len(caminho) - 2 else None
                    self.segmentos.append(Segmento(p, q, v if ultimo else None, entrega))
        self.indice = 0
        self.progresso = 0.0
        self.posicao = cenario.posicao(ordem[0])
        self.direcao = (0.0, 0.0, 1.0)
        self.ultimo_no = ordem[0]
        self.distancia = 0.0
        self.entregues: set[int] = set()
        if entregar_origem and ordem[0] in cenario.cidades and ordem[0] != cenario.deposito:
            # Numa reotimização, a cidade atual pode ser a primeira entrega
            # pendente da NOVA sequência. Isso é serviço explícito, não trânsito.
            self.entregues.add(ordem[0])
        self.pausada = False
        self.concluida = not self.segmentos
        self.parar_no_proximo_no = False
        self.aguardando_evento = False

    @property
    def entregas_realizadas(self) -> int:
        return len(self.entregues - {self.deposito})

    def avancar(self, segundos: float, velocidade: float = 7.0) -> list[int]:
        novas = []
        if self.pausada or self.concluida or self.aguardando_evento:
            return novas
        restante = max(0.0, segundos * velocidade)
        while restante > 0 and self.indice < len(self.segmentos):
            trecho = self.segmentos[self.indice]
            comprimento = trecho.comprimento
            passo = min(restante, max(0.0, comprimento - self.progresso))
            self.progresso += passo
            self.distancia += passo * self.escala
            restante -= passo
            fracao = min(1.0, self.progresso / comprimento) if comprimento else 1.0
            self.posicao = tuple(p + (q - p) * fracao for p, q in zip(trecho.inicio, trecho.fim))
            self.direcao = tuple(q - p for p, q in zip(trecho.inicio, trecho.fim))
            if self.progresso >= comprimento - 1e-9:
                if trecho.no_chegada is not None:
                    self.ultimo_no = trecho.no_chegada
                if trecho.entrega is not None and trecho.entrega != self.deposito:
                    self.entregues.add(trecho.entrega)
                    novas.append(trecho.entrega)
                self.indice += 1
                self.progresso = 0.0
                if self.parar_no_proximo_no and trecho.no_chegada is not None:
                    self.aguardando_evento = True
                    break
            else:
                break
        self.concluida = self.indice >= len(self.segmentos)
        return novas


def economia_percentual(base: float | None, atual: float) -> float | None:
    return None if not base or base <= 0 else (base - atual) / base * 100


def pontuar(custo: float, referencia: float, entregas: int, total: int, concluida: bool) -> int:
    if custo <= 0 or referencia <= 0 or total <= 0:
        return 0
    eficiencia = min(1.0, referencia / custo)
    cobertura = min(1.0, entregas / total)
    return round(700 * eficiencia * cobertura + 200 * cobertura + (100 if concluida else 0))

