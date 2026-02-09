#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mescla metadados extraídos dos PDFs com os YAMLs existentes
"""

import yaml
import sys
import re
from pathlib import Path

def carregar_yaml(path):
    """Carrega arquivo YAML"""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def salvar_yaml(data, path):
    """Salva arquivo YAML com formatação adequada"""
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, width=120)

def normalizar_nome_arquivo(nome):
    """Normaliza nome de arquivo para comparação"""
    # Remove prefixo numérico e extensão
    nome = re.sub(r'^\d+_', '', nome)
    nome = nome.replace('.pdf', '')
    # Remove acentos básicos para comparação
    nome = nome.lower()
    return nome

def encontrar_metadados(arquivo_pdf, metadados_extraidos):
    """Encontra metadados correspondentes ao arquivo"""
    # Busca direta pelo nome
    if arquivo_pdf in metadados_extraidos:
        return metadados_extraidos[arquivo_pdf]

    # Busca por nome normalizado
    nome_norm = normalizar_nome_arquivo(arquivo_pdf)
    for key, value in metadados_extraidos.items():
        if normalizar_nome_arquivo(key) == nome_norm:
            return value

    return None

def mesclar_artigo(artigo, metadados, arquivo_pdf):
    """Mescla metadados extraídos com artigo existente"""
    if not metadados:
        artigo['arquivo'] = arquivo_pdf
        return artigo

    # Atualiza arquivo
    artigo['arquivo'] = arquivo_pdf

    # Resumo
    if metadados.get('resumo') and not artigo.get('resumo'):
        artigo['resumo'] = metadados['resumo']

    # Abstract
    if metadados.get('abstract'):
        artigo['abstract'] = metadados['abstract']

    # Palavras-chave
    if metadados.get('palavras_chave') and not artigo.get('palavras_chave'):
        artigo['palavras_chave'] = metadados['palavras_chave']

    # Keywords
    if metadados.get('keywords'):
        artigo['keywords'] = metadados['keywords']

    # Eixo temático
    if metadados.get('eixo') and not artigo.get('eixo'):
        artigo['eixo'] = metadados['eixo']

    # Atualiza autores com emails e filiações
    if metadados.get('autores') and artigo.get('autores'):
        emails_extraidos = metadados.get('emails', [])

        for autor in artigo['autores']:
            # Tenta encontrar email correspondente
            nome_autor = f"{autor.get('nome', '')} {autor.get('sobrenome', '')}".lower()

            # Busca nos autores extraídos
            for autor_ext in metadados.get('autores', []):
                nome_ext = f"{autor_ext.get('nome', '')} {autor_ext.get('sobrenome', '')}".lower()

                # Verifica se nomes são similares
                if (nome_ext in nome_autor or nome_autor in nome_ext or
                    autor.get('sobrenome', '').lower() in nome_ext):

                    if autor_ext.get('email') and not autor.get('email'):
                        autor['email'] = autor_ext['email']
                    if autor_ext.get('afiliacao') and not autor.get('afiliacao'):
                        autor['afiliacao'] = autor_ext['afiliacao']
                    break

            # Se ainda não tem email, tenta pelos emails extraídos
            if not autor.get('email') and emails_extraidos:
                # Associa o primeiro email disponível ao autor principal
                if autor.get('principal', False) and emails_extraidos:
                    autor['email'] = emails_extraidos[0]

    # Se não tem autores no YAML mas tem nos metadados
    elif metadados.get('autores') and not artigo.get('autores'):
        artigo['autores'] = metadados['autores']

    return artigo

def gerar_lista_arquivos(pdf_dir):
    """Gera lista ordenada de arquivos PDF"""
    pdf_dir = Path(pdf_dir)
    return sorted([f.name for f in pdf_dir.glob('*.pdf')])

def mesclar_seminario(yaml_path, metadados_path, pdf_dir):
    """Mescla metadados em um seminário completo"""
    print(f"Carregando: {yaml_path}")
    dados = carregar_yaml(yaml_path)

    print(f"Carregando metadados: {metadados_path}")
    metadados = carregar_yaml(metadados_path)

    # Lista de PDFs na ordem
    arquivos_pdf = gerar_lista_arquivos(pdf_dir)
    print(f"PDFs encontrados: {len(arquivos_pdf)}")

    artigos = dados.get('artigos', [])
    print(f"Artigos no YAML: {len(artigos)}")

    # Mescla cada artigo
    atualizados = 0
    for i, artigo in enumerate(artigos):
        # Arquivo PDF correspondente (mesmo índice)
        if i < len(arquivos_pdf):
            arquivo_pdf = arquivos_pdf[i]
            meta = encontrar_metadados(arquivo_pdf, metadados)

            if meta:
                artigo_atualizado = mesclar_artigo(artigo, meta, arquivo_pdf)
                artigos[i] = artigo_atualizado
                atualizados += 1
            else:
                artigo['arquivo'] = arquivo_pdf

    dados['artigos'] = artigos

    # Salva backup e novo arquivo
    backup_path = yaml_path.replace('.yaml', '_backup.yaml')
    import shutil
    shutil.copy(yaml_path, backup_path)
    print(f"Backup salvo: {backup_path}")

    salvar_yaml(dados, yaml_path)
    print(f"YAML atualizado: {yaml_path}")
    print(f"Artigos atualizados: {atualizados}/{len(artigos)}")

def main():
    if len(sys.argv) < 4:
        print("Uso: python mesclar_metadados.py <yaml_seminario> <yaml_metadados> <dir_pdfs>")
        sys.exit(1)

    yaml_path = sys.argv[1]
    metadados_path = sys.argv[2]
    pdf_dir = sys.argv[3]

    mesclar_seminario(yaml_path, metadados_path, pdf_dir)

if __name__ == '__main__':
    main()
