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
