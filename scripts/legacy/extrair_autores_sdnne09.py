#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrai autores dos PDFs do sdnne09 com parser melhorado
Formato esperado:
SOBRENOME, NOME (n)
n. afiliação, email
"""

import os
import re
import subprocess
import yaml
from pathlib import Path

def extrair_texto_pdf(pdf_path, max_chars=8000):
    """Extrai texto do PDF usando pdftotext"""
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', str(pdf_path), '-'],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout[:max_chars]
    except Exception as e:
        print(f"  Erro: {e}")
        return ""

def extrair_autores(texto):
    """Extrai autores no formato SOBRENOME, NOME (n)"""
    autores = []

    # Primeiro, encontra a seção de autores (entre título e RESUMO)
    # Procura linhas que seguem o padrão SOBRENOME, NOME (n)
    linhas = texto.split('\n')

    autor_info = []  # Lista de (sobrenome, nome, num, linha_idx)
    autor_counter = 0  # Contador para autores sem número

    for idx, linha in enumerate(linhas[:60]):
        linha = linha.strip()

        # Pula linhas que claramente não são autores
        if not linha or linha.upper().startswith('RESUMO') or linha.upper().startswith('EIXO'):
            continue

        # Padrão 1: SOBRENOME, NOME (n) - com número em parênteses
        match = re.match(r'^([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]+(?:\s+[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]+)*),\s*([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇa-záéíóúàâêôãõç\s\.]+?)\s*\((\d+)\)\s*$', linha)
        if match:
            sobrenome = match.group(1).strip().title()
            nome = match.group(2).strip().title()
            num = int(match.group(3))
            autor_info.append((sobrenome, nome, num, idx))
            autor_counter = num
            continue

        # Padrão 2: SOBRENOME, Nome (sem número) - usado quando só tem um autor ou formato diferente
        # Ignora se a linha parece um título (muito longa ou tem palavras específicas)
        if len(linha) < 80 and ',' in linha:
            match2 = re.match(r'^([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]+(?:\s+[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]+)*),\s*([A-ZÁÉÍÓÚÀÂÊÔÃÕÇa-záéíóúàâêôãõç][A-ZÁÉÍÓÚÀÂÊÔÃÕÇa-záéíóúàâêôãõç\s\.]+)$', linha)
            if match2:
                # Verifica se não é um título (não contém palavras comuns de título)
                texto_completo = match2.group(0).upper()
                palavras_titulo = ['ARQUITETURA', 'MODERNA', 'PATRIMÔNIO', 'EDIFICIO', 'CONSTRUÇÃO', 'URBANISMO',
                                  'TIPOLOGIA', 'TOPOLOGIA', 'ANÁLISE', 'PROJETO', 'FUNCIONALIDADE']
                if not any(p in texto_completo for p in palavras_titulo):
                    sobrenome = match2.group(1).strip().title()
                    nome = match2.group(2).strip().title()
                    autor_counter += 1
                    autor_info.append((sobrenome, nome, autor_counter, idx))

    # Para cada autor encontrado, busca afiliação e email
    for sobrenome, nome, num, linha_idx in autor_info:
        autor = {
            'nome': nome,
            'sobrenome': sobrenome,
            'afiliacao': None,
            'email': None,
            'principal': num == 1
        }

        # Busca nas próximas linhas por "n. afiliação" e email
        # O formato é:
        # n. Título/Cargo,
        # Departamento/Instituição
        # email@dominio.com
        afil_linhas = []
        encontrou_afil = False

        for i in range(linha_idx + 1, min(linha_idx + 8, len(linhas))):
            linha = linhas[i].strip()

            # Pula linhas vazias
            if not linha:
                continue

            # Para se encontrar outro autor (SOBRENOME, NOME (n))
            if re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]+,\s*[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ].*\(\d+\)', linha):
                break

            # Para no RESUMO
            if linha.upper().startswith('RESUMO'):
                break

            # Linha de afiliação: começa com "n." ou é a primeira linha após o autor (sem número)
            if linha.startswith(f'{num}.'):
                encontrou_afil = True
                afil_linhas.append(linha[len(f'{num}.'):].strip())
                continue

            # Para autores sem número, a afiliação começa direto (Doutor, Mestrando, Professor, etc.)
            if not encontrou_afil and re.match(r'^(Doutor|Mestr|Professor|Graduand|Arquitet|Bolsista|Pesquisador)', linha, re.IGNORECASE):
                encontrou_afil = True
                afil_linhas.append(linha)
                continue

            # Se já encontrou afiliação, continua coletando
            if encontrou_afil:
                # Verifica se é email
                email_match = re.match(r'^([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$', linha)
                if email_match:
                    autor['email'] = email_match.group(1).lower()
                    break
                # Senão, é parte da afiliação
                afil_linhas.append(linha)

        # Processa afiliação coletada
        if afil_linhas:
            afil_texto = ' '.join(afil_linhas)

            # Remove email se estiver no texto
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', afil_texto)
            if email_match:
                if not autor['email']:
                    autor['email'] = email_match.group(1).lower()
                afil_texto = afil_texto.replace(email_match.group(1), '').strip()

            # Limpa afiliação - remove vírgulas finais e espaços extras
            afil_texto = re.sub(r',\s*$', '', afil_texto)
            afil_texto = re.sub(r'\s+', ' ', afil_texto).strip()

            if afil_texto and len(afil_texto) > 3:
                autor['afiliacao'] = afil_texto

        autores.append(autor)

    return autores

def processar_diretorio(pdf_dir):
    """Processa todos os PDFs e extrai autores"""
    pdf_dir = Path(pdf_dir)
    resultados = {}

    pdfs = sorted(pdf_dir.glob('*.pdf'))
    total = len(pdfs)

    for i, pdf in enumerate(pdfs, 1):
        print(f"[{i}/{total}] {pdf.name}")

        texto = extrair_texto_pdf(pdf)
        if texto:
            autores = extrair_autores(texto)
            if autores:
                resultados[pdf.name] = autores
                for a in autores:
                    print(f"    - {a['nome']} {a['sobrenome']} <{a['email']}>")

    return resultados

def atualizar_yaml(yaml_path, autores_extraidos, pdf_dir):
    """Atualiza o YAML com os autores extraídos"""
    print(f"\nAtualizando: {yaml_path}")

    with open(yaml_path, 'r', encoding='utf-8') as f:
        dados = yaml.safe_load(f)

    # Lista de PDFs na ordem
    pdf_dir = Path(pdf_dir)
    arquivos_pdf = sorted([f.name for f in pdf_dir.glob('*.pdf')])

    artigos = dados.get('artigos', [])
    atualizados = 0

    for i, artigo in enumerate(artigos):
        if i < len(arquivos_pdf):
            arquivo_pdf = arquivos_pdf[i]

            if arquivo_pdf in autores_extraidos:
                novos_autores = autores_extraidos[arquivo_pdf]
                if novos_autores:
                    artigo['autores'] = novos_autores
                    atualizados += 1

    dados['artigos'] = artigos

    # Salva
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(dados, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, width=200)

    print(f"Artigos atualizados: {atualizados}/{len(artigos)}")

def main():
    pdf_dir = "/home/danilomacedo/Dropbox/docomomo/26-27/site/migracao/nne/sdnne09/pdfs"
    yaml_path = "/home/danilomacedo/Dropbox/docomomo/26-27/site/migracao/nne/sdnne09.yaml"

    print("Extraindo autores dos PDFs do sdnne09...\n")
    autores = processar_diretorio(pdf_dir)

    print(f"\nTotal de PDFs com autores extraídos: {len(autores)}")

    atualizar_yaml(yaml_path, autores, pdf_dir)

if __name__ == '__main__':
    main()
