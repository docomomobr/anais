#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Limpa imperfeições nos YAMLs:
- Remove caracteres "!" isolados
- Remove quebras de linha indesejadas em textos
- Remove textos extras no final de keywords
- Limpa espaços duplicados
"""

import yaml
import re
import sys
from pathlib import Path

def limpar_texto(texto):
    """Limpa um texto removendo imperfeições"""
    if not texto or not isinstance(texto, str):
        return texto

    # Remove "!" isolados (com espaços ao redor ou no início/fim)
    texto = re.sub(r'\s*!\s*', ' ', texto)
    texto = re.sub(r'^!\s*', '', texto)
    texto = re.sub(r'\s*!$', '', texto)

    # Remove referências ao seminário inseridas no meio do texto
    texto = re.sub(r'\s*\d+°?\s*Seminário\s+Docomomo\s+Norte\s+e\s+Nordeste\s+São\s+Luís,?\s*2022\s*', ' ', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\s*9°\s*Seminário\s+Docomomo.*?2022\s*', ' ', texto, flags=re.IGNORECASE)

    # Remove quebras de linha e normaliza espaços
    texto = re.sub(r'\s+', ' ', texto)

    # Remove espaços no início e fim
    texto = texto.strip()

    return texto

def limpar_keyword(kw):
    """Limpa uma palavra-chave"""
    if not kw or not isinstance(kw, str):
        return kw

    # Remove "!"
    kw = re.sub(r'\s*!\s*', '', kw)

    # Remove textos extras do seminário (várias formas)
    kw = re.sub(r'\s*\d+°?\s*Seminário.*$', '', kw, flags=re.IGNORECASE)
    kw = re.sub(r'\s*9°\s*Seminário.*$', '', kw, flags=re.IGNORECASE)
    kw = re.sub(r'\s*São Luís.*2022.*$', '', kw, flags=re.IGNORECASE)
    kw = re.sub(r'\s*Docomomo.*$', '', kw, flags=re.IGNORECASE)

    # Remove ponto final
    kw = kw.rstrip('.')

    # Limpa espaços
    kw = kw.strip()

    # Se ficou muito curto ou vazio, retorna None
    if len(kw) < 2:
        return None

    return kw

def limpar_lista_keywords(keywords):
    """Limpa lista de palavras-chave"""
    if not keywords or not isinstance(keywords, list):
        return keywords

    resultado = []
    for kw in keywords:
        kw_limpa = limpar_keyword(kw)
        if kw_limpa:
            resultado.append(kw_limpa)

    return resultado

def limpar_artigo(artigo):
    """Limpa todos os campos de um artigo"""
    if not artigo:
        return artigo

    # Campos de texto simples
    campos_texto = ['titulo', 'subtitulo', 'resumo', 'abstract', 'eixo', 'secao']
    for campo in campos_texto:
        if campo in artigo and artigo[campo]:
            artigo[campo] = limpar_texto(artigo[campo])

    # Listas de keywords
    if 'palavras_chave' in artigo:
        artigo['palavras_chave'] = limpar_lista_keywords(artigo['palavras_chave'])

    if 'keywords' in artigo:
        artigo['keywords'] = limpar_lista_keywords(artigo['keywords'])

    # Autores
    if 'autores' in artigo and artigo['autores']:
        for autor in artigo['autores']:
            if autor.get('afiliacao'):
                autor['afiliacao'] = limpar_texto(autor['afiliacao'])

    return artigo

def limpar_yaml(yaml_path):
    """Limpa um arquivo YAML completo"""
    print(f"Processando: {yaml_path}")

    with open(yaml_path, 'r', encoding='utf-8') as f:
        dados = yaml.safe_load(f)

    if not dados:
        print("  Arquivo vazio ou inválido")
        return

    # Limpa campos do issue
    if 'issue' in dados:
        issue = dados['issue']
        for campo in ['titulo', 'subtitulo', 'descricao']:
            if campo in issue and issue[campo]:
                issue[campo] = limpar_texto(issue[campo])

    # Limpa artigos
    artigos = dados.get('artigos', [])
    total = len(artigos)
    limpos = 0

    for i, artigo in enumerate(artigos):
        artigo_original = str(artigo)
        artigo_limpo = limpar_artigo(artigo)
        artigos[i] = artigo_limpo

        if str(artigo_limpo) != artigo_original:
            limpos += 1

    dados['artigos'] = artigos

    # Salva arquivo limpo
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(dados, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, width=200)

    print(f"  Artigos processados: {total}")
    print(f"  Artigos modificados: {limpos}")

def main():
    if len(sys.argv) < 2:
        print("Uso: python limpar_yaml.py <arquivo.yaml> [arquivo2.yaml ...]")
        sys.exit(1)

    for yaml_path in sys.argv[1:]:
        limpar_yaml(yaml_path)
        print()

if __name__ == '__main__':
    main()
