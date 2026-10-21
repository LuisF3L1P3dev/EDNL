# Assets do NEXUS Logistics

Os modelos, texturas e sinais sonoros necessários ao cenário acompanham o projeto.
Não há download de assets durante a partida nem dependência de uma conta externa.

## Modelos de Kenney

Os seis pacotes abaixo foram criados e distribuídos por **Kenney**. Os arquivos
incluídos em `kenney/` estão no formato **GLB** (glTF binário), com as texturas
necessárias preservadas nos respectivos diretórios. O carregamento é feito por
`panda3d-gltf`, utilizado pela integração Ursina/Panda3D.

| Diretório | Pacote e página oficial | Uso no jogo |
|---|---|---|
| `kenney/suburban/` | [City Kit — Suburban](https://kenney.nl/assets/city-kit-suburban) | Casas e elementos residenciais |
| `kenney/commercial/` | [City Kit — Commercial](https://kenney.nl/assets/city-kit-commercial) | Prédios e estabelecimentos comerciais |
| `kenney/industrial/` | [City Kit — Industrial](https://kenney.nl/assets/city-kit-industrial) | Galpões e centros logísticos |
| `kenney/roads/` | [City Kit — Roads](https://kenney.nl/assets/city-kit-roads) | Sinalização, iluminação e elementos das vias |
| `kenney/cars/` | [Car Kit](https://kenney.nl/assets/car-kit) | Caminhão, vans e veículos decorativos |
| `kenney/nature/` | [Nature Kit](https://kenney.nl/assets/nature-kit) | Árvores e arbustos |

Todos esses pacotes possuem licença **Creative Commons Zero — CC0 1.0**. A licença
permite utilização pessoal, educacional e comercial; atribuição não é obrigatória.
O projeto mantém o crédito a Kenney e os arquivos `License.txt` originais em cada
diretório. Consulte o [texto da CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).

O arquivo [manifesto.json](manifesto.json) registra, para cada pacote, autoria,
licença, página oficial, URL do ZIP de origem, SHA-256 do ZIP e nomes dos modelos
incluídos no projeto. Foram selecionados 30 modelos, sem reproduzir os demais
formatos e arquivos dos pacotes completos. `tools/baixar_assets.py` permite
repetir essa importação a partir dos ZIPs oficiais ou do cache local.

O catálogo em `tsp_3d_game/graphics/catalogo_assets.py` mantém um cache por pacote
e modelo. A integração ajusta escala, posição e orientação na cena e preserva as
texturas e cores dos modelos. As ruas transitáveis continuam definidas pela
geometria do grafo; os assets complementam sua apresentação.

## Áudio original

`audio/entrega.wav` e `audio/conclusao.wav` são sinais musicais sintetizados
especificamente para este projeto. Não contêm gravações, músicas ou amostras de
terceiros. O código de geração está em [tools/gerar_audio.py](../tools/gerar_audio.py)
e usa apenas a biblioteca padrão do Python.

Para regenerá-los a partir da raiz do projeto:

```powershell
.\.venv\Scripts\python.exe tools/gerar_audio.py
```

Esse comando recria os dois WAVs mono de 16 bits, a 22.050 Hz. A reprodução e o
volume podem ser ajustados na categoria Áudio de Configurações. Os sons originais
seguem as condições de distribuição do código do projeto; a licença CC0 dos
pacotes Kenney aplica-se aos assets desses pacotes.
