#!/usr/bin/env python3
"""
Extrai metadados dos PDFs do 3o Seminario Docomomo Sul (sdsul03).
"""
import os, re, shutil, subprocess, yaml
from collections import OrderedDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YAML_PATH = os.path.join(os.path.dirname(BASE_DIR), 'sdsul03.yaml')
PDF_DIR = os.path.join(BASE_DIR, 'pdfs')

class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

def str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

OrderedDumper.add_representer(dict, dict_representer)
OrderedDumper.add_representer(OrderedDict, dict_representer)
OrderedDumper.add_representer(str, str_representer)

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout
    except Exception:
        return ''

def get_page_count(pdf_path):
    output = run_cmd(['pdfinfo', pdf_path])
    m = re.search(r'Pages:\s+(\d+)', output)
    return int(m.group(1)) if m else None

def extract_text(pdf_path, last_page=None):
    cmd = ['pdftotext']
    if last_page:
        cmd += ['-l', str(last_page)]
    cmd += [pdf_path, '-']
    return run_cmd(cmd)

def clean_text_block(text):
    lines = text.split('\n')
    cleaned_lines = []
    current_para = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_para:
                cleaned_lines.append(' '.join(current_para))
                current_para = []
            continue
        if re.match(r'^\d{1,3}$', stripped):
            continue
        current_para.append(stripped)
    if current_para:
        cleaned_lines.append(' '.join(current_para))
    result = '\n'.join(cleaned_lines)
    result = re.sub(r'  +', ' ', result)
    return result.strip()

def extract_section(text, start_patterns, end_patterns):
    best_start = None
    best_start_end = None
    for pat in start_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            if best_start is None or m.start() < best_start:
                best_start = m.start()
                best_start_end = m.end()
    if best_start is None:
        return None
    remaining = text[best_start_end:]
    best_end = len(remaining)
    for pat in end_patterns:
        for m in re.finditer(pat, remaining, re.IGNORECASE):
            pos = m.start()
            if pos > 20:
                if pos < best_end:
                    best_end = pos
                break
    section_text = remaining[:best_end].strip()
    section_text = clean_text_block(section_text)
    if len(section_text) < 30:
        return None
    return section_text

def extract_keywords_line(text, patterns):
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            rest = text[m.end():]
            end_m = re.search(
                r'\n\s*\n|\bAbstract\b|\bResumo\b|\bIntroduc|^\d+\s*$',
                rest, re.IGNORECASE | re.MULTILINE)
            if end_m:
                kw_text = rest[:end_m.start()]
            else:
                kw_text = rest[:500]
                m2 = re.search(r'\.\s+[A-Z]', kw_text)
                if m2:
                    kw_text = kw_text[:m2.start()+1]
            kw_text = kw_text.strip()
            # Truncar no marcador de keywords em outro idioma
            for cut_pat in [r'\nKey[- ]?words?\s*[:.\s]', r'\nPalavras[- ]?chave\s*[:.\s]', r'\nPalabras[- ]?clave\s*[:.\s]']:
                kw_cut = re.search(cut_pat, kw_text, re.IGNORECASE)
                if kw_cut:
                    kw_text = kw_text[:kw_cut.start()]
            kw_text = kw_text.strip()
            kw_text = re.sub(r'\s*\d+\s*$', '', kw_text)
            kw_text = re.sub(r'\s*\n\s*', ' ', kw_text)
            if not kw_text:
                continue
            if ';' in kw_text:
                kws = [k.strip().rstrip('.') for k in kw_text.split(';')]
            elif ' \u2013 ' in kw_text or ' - ' in kw_text:
                sep = ' \u2013 ' if ' \u2013 ' in kw_text else ' - '
                kws = [k.strip().rstrip('.') for k in kw_text.split(sep)]
            elif ',' in kw_text:
                kws = [k.strip().rstrip('.') for k in kw_text.split(',')]
            else:
                kws = [kw_text.strip().rstrip('.')]
            kws = [k for k in kws if k and len(k) > 1]
            kws = [k.strip('"').strip('\u201c').strip('\u201d').strip("'") for k in kws]
            if kws:
                return kws
    return []

