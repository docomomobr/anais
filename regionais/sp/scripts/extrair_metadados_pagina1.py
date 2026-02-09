#!/usr/bin/env python3
"""Extrai resumos, abstracts e palavras-chave das primeiras 2 páginas de cada artigo PDF.
Uso: python3 extrair_metadados_pagina1.py <yaml_path>
"""
import yaml
import subprocess
import re
import os
import sys

class OrderedDumper(yaml.SafeDumper):
    pass
def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())
OrderedDumper.add_representer(dict, dict_representer)


def extrair_texto_pdf(pdf_path, pages=2):
    """Extrai texto das primeiras N páginas de um PDF."""
    try:
        result = subprocess.run(
            ['pdftotext', '-f', '1', '-l', str(pages), pdf_path, '-'],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout
    except Exception as e:
        return ''


def extrair_resumo(texto):
    """Extrai resumo (português) do texto."""
    # Padrões comuns para início de resumo
    patterns = [
        r'(?:^|\n)\s*[Rr]esumo\s*[:\.]?\s*\n?(.*?)(?=\n\s*(?:Abstract|Palavras|Keywords|Introdução|Introduction|\d+\.\s))',
        r'(?:^|\n)\s*RESUMO\s*[:\.]?\s*\n?(.*?)(?=\n\s*(?:ABSTRACT|PALAVRAS|KEYWORDS|INTRODUÇÃO|\d+\.\s))',
    ]
    for pat in patterns:
        m = re.search(pat, texto, re.DOTALL | re.IGNORECASE)
        if m:
            resumo = m.group(1).strip()
            # Limpar quebras de linha internas
            resumo = re.sub(r'\s*\n\s*', ' ', resumo)
            resumo = resumo.strip()
            if len(resumo) > 30:
                return resumo
    return None


def extrair_abstract(texto):
    """Extrai abstract (inglês) do texto."""
    patterns = [
        r'(?:^|\n)\s*[Aa]bstract\s*[:\.]?\s*\n?(.*?)(?=\n\s*(?:Keywords|Palavras|Introdução|Introduction|Resumen|\d+\.\s))',
        r'(?:^|\n)\s*ABSTRACT\s*[:\.]?\s*\n?(.*?)(?=\n\s*(?:KEYWORDS|PALAVRAS|INTRODUÇÃO|\d+\.\s))',
    ]
    for pat in patterns:
        m = re.search(pat, texto, re.DOTALL | re.IGNORECASE)
        if m:
            abstract = m.group(1).strip()
            abstract = re.sub(r'\s*\n\s*', ' ', abstract)
            abstract = abstract.strip()
            if len(abstract) > 30:
                return abstract
    return None


def extrair_keywords(texto, label='[Pp]alavras[- ][Cc]have'):
    """Extrai palavras-chave do texto."""
    patterns = [
        rf'(?:^|\n)\s*{label}\s*[:\.]?\s*(.*?)(?=\n\s*(?:Abstract|Resumo|Resumen|Introdução|Introduction|\d+\.\s|$))',
        rf'(?:^|\n)\s*{label.upper()}\s*[:\.]?\s*(.*?)(?=\n\s*(?:ABSTRACT|RESUMO|INTRODUÇÃO|\d+\.\s|$))',
    ]
    for pat in patterns:
        m = re.search(pat, texto, re.DOTALL | re.IGNORECASE)
        if m:
            kw_text = m.group(1).strip()
            kw_text = re.sub(r'\s*\n\s*', ' ', kw_text)
            # Separar por ; ou .
            if ';' in kw_text:
                kws = [k.strip() for k in kw_text.split(';')]
            elif ',' in kw_text:
                kws = [k.strip() for k in kw_text.split(',')]
            else:
                kws = [kw_text]
            # Limpar
            kws = [re.sub(r'[\s.!]+$', '', k).strip() for k in kws if k.strip()]
            if kws:
                return kws
    return None


def extrair_keywords_en(texto):
    """Extrai keywords em inglês."""
    return extrair_keywords(texto, label='[Kk]eywords')


def extrair_autores_pagina(texto):
    """Tenta extrair autores da primeira página (para o 9º SP que não tem autores no sumário)."""
    # Procurar nomes após o título (primeira linha em caixa alta) e antes do resumo
    lines = texto.strip().split('\n')
    autores = []
    in_autores = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Pular título (primeira linha significativa, geralmente caixa alta)
        alpha = [c for c in stripped if c.isalpha()]
        if i < 3 and alpha and sum(1 for c in alpha if c.isupper()) / len(alpha) > 0.6:
            in_autores = True
            continue

        if in_autores:
            # Autor: nome com iniciais maiúsculas, possivelmente com números de nota
            # Parar quando encontrar "Resumo", "Abstract", email, etc.
            if re.match(r'(?:resumo|abstract|palavras|keywords)', stripped, re.IGNORECASE):
                break
            if '@' in stripped:
                break
            # Limpar números de notas
            nome = re.sub(r'\d+', '', stripped).strip()
            nome = re.sub(r'[*†‡§]', '', nome).strip()
            if nome and len(nome) > 3 and not nome.startswith('http'):
                # Verificar se parece nome (mixed case, não instituição)
                if not re.match(r'^[A-Z]{3,}', nome):  # Não é sigla
                    autores.append(nome)

    return autores


def processar_seminario(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    slug = data['issue']['slug']
    base_dir = os.path.dirname(yaml_path)
    pdf_dir = os.path.join(base_dir, slug, 'pdfs')

    total = 0
    com_resumo = 0
    com_abstract = 0
    com_keywords = 0

    for art in data['articles']:
        art_id = art['id']
        pdf_path = os.path.join(pdf_dir, f'{art_id}.pdf')

        if not os.path.exists(pdf_path):
            continue

        total += 1
        texto = extrair_texto_pdf(pdf_path)
        if not texto:
            continue

        # Extrair metadados
        resumo = extrair_resumo(texto)
        abstract = extrair_abstract(texto)
        palavras_chave = extrair_keywords(texto)
        keywords_en = extrair_keywords_en(texto)

        if resumo:
            art['abstract'] = resumo
            com_resumo += 1
        if abstract:
            art['abstract_en'] = abstract
            com_abstract += 1
        if palavras_chave:
            art['keywords'] = palavras_chave
            com_keywords += 1
        if keywords_en:
            art['keywords_en'] = keywords_en

        # Para o 9º SP: tentar extrair autores se estão como '?'
        if art['authors'] and art['authors'][0].get('givenname') == '?':
            nomes = extrair_autores_pagina(texto)
            if nomes:
                autores = []
                for idx, nome in enumerate(nomes):
                    parts = nome.split()
                    if len(parts) >= 2:
                        givenname = ' '.join(parts[:-1])
                        familyname = parts[-1]
                    else:
                        givenname = nome
                        familyname = ''
                    autores.append({
                        'givenname': givenname,
                        'familyname': familyname,
                        'affiliation': '',
                        'email': f'{familyname.lower().replace(" ", "")}@exemplo.com',
                        'primary_contact': idx == 0,
                    })
                art['authors'] = autores

    # Salvar
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)

    print(f'{slug}: {total} PDFs processados')
    print(f'  Resumos: {com_resumo}/{total}')
    print(f'  Abstracts: {com_abstract}/{total}')
    print(f'  Palavras-chave: {com_keywords}/{total}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python3 extrair_metadados_pagina1.py <yaml_path>')
        sys.exit(1)

    processar_seminario(sys.argv[1])
