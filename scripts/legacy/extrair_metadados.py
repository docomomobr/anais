#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrator de metadados de PDFs dos anais Docomomo
Extrai: título, subtítulo, autores, filiação, email, resumo, abstract, palavras-chave
"""

import os
import re
import subprocess
import yaml
import sys
from pathlib import Path

def extrair_texto_pdf(pdf_path, max_chars=15000):
    """Extrai texto do PDF usando pdftotext"""
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', str(pdf_path), '-'],
            capture_output=True, text=True, timeout=30
        )
        texto = result.stdout[:max_chars]
        # Limpa caracteres problemáticos
        texto = texto.replace('\x0c', '\n')  # form feed
        return texto
    except Exception as e:
        print(f"Erro ao extrair {pdf_path}: {e}")
        return ""

def extrair_emails(texto):
    """Extrai todos os emails do texto"""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, texto)))

def extrair_resumo(texto):
    """Extrai o resumo em português"""
    # Padrão para RESUMO seguido de texto até PALAVRAS-CHAVE ou RESUMEN ou ABSTRACT
    patterns = [
        r'RESUMO\s*\n(.*?)(?=PALAVRAS[- ]CHAVE|RESUMEN|ABSTRACT|KEYWORDS|\n\n[A-Z]{2,})',
        r'RESUMO\s*\n(.*?)(?=\n[A-Z][a-z]+[- ][a-z]+:)',  # até próxima seção
    ]
    for pattern in patterns:
        match = re.search(pattern, texto, re.DOTALL | re.IGNORECASE)
        if match:
            resumo = match.group(1).strip()
            # Limpa quebras de linha e espaços extras
            resumo = re.sub(r'\s+', ' ', resumo)
            resumo = resumo.strip()
            if len(resumo) > 50:  # resumo válido
                return resumo
    return None

def extrair_abstract(texto):
    """Extrai o abstract em inglês"""
    patterns = [
        r'ABSTRACT\s*\n(.*?)(?=KEYWORDS|KEY WORDS|INTRODUÇÃO|INTRODUCTION|\n\n[0-9]+\.|$)',
        r'ABSTRACT\s*\n(.*?)(?=\n[A-Z][a-z]+:)',
    ]
    for pattern in patterns:
        match = re.search(pattern, texto, re.DOTALL | re.IGNORECASE)
        if match:
            abstract = match.group(1).strip()
            abstract = re.sub(r'\s+', ' ', abstract)
            abstract = abstract.strip()
            if len(abstract) > 50:
                return abstract
    return None

def extrair_palavras_chave(texto):
    """Extrai palavras-chave em português"""
    patterns = [
        r'PALAVRAS[- ]CHAVE[:\s]*(.*?)(?=RESUMEN|ABSTRACT|KEYWORDS|\n\n)',
        r'Palavras[- ]chave[:\s]*(.*?)(?=\n\n|RESUMEN|ABSTRACT)',
    ]
    for pattern in patterns:
        match = re.search(pattern, texto, re.DOTALL | re.IGNORECASE)
        if match:
            kw = match.group(1).strip()
            kw = re.sub(r'\s+', ' ', kw)
            # Separa por ; ou .
            if ';' in kw:
                palavras = [p.strip().rstrip('.') for p in kw.split(';')]
            elif ',' in kw:
                palavras = [p.strip().rstrip('.') for p in kw.split(',')]
            else:
                palavras = [kw.rstrip('.')]
            return [p for p in palavras if p and len(p) > 1]
    return []

def extrair_keywords(texto):
    """Extrai keywords em inglês"""
    patterns = [
        r'KEYWORDS[:\s]*(.*?)(?=INTRODUÇÃO|INTRODUCTION|\n\n[0-9]+\.|\n\n[A-Z])',
        r'KEY WORDS[:\s]*(.*?)(?=\n\n)',
    ]
    for pattern in patterns:
        match = re.search(pattern, texto, re.DOTALL | re.IGNORECASE)
        if match:
            kw = match.group(1).strip()
            kw = re.sub(r'\s+', ' ', kw)
            if ';' in kw:
                keywords = [p.strip().rstrip('.') for p in kw.split(';')]
            elif ',' in kw:
                keywords = [p.strip().rstrip('.') for p in kw.split(',')]
            else:
                keywords = [kw.rstrip('.')]
            return [k for k in keywords if k and len(k) > 1]
    return []

def extrair_eixo(texto):
    """Extrai eixo temático (se presente no cabeçalho)"""
    match = re.search(r'EIXO\s+TEMÁTICO\s*(\d+)[:\s]*([^\n]+)?', texto, re.IGNORECASE)
    if match:
        num = match.group(1)
        nome = match.group(2).strip() if match.group(2) else ""
        return f"Eixo {num}: {nome}" if nome else f"Eixo {num}"
    return None

def extrair_autores_sdnne09(texto):
    """Extrai autores no formato do sdnne09: SOBRENOME, NOME (n)"""
    autores = []
    # Padrão: SOBRENOME, NOME (1) ou SOBRENOME, NOME COMPOSTO (1)
    pattern = r'([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]+),\s*([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-Za-záéíóúàâêôãõç\s\.]+)\s*\((\d+)\)'
    matches = re.findall(pattern, texto[:3000])

    # Também busca filiação e email
    for sobrenome, nome, num in matches:
        autor = {
            'nome': nome.strip(),
            'sobrenome': sobrenome.strip().title(),
            'afiliacao': None,
            'email': None,
            'principal': num == '1'
        }
        # Busca filiação e email após o número
        afil_pattern = rf'{num}\.\s*([^@\n]+?),\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}})'
        afil_match = re.search(afil_pattern, texto[:3000])
        if afil_match:
            autor['afiliacao'] = afil_match.group(1).strip()
            autor['email'] = afil_match.group(2).strip()
        autores.append(autor)

    return autores

def extrair_autores_sdnne07(texto):
    """Extrai autores no formato do sdnne07: NOME SOBRENOME; NOME SOBRENOME"""
    autores = []

    # Primeiro, encontra a linha de autores (geralmente após o título em inglês)
    # Procura por linha com nomes separados por ;
    lines = texto.split('\n')
    autor_line = None

    for i, line in enumerate(lines[:30]):
        # Linha de autores: múltiplos nomes com ; ou linha com MAIÚSCULAS
        if ';' in line and re.search(r'[A-ZÁÉÍÓÚ]{2,}', line):
            autor_line = line
            break
        # Ou linha toda em maiúsculas com nomes
        if re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s;,\.]+$', line.strip()) and len(line.strip()) > 10:
            autor_line = line
            break

    if autor_line:
        # Separa por ;
        nomes = [n.strip() for n in autor_line.split(';') if n.strip()]
        for i, nome_completo in enumerate(nomes):
            # Remove números e pontos
            nome_completo = re.sub(r'^\d+\.?\s*', '', nome_completo)
            nome_completo = nome_completo.strip()
            if nome_completo:
                partes = nome_completo.split()
                if len(partes) >= 2:
                    autor = {
                        'nome': ' '.join(partes[:-1]).title(),
                        'sobrenome': partes[-1].title(),
                        'afiliacao': None,
                        'email': None,
                        'principal': i == 0
                    }
                    autores.append(autor)

    # Busca filiações e emails
    emails = extrair_emails(texto[:4000])

    # Tenta associar emails aos autores
    for i, autor in enumerate(autores):
        # Busca bloco de filiação pelo número
        num = i + 1
        afil_pattern = rf'{num}\.\s*\n?(.*?)(?=\n{num+1}\.|RESUMO|\n\n)'
        afil_match = re.search(afil_pattern, texto[:4000], re.DOTALL)
        if afil_match:
            bloco = afil_match.group(1)
            # Extrai filiação (primeira linha significativa)
            linhas = [l.strip() for l in bloco.split('\n') if l.strip() and not l.strip().startswith('http')]
            if linhas:
                # Pega a filiação principal
                afil_texto = ' '.join(linhas)
                # Remove email do texto de filiação
                afil_texto = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', afil_texto)
                afil_texto = re.sub(r'http\S+', '', afil_texto)
                autor['afiliacao'] = afil_texto.strip()[:200] if afil_texto.strip() else None

            # Email do bloco
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', bloco)
            if email_match:
                autor['email'] = email_match.group(0)

    return autores

def processar_pdf(pdf_path, formato='sdnne07'):
    """Processa um PDF e retorna os metadados extraídos"""
    texto = extrair_texto_pdf(pdf_path)
    if not texto:
        return None

    metadados = {
        'arquivo': os.path.basename(pdf_path),
        'resumo': extrair_resumo(texto),
        'abstract': extrair_abstract(texto),
        'palavras_chave': extrair_palavras_chave(texto),
        'keywords': extrair_keywords(texto),
        'emails': extrair_emails(texto[:4000]),
    }

    # Eixo temático (principalmente sdnne09)
    eixo = extrair_eixo(texto)
    if eixo:
        metadados['eixo'] = eixo

    # Autores conforme formato
    if formato == 'sdnne09':
        metadados['autores'] = extrair_autores_sdnne09(texto)
    else:
        metadados['autores'] = extrair_autores_sdnne07(texto)

    return metadados

def processar_diretorio(pdf_dir, formato='sdnne07'):
    """Processa todos os PDFs de um diretório"""
    resultados = {}
    pdf_dir = Path(pdf_dir)

    pdfs = sorted(pdf_dir.glob('*.pdf'))
    total = len(pdfs)

    for i, pdf in enumerate(pdfs, 1):
        print(f"[{i}/{total}] Processando: {pdf.name}")
        metadados = processar_pdf(pdf, formato)
        if metadados:
            resultados[pdf.name] = metadados

    return resultados

def main():
    if len(sys.argv) < 2:
        print("Uso: python extrair_metadados.py <diretorio_pdfs> [formato]")
        print("  formato: sdnne07 ou sdnne09 (default: sdnne07)")
        sys.exit(1)

    pdf_dir = sys.argv[1]
    formato = sys.argv[2] if len(sys.argv) > 2 else 'sdnne07'

    print(f"Processando PDFs em: {pdf_dir}")
    print(f"Formato: {formato}")
    print()

    resultados = processar_diretorio(pdf_dir, formato)

    # Salva resultado como YAML
    output_file = Path(pdf_dir).parent / f"metadados_extraidos_{formato}.yaml"
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(resultados, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"\nResultados salvos em: {output_file}")
    print(f"Total de PDFs processados: {len(resultados)}")

if __name__ == '__main__':
    main()
