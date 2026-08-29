package dev.java.abb.repository;

import dev.java.abb.model.ArvoreBinaria;
import org.springframework.stereotype.Repository;

@Repository
public class ArvoreEmMemoriaRepository implements ArvoreRepository {

    private ArvoreBinaria arvore = new ArvoreBinaria();

    @Override
    public ArvoreBinaria obter() {
        return arvore;
    }

    @Override
    public void salvar(ArvoreBinaria arvore) {
        this.arvore = arvore;
    }
}
