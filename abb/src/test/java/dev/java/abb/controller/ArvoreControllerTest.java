package dev.java.abb.controller;

import dev.java.abb.service.ArvoreService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ArvoreControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ArvoreService service;

    @BeforeEach
    void limparArvore() {
        service.limpar();
    }

    @Test
    void deveConsultarArvoreVazia() throws Exception {
        mockMvc.perform(get("/api/arvore"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.raiz").doesNotExist())
                .andExpect(jsonPath("$.altura").value(-1))
                .andExpect(jsonPath("$.numeroNos").value(0))
                .andExpect(jsonPath("$.numeroFolhas").value(0));
    }

    @Test
    void deveInserirNumero() throws Exception {
        mockMvc.perform(post("/api/arvore/nos")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"valor\":42}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.raiz.valor").value(42))
                .andExpect(jsonPath("$.raiz.quantidade").value(1));
    }

    @Test
    void deveInserirListaDeNumeros() throws Exception {
        mockMvc.perform(post("/api/arvore/nos/lote")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"valores\":[10,20,40,60,20]}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.raiz.valor").value(10))
                .andExpect(jsonPath("$.altura").value(3))
                .andExpect(jsonPath("$.numeroNos").value(4))
                .andExpect(jsonPath("$.emOrdem[1].valor").value(20))
                .andExpect(jsonPath("$.emOrdem[1].quantidade").value(2));
    }

    @Test
    void deveRejeitarListaInvalidaSemInserirParcialmente() throws Exception {
        service.inserir(5);

        mockMvc.perform(post("/api/arvore/nos/lote")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"valores\":[10,null,20]}"))
                .andExpect(status().isBadRequest());

        mockMvc.perform(get("/api/arvore"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.numeroNos").value(1))
                .andExpect(jsonPath("$.raiz.valor").value(5));
    }

    @Test
    void deveRejeitarListaVazia() throws Exception {
        mockMvc.perform(post("/api/arvore/nos/lote")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"valores\":[]}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void deveRejeitarValorAusente() throws Exception {
        mockMvc.perform(post("/api/arvore/nos")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void deveRetornarNaoEncontradoAoRemoverValorAusente() throws Exception {
        mockMvc.perform(delete("/api/arvore/nos/999"))
                .andExpect(status().isNotFound());
    }

    @Test
    void deveCarregarExemploELimpar() throws Exception {
        mockMvc.perform(post("/api/arvore/exemplo"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.altura").value(2))
                .andExpect(jsonPath("$.numeroNos").value(7))
                .andExpect(jsonPath("$.numeroFolhas").value(4))
                .andExpect(jsonPath("$.emOrdem[0].valor").value(20))
                .andExpect(jsonPath("$.emOrdem[0].quantidade").value(2));

        mockMvc.perform(delete("/api/arvore"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.altura").value(-1))
                .andExpect(jsonPath("$.numeroNos").value(0));
    }
}
