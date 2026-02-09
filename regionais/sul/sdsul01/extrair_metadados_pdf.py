#!/usr/bin/env python3
"""
Extrai metadados (resumo, abstract, keywords, referencias) dos PDFs do sdsul01.
Usa OrderedDumper com width=10000 e sort_keys=False.
"""

import os, re, subprocess, yaml
from collections import OrderedDict

YAML_PATH = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul/sdsul01.yaml'
PDF_DIR = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul/sdsul01/pdfs'

class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

def str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

OrderedDumper.add_representer(OrderedDict, dict_representer)
OrderedDumper.add_representer(dict, dict_representer)
OrderedDumper.add_representer(str, str_representer)

FIELD_ORDER = [
    'id', 'seminario', 'title', 'subtitle', 'locale', 'section',
    'authors', 'resumo', 'abstract_en', 'palavras_chave', 'keywords_en',
    'pages_count', 'file', 'file_original', 'referencias',
]

def order_article(article):
    ordered = OrderedDict()
    for key in FIELD_ORDER:
        if key in article:
            ordered[key] = article[key]
    for key in article:
        if key not in ordered:
            ordered[key] = article[key]
    return ordered

def extract_text(pdf_path):
    try:
        result = subprocess.run(['pdftotext', pdf_path, '-'],
            capture_output=True, text=True, timeout=60)
        return result.stdout
    except Exception as e:
        print('  ERRO pdftotext: {}'.format(e))
        return ''

def clean_text(text):
    return text.replace('\x0c', '\n')

def find_header_end(lines):
    """Identifica o fim do cabecalho (titulo + autores + credenciais)."""
    header_pats = [
        re.compile(r'^[A-Z\u00C0-\u00DC\s,.:;\-\u2013\u2014()\'\"\u201C\u201D]+$'),
        re.compile(r'^\s*$'),
        re.compile(r'^(Arquiteto|Mestre|Doutor|Professor|Doutorando|Mestrando|Livre.Docente)', re.I),
        re.compile(r'^(Acad\u00eamic[oa]|Alun[oa]|Bolsista|Pesquisador|Engenheiro)', re.I),
        re.compile(r'^\([A-Z]'),
        re.compile(r'^(PROPAR|FAU|IAU|PPG|PPGAU)', re.I),
        re.compile(r'@'),
        re.compile(r'^(Tel|Fax|CEP|Rua|Av\.|Avenida|Campus)', re.I),
        re.compile(r'^\d{5}[\-.]?\d{3}'),
        re.compile(r'^\(\d{2,3}\)\s?\d'),
        re.compile(r'^Curso de |^Departamento de |^Faculdade de |^Centro de ', re.I),
        re.compile(r'^Pr\u00e9dio \d', re.I),
    ]
    last_hdr = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        is_hdr = any(p.search(s) for p in header_pats)
        if is_hdr and i < 25:
            last_hdr = i
        elif not is_hdr and i > 3 and len(s) > 50:
            pass  # no skip tolerance
            return i
    return last_hdr + 1

def extract_resumo_explicit(text):
    pat = re.compile(
        r'(?:^|\n)\s*RESUMO\s*\n(.*?)(?=\n\s*(?:ABSTRACT|PALAVRAS[- ]?CHAVE|KEY\s*WORDS|KEYWORDS|Introdu|INTRODU|\d+[\s.\u2013\-]+\s*Introdu)|$)',
        re.DOTALL | re.IGNORECASE)
    m = pat.search(text)
    if m:
        r = m.group(1).strip()
        r = re.sub(r'\n(?!\n)', ' ', r)
        r = re.sub(r'\s+', ' ', r).strip()
        if len(r) > 50:
            return r
    return None

def extract_abstract_explicit(text):
    pat = re.compile(
        r'(?:^|\n)\s*ABSTRACT\s*\n(.*?)(?=\n\s*(?:KEY\s*WORDS|KEYWORDS|PALAVRAS|Introdu|INTRODU|\d+[\s.\u2013\-]+\s*Introdu)|$)',
        re.DOTALL | re.IGNORECASE)
    m = pat.search(text)
    if m:
        a = m.group(1).strip()
        a = re.sub(r'\n(?!\n)', ' ', a)
        a = re.sub(r'\s+', ' ', a).strip()
        if len(a) > 50:
            return a
    return None

def parse_kw_list(raw):
    raw = re.sub(r'\n', ' ', raw).strip().rstrip('.')
    if ';' in raw:
        kws = [k.strip().rstrip('.') for k in raw.split(';') if k.strip()]
    elif ',' in raw:
        kws = [k.strip().rstrip('.') for k in raw.split(',') if k.strip()]
    else:
        kws = [raw.strip()]
    return [k for k in kws if k and len(k) > 1]

def extract_keywords_pt(text):
    pat = re.compile(
        r'(?:^|\n)\s*PALAVRAS[- ]?CHAVE\s*[:\s]*(.+?)(?=\n\s*(?:ABSTRACT|KEY\s*WORDS|KEYWORDS|Introdu|INTRODU|\d+[.\-\u2013]\s)|$)',
        re.DOTALL | re.IGNORECASE)
    m = pat.search(text)
    if m:
        return parse_kw_list(m.group(1))
    return None

