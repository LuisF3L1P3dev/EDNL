"""Verificação integrada acionada somente por --teste-grafico."""

from pathlib import Path
from time import perf_counter
from copy import deepcopy
from statistics import median
import json

from panda3d.core import Filename, SceneGraphAnalyzer


def instalar_verificacao(app, jogo, captura):
    inicio = perf_counter()
    estado = {"fase": -1, "frames": 0, "espera": 0, "entregas": 0}
    captura = Path(captura).resolve()
    captura.parent.mkdir(parents=True, exist_ok=True)
    preferencias_originais = deepcopy(jogo.preferencias)
    jogo.arquivo_preferencias = captura.with_stem(captura.stem + "_preferencias").with_suffix(".json")
    amostras_quadros = []
    ultimo_quadro = None

    def fotografar(sufixo):
        app.graphicsEngine.renderFrame()
        assert app.win.saveScreenshot(Filename.fromOsSpecific(str(captura.with_stem(captura.stem + sufixo))))

    def verificar_pontes():
        if not hasattr(jogo.mundo, "vias"):
            return
        from ursina import Vec3
        from panda3d.core import (BitMask32, CollisionNode, CollisionRay,
                                 CollisionTraverser, CollisionHandlerQueue)
        vias = jogo.mundo.vias
        assert set(vias.pontes) == {(a, b) for a, b, d in jogo.cenario.grafo.edges(data=True) if d["ponte"]}
        # Raios contra a malha efetivamente desenhada detectam frestas,
        # rampas achatadas e desníveis entre tabuleiro e cruzamentos.
        mascara = vias.raiz.get_collide_mask()
        vias.raiz.set_collide_mask(BitMask32.bit(30))
        sensor = CollisionNode("verificar_piso")
        sensor.set_from_collide_mask(BitMask32.bit(30))
        sensor.set_into_collide_mask(BitMask32.all_off())
        raio = CollisionRay()
        raio.set_direction(0, -1, 0)
        sensor.add_solid(raio)
        caminho_sensor = vias.raiz.attach_new_node(sensor)
        fila, coletor = CollisionHandlerQueue(), CollisionTraverser()
        coletor.add_collider(caminho_sensor, fila)
        try:
            for a, b in vias.pontes:
                pontos = jogo.cenario.grafo[a][b]["pontos"]
                for p, q in zip(pontos, pontos[1:]):
                    for passo in range(13):
                        t = passo / 12
                        x, y, z = [v + (w - v) * t for v, w in zip(p, q)]
                        for lateral in (-.5, 0, .5):
                            # Evita ambiguidade numérica do CollisionRay
                            # exatamente sobre arestas compartilhadas.
                            sx, sz = x + .0001, z + lateral + .0001
                            raio.set_origin(sx, 20, sz)
                            fila.clear_entries()
                            coletor.traverse(vias.raiz)
                            fila.sort_entries()
                            assert fila.get_num_entries(), f"Fresta na ponte {a}-{b}, posição {x, z + lateral}"
                            piso = fila.get_entry(0).get_surface_point(vias.raiz).y
                            previsto = vias.perfil.altura(sx, sz) + .08
                            assert abs(piso - previsto) < .002, f"Piso desalinhado em {a}-{b} ({x}, {z + lateral}): {piso} / {previsto}"
        finally:
            caminho_sensor.remove_node()
            vias.raiz.set_collide_mask(mascara)
        estado["pontes_validadas"] = len(vias.pontes)
        estado["amostras_piso_pontes"] = len(vias.pontes) * 2 * 13 * 3
        controle = jogo.controle_camera
        alvo, escala = Vec3(controle.alvo), controle.escala_desejada
        a, b = vias.pontes[1]
        centro = jogo.cenario.grafo[a][b]["pontos"][1]
        controle.alvo = Vec3(*centro)
        controle.escala_desejada = 12
        controle.atualizar(0, None, False)
        jogo.ui.alternar_hud()
        for rotulo in jogo.mundo.rotulos.values():
            rotulo.enabled = False
        fotografar("_ponte")
        for rotulo in jogo.mundo.rotulos.values():
            rotulo.enabled = True
        jogo.ui.alternar_hud()
        controle.alvo, controle.escala_desejada = alvo, escala
        controle.atualizar(0, None, False)

    def verificar_interface():
        from .graphics.catalogo_assets import CATALOGO
        from .graphics.estilo import VERDE
        from .core.preferencias import PADROES, carregar_preferencias
        from .ui.configuracoes import CATEGORIAS
        assinatura = jogo.cenario.assinatura
        matriz = jogo.matriz
        custos = matriz.custos.copy()
        assert jogo.veiculo.modelo_entrega is not None
        assert len(jogo.veiculo.rodas) == 4
        frente = [r.get_z(jogo.veiculo.raiz) for r in jogo.veiculo.rodas if "front" in r.name]
        tras = [r.get_z(jogo.veiculo.raiz) for r in jogo.veiculo.rodas if "back" in r.name]
        assert min(frente) > max(tras), "A cabine deve apontar para o avanço do veículo."
        assert all(som.clip for som in jogo.audio.sons.values())
        assert CATALOGO.carregamentos < 40
        verificar_pontes()
        jogo.ui.alternar_hud()
        assert not jogo.ui.esquerda.enabled and not jogo.ui.direita.enabled
        jogo.ui.alternar_hud()
        jogo.ui.abrir_missao()
        jogo.ui.quantidade.text = "8"
        jogo.ui.semente.text = "123456"
        jogo.ui.fechar_missao()
        assert jogo.ui.quantidade.text == str(len(jogo.cenario.cidades))
        assert jogo.ui.semente.text == str(jogo.cenario.semente)
        jogo.input("f10")
        janela = jogo.janela_configuracoes
        ordem = jogo.estado.ordem_manual.copy()
        jogo.selecionar_cidade(jogo.cenario.cidades[1])
        assert jogo.estado.ordem_manual == ordem
        for categoria in CATEGORIAS:
            janela.mostrar(categoria)
        janela.mostrar("Geral")
        fotografar("_configuracoes")
        janela.rascunho["unidade"] = "m"
        janela.fechar()
        assert jogo.preferencias == preferencias_originais
        jogo.abrir_configuracoes()
        janela = jogo.janela_configuracoes
        janela.rascunho.update(qualidade="Baixa", sombras=False, brilho_rotas=False,
                               mostrar_nomes=True, mostrar_rota_computador=False, unidade="m")
        janela.aplicar()
        assert jogo.janela_configuracoes is None
        assert jogo.matriz is matriz and (jogo.matriz.custos == custos).all()
        assert jogo.cenario.assinatura == assinatura
        assert not jogo.sol.shadows and not jogo.efeitos.ativo
        assert carregar_preferencias(jogo.arquivo_preferencias) == jogo.preferencias
        ordem_completa = jogo.cenario.cidades + [jogo.cenario.cidades[0]]
        jogo.rotas.desenhar("ativa", matriz, ordem_completa, VERDE, progressiva=True)
        entidade = jogo.rotas.camadas["ativa"]
        assert not entidade.enabled and not entidade.halo.enabled
        criacoes = jogo.rotas.reconstrucoes
        for _ in range(30):
            jogo.rotas.atualizar(.1)
        assert jogo.rotas.camadas["ativa"] is entidade
        assert jogo.rotas.reconstrucoes == criacoes
        jogo.rotas.limpar("ativa")
        jogo.abrir_configuracoes()
        janela = jogo.janela_configuracoes
        janela.restaurar()
        assert janela.rascunho == PADROES and jogo.preferencias["unidade"] == "m"
        janela.fechar()
        jogo.aplicar_preferencias(preferencias_originais)
        assert jogo.matriz is matriz and jogo.cenario.assinatura == assinatura
        jogo.ui.alternar_painel("lista")
        assert jogo.ui.lista.enabled
        jogo.ui.alternar_painel("detalhes")
        assert jogo.ui.detalhes.enabled and not jogo.ui.lista.enabled
        jogo.ui.alternar_painel("detalhes")

    def verificar(tarefa):
        nonlocal ultimo_quadro
        estado["frames"] += 1
        try:
            if perf_counter() - inicio > 90:
                raise TimeoutError(f"Verificação gráfica excedeu 90s, fase {estado['fase']}, status {jogo.estado.status}.")
            if jogo.erro_trabalhador:
                raise AssertionError(jogo.erro_trabalhador)
            if jogo.estado.ocupada:
                return tarefa.cont
            fase = estado["fase"]
            if fase == -1:
                quantidade, semente = len(jogo.cenario.cidades), jogo.cenario.semente
                jogo.ui.abrir_missao()
                jogo.ui.quantidade.text = str(quantidade)
                jogo.ui.semente.text = str(semente + 1)
                jogo.ui.base_pendente = 1
                fotografar("_nova_missao")
                jogo.ui.confirmar_missao()
                assert len(jogo.cenario.cidades) == quantidade and jogo.cenario.semente == semente + 1
                assert jogo.cenario.deposito == jogo.cenario.cidades[1]
                estado["fase"] = 0
            elif fase == 0:
                assert len(jogo.mundo.marcadores) == len(jogo.cenario.cidades)
                verificar_interface()
                jogo.alternar_grafo()
                jogo.trocar_camera()
                jogo.trocar_camera()
                jogo.trocar_camera()
                for no in jogo.cenario.cidades:
                    jogo.selecionar_cidade(no)
                assert jogo.estado.manual is not None
                estado["fase"] = 1
            elif fase == 1:
                jogo.estado.algoritmo = "OR-Tools + GLS"
                jogo.otimizar()
                estado["fase"] = 2
            elif fase == 2:
                assert jogo.estado.ativa.algoritmo == "OR-Tools + GLS"
                jogo.iniciar_simulacao()
                from ursina import Vec3
                controle = jogo.controle_camera
                modo, alvo, escala = controle.modo, Vec3(controle.alvo), controle.escala_desejada
                controle.escolher("Seguir veículo")
                controle.alvo = Vec3(jogo.veiculo.raiz.world_position)
                controle.escala_desejada = min(escala, 28)
                controle.atualizar(0, None, False)
                jogo.mundo.animar(0)
                fotografar("_veiculo")
                controle.escolher(modo)
                controle.alvo, controle.escala_desejada = alvo, escala
                controle.atualizar(0, None, False)
                jogo.mundo.animar(0)
                jogo.estado.velocidade = 8.0
                estado["fase"] = 3
            elif fase == 3:
                # Atualizar o motor do percurso diretamente mantém o teste curto,
                # preservando as mesmas transições usadas pela animação em tempo real.
                sim = jogo.simulacao
                sim.avancar(1, 30)
                jogo.veiculo.atualizar(sim.posicao, sim.direcao, 1)
                if jogo.estado.modalidade == "euclidiano":
                    assert jogo.veiculo.drone.enabled and not jogo.veiculo.carroceria.enabled
                    estado["fase"] = 5
                elif sim.distancia > 100:
                    jogo.evento_dinamico("bloqueio")
                    estado["fase"] = 4
            elif fase == 4:
                if jogo.evento_pendente:
                    jogo.simulacao.avancar(1, 30)
                    return tarefa.cont
                if jogo.contexto_dinamico and not jogo.estado.ocupada and jogo.estado.ativa.reotimizacao:
                    estado["fase"] = 5
            elif fase == 5:
                sim = jogo.simulacao
                sim.avancar(1, 80)
                jogo.veiculo.atualizar(sim.posicao, sim.direcao, 1)
                jogo.mundo.atualizar_cidades(jogo.estado.ativa.ordem, sim.entregues, jogo.cenario.deposito)
                if sim.concluida:
                    assert sim.entregas_realizadas == len(jogo.cenario.cidades) - 1
                    assert sim.ultimo_no == jogo.cenario.deposito
                    estado["entregas"] = sim.entregas_realizadas
                    jogo.reiniciar()
                    estado["fase"] = 6
            elif fase == 6:
                jogo.comparar()
                estado["fase"] = 7
            elif fase == 7:
                assert len(jogo.estado.resultados) >= 4
                if jogo.janela_resultados:
                    app.graphicsEngine.renderFrame()
                    app.win.saveScreenshot(Filename.fromOsSpecific(str(captura.with_stem(captura.stem + "_ranking"))))
                    jogo.janela_resultados.exportar_grafico()
                    jogo.janela_resultados.fechar()
                jogo.ui.atualizar_lista()
                jogo.ui.atualizar()
                jogo.estado.velocidade = 1
                jogo.notificar("VERIFICAÇÃO CONCLUÍDA", "Planejamento manual, OR-Tools, bloqueio, reotimização, retorno e comparação validados.")
                estado["fase"] = 8
                estado["espera"] = estado["frames"] + 12
            elif fase == 8 and estado["frames"] >= estado["espera"]:
                estado["fase"] = 9
                ultimo_quadro = perf_counter()
            elif fase == 9:
                agora = perf_counter()
                amostras_quadros.append(agora - ultimo_quadro)
                ultimo_quadro = agora
                if len(amostras_quadros) < 90:
                    return tarefa.cont
                fotografar("")
                analisador = SceneGraphAnalyzer()
                analisador.add_node(jogo.mundo.decoracao.raiz.node())
                dados = {"sucesso": True, "cidades": len(jogo.cenario.cidades),
                         "semente": jogo.cenario.semente,
                         "modalidade": jogo.estado.modalidade,
                         "entregas_dinamicas": estado["entregas"],
                         "algoritmos": list(jogo.estado.resultados),
                         "frames": estado["frames"], "segundos": perf_counter() - inicio,
                         "hud_configuracoes": True, "assets_reutilizados": True,
                         "pontes_validadas": estado.get("pontes_validadas", 0),
                         "amostras_piso_pontes": estado.get("amostras_piso_pontes", 0),
                         "fps_mediana_cena": round(1 / median(amostras_quadros), 1),
                         "geometrias_decoracao": analisador.get_num_geoms(),
                         "triangulos_decoracao": analisador.get_num_tris(),
                         "captura": str(captura)}
                captura.with_suffix(".json").write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
                print("VERIFICACAO_GRAFICA_OK", json.dumps(dados, ensure_ascii=True))
                jogo.fechar()
                app.userExit()
                return tarefa.done
        except Exception as erro:
            captura.with_suffix(".erro.txt").write_text(str(erro), encoding="utf-8")
            jogo.fechar()
            raise
        return tarefa.cont

    app.taskMgr.add(verificar, "verificacao_nexus", sort=20)

