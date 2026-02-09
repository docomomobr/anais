#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Limpa nomes de autores mal formatados nos YAMLs
"""

import yaml
import re
import sys

def limpar_nome(nome):
    """Limpa um nome de autor"""
    if not nome or not isinstance(nome, str):
        return nome

    # Remove quebras de linha
    nome = nome.replace('\n', ' ')

    # Remove textos extras comuns (títulos, graus)
    nome = re.sub(r'\s*Doutor[a]?\s+Em\s+.*', '', nome, flags=re.IGNORECASE)
    nome = re.sub(r'\s*Mestr[ea]\s+Em\s+.*', '', nome, flags=re.IGNORECASE)
    nome = re.sub(r'\s*Graduand[oa]\s+Em\s+.*', '', nome, flags=re.IGNORECASE)
    nome = re.sub(r'\s*Arquitet[oa]\s+E\s+.*', '', nome, flags=re.IGNORECASE)
    nome = re.sub(r'\s*Professor[a]?\s+.*', '', nome, flags=re.IGNORECASE)

    # Normaliza espaços
    nome = re.sub(r'\s+', ' ', nome)
    nome = nome.strip()

    # Remove pontos no final
    nome = nome.rstrip('.')

    return nome

def limpar_artigo(artigo):
    """Limpa autores de um artigo"""
    if not artigo or 'autores' not in artigo:
        return artigo

    for autor in artigo.get('autores', []):
        if autor.get('nome'):
            autor['nome'] = limpar_nome(autor['nome'])
        if autor.get('sobrenome'):
            autor['sobrenome'] = limpar_nome(autor['sobrenome'])

    return artigo

def processar_yaml(yaml_path):
    """Processa e limpa um arquivo YAML"""
    print(f"Processando: {yaml_path}")

    with open(yaml_path, 'r', encoding='utf-8') as f:
        dados = yaml.safe_load(f)

    if not dados:
        return

    artigos = dados.get('artigos', [])
    modificados = 0

    for artigo in artigos:
        original = str(artigo.get('autores', []))
        artigo = limpar_artigo(artigo)
        if str(artigo.get('autores', [])) != original:
            modificados += 1

    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(dados, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, width=200)

    print(f"  Artigos com autores corrigidos: {modificados}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python limpar_autores.py <arquivo.yaml>")
        sys.exit(1)

    for yaml_path in sys.argv[1:]:
        processar_yaml(yaml_path)
