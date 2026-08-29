package dev.java.abb.repository;

import dev.java.abb.model.ArvoreBinaria;

public interface ArvoreRepository {

    ArvoreBinaria obter();

    void salvar(ArvoreBinaria arvore);
}
