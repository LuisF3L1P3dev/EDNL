# Laboratório de Busca em Labirintos

Aplicação educacional em Python e Tkinter para visualizar e comparar a
Busca Gulosa (Greedy Best-First Search) e o algoritmo A*.

## Requisitos

- Python 3.10 ou superior;
- Tkinter, normalmente incluído na instalação oficial do Python;
- nenhum pacote externo.

## Executar

Abra um terminal nesta pasta e execute:

```powershell
python main.py
```

No ambiente virtual deste repositório, a partir da raiz:

```powershell
.\venv\Scripts\python.exe .\LabirintoAestrela\ProjetoLabirinto\main.py
```

## Como usar

1. Escolha o modo **Individual** ou **Comparação**.
2. Selecione movimentos em quatro ou oito direções.
3. Desenhe paredes com o mouse ou use **Gerar labirinto**.
4. Use as ferramentas **Ponto A** e **Ponto B** para reposicionar o agente e
   o alvo. O botão direito funciona como borracha.
5. Clique em **Executar**. É possível pausar, continuar ou interromper a
   animação sem bloquear a janela.

As métricas mostram tempo computacional da busca, nós explorados, tamanho da
fronteira, custo e quantidade de passos do caminho. O atraso configurado para
a animação não entra no tempo computacional.

## Regras de movimento

- movimentos ortogonais custam 10;
- movimentos diagonais custam 14;
- diagonais não podem atravessar cantos bloqueados;
- A* usa Manhattan no modo de quatro direções e distância octil no modo de
  oito direções;
- a Busca Gulosa ordena a fronteira apenas pela estimativa heurística.

## Testes

```powershell
python -m unittest discover -s tests -v
```
