"""Composição determinística de quadras, mantendo livre o espaço das estradas."""
import random
from ursina import Entity, Text, color
from .materiais import shader_cidade as lit_with_shadows_shader
from .catalogo_assets import CATALOGO
from .lotes_estaticos import agrupar_estatico


class DecoracaoCidade:
    def __init__(self, mundo):
        self.mundo = mundo
        self.cenario = mundo.cenario
        self.sorteio = random.Random(self.cenario.semente + 2026)
        self.qualidade = mundo.preferencias.get("qualidade", "Alta")
        self.detalhe = {"Baixa": 0, "Média": 1, "Alta": 2}[self.qualidade]
        self.raiz = Entity(parent=mundo.raiz, name="Quadras_decoradas")
        self.letreiros = Entity(parent=mundo.raiz, name="Letreiros")
        self.grupos = []
        self.deposito_posicionado = False
        self._quadras()
        self._margens()
        regioes = {}
        for grupo in self.grupos:
            if grupo.name.startswith("Quadra_"):
                _, linha, coluna = grupo.name.split("_")
                chave = (int(linha) // 3, int(coluna) // 3)
                if chave not in regioes:
                    regioes[chave] = self.raiz.attach_new_node(f"Regiao_{chave}")
                grupo.wrt_reparent_to(regioes[chave])
            else:
                regioes[grupo.name] = grupo
        for regiao in regioes.values():
            agrupar_estatico(regiao)

    def asset(self, pacote, nome, pai, x, y, z, tamanho, giro=0):
        objeto = CATALOGO.criar(pacote, nome, pai, (x, y, z), tamanho, giro)
        if objeto is None:
            objeto = Entity(parent=pai, model="cube", position=(x, y + tamanho / 2, z), scale=tamanho,
                             color=color.hex("#E7DAB9"), shader=lit_with_shadows_shader)
        return objeto

    def cubo(self, pai, posicao, escala, cor):
        return Entity(parent=pai, model="cube", position=posicao, scale=escala,
                      color=color.hex(cor), shader=lit_with_shadows_shader, add_to_scene_entities=False)

    def arvore(self, pai, x, y, z, tamanho=1.2):
        nome = self.sorteio.choice(("tree_detailed", "tree_oak", "tree_default", "tree_detailed_dark"))
        self.asset("nature", nome, pai, x, y, z, tamanho, self.sorteio.choice((0, 90, 180, 270)))

    def _quadras(self):
        c, r = self.cenario, self.sorteio
        for linha in range(c.lado - 1):
            for coluna in range(c.lado - 1):
                if coluna == c.lado // 2 - 1:
                    continue
                grupo = Entity(parent=self.raiz, name=f"Quadra_{linha}_{coluna}", add_to_scene_entities=False)
                self.grupos.append(grupo)
                nos = [linha * c.lado + coluna, linha * c.lado + coluna + 1,
                       (linha + 1) * c.lado + coluna, (linha + 1) * c.lado + coluna + 1]
                x = (coluna - (c.lado - 1) / 2 + .5) * c.espacamento
                z = (linha - (c.lado - 1) / 2 + .5) * c.espacamento
                y = sum(c.posicao(no)[1] for no in nos) / 4 + .035
                self.cubo(grupo, (x, y - .12, z), (4.05, .22, 4.05), "#CED2C4")
                self.cubo(grupo, (x, y + .006, z), (3.75, .026, 3.75), "#75A957")
                tipo = r.random()
                base = c.deposito in nos and not self.deposito_posicionado
                self.deposito_posicionado |= base
                if base or tipo < .19:
                    self._logistica(grupo, x, y, z, base)
                elif tipo < .38:
                    self._parque(grupo, x, y, z)
                else:
                    comercial = tipo > .72
                    for indice, (dx, dz) in enumerate(((-1.0, -1.), (1., -1.), (-1., 1.), (1., 1.))):
                        if comercial:
                            nome = r.choice(("building-a", "building-b", "building-c", "building-d", "building-e", "building-f"))
                            self.asset("commercial", nome, grupo, x + dx, y + .04, z + dz, 1.66, 180 if dz > 0 else 0)
                        else:
                            nome = r.choice(("building-type-a", "building-type-b", "building-type-c", "building-type-f", "building-type-h", "building-type-j"))
                            self.asset("suburban", nome, grupo, x + dx, y + .04, z + dz, 1.58, 180 if dz > 0 else 0)
                        if self.detalhe > 0:
                            self.arvore(grupo, x + dx + .63, y + .05, z + dz + .62, .42)
                    # Passeio interno e pequenas áreas de jardim.
                    self.cubo(grupo, (x, y + .04, z), (.20, .03, 3.9), "#F0EADA")
                    self.cubo(grupo, (x, y + .04, z), (3.9, .03, .20), "#F0EADA")
                if self.detalhe >= 1 and (linha + coluna) % 2 == 0:
                    self.asset("roads", "light-curved", grupo, x - 1.86, y, z - 1.83, .38, 90)
                if self.detalhe == 2:
                    self.asset("roads", "dumpster", grupo, x + 1.65, y, z, .30)

    def _logistica(self, pai, x, y, z, base):
        nome = "building-a" if base else self.sorteio.choice(("building-b", "building-c", "building-e"))
        self.cubo(pai, (x, y + .035, z), (3.76, .035, 3.76), "#657078")
        self.asset("industrial", nome, pai, x, y + .06, z + .55, 2.95, 0)
        # Pátio separado da rede de ruas: carros estacionados são decoração.
        for i in range(4):
            self.cubo(pai, (x - 1.55 + i * .82, y + .061, z - 1.1), (.035, .018, 1.15), "#E6E6CF")
        if self.detalhe > 0:
            for dx, modelo in ((-1.15, "van"), (-.32, "delivery"), (.55, "sedan")):
                self.asset("cars", modelo, pai, x + dx, y + .07, z - 1.05, .86)
            self.asset("industrial", "shipping-container-a", pai, x + 1.55, y + .07, z - .9, .65, 90)
        if base:
            self.cubo(pai, (x, y + .09, z - 1.77), (2.7, .03, .06), "#00C3D6")
            Text(parent=self.letreiros, text="NEXUS", position=(x, y + 1.65, z), scale=14,
                 origin=(0, 0), billboard=True, color=color.hex("#0A3F58"), add_to_scene_entities=False)

    def _parque(self, pai, x, y, z):
        self.cubo(pai, (x, y + .035, z), (3.8, .03, .44), "#E0D3AD")
        self.cubo(pai, (x, y + .035, z), (.44, .03, 3.8), "#E0D3AD")
        for dx, dz in ((-1.0, -1.), (1., -1.), (-1., 1.), (1., 1.)):
            self.arvore(pai, x + dx, y + .04, z + dz, self.sorteio.uniform(.95, 1.35))
            if self.detalhe == 2:
                self.asset("nature", "plant_bush", pai, x + dx * .62, y + .04, z + dz * .62, .40)
        # Bancos simples, agrupados com a quadra.
        if self.detalhe:
            for dz in (-.38, .38):
                self.cubo(pai, (x + .55, y + .19, z + dz), (.65, .08, .19), "#946F43")
                for dx in (.34, .77):
                    self.cubo(pai, (x + dx, y + .10, z + dz), (.055, .20, .13), "#334350")

    def _margens(self):
        if not self.detalhe:
            return
        c, r = self.cenario, self.sorteio
        for lado in (-1, 1):
            grupo = Entity(parent=self.raiz, name=f"Jardins_{lado}", add_to_scene_entities=False)
            self.grupos.append(grupo)
            limite = (c.lado - 1) * c.espacamento / 2
            for i in range(c.lado * (2 if self.detalhe == 2 else 1)):
                z = -limite + i * (2.8 if self.detalhe == 2 else 5.6)
                if z <= limite:
                    self.arvore(grupo, lado * (limite + 2), .08, z, r.uniform(.9, 1.5))
