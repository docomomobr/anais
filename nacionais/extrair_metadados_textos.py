#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrai metadados (abstract, abstract_en, keywords, keywords_en, references)
de arquivos de texto (pdftotext) e os adiciona ao YAML nacional correspondente.

Uso:
    python3 extrair_metadados_textos.py sdbr04
    python3 extrair_metadados_textos.py sdbr01 sdbr02 sdbr03 sdbr04 sdbr05
"""

import os
import re
import sys
import yaml
from collections import OrderedDict
from pathlib import Path

TEXTOS_DIR = Path(os.path.expanduser(
    "~/Dropbox/docomomo/momopedia_br/data/textos"
))
YAML_DIR = Path(os.path.expanduser(
    "~/Dropbox/docomomo/26-27/anais/nacionais"
))

CAMPO_ORDEM = [
    'title', 'subtitle', 'authors', 'section', 'pages', 'locale',
    'abstract', 'abstract_en', 'keywords', 'keywords_en', 'references',
]

class OrderedDumper(yaml.SafeDumper):
    pass

def _dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

def _str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

OrderedDumper.add_representer(OrderedDict, _dict_representer)
OrderedDumper.add_representer(dict, _dict_representer)
OrderedDumper.add_representer(str, _str_representer)


def ler_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def salvar_yaml(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        issue = data.get('issue', {})
        slug = issue.get('slug', '')
        title = issue.get('title', '')
        source = issue.get('source', '')
        subtitle = issue.get('subtitle', '')
        f.write(f"# {title} - {slug}\n")
        if subtitle:
            f.write("# Espelho dos metadados publicados no OJS\n")
        f.write(f"# Fonte: {source}\n\n")
        f.write("issue:\n")
        for k, v in issue.items():
            if isinstance(v, list):
                if not v:
                    f.write(f"  {k}: []\n")
                else:
                    f.write(f"  {k}:\n")
                    for item in v:
                        f.write(f'    - "{item}"\n')
            elif v is None:
                f.write(f"  {k}: null\n")
            elif isinstance(v, str):
                f.write(f'  {k}: "{v}"\n')
            elif isinstance(v, bool):
                val_str = 'true' if v else 'false'
                f.write(f"  {k}: {val_str}\n")
            else:
                f.write(f"  {k}: {v}\n")
        f.write("\narticles:\n")
        for art in data.get('articles', []):
            ordered = ordenar_artigo(art)
            art_yaml = yaml.dump(
                [ordered], Dumper=OrderedDumper,
                allow_unicode=True, default_flow_style=False,
                sort_keys=False, width=10000
            )
            f.write(art_yaml)
            f.write("\n")


def ordenar_artigo(art):
    ordered = OrderedDict()
    for key in CAMPO_ORDEM:
        if key in art:
            ordered[key] = art[key]
    for key in art:
        if key not in ordered:
            ordered[key] = art[key]
    return ordered


def limpar_texto(texto):
    texto = texto.replace('\x0c', '\n')
    texto = re.sub(
        r'^\s*\d+[ºª]\s*[Ss]emin[aá]rio\s*[Dd]ocomomo\s*[Bb]rasil.*$',
        '', texto, flags=re.MULTILINE
    )
    texto = re.sub(r'^\s*\d{1,3}\s*$', '', texto, flags=re.MULTILINE)
    return texto


RESUMO_TERM = (
    r'ABSTRACT|Abstract'
    r'|PALAVRAS[\s\-]*CHAVE|Palavras[\s\-]*[Cc]have'
    r'|KEYWORDS|Keywords|Key[\s\-]*[Ww]ords'
    r'|RESUMEN|Resumen'
    r'|INTRODU[CÇ][AÃ]O|Introdu[cç][aã]o|Introduction|INTRODUCTION'
    r'|Texto\s+[Pp]rincipal|TEXTO\s+PRINCIPAL'
    r'|Antecedentes|ANTECEDENTES'
    r'|Apresenta[cç][aã]o|APRESENTA[CÇ][AÃ]O'
    r'|Considera[cç][oõ]es|CONSIDERA[CÇ][OÕ]ES'
    r'|Metodologia|METODOLOGIA'
    r'|Hist[oó]rico|HIST[OÓ]RICO'
    r'|Contextualiza[cç][aã]o|CONTEXTUALIZA[CÇ][AÃ]O'
    r'|Justificativa|JUSTIFICATIVA'
)

ABSTRACT_TERM = (
    r'KEYWORDS|Keywords|Key[\s\-]*[Ww]ords'
    r'|PALAVRAS[\s\-]*CHAVE|Palavras[\s\-]*[Cc]have'
    r'|INTRODU[CÇ][AÃ]O|Introdu[cç][aã]o|Introduction|INTRODUCTION'
    r'|RESUMO|Resumo'
    r'|RESUMEN|Resumen'
    r'|Texto\s+[Pp]rincipal|TEXTO\s+PRINCIPAL'
    r'|Antecedentes|ANTECEDENTES'
    r'|RÉSUMÉ'
)


def extrair_resumo(texto):
    # Max chars for abstract (avoid capturing entire article text)
    MAX_ABSTRACT = 5000
    patterns = [
        (r'(?:^|\n)\s*(?:RESUMO|Resumo)\s*[:\.]?\s*\n'
         r'(.*?)'
         r'(?=\n\s*(?:' + RESUMO_TERM + r')\b)'),
        r'(?:^|\n)\s*(?:RESUMO|Resumo)\s*[:\.]?\s*\n(.*?)(?=\n\s*\n\s*\n)',
        r'(?:^|\n)\s*(?:RESUMO|Resumo)\s*[:\.]?\s*\n(.*?)(?=\n\s*\d+\s*[\.\-\u2013\u2014]\s*[A-Z\u00c0-\u00dc])',
        r'(?:^|\n)\s*(?:RESUMO|Resumo)\s*[:\.]?\s*\n(.*)',
    ]
    for pat in patterns:
        m = re.search(pat, texto, re.DOTALL)
        if m:
            resumo = _clean_text(m.group(1))
            if len(resumo) > 50 and len(resumo) <= MAX_ABSTRACT:
                return resumo
    return None


def extrair_abstract(texto):
    patterns = [
        (r'(?:^|\n)\s*(?:ABSTRACT|Abstract)\s*[:\.]?\s*\n'
         r'(.*?)'
         r'(?=\n\s*(?:' + ABSTRACT_TERM + r')\b)'),
        r'(?:^|\n)\s*(?:ABSTRACT|Abstract)\s*[:\.]?\s*\n(.*?)(?=\n\s*\n\s*\n)',
        r'(?:^|\n)\s*(?:ABSTRACT|Abstract)\s*[:\.]?\s*\n(.*?)(?=\n\s*\d+\s*[\.\-\u2013\u2014]\s*[A-Z])',
    ]
    for pat in patterns:
        m = re.search(pat, texto, re.DOTALL)
        if m:
            abstract = _clean_text(m.group(1))
            if len(abstract) > 50:
                return abstract
    return None


def extrair_palavras_chave(texto):
    patterns = [
        r'[Pp]alavras[\s\-]*[Cc]have[s]?\s*[:\-\u2013\u2014.]\s*(.*?)(?=\n\s*(?:ABSTRACT|Abstract|KEYWORDS|Keywords|Key[\s\-]*[Ww]ords|INTRODU[CÇ]|Introdu[cç]|RESUMO|Resumo)\b)',
        r'[Pp]alavras[\s\-]*[Cc]have[s]?\s*[:\-\u2013\u2014.]\s*(.*?)(?=\n\s*\n)',
    ]
    for pat in patterns:
        m = re.search(pat, texto, re.DOTALL | re.IGNORECASE)
        if m:
            result = _parse_keywords(m.group(1))
            if result:
                return result
    return None


def extrair_keywords_en(texto):
    patterns = [
        r'[Kk]ey[\s\-]*[Ww]ords?\s*[:\-\u2013\u2014.]\s*(.*?)(?=\n\s*(?:INTRODU[CÇ]|Introdu[cç]|Introduction|INTRODUCTION|RESUMO|Resumo|RÉSUMÉ|Resumen|RESUMEN)\b)',
        r'[Kk]ey[\s\-]*[Ww]ords?\s*[:\-\u2013\u2014.]\s*(.*?)(?=\n\s*\n)',
    ]
    for pat in patterns:
        m = re.search(pat, texto, re.DOTALL | re.IGNORECASE)
        if m:
            result = _parse_keywords(m.group(1))
            if result:
                return result
    return None


def extrair_referencias(texto):
    ref_patterns = [
        r'(?:^|\n)\s*(?:REFERÊNCIAS\s+BIBLIOGRÁFICAS|Referências\s+[Bb]ibliográficas)\s*[:\.]?\s*\n',
        r'(?:^|\n)\s*(?:REFERÊNCIAS|Referências|REFERENCIAS|Referencias)\s*[:\.]?\s*\n',
        r'(?:^|\n)\s*(?:BIBLIOGRAFIA|Bibliografia)\s*[:\.]?\s*\n',
        r'(?:^|\n)\s*(?:REFERENCES|References)\s*[:\.]?\s*\n',
        r'(?:^|\n)\s*(?:FONTES\s*(?:E\s*)?REFERÊNCIAS|Fontes\s*(?:e\s*)?[Rr]eferências)\s*[:\.]?\s*\n',
    ]
    ref_text = None
    for pat in ref_patterns:
        m = re.search(pat, texto, re.IGNORECASE)
        if m:
            ref_text = texto[m.end():]
            break
    if not ref_text:
        return None
    for end_pat in [
        r'\n\s*(?:Créditos|CRÉDITOS)\s*\n',
        r'\n\s*(?:Notas|NOTAS)\s*:?\s*\n',
        r'\n\s*(?:Anexo|ANEXO)\s',
        r'\n\s*Sumário\s+de\s+Autores\b',
        r'\n\s*Sumário\s+de\s+Artigos\b',
        r'\n\s*Sumário\s*$',
        r'\n\s*Currículos?\s*\n',
        r'\n\s*Endereço\s*\n',
    ]:
        em = re.search(end_pat, ref_text, re.IGNORECASE)
        if em:
            ref_text = ref_text[:em.start()]
    return _parse_references(ref_text)


def _clean_text(text):
    text = text.strip()
    text = re.sub(r'\s*\n\s*', ' ', text)
    text = re.sub(r'  +', ' ', text)
    text = text.strip()
    text = re.sub(r'\s+\d{1,3}\s*$', '', text)
    return text


def _parse_keywords(kw_text):
    kw_text = kw_text.strip()
    kw_text = re.sub(r'\s*\n\s*', ' ', kw_text)
    kw_text = re.sub(r'[\s.]+$', '', kw_text)
    if ';' in kw_text:
        kws = [k.strip() for k in kw_text.split(';')]
    elif ',' in kw_text:
        kws = [k.strip() for k in kw_text.split(',')]
    else:
        kws = [kw_text]
    result = []
    for k in kws:
        k = re.sub(r'[\s.!;]+$', '', k).strip()
        k = re.sub(r'^\s*[\-\u2013\u2014\u2022\xb7]\s*', '', k).strip()
        if len(k) >= 2:
            result.append(k)
    return result if result else None


def _parse_references(ref_text):
    ref_text = ref_text.strip()
    if not ref_text:
        return None
    entries = []
    current = []
    for line in ref_text.split('\n'):
        stripped = line.strip()
        if not stripped:
            if current:
                entries.append(' '.join(current))
                current = []
            continue
        is_new_ref = bool(
            re.match(r'^[A-Z\u00c0-\u00dc][A-Z\u00c0-\u00dc\s]{2,},', stripped) or
            re.match(r'^_{3,}', stripped) or
            re.match(r'^-{3,}', stripped) or
            re.match(r'^\[\d+\]', stripped)
        )
        if is_new_ref and current:
            entries.append(' '.join(current))
            current = [stripped]
        else:
            current.append(stripped)
    if current:
        entries.append(' '.join(current))
    if len(entries) <= 2 and len(ref_text) > 300:
        entries2 = _split_refs_by_surname(ref_text)
        if len(entries2) > len(entries):
            entries = entries2
    cleaned = []
    for e in entries:
        e = re.sub(r'\s+', ' ', e).strip()
        if len(e) < 15:
            continue
        if re.match(r'^\d+$', e):
            continue
        if re.match(r'^Sumário', e, re.IGNORECASE):
            continue
        cleaned.append(e)
    return cleaned if cleaned else None


def _split_refs_by_surname(text):
    entries = []
    current = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r'^[A-Z\u00c0-\u00dc][A-Z\u00c0-\u00dc\s]{2,},', stripped):
            if current:
                entries.append(' '.join(current))
            current = [stripped]
        elif re.match(r'^_{3,}|^-{3,}', stripped):
            if current:
                entries.append(' '.join(current))
            current = [stripped]
        else:
            current.append(stripped)
    if current:
        entries.append(' '.join(current))
    return entries


def processar_seminario(slug):
    yaml_path = YAML_DIR / f"{slug}.yaml"
    if not yaml_path.exists():
        print(f"ERRO: YAML não encontrado: {yaml_path}")
        return
    data = ler_yaml(yaml_path)
    articles = data.get('articles', [])
    total = len(articles)
    stats = {
        'total': total, 'txt_found': 0, 'txt_missing': 0,
        'new': {'abstract': 0, 'abstract_en': 0, 'keywords': 0,
                'keywords_en': 0, 'references': 0},
        'existing': {'abstract': 0, 'abstract_en': 0, 'keywords': 0,
                     'keywords_en': 0, 'references': 0},
    }
    for i, art in enumerate(articles):
        idx = i + 1
        txt_name = f"{slug}-{idx:03d}.txt"
        txt_path = TEXTOS_DIR / txt_name
        if not txt_path.exists():
            stats['txt_missing'] += 1
            continue
        stats['txt_found'] += 1
        texto = txt_path.read_text(encoding='utf-8', errors='replace')
        texto = limpar_texto(texto)
        for field, extractor in [
            ('abstract', extrair_resumo),
            ('abstract_en', extrair_abstract),
            ('keywords', extrair_palavras_chave),
            ('keywords_en', extrair_keywords_en),
            ('references', extrair_referencias),
        ]:
            if field in art and art[field]:
                stats['existing'][field] += 1
            else:
                val = extractor(texto)
                if val:
                    art[field] = val
                    stats['new'][field] += 1
    salvar_yaml(yaml_path, data)
    found = stats['txt_found']
    print(f"\n{'='*60}")
    print(f"  {slug.upper()} - Estatísticas de extração")
    print(f"{'='*60}")
    print(f"  Total artigos:      {stats['total']}")
    print(f"  Textos encontrados: {stats['txt_found']}")
    print(f"  Textos faltantes:   {stats['txt_missing']}")
    print(f"  ---")
    for field in ['abstract', 'abstract_en', 'keywords', 'keywords_en', 'references']:
        n = stats['new'][field]
        e = stats['existing'][field]
        t = n + e
        label = f"{field:14s}"
        print(f"  {label} novos: {n:3d}  já existiam: {e:3d}  total: {t:3d}/{found}")
    print(f"{'='*60}")
    return stats


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 extrair_metadados_textos.py <slug> [slug2 ...]")
        print("  Exemplo: python3 extrair_metadados_textos.py sdbr04")
        sys.exit(1)
    for slug in sys.argv[1:]:
        processar_seminario(slug)


if __name__ == '__main__':
    main()