def extract_abstract_and_keywords(text, locale):
    abstract = None
    abstract_en = None
    keywords = []
    keywords_en = []
    if locale == 'es':
        abstract = extract_section(text,
            start_patterns=[r'\bAbstract\b', r'\bResumen\b'],
            end_patterns=[r'\bPalabras[- ]?clave\b', r'\bKeywords?\b', r'\bIntroduc'])
    else:
        abstract = extract_section(text,
            start_patterns=[r'\bResumo\b'],
            end_patterns=[r'\bAbstract\b', r'\bPalavras[- ]?chave\b', r'\bKeywords?\b', r'\bIntroduc'])
    if locale != 'es':
        abstract_en = extract_section(text,
            start_patterns=[r'\bAbstract\b'],
            end_patterns=[r'\bPalavras[- ]?chave\b', r'\bKeywords?\b', r'\bIntroduc', r'\bIntroduction\b'])
    else:
        tmp = extract_section(text,
            start_patterns=[r'\bAbstract\b'],
            end_patterns=[r'\bKeywords?\b', r'\bPalabras[- ]?clave\b', r'\bIntroduc'])
        if tmp and len(tmp) > 50:
            abstract_en = tmp
    kw_pt = extract_keywords_line(text,
        patterns=[r'Palavras[- ]?chave\s*[:.]?\s*', r'Palabras[- ]?clave\s*[:.]?\s*'])
    kw_en = extract_keywords_line(text,
        patterns=[r'Keywords?\s*[:.]?\s*', r'Key[- ]?words?\s*[:.]?\s*'])
    if kw_pt:
        keywords = kw_pt
    if kw_en:
        keywords_en = kw_en
    return abstract, abstract_en, keywords, keywords_en

def extract_references(full_text):
    patterns = [
        r'\n\s*Refer\u00eancias\s+[Bb]ibliogr\u00e1ficas\s*\n',
        r'\n\s*Refer[e\u00ea]ncias\s*\n',
        r'\n\s*Bibliografia\s*\n',
        r'\n\s*Bibliograf\u00eda\s*\n',
        r'\n\s*REFER\u00caNCIAS\s+BIBLIOGR\u00c1FICAS\s*\n',
        r'\n\s*REFER\u00caNCIAS\s*\n',
        r'\n\s*BIBLIOGRAFIA\s*\n',
    ]
    start_pos = None
    for pat in patterns:
        m = re.search(pat, full_text, re.IGNORECASE)
        if m:
            start_pos = m.end()
            break
    if start_pos is None:
        return []
    refs_text = full_text[start_pos:]
    end_patterns = [
        r'\n\s*Notas\s*\n',
        r'\n\s*NOTAS\s*\n',
        r'\n\s*Fontes?\s+d[aeo]s?\s+figuras?\s*\n',
        r'\n\s*Anexo\s*\n',
    ]
    for pat in end_patterns:
        m = re.search(pat, refs_text, re.IGNORECASE)
        if m:
            refs_text = refs_text[:m.start()]
            break
    lines = refs_text.split('\n')
    joined_lines = []
    current = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                joined_lines.append(' '.join(current))
                current = []
            continue
        if re.match(r'^\d{1,3}$', stripped):
            continue
        if re.match(r'^\d{1,2}\s+[A-Z]', stripped) and not re.match(r'^\d{4}', stripped):
            if current:
                joined_lines.append(' '.join(current))
                current = []
            break
        current.append(stripped)
    if current:
        joined_lines.append(' '.join(current))
    refs = []
    for line in joined_lines:
        line = re.sub(r'  +', ' ', line).strip()
        if not line:
            continue
        if refs and not re.match(r'^[A-Z\u00c0-\u00dc"\u201c\'\u2014\u2013_]', line):
            refs[-1] = refs[-1] + ' ' + line
        else:
            refs.append(line)
    cleaned_refs = []
    for ref in refs:
        ref = ref.strip()
        if len(ref) < 10:
            continue
        if re.match(r'^\d+\s+(Segundo|Sobre|Conferir|Destaque|Trata-se|Em\s)', ref):
            continue
        cleaned_refs.append(ref)
    return cleaned_refs

def rename_pdfs(articles):
    renamed = 0
    for art in articles:
        target = art.get('file')
        original = art.get('file_original')
        if not target or not original:
            continue
        target_path = os.path.join(PDF_DIR, target)
        original_path = os.path.join(PDF_DIR, original)
        if os.path.exists(target_path):
            continue
        if os.path.exists(original_path):
            shutil.copy2(original_path, target_path)
            renamed += 1
            print(f"  Copiado: {original} -> {target}")
        else:
            print(f"  AVISO: PDF nao encontrado: {original}")
    return renamed

