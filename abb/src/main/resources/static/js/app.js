const API = "/api/arvore";
const SVG_NS = "http://www.w3.org/2000/svg";

const elements = {
    form: document.querySelector("#operacao-form"),
    input: document.querySelector("#numero"),
    inserir: document.querySelector("#inserir"),
    remover: document.querySelector("#remover"),
    exemplo: document.querySelector("#carregar-exemplo"),
    limpar: document.querySelector("#limpar"),
    status: document.querySelector("#status"),
    altura: document.querySelector("#altura"),
    numeroNos: document.querySelector("#numero-nos"),
    numeroFolhas: document.querySelector("#numero-folhas"),
    stage: document.querySelector("#tree-stage"),
    svg: document.querySelector("#tree-svg"),
    empty: document.querySelector("#empty-state"),
    percurso: document.querySelector("#percurso")
};

let ultimoEstado = null;
let ocupado = false;

elements.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const valores = lerNumeros();
    if (valores === null) return;

    await executar(
        () => requisitar(`${API}/nos/lote`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({valores})
        }),
        valores.length === 1
            ? `Número ${valores[0]} inserido.`
            : `${valores.length} números inseridos.`
    );
});

elements.remover.addEventListener("click", async () => {
    const valor = lerNumeroUnico();
    if (valor === null) return;
    await executar(
        () => requisitar(`${API}/nos/${valor}`, {method: "DELETE"}),
        `Uma ocorrência de ${valor} foi removida.`
    );
});

elements.exemplo.addEventListener("click", async () => {
    await executar(
        () => requisitar(`${API}/exemplo`, {method: "POST"}),
        "Exemplo da aula carregado."
    );
});

elements.limpar.addEventListener("click", async () => {
    await executar(
        () => requisitar(API, {method: "DELETE"}),
        "Árvore limpa."
    );
});

window.addEventListener("resize", () => {
    if (ultimoEstado?.raiz) desenharArvore(ultimoEstado.raiz);
});

inicializar();

async function inicializar() {
    try {
        definirOcupado(true);
        renderizar(await requisitar(API));
    } catch (erro) {
        mostrarStatus(erro.message, true);
    } finally {
        definirOcupado(false);
    }
}

async function executar(operacao, mensagem) {
    if (ocupado) return;
    try {
        definirOcupado(true);
        const estado = await operacao();
        renderizar(estado);
        mostrarStatus(mensagem, false);
        elements.input.select();
    } catch (erro) {
        mostrarStatus(erro.message, true);
    } finally {
        definirOcupado(false);
    }
}

async function requisitar(url, options = {}) {
    const response = await fetch(url, options);
    const possuiJson = response.headers.get("content-type")?.includes("application/json");
    const body = possuiJson ? await response.json() : null;

    if (!response.ok) {
        throw new Error(body?.detail || body?.message || "Não foi possível concluir a operação.");
    }
    return body;
}

function lerNumeros() {
    if (!elements.input.reportValidity()) return null;

    const partes = elements.input.value.split(",").map(parte => parte.trim());
    const formatoInvalido = partes.some(parte => !/^[+-]?\d+$/.test(parte));
    if (formatoInvalido) {
        mostrarStatus("Use somente números inteiros separados por vírgulas.", true);
        return null;
    }

    const valores = partes.map(Number);
    const foraDoIntervalo = valores.some(valor =>
        !Number.isInteger(valor) || valor < -2147483648 || valor > 2147483647
    );
    if (foraDoIntervalo) {
        mostrarStatus("Cada número deve estar entre -2147483648 e 2147483647.", true);
        return null;
    }
    return valores;
}

function lerNumeroUnico() {
    const valores = lerNumeros();
    if (valores === null) return null;
    if (valores.length !== 1) {
        mostrarStatus("Para remover, informe apenas um número inteiro.", true);
        return null;
    }
    return valores[0];
}

function definirOcupado(valor) {
    ocupado = valor;
    [elements.inserir, elements.remover, elements.exemplo, elements.limpar]
        .forEach(button => button.disabled = valor);
}

function mostrarStatus(mensagem, erro) {
    elements.status.textContent = mensagem;
    elements.status.className = `status ${erro ? "error" : "success"}`;
}

