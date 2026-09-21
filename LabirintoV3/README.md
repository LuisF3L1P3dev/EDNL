# Labirinto V3 — Busca Gulosa vs. A*

Aplicação educacional em Python com interface gráfica Pygame para visualizar
como a Busca Gulosa e o algoritmo A* planejam e percorrem uma rota entre os
pontos A e B.

## Recursos

- execução individual ou duelo lado a lado no mesmo mapa;
- animação incremental da fronteira, dos nós explorados e do caminho;
- caminhada do agente depois do planejamento;
- tempo computacional, nós explorados, fronteira, custo e passos em tempo real;
- editor de paredes e reposicionamento dos pontos A e B;
- cenários aberto, armadilha para a Gulosa, labirinto clássico e aleatório;
- inspeção de `g`, `h` e prioridade ao passar o mouse sobre uma célula.

O movimento é ortogonal, cada passo custa 1 e a heurística é a distância de
Manhattan. A Busca Gulosa prioriza somente `h(n)`; o A* prioriza
`f(n) = g(n) + h(n)`.

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
| `1` / `2` / `3` | Parede / mover A / mover B |
| `R` | Reinicia a visualização, preservando o mapa |
| `C` | Limpa o mapa |
| `Esc` | Fecha a aplicação |

A edição fica bloqueada durante a execução e a pausa. Use **Reiniciar** para
voltar à edição. Trocar o mapa limpa resultados anteriores para que a
comparação nunca misture cenários diferentes.

O tempo exibido mede somente o trabalho do algoritmo, sem incluir pausas ou o
intervalo configurado para a animação.

## Testes

Os testes usam apenas a biblioteca padrão:

```powershell
$env:PYTHONPATH = ".\LabirintoV3"
.\venv\Scripts\python.exe -m unittest discover -s .\LabirintoV3\tests -v
Remove-Item Env:PYTHONPATH
```
