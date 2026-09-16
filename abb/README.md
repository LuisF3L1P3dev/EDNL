# Laboratório ABB

Aplicação web para estudar e visualizar uma **Árvore Binária de Busca (ABB)**. O projeto permite inserir e remover números inteiros, acompanhar valores repetidos e observar como cada operação altera a estrutura da árvore, sua altura, quantidade de nós, folhas e percurso em ordem.

O backend foi desenvolvido em Java com Spring Boot. A interface utiliza HTML, CSS e JavaScript puro e desenha a árvore no navegador usando SVG.

## Funcionalidades

- Inserção de um número ou de uma lista de números.
- Remoção de uma ocorrência de um valor.
- Agrupamento de valores repetidos no mesmo nó.
- Visualização da árvore e das ligações entre seus nós.
- Cálculo da altura, do número de nós distintos e do número de folhas.
- Exibição do percurso em ordem.
- Carregamento de uma árvore de exemplo.
- Limpeza completa da árvore.

## Conceito de Árvore Binária de Busca

Uma Árvore Binária de Busca organiza os valores de modo que, para cada nó:

- valores menores ficam na subárvore esquerda;
- valores maiores ficam na subárvore direita.

Por exemplo, inserindo `50, 30, 70, 20, 40, 60, 80`, a árvore resultante é:

```text
        50
       /  \
     30    70
    / \    / \
   20 40  60 80
```

O percurso **em ordem** visita esquerda, raiz e direita. Em uma ABB, isso produz os valores em ordem crescente:

```text
20, 30, 40, 50, 60, 70, 80
```

### Valores repetidos

Valores iguais não criam novos nós. Cada nó possui uma propriedade `quantidade`, incrementada a cada repetição. Assim, inserir `20` duas vezes mantém um único nó com `quantidade = 2`. Ao remover esse valor, somente uma ocorrência é retirada; o nó é removido da estrutura apenas quando sua última ocorrência é excluída.

### Remoção

A remoção trata três situações:

1. Um nó folha pode ser removido diretamente.
2. Um nó com um filho é substituído por esse filho.
3. Um nó com dois filhos é substituído pelo menor nó de sua subárvore direita, chamado sucessor em ordem.

### Altura e complexidade

Neste projeto, a altura é medida em arestas. Uma árvore vazia possui altura `-1` e uma árvore com apenas a raiz possui altura `0`.

As operações de busca, inserção e remoção percorrem a altura `h` da árvore, portanto têm complexidade `O(h)`. Em uma árvore razoavelmente equilibrada, isso se aproxima de `O(log n)`. Como esta implementação não realiza balanceamento automático, inserções ordenadas podem formar uma árvore degenerada e levar ao pior caso `O(n)`.

## Arquitetura

```text
Navegador
  index.html + style.css + app.js
                 │
                 │ HTTP / JSON
                 ▼
ArvoreController (API REST)
                 │
                 ▼
ArvoreService (casos de uso)
                 │
        ┌────────┴────────┐
        ▼                 ▼
ArvoreBinaria       ArvoreRepository
(regras da ABB)     (estado em memória)
```

### Backend Java

- **`ArvoreController`** expõe os endpoints REST, recebe os dados enviados pelo navegador e valida o formato básico das requisições.
- **`ArvoreService`** coordena os casos de uso e sincroniza o acesso ao estado compartilhado da árvore.
- **`ArvoreBinaria`** implementa os algoritmos de inserção, remoção, percurso e cálculo das métricas.
- **`ArvoreEmMemoriaRepository`** mantém a instância atual da árvore enquanto a aplicação está em execução.
- **`EstadoArvore`** é uma fotografia imutável da árvore retornada pela API, evitando expor diretamente os nós internos mutáveis.

### Frontend

O Spring Boot entrega os arquivos estáticos presentes em `src/main/resources/static`. O arquivo `app.js`:

1. captura as ações realizadas na interface;
2. chama a API `/api/arvore` com `fetch`;
3. recebe o estado calculado pelo backend em JSON;
4. atualiza as métricas e desenha os nós e ligações em SVG.

Portanto, o JavaScript é responsável pela interação e pela representação visual, enquanto o Java mantém o estado e executa as regras da Árvore Binária de Busca. Não há renderização de HTML no servidor nem mecanismo de templates como Thymeleaf.