def ordered_article(art):
    ORDER = [
        'id', 'title', 'subtitle', 'authors', 'section', 'locale',
        'file', 'file_original', 'abstract', 'abstract_en',
        'keywords', 'keywords_en', 'page_count', 'references',
    ]
    ordered = OrderedDict()
    for key in ORDER:
        if key in art:
            ordered[key] = art[key]
    for key in art:
        if key not in ordered:
            ordered[key] = art[key]
    return ordered

def main():
    print(f"Carregando YAML: {YAML_PATH}")
    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    articles = data['articles']
    print(f"Artigos no YAML: {len(articles)}")
    print("\n-- Renomeando PDFs --")
    renamed = rename_pdfs(articles)
    print(f"  PDFs copiados: {renamed}")
    stats = {
        'abstract_added': 0, 'abstract_en_added': 0,
        'keywords_added': 0, 'keywords_en_added': 0,
        'page_count_added': 0, 'references_added': 0,
        'pdf_not_found': 0,
    }
    print("\n-- Extraindo metadados --")
    for i, art in enumerate(articles):
        art_id = art.get('id', f'artigo-{i+1}')
        pdf_file = art.get('file', '')
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        locale = art.get('locale', 'pt-BR')
        if not os.path.exists(pdf_path):
            print(f"  [{art_id}] PDF nao encontrado: {pdf_file}")
            stats['pdf_not_found'] += 1
            continue
        print(f"  [{art_id}] {pdf_file}")
        if not art.get('page_count'):
            pc = get_page_count(pdf_path)
            if pc:
                art['page_count'] = pc
                stats['page_count_added'] += 1
        text_first = extract_text(pdf_path, last_page=3)
        if not text_first:
            print("    AVISO: pdftotext retornou vazio")
            continue
        abs_pt, abs_en, kws, kws_en = extract_abstract_and_keywords(text_first, locale)
        if not art.get('abstract') and abs_pt:
            art['abstract'] = abs_pt
            stats['abstract_added'] += 1
            print(f"    + abstract ({len(abs_pt)} chars)")
        if not art.get('abstract_en') and abs_en:
            art['abstract_en'] = abs_en
            stats['abstract_en_added'] += 1
            print(f"    + abstract_en ({len(abs_en)} chars)")
        if (not art.get('keywords') or art['keywords'] == []) and kws:
            art['keywords'] = kws
            stats['keywords_added'] += 1
            print(f"    + keywords: {kws}")
        if (not art.get('keywords_en') or art['keywords_en'] == []) and kws_en:
            art['keywords_en'] = kws_en
            stats['keywords_en_added'] += 1
            print(f"    + keywords_en: {kws_en}")
        if not art.get('references'):
            full_text = extract_text(pdf_path)
            refs = extract_references(full_text)
            if refs:
                art['references'] = refs
                stats['references_added'] += 1
                print(f"    + references ({len(refs)} itens)")
    data['articles'] = [ordered_article(art) for art in articles]
    print(f"\n-- Salvando YAML: {YAML_PATH} --")
    with open(YAML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)
    print("\n== RESUMO ==")
    print(f"  Total de artigos:    {len(articles)}")
    print(f"  PDFs renomeados:     {renamed}")
    print(f"  PDFs nao encontrados:{stats['pdf_not_found']}")
    print(f"  Abstracts adicionados:   {stats['abstract_added']}")
    print(f"  Abstracts_en adicionados:{stats['abstract_en_added']}")
    print(f"  Keywords adicionados:    {stats['keywords_added']}")
    print(f"  Keywords_en adicionados: {stats['keywords_en_added']}")
    print(f"  Page count adicionados:  {stats['page_count_added']}")
    print(f"  Referencias adicionadas: {stats['references_added']}")
    n_abstract = sum(1 for a in articles if a.get('abstract'))
    n_abstract_en = sum(1 for a in articles if a.get('abstract_en'))
    n_kw = sum(1 for a in articles if a.get('keywords') and a['keywords'] != [])
    n_kw_en = sum(1 for a in articles if a.get('keywords_en') and a['keywords_en'] != [])
    n_refs = sum(1 for a in articles if a.get('references') and a['references'] != [])
    n_pages = sum(1 for a in articles if a.get('page_count'))
    print(f"\n  Cobertura final:")
    print(f"    abstract:    {n_abstract}/{len(articles)}")
    print(f"    abstract_en: {n_abstract_en}/{len(articles)}")
    print(f"    keywords:    {n_kw}/{len(articles)}")
    print(f"    keywords_en: {n_kw_en}/{len(articles)}")
    print(f"    page_count:  {n_pages}/{len(articles)}")
    print(f"    references:  {n_refs}/{len(articles)}")

if __name__ == '__main__':
    main()
