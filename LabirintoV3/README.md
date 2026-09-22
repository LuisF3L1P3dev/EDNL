# Labirinto V3 — Busca Gulosa vs. A*

Aplicação educacional em Python com interface gráfica Pygame para visualizar
como a Busca Gulosa e o algoritmo A* planejam e percorrem uma rota entre os
pontos A e B.

## Recursos

- execução individual ou duelo lado a lado no mesmo mapa;
- animação incremental da fronteira, dos nós explorados e do caminho;
- caminhada do agente depois do planejamento;
- tempo computacional, nós explorados, fronteira, custo e passos em tempo real;
- editor de paredes, Borracha e reposicionamento dos pontos A e B;
- escolha entre as heurísticas Manhattan e Euclidiana;
- mapas retangulares personalizados de 5–61 linhas por 7–81 colunas;
- oito cenários responsivos ao tamanho atual: Mundo aberto, Armadilha Gulosa,
  Labirinto clássico, Aleatório, Zigue-zague, Salas e portas, Espiral e Duas
  rotas;
- inspeção de `g`, `h` e prioridade ao passar o mouse sobre uma célula.

O movimento é ortogonal e cada passo custa 1. A heurística pode ser Manhattan
ou Euclidiana; ambas são admissíveis nesse modelo. A Busca Gulosa prioriza
somente `h(n)` e o A* prioriza `f(n) = g(n) + h(n)`.

## Instalação e execução

Requer Python 3.10 ou superior. A dependência `pygame-ce` disponibiliza o
módulo compatível `pygame` e possui suporte ao Python 3.14 usado neste
repositório.

```powershell
cd LabirintoV3
python -m pip install -r requirements.txt
python main.py
```

A partir da raiz, usando o ambiente virtual do repositório:

```powershell
.\venv\Scripts\python.exe -m pip install -r .\LabirintoV3\requirements.txt
.\venv\Scripts\python.exe .\LabirintoV3\main.py
```

## Controles

| Controle | Ação |
|---|---|
| Clique/arraste esquerdo | Usa a ferramenta selecionada |
| Clique/arraste direito | Apaga paredes |
| `Espaço` | Executa, pausa ou continua |
| `Tab` | Alterna entre Individual e Duelo |
| `G` / `A` | Seleciona Gulosa / A* no modo Individual |
| `1` / `2` / `3` / `4` | Parede / mover A / mover B / Borracha |
| `E` | Seleciona a Borracha |
| `R` | Reinicia a visualização, preservando o mapa |
| `C` | Limpa o mapa |
| `Esc` | Fecha a aplicação |

A edição fica bloqueada durante a execução e a pausa. Use **Reiniciar** para
voltar à edição. Trocar o mapa limpa resultados anteriores para que a
comparação nunca misture cenários diferentes.

O botão com as dimensões atuais abre o diálogo de tamanho. Use clique ou
`Tab` para alternar entre Linhas e Colunas, `Enter` para aplicar e `Esc` para
cancelar. Aplicar regenera o cenário selecionado nas novas dimensões e limpa
busca, caminhada, métricas e histórico. Trocar de cenário preserva o tamanho
atual; **Limpar mapa** seleciona Mundo aberto sem mudar linhas ou colunas.

O tempo exibido mede somente o trabalho do algoritmo, sem incluir pausas ou o
intervalo configurado para a animação.

## Testes

Os testes usam `unittest` e o driver gráfico headless do Pygame:

```powershell
$env:PYTHONPATH = ".\LabirintoV3"
.\venv\Scripts\python.exe -m unittest discover -s .\LabirintoV3\tests -v
Remove-Item Env:PYTHONPATH
```