function renderizar(estado) {
    ultimoEstado = estado;
    elements.altura.textContent = estado.altura;
    elements.numeroNos.textContent = estado.numeroNos;
    elements.numeroFolhas.textContent = estado.numeroFolhas;
    renderizarPercurso(estado.emOrdem);

    const vazia = estado.raiz === null;
    elements.empty.hidden = !vazia;
    elements.svg.style.display = vazia ? "none" : "block";
    if (!vazia) desenharArvore(estado.raiz);
}

function renderizarPercurso(valores) {
    elements.percurso.replaceChildren();
    if (valores.length === 0) {
        const vazio = document.createElement("span");
        vazio.className = "traversal-empty";
        vazio.textContent = "Nenhum valor para percorrer.";
        elements.percurso.append(vazio);
        return;
    }

    valores.forEach(({valor, quantidade}) => {
        const item = document.createElement("span");
        item.className = "traversal-item";
        item.textContent = valor;
        if (quantidade > 1) {
            const repeticoes = document.createElement("small");
            repeticoes.textContent = `×${quantidade}`;
            item.append(repeticoes);
        }
        elements.percurso.append(item);
    });
}

function desenharArvore(raiz) {
    const espacamentoX = 104;
    const espacamentoY = 100;
    const margemX = 62;
    const margemY = 55;
    let indice = 0;
    let profundidadeMaxima = 0;

    function posicionar(no, profundidade) {
        if (!no) return null;
        const esquerda = posicionar(no.esquerda, profundidade + 1);
        const posicionado = {
            ...no,
            x: margemX + indice * espacamentoX,
            y: margemY + profundidade * espacamentoY,
            profundidade,
            esquerda: null,
            direita: null
        };
        indice++;
        profundidadeMaxima = Math.max(profundidadeMaxima, profundidade);
        posicionado.esquerda = esquerda;
        posicionado.direita = posicionar(no.direita, profundidade + 1);
        return posicionado;
    }

    const arvore = posicionar(raiz, 0);
    const larguraConteudo = margemX * 2 + Math.max(0, indice - 1) * espacamentoX;
    const largura = Math.max(elements.stage.clientWidth, larguraConteudo);
    const altura = Math.max(360, margemY * 2 + profundidadeMaxima * espacamentoY);

    elements.svg.replaceChildren();
    elements.svg.setAttribute("width", largura);
    elements.svg.setAttribute("height", altura);
    elements.svg.setAttribute("viewBox", `0 0 ${largura} ${altura}`);

    const deslocamento = Math.max(0, (largura - larguraConteudo) / 2);
    deslocar(arvore, deslocamento);
    desenharLigacoes(arvore);
    desenharNos(arvore, true);
}

function deslocar(no, valor) {
    if (!no) return;
    no.x += valor;
    deslocar(no.esquerda, valor);
    deslocar(no.direita, valor);
}

function desenharLigacoes(no) {
    if (!no) return;
    [no.esquerda, no.direita].filter(Boolean).forEach(filho => {
        const path = criarSvg("path", {
            class: "tree-edge",
            d: `M ${no.x} ${no.y + 28} C ${no.x} ${no.y + 62}, ${filho.x} ${filho.y - 62}, ${filho.x} ${filho.y - 28}`
        });
        elements.svg.append(path);
        desenharLigacoes(filho);
    });
}

function desenharNos(no, raiz) {
    if (!no) return;
    const grupo = criarSvg("g", {
        class: `tree-node${raiz ? " root-node" : ""}`,
        transform: `translate(${no.x} ${no.y})`
    });
    grupo.append(criarSvg("circle", {r: 28}));

    const valor = criarSvg("text", {class: "tree-value", y: 1});
    valor.textContent = no.valor;
    grupo.append(valor);

    const titulo = criarSvg("title");
    titulo.textContent = `Valor ${no.valor}, ${no.quantidade} ocorrência${no.quantidade === 1 ? "" : "s"}`;
    grupo.append(titulo);

    if (no.quantidade > 1) {
        grupo.append(criarSvg("rect", {class: "quantity-pill", x: 13, y: -36, width: 31, height: 18, rx: 9}));
        const quantidade = criarSvg("text", {class: "quantity-text", x: 28.5, y: -26.5});
        quantidade.textContent = `×${no.quantidade}`;
        grupo.append(quantidade);
    }

    elements.svg.append(grupo);
    desenharNos(no.esquerda, false);
    desenharNos(no.direita, false);
}

function criarSvg(tag, atributos = {}) {
    const element = document.createElementNS(SVG_NS, tag);
    Object.entries(atributos).forEach(([nome, valor]) => element.setAttribute(nome, valor));
    return element;
}
