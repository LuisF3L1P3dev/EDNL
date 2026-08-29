package dev.java.abb.service;

import dev.java.abb.model.ArvoreBinaria;
import dev.java.abb.model.EstadoArvore;
import dev.java.abb.repository.ArvoreRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class ArvoreService {

    private static final int[] EXEMPLO = {50, 30, 70, 20, 40, 60, 80, 80, 20};

    private final ArvoreRepository repository;

    public ArvoreService(ArvoreRepository repository) {
        this.repository = repository;
    }

    public synchronized EstadoArvore consultar() {
        return repository.obter().consultarEstado();
    }

    public synchronized EstadoArvore inserir(int valor) {
        ArvoreBinaria arvore = repository.obter();
        arvore.inserir(valor);
        repository.salvar(arvore);
        return arvore.consultarEstado();
    }

    public synchronized EstadoArvore inserirTodos(List<Integer> valores) {
        ArvoreBinaria arvore = repository.obter();
        arvore.inserirTodos(valores);
        repository.salvar(arvore);
        return arvore.consultarEstado();
    }

    public synchronized Optional<EstadoArvore> remover(int valor) {
        ArvoreBinaria arvore = repository.obter();
        if (!arvore.remover(valor)) {
            return Optional.empty();
        }
        repository.salvar(arvore);
        return Optional.of(arvore.consultarEstado());
    }

    public synchronized EstadoArvore carregarExemplo() {
        ArvoreBinaria arvore = new ArvoreBinaria();
        for (int valor : EXEMPLO) {
            arvore.inserir(valor);
        }
        repository.salvar(arvore);
        return arvore.consultarEstado();
    }

    public synchronized EstadoArvore limpar() {
        ArvoreBinaria arvore = new ArvoreBinaria();
        repository.salvar(arvore);
        return arvore.consultarEstado();
    }
}
