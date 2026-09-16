package dev.java.abb.controller;

import dev.java.abb.model.EstadoArvore;
import dev.java.abb.service.ArvoreService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@RestController
@RequestMapping("/api/arvore")
public class ArvoreController {

    private final ArvoreService service;

    public ArvoreController(ArvoreService service) {
        this.service = service;
    }

    @GetMapping
    public EstadoArvore consultar() {
        return service.consultar();
    }

    @PostMapping("/nos")
    @ResponseStatus(HttpStatus.CREATED)
    public EstadoArvore inserir(@RequestBody InserirNumeroRequest requisicao) {
        if (requisicao == null || requisicao.valor() == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Informe um numero inteiro.");
        }
        return service.inserir(requisicao.valor());
    }

    @PostMapping("/nos/lote")
    @ResponseStatus(HttpStatus.CREATED)
    public EstadoArvore inserirTodos(@RequestBody InserirNumerosRequest requisicao) {
        if (requisicao == null
                || requisicao.valores() == null
                || requisicao.valores().isEmpty()
                || requisicao.valores().stream().anyMatch(valor -> valor == null)) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "Informe uma lista com ao menos um numero inteiro."
            );
        }
        return service.inserirTodos(requisicao.valores());
    }

    @DeleteMapping("/nos/{valor}")
    public EstadoArvore remover(@PathVariable int valor) {
        return service.remover(valor).orElseThrow(() ->
                new ResponseStatusException(HttpStatus.NOT_FOUND, "O numero nao existe na arvore."));
    }

    @PostMapping("/exemplo")
    public EstadoArvore carregarExemplo() {
        return service.carregarExemplo();
    }

    @DeleteMapping
    public EstadoArvore limpar() {
        return service.limpar();
    }

    public record InserirNumeroRequest(Integer valor) {
    }

    public record InserirNumerosRequest(List<Integer> valores) {
    }
}
