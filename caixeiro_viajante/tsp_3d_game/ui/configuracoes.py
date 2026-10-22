"""Modal de preferências com edição transacional e cinco categorias."""
from copy import deepcopy
from ursina import Entity, camera, color, destroy
from .dashboard import botao, painel, texto
from ..core.preferencias import PADROES
from ..graphics.ciclo_vida import destruir_arvore as destroy
from ..graphics.estilo import CIANO, FUNDO, PAINEL, SUAVE, TEXTO, VERDE, ROSA, SUPERFICIE

CATEGORIAS = {
    "Geral": [("mostrar_nomes", "Nomes das cidades", [False, True]),
              ("mostrar_rota_computador", "Exibir rota do computador", [False, True]),
              ("unidade", "Unidade de distância", ["km", "m"]),
              ("dicas", "Dicas de navegação", [False, True])],
    "Gráficos": [("qualidade", "Detalhes do cenário", ["Baixa", "Média", "Alta"]),
                 ("sombras", "Sombras dos objetos", [False, True]),
                 ("brilho_rotas", "Brilho das rotas e entregas", [False, True])],
    "Áudio": [("audio_ativo", "Efeitos de entrega e conclusão", [False, True]),
              ("volume", "Volume dos efeitos", [0., .15, .35, .6, 1.])],
    "Câmera": [("sensibilidade", "Sensibilidade de navegação", [.5, .75, 1., 1.5, 2.]),
               ("suavizar_camera", "Suavizar movimento e zoom", [False, True]),
               ("inverter_giro", "Inverter giro horizontal", [False, True])],
    "Controles": [("teclas_movimento", "Mover pelo mapa", ["WASD", "Setas"])],
}


class JanelaConfiguracoes:
    def __init__(self, jogo):
        self.jogo = jogo
        self.rascunho = deepcopy(jogo.preferencias)
        self.categoria = "Geral"
        self.raiz = Entity(parent=camera.ui, z=-3)
        fundo = botao(self.raiz, "", 0, 0, camera.aspect_ratio, 1, lambda: None,
                      color.rgba32(3, 9, 19, 210), raio=0)
        fundo.moldura.enabled = False
        fundo.z = .3
        fundo.highlight_color = fundo.pressed_color = fundo.color
        painel(self.raiz, 0, 0, 1.10, .72, bloquear=True)
        painel(self.raiz, -.548, 0, .004, .72, CIANO)
        texto(self.raiz, "CONFIGURAÇÕES", -.495, .31, 1.0, titulo=True)
        texto(self.raiz, "Personalize sua operação", -.495, .268, .5, SUAVE)
        self.fechar_x = botao(self.raiz, "×", .485, .30, .045, .035, self.fechar)
        self.abas = {}
        for i, nome in enumerate(CATEGORIAS):
            self.abas[nome] = botao(self.raiz, nome, -.386, .178 - i * .071, .22, .050,
                                     lambda nome=nome: self.mostrar(nome))
        self.conteudo = None
        self.erro = texto(self.raiz, "", -.12, -.235, .46, ROSA)
        botao(self.raiz, "Restaurar padrão", -.36, -.30, .27, .043, self.restaurar)
        botao(self.raiz, "Cancelar", .14, -.30, .20, .043, self.fechar)
        botao(self.raiz, "Aplicar", .38, -.30, .20, .043, self.aplicar, CIANO, FUNDO)
        self.mostrar("Geral")

    def mostrar(self, categoria):
        self.categoria = categoria
        if self.conteudo:
            destroy(self.conteudo)
        self.conteudo = Entity(parent=self.raiz)
        for nome, aba in self.abas.items():
            aba.color = CIANO.tint(-.55) if nome == categoria else SUPERFICIE
        for i, (chave, rotulo, opcoes) in enumerate(CATEGORIAS[categoria]):
            y = .18 - i * .078
            texto(self.conteudo, rotulo, -.18, y + .012, .58)
            valor = self.rascunho[chave]
            exibido = ("Ligado" if valor else "Desligado") if isinstance(valor, bool) else f"{valor * 100:.0f}%" if chave == "volume" else str(valor)
            botao(self.conteudo, exibido, .36, y, .25, .041,
                  lambda c=chave, o=opcoes: self.alternar(c, o), color.hex("#1B4A43") if valor is True else SUPERFICIE)
        if categoria == "Controles":
            texto(self.conteudo, "Roda do mouse: zoom\nBotão direito: girar · botão do meio: deslocar\nO: otimizar · B: comparar · N: novo mapa\nEspaço: pausar · C: câmera · G: grafo\nBackspace: desfazer · Tab: HUD · H: ajuda\nEsc: fechar janela / sair do jogo", -.18, .098, .53, SUAVE)
        if categoria == "Gráficos":
            texto(self.conteudo, "A densidade altera apenas a decoração.\nRuas e destinos da missão são preservados.", -.18, -.095, .5, SUAVE)
        if categoria == "Áudio":
            texto(self.conteudo, "Sinais curtos acompanham entregas e conclusão.\nNão há música de fundo nesta versão.", -.18, -.02, .5, SUAVE)

    def alternar(self, chave, opcoes):
        atual = self.rascunho[chave]
        self.rascunho[chave] = opcoes[(opcoes.index(atual) + 1) % len(opcoes)] if atual in opcoes else opcoes[0]
        self.mostrar(self.categoria)

    def restaurar(self):
        self.rascunho = deepcopy(PADROES)
        self.mostrar(self.categoria)

    def aplicar(self):
        try:
            self.jogo.aplicar_preferencias(self.rascunho)
        except (ValueError, OSError) as erro:
            self.erro.text = str(erro)[:85]
            return
        self.fechar()

    def fechar(self):
        destroy(self.raiz)
        self.jogo.janela_configuracoes = None
