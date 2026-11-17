# TASK 07 — orientação e movimento da van

O diagnóstico do OBJ foi aplicado no carregamento: a frente original do
`delivery` é `+Z`; o importador a converte para `-Y` no Panda3D. O filho do
modelo recebe `H=180`, enquanto o pai `veiculo` continua orientado pelo heading
matemático que considera frente local `+Y`. A velocidade nunca é invertida.

`direcao_antecipada` percorre a polilinha da rua e, perto do fim, continua pela
próxima aresta. Assim a van começa a girar antes de uma curva de 90 graus e
segue rampas/ponte pelo centro da via. A rotação usa o menor delta angular,
normalizado em `(-180, 180]`, e é limitada a 300° por segundo. Em pausa o
heading fica estável; reinício, retomada e velocidades 1×/2×/4× preservam o
relógio de `Viagem` existente.

Os testes cobrem as quatro direções cardinais, correção fixa de 180°, transição
para a próxima rua, rampa com componente Z, giro através de ±180°, pausa,
reinício, velocidades e a troca de destaque de trecho da integração.

Verificação local: `python -m unittest tests.test_mundo3d tests.test_integracao
-v` executou 13 testes com sucesso. A captura temporária
`tmp/task07_curva.png` mostra a van em movimento ao entrar na esquina do segundo
trecho; ela é somente evidência de revisão e não integra os arquivos da tarefa.
