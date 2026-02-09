#!/usr/bin/env python3
"""
Extrai metadados dos PDFs do 8o Seminario Docomomo Sul (sdsul08).
Campos extraidos: resumo, resumo_en, palavras_chave, palavras_chave_en,
                  referencias, paginas_count
"""
import os, re, subprocess, yaml
from collections import OrderedDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YAML_PATH = os.path.join(os.path.dirname(BASE_DIR), 'sdsul08.yaml')
PDF_DIR = os.path.join(BASE_DIR, 'pdfs')


# -- YAML helpers ----------------------------------------------------------

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


# -- Helpers ----------------------------------------------------------------

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
    """Join broken lines into paragraphs, remove page numbers."""
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
        # Skip standalone page numbers
        if re.match(r'^\d{1,3}\s*\|?\s*$', stripped):
            continue
        # Skip page headers/footers
        if re.match(r'^\|?\s*\d{1,3}\s*$', stripped):
            continue
        if 'VIII SEMIN' in stripped and 'DOCOMOMO' in stripped:
            continue
        # Skip author+title footers like "Titulo | Autor"
        if re.match(r'^.{10,}\s*\|\s*.{5,}$', stripped) and len(stripped) < 120:
            continue
        current_para.append(stripped)
    if current_para:
        cleaned_lines.append(' '.join(current_para))
    result = '\n'.join(cleaned_lines)
    result = re.sub(r'  +', ' ', result)
    return result.strip()


# -- Resumo extraction -----------------------------------------------------

def extract_resumo(text, locale):
    """Extract the Resumo section from full articles (Artigo completo).

    The format is: Resumo. <text> followed by page number or body text.
    There are no Abstract/Keywords sections in sdsul08.
    """
    # For English articles, look for Abstract
    if locale == 'en':
        return _extract_labeled_section(text,
            start_patterns=[r'\bAbstract\b[.\s:]'],
            end_patterns=[r'\bKeywords?\b', r'\bIntroduc', r'\n\d{2,3}\s*\|'])

    # For PT articles, look for "Resumo."
    return _extract_labeled_section(text,
        start_patterns=[r'\bResumo\b[.\s:]'],
        end_patterns=[r'\bAbstract\b', r'\bPalavras[- ]?chave\b',
                      r'\bKeywords?\b', r'\bIntroduc',
                      r'\n\d{2,3}\s*\|'])


def extract_resumo_en(text, locale):
    """Extract Abstract (English) section if present."""
    if locale == 'en':
        return None  # For English articles, the main resumo IS in English

    return _extract_labeled_section(text,
        start_patterns=[r'\bAbstract\b[.\s:]'],
        end_patterns=[r'\bKeywords?\b', r'\bKey[- ]?words?\b',
                      r'\bPalavras[- ]?chave\b', r'\bIntroduc',
                      r'\n\d{2,3}\s*\|'])


def _extract_labeled_section(text, start_patterns, end_patterns):
    """Extract a labeled section from text."""
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
            if pos > 20:  # minimum section length
                if pos < best_end:
                    best_end = pos
                break

    section_text = remaining[:best_end].strip()
    section_text = clean_text_block(section_text)

    if len(section_text) < 30:
        return None
    return section_text


# -- Keywords extraction ---------------------------------------------------