## Fluxo de uma inserção

Ao inserir `10, 20, 40` pela interface:

1. `app.js` envia `POST /api/arvore/nos/lote` com os valores em JSON.
2. `ArvoreController` valida a requisição e chama `ArvoreService`.
3. O serviço obtém a árvore do repositório e solicita a inserção dos valores.
4. `ArvoreBinaria` posiciona cada valor conforme as regras da ABB.
5. O backend cria um `EstadoArvore` e o Spring o serializa como JSON.
6. `app.js` usa a resposta para redesenhar a árvore no navegador.

## Tecnologias

- Java 21
- Spring Boot 4.1.1
- Spring Web MVC
- Maven Wrapper
- JUnit 5, AssertJ e MockMvc
- HTML5, CSS3, JavaScript e SVG

## Como executar

### Pré-requisitos

- JDK 21 instalado e configurado.
- Não é necessário instalar o Maven, pois o projeto inclui o Maven Wrapper.

No Windows PowerShell ou Prompt de Comando:

```powershell
.\mvnw.cmd spring-boot:run
```

No Linux ou macOS:

```bash
./mvnw spring-boot:run
```

Como alternativa, caso o Maven Wrapper não possa ser iniciado no ambiente, use uma instalação local do Maven:

```bash
mvn spring-boot:run
```

Depois, acesse [http://localhost:8080](http://localhost:8080).

## API REST

A URL-base da API é `/api/arvore`.

| Método | Endpoint | Corpo da requisição | Resposta | Descrição |
|---|---|---|---|---|
| `GET` | `/api/arvore` | — | `200 OK` | Consulta o estado atual. |
| `POST` | `/api/arvore/nos` | `{"valor": 42}` | `201 Created` | Insere um número. |
| `POST` | `/api/arvore/nos/lote` | `{"valores": [10, 20, 40]}` | `201 Created` | Insere vários números na ordem informada. |
| `DELETE` | `/api/arvore/nos/{valor}` | — | `200 OK` ou `404 Not Found` | Remove uma ocorrência do valor. |
| `POST` | `/api/arvore/exemplo` | — | `200 OK` | Substitui o estado atual pela árvore de exemplo. |
| `DELETE` | `/api/arvore` | — | `200 OK` | Limpa a árvore. |

Uma resposta da API possui este formato:

```json
{
  "raiz": {
    "valor": 10,
    "quantidade": 1,
    "esquerda": null,
    "direita": {
      "valor": 20,
      "quantidade": 2,
      "esquerda": null,
      "direita": null
    }
  },
  "altura": 1,
  "numeroNos": 2,
  "numeroFolhas": 1,
  "emOrdem": [
    {"valor": 10, "quantidade": 1},
    {"valor": 20, "quantidade": 2}
  ]
}
```

## Estrutura do projeto

```text
src
├── main
│   ├── java/dev/java/abb
│   │   ├── controller     # Endpoints da API REST
│   │   ├── model          # Árvore, nós e estado retornado
│   │   ├── repository     # Armazenamento da árvore
│   │   ├── service        # Casos de uso da aplicação
│   │   └── AbbApplication.java
│   └── resources
│       ├── static
│       │   ├── css        # Estilos da interface
│       │   ├── js         # Integração com a API e desenho SVG
│       │   └── index.html
│       └── application.properties
└── test
    └── java/dev/java/abb
        ├── controller     # Testes de integração da API
        └── model          # Testes dos algoritmos da ABB
```

## Testes

Para executar todos os testes:

No Windows:

```powershell
.\mvnw.cmd test
```

No Linux ou macOS:

```bash
./mvnw test
```

Com uma instalação local do Maven, o comando equivalente é:

```bash
mvn test
```

Os testes verificam, entre outros cenários:

- representação de uma árvore vazia;
- inserção, ordenação e contagem de valores repetidos;
- inserção em lote sem alteração parcial quando a entrada é inválida;
- remoção de folhas e nós com um ou dois filhos;
- cálculo da altura e percurso em ordem;
- validações e códigos HTTP da API.

## Persistência

A árvore é armazenada somente em memória. Todos os usuários da instância da aplicação compartilham o mesmo estado, e os dados são perdidos quando o processo do Spring Boot é encerrado ou reiniciado. Não há banco de dados configurado neste projeto.
