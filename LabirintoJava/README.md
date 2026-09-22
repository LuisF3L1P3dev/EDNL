# Labirinto: Busca Gulosa e A*

Aplicação desktop educacional em JavaFX. Um agente planeja uma rota de **A** até **B** numa grade com obstáculos e depois percorre o caminho encontrado. O destino fica fixo durante toda a execução.

## Pré-requisitos e comandos

- JDK **21** e `JAVA_HOME` apontando para ele.
- JavaFX **21.0.6**. O Maven baixa `javafx-controls`, `javafx-fxml` e as bibliotecas nativas necessárias; não é preciso instalar o SDK JavaFX à parte.
- Maven Wrapper **3.8.5**, incluído no projeto. Uma conexão com o Maven Central é necessária na primeira execução.

No Windows, dentro da pasta do projeto:

```powershell
.\mvnw.cmd test
.\mvnw.cmd javafx:run
```

Em Linux/macOS, substitua `.\mvnw.cmd` por `./mvnw`. Para apenas compilar, use `./mvnw compile` ou `.\mvnw.cmd compile`.

## Aprenda por etapas

1. **Monte a grade.** Escolha um mapa predefinido ou ajuste colunas e linhas (5 a 50). Selecione uma ferramenta e clique ou arraste para desenhar/apagar obstáculos. As ferramentas **Definir A** e **Definir B** movem início e destino. É possível colocar A e B na mesma célula.
2. **Escolha o movimento.** Em quatro direções, cada passo custa 10 e a estimativa restante é Manhattan: `H = 10 × (|dx| + |dy|)`. Em oito direções, diagonais custam 14 e a estimativa é octil: `H = 10 × max(|dx|, |dy|) + 4 × min(|dx|, |dy|)`. A diagonal só é legal quando suas duas células laterais estão livres.
3. **Observe a busca.** Escolha **Busca Gulosa** ou **A*** e clique em **Iniciar**. A fronteira (amarelo) contém células descobertas ainda não expandidas; exploradas ficam em azul. **Pausar**, **Continuar**, **Avançar 1 passo** e o controle de velocidade permitem examinar as expansões. Cada passo de busca expande exatamente um nó válido da fila. Passe o mouse sobre uma célula para consultar G, H e F.
4. **Acompanhe a rota.** Quando uma rota é encontrada, ela fica verde e o agente roxo percorre cada movimento. A métrica **Percorrido** soma os custos já realizados. **Reiniciar** volta ao mapa editável; **Limpar mapa** remove os obstáculos e mantém A e B.
5. **Compare.** Marque **Comparar lado a lado** antes de iniciar. Cada algoritmo recebe uma cópia independente do mesmo mapa, início, destino e regras. A tabela mostra tempo computacional da busca, nós explorados e custo. O mapa **Gulosa mais cara**, com quatro direções, produz custo 220 na Busca Gulosa e 180 no A*.

Durante uma execução, mapa e regras ficam bloqueados. Reiniciar ou limpar cancela a execução ativa e descarta respostas atrasadas de seus executores.

## O que os números significam

- **G:** custo do caminho conhecido desde A até a célula.
- **H:** estimativa de custo restante até B.
- **F:** `G + H`. O A* escolhe o menor F; a Busca Gulosa escolhe **somente o menor H**. F é mostrado para estudo também na Busca Gulosa, mas não afeta sua prioridade.
- **Explorados:** nós únicos removidos da fila para expansão. **Descobertos:** nós únicos que receberam um G. **Fronteira:** células distintas descobertas ainda não expandidas, sem contar entradas obsoletas da `PriorityQueue`.
- **Tempo computacional:** soma do tempo de cada chamada incremental de busca, medido com `System.nanoTime()`. Exclui pausas, esperas de animação e desenho da interface.
- **Tempo visual:** duração ativa da simulação, incluindo intervalos de animação e deslocamento do agente, excluindo pausas.

As medições de tempo variam com JIT, sistema operacional e carga da máquina. Uma execução isolada não é um benchmark conclusivo.

## Por que os resultados podem diferir

A Busca Gulosa segue a célula cuja estimativa H parece mais próxima de B. Ela costuma avançar de modo direto, mas pode escolher um desvio longo e **não garante** a rota de menor custo. O A* combina o custo já percorrido G com H; quando encontra um G melhor, troca o pai e atualiza a fila. Manhattan no modo de quatro direções e octil no modo de oito direções são admissíveis e consistentes para os custos adotados. Assim, o A* termina ao retirar B como próximo nó válido e encontra uma rota ótima.

## Organização do código

- `model`: grade, posição, regras de movimento, valores dos nós e resultado de cada expansão.
- `algorithm`: interface `SearchAlgorithm`, sessões incrementais e implementações Gulosa/A*. Não importa JavaFX.
- `service`: leitura dos mapas e executor de uma sessão de busca em segundo plano.
- `controller`: estado da simulação, controles, pausa, comparação e proteção contra respostas de execuções canceladas.
- `view` e recursos: `Canvas` da grade, FXML, CSS e três mapas em texto.

O `Timeline` da JavaFX Application Thread solicita no máximo uma expansão pendente por sessão. Cada sessão trabalha em seu próprio executor. O resultado de um passo volta à thread gráfica por `Platform.runLater`; somente então a grade e as métricas são atualizadas. A tela recebe as alterações do passo em conjunto, sem um evento visual por vizinho. Ao fechar a janela, os executores são encerrados.

## Testes

`mvnw test` executa JUnit 5. Os testes verificam validade e custo da rota, obstáculos, proibição de diagonais entre quinas, ausência de caminho, A igual a B, consistência das heurísticas, melhoria de G, o exemplo Gulosa/A* e otimalidade do A* contra uma implementação independente de Dijkstra em mapas fixos e gerados. Nenhum teste depende de um tempo exato de execução.
