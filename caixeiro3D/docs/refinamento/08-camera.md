# TASK 08 — câmera e enquadramento

A câmera permanece ortográfica e isométrica. O seu enquadramento inicial e o
comando **Centrar** passaram a receber o envelope da cena, não apenas as
posições matemáticas dos nós. Esse envelope contém os quatro cantos e a altura
da ilha, todas as polilinhas das ruas e rampas, os volumes circunscritos dos
lotes, prédios e árvores, e as âncoras elevadas dos marcadores numerados.

Assim, nos mapas de 5 e 18 pontos, a cidade inteira permanece no viewport sem
cortar pontes, desvios ou pins de telhado. Ao trocar de mapa, o novo envelope é
recalculado antes de limpar a viagem. Scroll continua usando os limites de zoom
existentes, arrastar com botão direito conserva os limites de pan, e **Centrar**
restaura zoom `1.0` e pan nulo para o novo envelope.

Validação: `python -m unittest
tests.test_render3d.TestRender3D.test_camera_enquadra_ilha_ruas_predios_e_ancoras_em_ambos_os_mapas
-v` passou para os dois mapas; o teste projeta todo o envelope antes e após
pan/zoom/centralização. A suíte `tests.test_camera3d` mantém a cobertura dos
limites de zoom, arrasto, redimensionamento e viewport.