def extract_keywords_line(text, patterns):
    """Extract keywords from a labeled line."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            rest = text[m.end():]
            # Find end of keywords
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
            # Truncate at other-language keyword markers
            for cut_pat in [r'\nKey[- ]?words?\s*[:.\s]',
                            r'\nPalavras[- ]?chave\s*[:.\s]',
                            r'\nPalabras[- ]?clave\s*[:.\s]']:
                kw_cut = re.search(cut_pat, kw_text, re.IGNORECASE)
                if kw_cut:
                    kw_text = kw_text[:kw_cut.start()]
            kw_text = kw_text.strip()
            kw_text = re.sub(r'\s*\d+\s*$', '', kw_text)
            kw_text = re.sub(r'\s*\n\s*', ' ', kw_text)
            if not kw_text:
                continue
            # Split keywords
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


def extract_all_keywords(text):
    """Extract both PT and EN keywords."""
    kw_pt = extract_keywords_line(text,
        patterns=[r'Palavras[- ]?chave\s*[:.]?\s*',
                  r'Palabras[- ]?clave\s*[:.]?\s*'])
    kw_en = extract_keywords_line(text,
        patterns=[r'Keywords?\s*[:.]?\s*',
                  r'Key[- ]?words?\s*[:.]?\s*'])
    return kw_pt, kw_en


# -- References extraction -------------------------------------------------

def extract_references(full_text):
    """Extract reference list from the end of the article."""
    patterns = [
        r'\n\s*Refer\u00eancias\s+[Bb]ibliogr\u00e1ficas\s*\n',
        r'\n\s*Refer[e\u00ea]ncias\s*\n',
        r'\n\s*Refer\u00eancia\s*\n',
        r'\n\s*References?\s*\n',
        r'\n\s*Bibliografia\s*\n',
        r'\n\s*Bibliograf\u00eda\s*\n',
        r'\n\s*REFER\u00caNCIAS\s+BIBLIOGR\u00c1FICAS\s*\n',
        r'\n\s*REFER\u00caNCIAS?\s*\n',
        r'\n\s*REFERENCES?\s*\n',
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

    # Trim at end markers
    end_patterns = [
        r'\n\s*Notas\s*\n',
        r'\n\s*NOTAS\s*\n',
        r'\n\s*Fontes?\s+d[aeo]s?\s+figuras?\s*\n',
        r'\n\s*Anexo\s*\n',
        r'\n\s*Apresenta\u00e7\u00e3o\s+["\u201c\u201d]',  # session info at end
    ]
    for pat in end_patterns:
        m = re.search(pat, refs_text, re.IGNORECASE)
        if m:
            refs_text = refs_text[:m.start()]
            break

    # Filter lines: remove page numbers, headers, footers
    lines = refs_text.split('\n')
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip empty lines (mark as separator)
        if not stripped:
            filtered_lines.append('')
            continue
        # Skip standalone page numbers
        if re.match(r'^\|?\s*\d{1,3}\s*\|?\s*$', stripped):
            continue
        # Skip page headers/footers
        if 'VIII SEMIN' in stripped and 'DOCOMOMO' in stripped:
            continue
        # Skip article title footers (e.g. "Titulo | Autor")
        if re.match(r'^.{10,}\s*\|\s*.{5,}$', stripped) and len(stripped) < 120:
            continue
        # Skip form-feed characters
        if stripped == '\x0c':
            continue
        filtered_lines.append(stripped)

    # First pass: join continuation lines into complete lines.
    # A continuation line is one that doesn't start with an uppercase word
    # (i.e., it's part of the previous reference).
    joined_lines = []
    current = []
    for line in filtered_lines:
        if not line:
            # Blank line acts as separator
            if current:
                joined_lines.append(' '.join(current))
                current = []
            continue
        # Check if this line starts a new reference:
        # - Starts with UPPERCASE word(s) followed by comma/period
        # - Starts with _ (continuation with same author)
        # - Starts with quotation marks
        is_new_ref = bool(re.match(
            r'^(?:'
            r'[A-Z\u00c0-\u00dc][A-Z\u00c0-\u00dc\s/]{1,}[,.]'  # UPPERCASE SURNAME,
            r'|_+[.]'                                               # ______. (same author)
            r'|"[A-Z]'                                              # "Quoted
            r'|\u201c[A-Z]'                                         # Smart-quoted
            r')', line))
        if is_new_ref and current:
            joined_lines.append(' '.join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        joined_lines.append(' '.join(current))

    # Clean individual references
    refs = []
    for line in joined_lines:
        line = re.sub(r'  +', ' ', line).strip()
        if not line:
            continue
        if len(line) < 10:
            continue
        # Skip footnote-like text
        if re.match(r'^\d+\s+(Segundo|Sobre|Conferir|Destaque|Trata-se|Em\s)', line):
            continue
        refs.append(line)

    return refs


# -- Field ordering ---------------------------------------------------------

def ordered_article(art):
    """Reorder article fields to match existing convention plus new fields."""
    ORDER = [
        'id', 'seminario', 'titulo', 'subtitulo', 'locale', 'secao', 'paginas',
        'autores',
        'arquivo_pdf',
        'resumo', 'resumo_en',
        'palavras_chave', 'palavras_chave_en',
        'paginas_count',
        'referencias',
        'status',
    ]
    ordered = OrderedDict()
    for key in ORDER:
        if key in art:
            ordered[key] = art[key]
    # Add any remaining keys not in ORDER
    for key in art:
        if key not in ordered:
            ordered[key] = art[key]
    return ordered


# -- Main -------------------------------------------------------------------

def main():
    print('Carregando YAML: %s' % YAML_PATH)
    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    articles = data['articles']
    print('Artigos no YAML: %d' % len(articles))

    stats = {
        'resumo_added': 0, 'resumo_en_added': 0,
        'palavras_chave_added': 0, 'palavras_chave_en_added': 0,
        'paginas_count_added': 0, 'referencias_added': 0,
        'pdf_not_found': 0,
    }

    print('\n-- Extraindo metadados --')
    for i, art in enumerate(articles):
        art_id = art.get('id', 'artigo-%d' % (i + 1))
        pdf_file = art.get('arquivo_pdf', '')
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        locale = art.get('locale', 'pt-BR')

        if not os.path.exists(pdf_path):
            print('  [%s] PDF nao encontrado: %s' % (art_id, pdf_file))
            stats['pdf_not_found'] += 1
            continue

        print('  [%s] %s' % (art_id, pdf_file))

        # Page count
        if not art.get('paginas_count'):
            pc = get_page_count(pdf_path)
            if pc:
                art['paginas_count'] = pc
                stats['paginas_count_added'] += 1

        # Extract first pages for resumo/abstract/keywords
        text_first = extract_text(pdf_path, last_page=4)
        if not text_first:
            print('    AVISO: pdftotext retornou vazio')
            continue

        # Detect article type
        is_resumo_expandido = 'Resumo expandido' in text_first[:500]

        # Resumo
        if not art.get('resumo'):
            if is_resumo_expandido:
                # For "Resumo expandido", the whole text is the abstract
                # Extract everything after the "(Resumo expandido)" marker
                full_text = extract_text(pdf_path)
                resumo = _extract_resumo_expandido(full_text, locale)
                if resumo:
                    art['resumo'] = resumo
                    stats['resumo_added'] += 1
                    print('    + resumo (expandido, %d chars)' % len(resumo))
            else:
                resumo = extract_resumo(text_first, locale)
                if resumo:
                    art['resumo'] = resumo
                    stats['resumo_added'] += 1
                    print('    + resumo (%d chars)' % len(resumo))

        # Resumo EN (Abstract)
        if not art.get('resumo_en'):
            abs_en = extract_resumo_en(text_first, locale)
            if abs_en:
                art['resumo_en'] = abs_en
                stats['resumo_en_added'] += 1
                print('    + resumo_en (%d chars)' % len(abs_en))

        # Keywords
        if not art.get('palavras_chave') or art['palavras_chave'] == []:
            kw_pt, _ = extract_all_keywords(text_first)
            if kw_pt:
                art['palavras_chave'] = kw_pt
                stats['palavras_chave_added'] += 1
                print('    + palavras_chave: %s' % kw_pt)

        if not art.get('palavras_chave_en') or art['palavras_chave_en'] == []:
            _, kw_en = extract_all_keywords(text_first)
            if kw_en:
                art['palavras_chave_en'] = kw_en
                stats['palavras_chave_en_added'] += 1
                print('    + palavras_chave_en: %s' % kw_en)

        # References
        if not art.get('referencias'):
            full_text = extract_text(pdf_path)
            refs = extract_references(full_text)
            if refs:
                art['referencias'] = refs
                stats['referencias_added'] += 1
                print('    + referencias (%d itens)' % len(refs))

    # Reorder fields and save
    data['articles'] = [ordered_article(art) for art in articles]

    print('\n-- Salvando YAML: %s --' % YAML_PATH)
    with open(YAML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)

    # Summary stats
    print('\n== RESUMO ==')
    print('  Total de artigos:        %d' % len(articles))
    print('  PDFs nao encontrados:    %d' % stats['pdf_not_found'])
    print('  Resumos adicionados:     %d' % stats['resumo_added'])
    print('  Resumos_en adicionados:  %d' % stats['resumo_en_added'])
    print('  Palavras_chave adicion.: %d' % stats['palavras_chave_added'])
    print('  Palavras_chave_en adic.: %d' % stats['palavras_chave_en_added'])
    print('  Paginas_count adicion.:  %d' % stats['paginas_count_added'])
    print('  Referencias adicionadas: %d' % stats['referencias_added'])

    # Final coverage
    n_resumo = sum(1 for a in articles if a.get('resumo'))
    n_resumo_en = sum(1 for a in articles if a.get('resumo_en'))
    n_kw = sum(1 for a in articles if a.get('palavras_chave') and a['palavras_chave'] != [])
    n_kw_en = sum(1 for a in articles if a.get('palavras_chave_en') and a['palavras_chave_en'] != [])
    n_refs = sum(1 for a in articles if a.get('referencias') and a['referencias'] != [])
    n_pages = sum(1 for a in articles if a.get('paginas_count'))

    print('\n  Cobertura final:')
    print('    resumo:           %d/%d' % (n_resumo, len(articles)))
    print('    resumo_en:        %d/%d' % (n_resumo_en, len(articles)))
    print('    palavras_chave:   %d/%d' % (n_kw, len(articles)))
    print('    palavras_chave_en:%d/%d' % (n_kw_en, len(articles)))
    print('    paginas_count:    %d/%d' % (n_pages, len(articles)))
    print('    referencias:      %d/%d' % (n_refs, len(articles)))


def _extract_resumo_expandido(full_text, locale):
    """For 'Resumo expandido' articles, extract the entire body text as the resumo.

    These articles have no separate Resumo section -- the whole text IS the abstract.
    We extract everything after '(Resumo expandido)' until 'Referencias' or end.
    """
    m = re.search(r'\(Resumo expandido\)\s*\n', full_text)
    if not m:
        return None

    body = full_text[m.end():]

    # Trim at references or presentation info
    end_patterns = [
        r'\nRefer\u00eancias\s*\n',
        r'\nRefer[e\u00ea]ncias\s+[Bb]ibliogr\u00e1ficas\s*\n',
        r'\nREFER\u00caNCIAS\s*\n',
        r'\nBibliografia\s*\n',
        r'\nApresenta\u00e7\u00e3o\s+["\u201c\u201d]',
    ]
    for pat in end_patterns:
        em = re.search(pat, body, re.IGNORECASE)
        if em:
            body = body[:em.start()]
            break

    result = clean_text_block(body)
    if len(result) < 50:
        return None
    return result


if __name__ == '__main__':
    main()