def extract_keywords_en(text):
    for ps in [
        r'(?:^|\n)\s*KEY\s*WORDS\s*[:\s]*(.+?)(?=\n\s*(?:Introdu|INTRODU|\d+[.\-\u2013]\s|RESUMO|\n\n)|$)',
        r'(?:^|\n)\s*KEYWORDS\s*[:\s]*(.+?)(?=\n\s*(?:Introdu|INTRODU|\d+[.\-\u2013]\s|RESUMO|\n\n)|$)',
    ]:
        pat = re.compile(ps, re.DOTALL | re.IGNORECASE)
        m = pat.search(text)
        if m:
            result = parse_kw_list(m.group(1))
            if result:
                return result
    return None

def extract_first_paragraphs(text, max_chars=2000):
    """Para artigos sem RESUMO explicito, extrai primeiros paragrafos."""
    lines = text.split('\n')
    hdr_end = find_header_end(lines)
    content = lines[hdr_end:]
    paras = []
    cur = []
    for line in content:
        s = line.strip()
        if not s:
            if cur:
                pt = ' '.join(cur)
                if (len(pt) > 60 and not pt.startswith('Fig') and
                    not pt.startswith('Figura') and not re.match(r'^\d+\s*$', pt)
                    and not re.match(r'^Tabela\s', pt)):
                    paras.append(pt)
                cur = []
        else:
            if re.match(r'^\d+$', s):
                continue
            cur.append(s)
    if cur:
        pt = ' '.join(cur)
        if len(pt) > 60:
            paras.append(pt)
    if not paras:
        return None
    result = []
    tlen = 0
    for p in paras[:3]:
        if tlen + len(p) > max_chars and result:
            break
        result.append(p)
        tlen += len(p)
    if not result:
        return None
    r = '\n'.join(result)
    r = re.sub(r'  +', ' ', r)
    return r.strip()

def extract_references(text):
    """Extrai secao de referencias do final do texto."""
    ref_pat = re.compile(
        r'(?:^|\n)\s*(REFER\u00caNCIAS BIBLIOGR\u00c1FICAS|Refer\u00eancias Bibliogr\u00e1ficas|'
        r'Refer\u00eancias bibliogr\u00e1ficas|REFER\u00caNCIAS|Refer\u00eancias|'
        r'REFERENCIAS BIBLIOGRAFICAS|Referencias Bibliograficas|'
        r'BIBLIOGRAFIA|Bibliografia|NOTAS E REFER\u00caNCIAS|Refer\u00eancias:)\s*:?\s*\n',
        re.MULTILINE)
    matches = list(ref_pat.finditer(text))
    if not matches:
        return None
    m = matches[-1]
    rt = text[m.end():].strip()
    rt = re.sub(r'\n\s*\d{1,2}\s*$', '', rt)
    lines = rt.split('\n')
    refs = []
    cur = []
    for line in lines:
        s = line.strip()
        if not s:
            if cur:
                r = ' '.join(cur).strip()
                if r and len(r) > 10:
                    refs.append(r)
                cur = []
            continue
        is_new = False
        if re.match(r'^[A-Z\u00C0-\u00DC_]{2,}[\s,.]', s):
            is_new = True
        elif re.match(r'^(\[\d+\]|\d+[.\)])\s', s):
            is_new = True
        elif re.match(r'^[_\-]{3,}', s):
            is_new = True
        if is_new and cur:
            r = ' '.join(cur).strip()
            if r and len(r) > 10:
                refs.append(r)
            cur = [s]
        else:
            cur.append(s)
    if cur:
        r = ' '.join(cur).strip()
        if r and len(r) > 10:
            refs.append(r)
    clean = []
    for r in refs:
        if re.match(r'^(Fontes das Ilustra|Cr\u00e9dito das imagens|Fonte das figuras)', r, re.I):
            break
        if len(r) < 20:
            continue
        r = re.sub(r'\s+', ' ', r).strip()
        clean.append(r)
    return clean if clean else None

def process_article(article):
    extracted = {}
    pdf_file = article.get('file_original') or article.get('file')
    if not pdf_file:
        return extracted
    pdf_path = os.path.join(PDF_DIR, pdf_file)
    if not os.path.exists(pdf_path):
        pdf_path = os.path.join(PDF_DIR, article.get('file', ''))
        if not os.path.exists(pdf_path):
            print('  PDF nao encontrado: {}'.format(pdf_file))
            return extracted
    text = extract_text(pdf_path)
    if not text or len(text) < 100:
        print('  Texto muito curto ou vazio')
        return extracted
    text = clean_text(text)
    if not article.get('resumo'):
        resumo = extract_resumo_explicit(text)
        if resumo:
            extracted['resumo'] = resumo
            extracted['_src'] = 'explicit'
        else:
            resumo = extract_first_paragraphs(text)
            if resumo:
                extracted['resumo'] = resumo
                extracted['_src'] = 'first_paragraphs'
    if not article.get('abstract_en'):
        ab = extract_abstract_explicit(text)
        if ab:
            extracted['abstract_en'] = ab
    if not article.get('palavras_chave'):
        kw = extract_keywords_pt(text)
        if kw:
            extracted['palavras_chave'] = kw
    if not article.get('keywords_en'):
        kw = extract_keywords_en(text)
        if kw:
            extracted['keywords_en'] = kw
    if not article.get('referencias'):
        refs = extract_references(text)
        if refs:
            extracted['referencias'] = refs
    return extracted

