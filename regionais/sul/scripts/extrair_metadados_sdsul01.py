#!/usr/bin/env python3
"""Extrai resumos, abstracts, keywords, referencias e page count dos PDFs do sdsul01.
Atualiza o YAML existente sem sobrescrever campos ja preenchidos.

Uso: python3 extrair_metadados_sdsul01.py
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

def str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

OrderedDumper.add_representer(str, str_representer)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YAML_PATH = os.path.join(BASE_DIR, 'sdsul01.yaml')
PDF_DIR = os.path.join(BASE_DIR, 'sdsul01', 'pdfs')

FIELD_ORDER = [
    'id', 'seminario', 'title', 'subtitle', 'locale', 'section', 'authors',
    'resumo', 'abstract_en', 'palavras_chave', 'keywords_en',
    'pages_count', 'file', 'file_original', 'referencias',
]


def reorder_article(art):
    ordered = {}
    for key in FIELD_ORDER:
        if key in art:
            ordered[key] = art[key]
    for key in art:
        if key not in ordered:
            ordered[key] = art[key]
    return ordered


def extrair_texto_pdf(pdf_path, last_page=None):
    try:
        cmd = ['pdftotext']
        if last_page:
            cmd += ['-l', str(last_page)]
        cmd += [pdf_path, '-']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.stdout
    except Exception:
        return ''


def get_page_count(pdf_path):
    try:
        result = subprocess.run(['pdfinfo', pdf_path], capture_output=True, text=True, timeout=15)
        m = re.search(r'Pages:\s+(\d+)', result.stdout)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None


def extrair_resumo(texto):
    patterns = [
        r'(?:^|\n)\s*RESUMO\s*[:\.]?\s*\n(.*?)(?=\n\s*(?:ABSTRACT|Abstract|PALAVRAS[- ]CHAVE|Palavras[- ][Cc]have|KEYWORDS|Keywords|KEY\s*WORDS|Key\s*[Ww]ords|INTRODU|Introduction|INTRODUCTION|\d+[\.\s]+\s*[A-Z]))',
        r'(?:^|\n)\s*[Rr]esumo\s*[:\.]?\s*\n(.*?)(?=\n\s*(?:ABSTRACT|Abstract|PALAVRAS[- ]CHAVE|Palavras[- ][Cc]have|KEYWORDS|Keywords|KEY\s*WORDS|Key\s*[Ww]ords|INTRODU|Introduction|INTRODUCTION|\d+[\.\s]+\s*[A-Z]))',
    ]
    for pat in patterns:
        m = re.search(pat, texto, re.DOTALL)
        if m:
            resumo = m.group(1).strip()
            resumo = re.sub(r'\s*\n\s*', ' ', resumo)
            resumo = re.sub(r'\s+\d+\s*$', '', resumo)
            resumo = resumo.strip()
            if len(resumo) > 50:
                return resumo
    return None


def extrair_abstract(texto):
    patterns = [
        r'(?:^|\n)\s*ABSTRACT\s*[:\.]?\s*\n(.*?)(?=\n\s*(?:KEYWORDS|Keywords|KEY\s*WORDS|Key\s*[Ww]ords|PALAVRAS[- ]CHAVE|Palavras[- ][Cc]have|INTRODU|Introduction|INTRODUCTION|RESUMEN|Resumen|\d+[\.\s]+\s*[A-Z]))',
        r'(?:^|\n)\s*[Aa]bstract\s*[:\.]?\s*\n(.*?)(?=\n\s*(?:KEYWORDS|Keywords|KEY\s*WORDS|Key\s*[Ww]ords|PALAVRAS[- ]CHAVE|Palavras[- ][Cc]have|INTRODU|Introduction|INTRODUCTION|RESUMEN|Resumen|\d+[\.\s]+\s*[A-Z]))',
    ]
    for pat in patterns:
        m = re.search(pat, texto, re.DOTALL)
        if m:
            abstract = m.group(1).strip()
            abstract = re.sub(r'\s*\n\s*', ' ', abstract)
            abstract = re.sub(r'\s+\d+\s*$', '', abstract)
            abstract = abstract.strip()
            if len(abstract) > 50:
                return abstract
    return None


def extrair_keywords(texto, label_pattern=r'PALAVRAS[- ]CHAVE|Palavras[- ][Cc]have'):
    patterns = [
        rf'(?:^|\n)\s*(?:{label_pattern})\s*[:\.]?\s*(.*?)(?=\n\s*(?:ABSTRACT|Abstract|RESUMO|Resumo|KEYWORDS|Keywords|KEY\s*WORDS|Key\s*[Ww]ords|INTRODU|Introduction|INTRODUCTION|\d+[\.\s]+\s*[A-Z]|\n\n))',
    ]
    for pat in patterns:
        m = re.search(pat, texto, re.DOTALL | re.IGNORECASE)
        if m:
            kw_text = m.group(1).strip()
            kw_text = re.sub(r'\s*\n\s*', ' ', kw_text)
            if ';' in kw_text:
                kws = [k.strip() for k in kw_text.split(';')]
            elif ',' in kw_text:
                kws = [k.strip() for k in kw_text.split(',')]
            else:
                kws = [kw_text]
            kws = [re.sub(r'[\s.!;,]+$', '', k).strip() for k in kws if k.strip()]
            kws = [k for k in kws if len(k) < 100 and len(k) > 1]
            if kws:
                return kws
    return None


def extrair_keywords_en(texto):
    return extrair_keywords(texto, label_pattern=r'KEYWORDS|Keywords|KEY\s*WORDS|Key\s*[Ww]ords')


def extrair_referencias(texto):
    ref_patterns = [
        '(?:^|\\n)\\s*(?:\\d+\\.?\\s*)?REFERÊNCIAS\\s*BIBLIOGRÁFICAS\\s*[:\\.]*\\s*\\n',
        '(?:^|\\n)\\s*(?:\\d+\\.?\\s*)?Referências\\s*[Bb]ibliográficas\\s*[:\\.]*\\s*\\n',
        '(?:^|\\n)\\s*(?:\\d+\\.?\\s*)?REFERÊNCIAS\\s*[:\\.]*\\s*\\n',
        '(?:^|\\n)\\s*(?:\\d+\\.?\\s*)?Referências\\s*[:\\.]*\\s*\\n',
        '(?:^|\\n)\\s*(?:\\d+\\.?\\s*)?Referência\\s*[:\\.]*\\s*\\n',
        '(?:^|\\n)\\s*(?:\\d+\\.?\\s*)?REFERENCIAS\\s*BIBLIOGRAFICAS\\s*[:\\.]*\\s*\\n',
        '(?:^|\\n)\\s*(?:\\d+\\.?\\s*)?BIBLIOGRAFÍA\\s*[:\\.]*\\s*\\n',
        '(?:^|\\n)\\s*(?:\\d+\\.?\\s*)?BIBLIOGRAFIA\\s*[:\\.]*\\s*\\n',
        '(?:^|\\n)\\s*(?:\\d+\\.?\\s*)?Bibliografia\\s*[Cc]?onsultada\\s*[:\\.]*\\s*\\n',
        '(?:^|\\n)\\s*(?:\\d+\\.?\\s*)?Bibliografia\\s*[:\\.]*\\s*\\n',
    ]
    ref_start = None
    for pat in ref_patterns:
        m = re.search(pat, texto)
        if m:
            ref_start = m.end()
            break
    if ref_start is None:
        return None

    ref_text = texto[ref_start:]

    end_patterns = [
        '\\n\\s*(?:LISTA DE FIGURAS|CRÉDITOS|Créditos|ANEXOS?|Anexos?|APÊNDICE|Apêndice)\\b',
        '\\n\\s*(?:ILUSTRAÇÕES|Ilustrações|Fontes das Ilustra|FONTES DAS ILUSTRA)\\b',
        '\\n\\s*\\d+\\s*$',
    ]
    for pat in end_patterns:
        m = re.search(pat, ref_text)
        if m:
            ref_text = ref_text[:m.start()]

    refs = parse_referencias(ref_text)
    return refs if refs else None


def parse_referencias(ref_text):
    refs = []
    lines = ref_text.strip().split('\n')
    current_ref = ''

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_ref:
                refs.append(current_ref.strip())
                current_ref = ''
            continue
        if re.match(r'^\d{1,3}$', stripped):
            continue
        if re.match(r'^(?:Fig\.\s*\d|Figura\s*\d|Fonte:|Foto\s*\d)', stripped, re.IGNORECASE):
            if current_ref:
                refs.append(current_ref.strip())
                current_ref = ''
            continue

        is_new_ref = False
        if re.match(r'^[A-Z\u00c0-\u00dc][A-Z\u00c0-\u00dc]+[,\s]', stripped):
            is_new_ref = True
        elif re.match(r'^_{2,}', stripped):
            is_new_ref = True
        elif re.match(r'^\d+[\.\)]\s', stripped):
            is_new_ref = True
        elif re.match(r'^[-\u2013\u2014]\s', stripped):
            is_new_ref = True

        if is_new_ref and current_ref:
            refs.append(current_ref.strip())
            current_ref = stripped
        elif is_new_ref:
            current_ref = stripped
        else:
            if current_ref:
                current_ref += ' ' + stripped
            else:
                current_ref = stripped

    if current_ref:
        refs.append(current_ref.strip())

    cleaned = []
    for ref in refs:
        ref = ref.strip()
        if len(ref) < 15:
            continue
        if re.match(r'^(?:Fig\.\s*\d|Figura\s*\d|Fonte:|Foto\s*\d|Quadro\s*\d)', ref, re.IGNORECASE):
            continue
        cleaned.append(ref)
    return cleaned


def main():
    print(f"Carregando YAML: {YAML_PATH}")
    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    articles = data['articles']
    total = len(articles)

    stats = {
        'resumo_novo': 0, 'resumo_existente': 0,
        'abstract_novo': 0, 'abstract_existente': 0,
        'kw_novo': 0, 'kw_existente': 0,
        'kw_en_novo': 0, 'kw_en_existente': 0,
        'refs_novo': 0, 'refs_existente': 0,
        'pages_atualizado': 0, 'pdf_nao_encontrado': 0,
    }

    for art in articles:
        art_id = art['id']
        pdf_file = art.get('file', '')
        pdf_path = os.path.join(PDF_DIR, pdf_file)

        if not os.path.exists(pdf_path):
            print(f"  {art_id}: PDF nao encontrado: {pdf_file}")
            stats['pdf_nao_encontrado'] += 1
            continue

        pc = get_page_count(pdf_path)
        if pc is not None:
            old_pc = art.get('pages_count')
            if old_pc != pc:
                art['pages_count'] = pc
                stats['pages_atualizado'] += 1

        texto_inicio = extrair_texto_pdf(pdf_path, last_page=3)

        if texto_inicio:
            if not art.get('resumo'):
                resumo = extrair_resumo(texto_inicio)
                if resumo:
                    art['resumo'] = resumo
                    stats['resumo_novo'] += 1
                    print(f"  {art_id}: resumo extraido ({len(resumo)} chars)")
            else:
                stats['resumo_existente'] += 1

            if not art.get('abstract_en'):
                abstract = extrair_abstract(texto_inicio)
                if abstract:
                    art['abstract_en'] = abstract
                    stats['abstract_novo'] += 1
                    print(f"  {art_id}: abstract extraido ({len(abstract)} chars)")
            else:
                stats['abstract_existente'] += 1

            if not art.get('palavras_chave'):
                kw = extrair_keywords(texto_inicio)
                if kw:
                    art['palavras_chave'] = kw
                    stats['kw_novo'] += 1
                    print(f"  {art_id}: palavras-chave extraidas: {kw}")
            else:
                stats['kw_existente'] += 1

            if not art.get('keywords_en'):
                kw_en = extrair_keywords_en(texto_inicio)
                if kw_en:
                    art['keywords_en'] = kw_en
                    stats['kw_en_novo'] += 1
                    print(f"  {art_id}: keywords_en extraidas: {kw_en}")
            else:
                stats['kw_en_existente'] += 1

        if not art.get('referencias'):
            texto_completo = extrair_texto_pdf(pdf_path)
            if texto_completo:
                refs = extrair_referencias(texto_completo)
                if refs:
                    art['referencias'] = refs
                    stats['refs_novo'] += 1
                    print(f"  {art_id}: {len(refs)} referencias extraidas")
        else:
            stats['refs_existente'] += 1

    data['articles'] = [reorder_article(art) for art in articles]

    print(f"\nSalvando YAML: {YAML_PATH}")
    with open(YAML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)

    print(f"\n{'='*60}")
    print(f"SUMARIO - sdsul01 ({total} artigos)")
    print(f"{'='*60}")
    print(f"  Resumos:        {stats['resumo_novo']} novos + {stats['resumo_existente']} existentes = {stats['resumo_novo'] + stats['resumo_existente']}/{total}")
    print(f"  Abstracts:      {stats['abstract_novo']} novos + {stats['abstract_existente']} existentes = {stats['abstract_novo'] + stats['abstract_existente']}/{total}")
    print(f"  Palavras-chave: {stats['kw_novo']} novos + {stats['kw_existente']} existentes = {stats['kw_novo'] + stats['kw_existente']}/{total}")
    print(f"  Keywords (EN):  {stats['kw_en_novo']} novos + {stats['kw_en_existente']} existentes = {stats['kw_en_novo'] + stats['kw_en_existente']}/{total}")
    print(f"  Referencias:    {stats['refs_novo']} novos + {stats['refs_existente']} existentes = {stats['refs_novo'] + stats['refs_existente']}/{total}")
    print(f"  Pages count:    {stats['pages_atualizado']} atualizados")
    print(f"  PDFs ausentes:  {stats['pdf_nao_encontrado']}")


if __name__ == '__main__':
    main()
