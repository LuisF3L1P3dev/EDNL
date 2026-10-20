"""Verificação integrada acionada somente por --teste-grafico."""

from pathlib import Path
from time import perf_counter
import json

from panda3d.core import Filename


def instalar_verificacao(app, jogo, captura):
    inicio = perf_counter()
    estado = {"fase": 0, "frames": 0, "espera": 0, "entregas": 0}
    captura = Path(captura).resolve()
    captura.parent.mkdir(parents=True, exist_ok=True)

    def verificar(tarefa):
        estado["frames"] += 1
        try:
            if perf_counter() - inicio > 90:
                raise TimeoutError(f"Verificação gráfica excedeu 90s, fase {estado['fase']}, status {jogo.estado.status}.")
            if jogo.erro_trabalhador:
                raise AssertionError(jogo.erro_trabalhador)
            if jogo.estado.ocupada:
                return tarefa.cont
            fase = estado["fase"]
            if fase == 0:
                assert len(jogo.mundo.marcadores) == len(jogo.cenario.cidades)
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
                app.graphicsEngine.renderFrame()
                assert app.win.saveScreenshot(Filename.fromOsSpecific(str(captura)))
                dados = {"sucesso": True, "cidades": len(jogo.cenario.cidades),
                         "modalidade": jogo.estado.modalidade,
                         "entregas_dinamicas": estado["entregas"],
                         "algoritmos": list(jogo.estado.resultados),
                         "frames": estado["frames"], "segundos": perf_counter() - inicio,
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