def main():
    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    articles = data['articles']
    print('Total de artigos no YAML: {}'.format(len(articles)))
    print()
    stats = dict(
        resumo_existing=0, resumo_expl=0, resumo_para=0,
        abstract_en_existing=0, abstract_en_new=0,
        kw_existing=0, kw_new=0,
        kwen_existing=0, kwen_new=0,
        ref_existing=0, ref_new=0,
    )
    for article in articles:
        aid = article['id']
        print('Processando {}...'.format(aid))
        if article.get('resumo'): stats['resumo_existing'] += 1
        if article.get('abstract_en'): stats['abstract_en_existing'] += 1
        if article.get('palavras_chave'): stats['kw_existing'] += 1
        if article.get('keywords_en'): stats['kwen_existing'] += 1
        if article.get('referencias'): stats['ref_existing'] += 1
        ex = process_article(article)
        if 'resumo' in ex:
            src = ex.pop('_src', '?')
            article['resumo'] = ex['resumo']
            if src == 'explicit':
                stats['resumo_expl'] += 1
                print('  resumo: extraido (explicito, {} chars)'.format(len(ex['resumo'])))
            else:
                stats['resumo_para'] += 1
                print('  resumo: extraido (paragrafos, {} chars)'.format(len(ex['resumo'])))
        elif '_src' in ex:
            ex.pop('_src')
        if 'abstract_en' in ex:
            article['abstract_en'] = ex['abstract_en']
            stats['abstract_en_new'] += 1
            print('  abstract_en: extraido ({} chars)'.format(len(ex['abstract_en'])))
        if 'palavras_chave' in ex:
            article['palavras_chave'] = ex['palavras_chave']
            stats['kw_new'] += 1
            print('  palavras_chave: {}'.format(ex['palavras_chave']))
        if 'keywords_en' in ex:
            article['keywords_en'] = ex['keywords_en']
            stats['kwen_new'] += 1
            print('  keywords_en: {}'.format(ex['keywords_en']))
        if 'referencias' in ex:
            article['referencias'] = ex['referencias']
            stats['ref_new'] += 1
            print('  referencias: {} refs extraidas'.format(len(ex['referencias'])))
    data['articles'] = [order_article(a) for a in articles]
    out = OrderedDict()
    out['issue'] = data['issue']
    out['articles'] = data['articles']
    with open(YAML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(dict(out), f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)
    print()
    print('=' * 60)
    print('ESTATISTICAS')
    print('=' * 60)
    t = len(articles)
    print('Total de artigos: {}'.format(t))
    print()
    rt = stats['resumo_existing'] + stats['resumo_expl'] + stats['resumo_para']
    print('RESUMO:')
    print('  Ja existiam:              {}'.format(stats['resumo_existing']))
    print('  Extraidos (explicito):    {}'.format(stats['resumo_expl']))
    print('  Extraidos (paragrafos):   {}'.format(stats['resumo_para']))
    print('  Total com resumo:         {}/{}'.format(rt, t))
    print()
    at = stats['abstract_en_existing'] + stats['abstract_en_new']
    print('ABSTRACT (EN):')
    print('  Ja existiam:              {}'.format(stats['abstract_en_existing']))
    print('  Extraidos:                {}'.format(stats['abstract_en_new']))
    print('  Total com abstract_en:    {}/{}'.format(at, t))
    print()
    kt = stats['kw_existing'] + stats['kw_new']
    print('PALAVRAS-CHAVE:')
    print('  Ja existiam:              {}'.format(stats['kw_existing']))
    print('  Extraidas:                {}'.format(stats['kw_new']))
    print('  Total com palavras_chave: {}/{}'.format(kt, t))
    print()
    ket = stats['kwen_existing'] + stats['kwen_new']
    print('KEYWORDS (EN):')
    print('  Ja existiam:              {}'.format(stats['kwen_existing']))
    print('  Extraidas:                {}'.format(stats['kwen_new']))
    print('  Total com keywords_en:    {}/{}'.format(ket, t))
    print()
    rft = stats['ref_existing'] + stats['ref_new']
    print('REFERENCIAS:')
    print('  Ja existiam:              {}'.format(stats['ref_existing']))
    print('  Extraidas:                {}'.format(stats['ref_new']))
    print('  Total com referencias:    {}/{}'.format(rft, t))
    print()

if __name__ == '__main__':
    main()
