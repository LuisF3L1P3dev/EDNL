# Assets Kenney locais

Inventário recursivo de `assets/`: quatro kits, cada modelo distribuído em OBJ, GLB e FBX. As contagens de PNG incluem prévias, além de texturas; não são contagens de texturas distintas.

| Kit (chave) | OBJ | GLB | FBX | MTL | PNG |
| --- | ---: | ---: | ---: | ---: | ---: |
| Car Kit (`carro`) | 50 | 50 | 50 | 50 | 54 |
| City Kit Commercial (`cidade`) | 41 | 41 | 41 | 41 | 50 |
| City Kit Roads (`rua`) | 95 | 95 | 95 | 95 | 102 |
| City Kit Suburban (`suburbio`) | 40 | 40 | 40 | 40 | 51 |
| Total | 226 | 226 | 226 | 226 | 257 |

Exemplos disponíveis (nomes sem extensão):

- Veículos e entregas: `carro/delivery`, `carro/delivery-flat`, `carro/garbage-truck`, `carro/ambulance`.
- Ruas e cruzamentos: `rua/road-straight`, `rua/road-crossroad`, `rua/road-intersection`, `rua/road-curve`, `rua/road-bend-sidewalk`.
- Casas e jardins: `suburbio/building-type-a` a `building-type-u`, `suburbio/planter`, `suburbio/tree-large`, `suburbio/tree-small`.
- Comércio e prédios: `cidade/building-a` a `building-n`, `cidade/building-skyscraper-a` a `building-skyscraper-e`, `cidade/detail-awning`.
- Calçadas, sinais e decoração: `rua/road-side`, `rua/road-sign-stop`, `rua/traffic-light`, `rua/light-curved`, `suburbio/path-stones-long`, `suburbio/fence`.

Os GLB estão presentes, mas o carregador do projeto de origem usa OBJ diretamente no Panda3D, sem plugin adicional. `assets3d.Biblioteca` mantém essa abordagem: converte Y-up em Z-up, triangula faces, conserva normais e UVs e aplica as texturas referenciadas pelos MTLs. Modelos e texturas são armazenados em cache por biblioteca. A raiz retornada por `modelo` é compartilhada; para manipular uma cópia independente, use `copyTo` ou `instancia_normalizada(modelo, tamanho)`, que preserva proporções e origem. O carregador destina-se aos OBJ/MTL desses kits, não a todas as variantes do formato. Arquivos ausentes geram erro com o caminho correspondente.

Os arquivos `License.txt` de cada kit acompanham os assets; consulte-os para as condições de uso. Nenhum asset foi baixado para este inventário.
