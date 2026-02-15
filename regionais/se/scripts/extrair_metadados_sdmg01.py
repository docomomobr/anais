#!/usr/bin/env python3
"""Extrai metadados dos PDFs do 1º Seminário Docomomo MG.

Usa pdftotext para extrair texto, depois regex para parsear:
- Título
- Autores (nome, email, afiliação)
- Resumo (PT) e Abstract (EN)
- Palavras-chave (PT) e Keywords (EN)
- Referências bibliográficas

Saída: JSON com todos os metadados extraídos.

Uso:
    python3 regionais/mg/scripts/extrair_metadados.py
    python3 regionais/mg/scripts/extrair_metadados.py --verbose
"""

import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIGOS_DIR = os.path.join(BASE, 'ARTIGOS', 'PDFS')
POSTERS_DIR = os.path.join(BASE, 'POSTERS', 'PDF')
OUTPUT = os.path.join(BASE, 'metadados_extraidos.json')

# Mapeamento PDF → ordem no programa (do PPSX)
# Artigos (apresentações orais): 1-16
ARTIGOS_MAP = [
    'ADRIANA - ANA TERESA -  MAX.doc.pdf',
    'ANITA DI MARCO - LUCIANA.doc.pdf',
    'CELINA BORGES - DENISE BAHIA.docx.pdf',
    'CLARA LUIZA.doc.pdf',
    'FABIO MARTINS - RAQUEL.doc.pdf',
    'KLAUS CHAVES.doc.pdf',
    'LAURA RENNÓ  RICARDO TEI.doc.pdf',
    'MARIA BEATRIZ CAPELLO.doc.pdf',
    'MARIA ELIZA GUERRA.doc.pdf',
    'MAURO FERREIRA.doc.pdf',
    'RAQUEL FERNANDES - VERA .doc.pdf',
    'RAQUEL VON RANDOW - MAR.doc.pdf',
    'MIGUEL BUZZAR.doc.pdf',
    'MARCUS VINICIUS GUIMARÃES.doc.pdf',
    'LISANDRA MARA.doc.pdf',
    'LUCY ANA.doc.pdf',
]

# Pôsteres: 17-26
POSTERS_MAP = [
    'ADRIANA MAX E ANA TERESA.pdf',
    'AGNES E CLARA.pdf',
    'ALINE WERNECK.pdf',
    'ARIEL E HENRIQUE.pdf',
    'JUSCELINO MACHADO.pdf',
    'ANA PAULA TAVAREZ.pdf',
    'LARISSA GALVÃO_OK.doc.pdf',
    'LUIS EDUARDO BORBA.pdf',
    'MARISTELA SIOLARI - OK.doc.pdf',
    'REGINA LUSTOZA.pdf',
]


def extract_text(pdf_path):
    """Extrai texto do PDF com pdftotext."""
    result = subprocess.run(
        ['pdftotext', '-layout', pdf_path, '-'],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout


def extract_text_raw(pdf_path):
    """Extrai texto do PDF sem -layout (flow mode, melhor para parsing)."""
    result = subprocess.run(
        ['pdftotext', pdf_path, '-'],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout


def clean_text(text):
    """Remove espaços extras e normaliza quebras de linha."""
    # Remove linhas com apenas números (paginação)
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped and re.match(r'^\d{1,3}$', stripped):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)


def find_email_positions(text):
    """Encontra posições de todos os emails no texto."""
    return [(m.start(), m.end(), m.group()) for m in re.finditer(r'[\w.+-]+@[\w.-]+\.\w+', text)]


def extract_title(text):
    """Extrai título das primeiras linhas do texto."""
    lines = text.strip().split('\n')
    title_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if title_lines:
                break
            continue
        # Parar se encontrar email, nome de autor (com número superscrito), ou "Resumo"/"Abstract"
        if re.search(r'@', stripped):
            break
        if re.match(r'^(Resumo|Abstract|RESUMO|ABSTRACT)', stripped):
            break
        # Se a linha for muito curta e parecer um número de nota
        if re.match(r'^\d+$', stripped):
            break
        # Se encontrar padrão de autor (nome seguido de número superscrito)
        # Heurística: linha com nome que termina em número colado
        if re.match(r'^[A-ZÀ-Ú][a-zà-ú].*\d$', stripped) and len(stripped) < 60:
            break
        title_lines.append(stripped)

    title = ' '.join(title_lines)
    # Limpar artefatos
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def extract_authors_and_affiliations(text):
    """Extrai autores, emails e afiliações do cabeçalho do texto.

    Lida com múltiplos padrões:
    - Nome\\nemail (1 por linha)
    - Nome1\\nNome2\\nemail1; email2 (nomes separados, emails juntos)
    - NOME1, NOME2 (comma-separated, uppercase)
    - Nome\\nE-mail: email
    - Nome\\nCo-autora Nome2\\nemail
    """
    # Pegar região do texto entre o título e o resumo/abstract
    header_end = None
    for pattern in [r'\bResumo\b', r'\bRESUMO\b', r'\bAbstract\b', r'\bABSTRACT\b']:
        m = re.search(pattern, text)
        if m:
            if header_end is None or m.start() < header_end:
                header_end = m.start()

    if header_end is None:
        header_end = min(len(text), 3000)

    header = text[:header_end]
    lines = header.split('\n')

    # Phase 1: Collect all names and emails from the header
    name_lines = []  # (line_index, cleaned_name)
    email_lines = []  # (line_index, [emails])

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Find all emails in this line
        emails_in_line = re.findall(r'[\w.+-]+@[\w.-]+\.\w+', stripped)

        if emails_in_line:
            email_lines.append((i, emails_in_line))

            # Check if there are names on the same line before the email
            # Pattern: "NOME1, NOME2 1" or "Nome1  email"
            before_first_email = stripped[:stripped.find(emails_in_line[0])].strip()
            # Remove "E-mail:", "e-mail:", etc.
            before_first_email = re.sub(r'^E-?mail\s*:\s*', '', before_first_email, flags=re.IGNORECASE).strip()
            # Remove trailing comma, semicolon, numbers
            before_first_email = re.sub(r'[,;\d]+$', '', before_first_email).strip()

            if before_first_email and len(before_first_email) > 3:
                # Could be comma-separated names: "NOME1, NOME2"
                if ',' in before_first_email:
                    for name in before_first_email.split(','):
                        name = re.sub(r'\d+$', '', name).strip()
                        if name and len(name) > 3:
                            name_lines.append((i, name))
                else:
                    name_lines.append((i, before_first_email))
        else:
            # Non-email line: could be a name if it's short and looks like one
            # Remove superscript numbers
            cleaned = re.sub(r'\d+$', '', stripped).strip()
            cleaned = re.sub(r'^Co-autor[a]?\s+', '', cleaned, flags=re.IGNORECASE).strip()

            # Skip if it looks like a title (first few lines, already parsed)
            # Skip if it looks like a footnote or affiliation
            if (re.match(r'^\d+\s+\S', stripped) and len(stripped) > 30):
                continue
            # Skip URLs
            if re.match(r'^https?://', stripped) or 'lattes.cnpq' in stripped:
                continue
            # Skip if it starts with "Endereço" or other non-name patterns
            if re.match(r'^(Endereço|http|www|Curso|Professor|Doutor|Arquiteto|Estudante|Mestre)', stripped):
                continue

            # Looks like a name if: starts with uppercase letter, < 60 chars, has spaces
            if (cleaned and len(cleaned) > 3 and len(cleaned) < 60
                    and ' ' in cleaned
                    and re.match(r'^[A-ZÀ-Ú]', cleaned)):
                # Must be before the first email or between emails
                if email_lines or any(re.search(r'@', lines[j].strip()) for j in range(i+1, min(i+5, len(lines)))):
                    name_lines.append((i, cleaned))

    # Phase 2: Match names to emails
    authors = []

    if name_lines and not email_lines:
        # No emails found — just use names
        for _, name in name_lines:
            authors.append({'name': name, 'email': None, 'affiliation': None})
    elif len(name_lines) == len(email_lines) == 0:
        return []
    elif email_lines:
        # Try to match: each name to the closest following email
        email_idx = 0
        pending_names = []

        for nl_idx, (name_line, name) in enumerate(name_lines):
            # Find the next email line after this name
            matched = False
            for el_idx, (email_line, emails) in enumerate(email_lines):
                if email_line >= name_line:
                    pending_names.append(name)
                    # Check if next name is also before this email line
                    if nl_idx + 1 < len(name_lines) and name_lines[nl_idx + 1][0] < email_line:
                        continue  # More names coming before this email

                    # Distribute emails to pending names
                    for pi, pname in enumerate(pending_names):
                        email = emails[pi] if pi < len(emails) else (emails[-1] if emails else None)
                        authors.append({'name': pname, 'email': email, 'affiliation': None})
                    pending_names = []
                    matched = True
                    break

            if not matched and pending_names == []:
                pending_names.append(name)

        # Handle remaining unmatched names
        if pending_names:
            # Use last email line's emails or None
            last_emails = email_lines[-1][1] if email_lines else []
            for pi, pname in enumerate(pending_names):
                email = last_emails[pi] if pi < len(last_emails) else None
                authors.append({'name': pname, 'email': email, 'affiliation': None})

    # Phase 3: Find affiliations from footnotes
    footnotes = {}
    for line in lines:
        stripped = line.strip()
        m = re.match(r'^(\d+)\s+(.{10,})', stripped)
        if m and not re.search(r'@', stripped):
            footnote_num = m.group(1)
            footnote_text = m.group(2).strip()
            if len(footnote_text) < 300:
                footnotes[footnote_num] = footnote_text

    # Match footnotes to authors by position (1-based)
    for idx, author in enumerate(authors):
        fn_key = str(idx + 1)
        if fn_key in footnotes:
            author['affiliation'] = footnotes[fn_key]

    return authors


def extract_abstract_pt(text):
    """Extrai resumo em português."""
    # Procurar bloco entre "Resumo" e "Palavras-chave" (ou "Abstract" ou "Keywords")
    patterns = [
        (r'(?:^|\n)\s*(?:Resumo|RESUMO)\s*\n(.*?)(?=\n\s*(?:Palavras[- ]?chave|PALAVRAS|Abstract|ABSTRACT|Key[- ]?words))',
         re.DOTALL | re.IGNORECASE),
    ]
    for pat, flags in patterns:
        m = re.search(pat, text, flags)
        if m:
            abstract = m.group(1).strip()
            abstract = re.sub(r'\s+', ' ', abstract)
            if len(abstract) > 50:
                return abstract
    return None


def extract_abstract_en(text):
    """Extrai abstract em inglês."""
    patterns = [
        (r'(?:^|\n)\s*(?:Abstract|ABSTRACT)\s*\n(.*?)(?=\n\s*(?:Key[- ]?words|KEY|Resumo|RESUMO|Palavras))',
         re.DOTALL | re.IGNORECASE),
    ]
    for pat, flags in patterns:
        m = re.search(pat, text, flags)
        if m:
            abstract = m.group(1).strip()
            abstract = re.sub(r'\s+', ' ', abstract)
            if len(abstract) > 50:
                return abstract
    return None


def _split_keywords(kw_text):
    """Separa keywords por ; ou , ou . (quando separador é ponto)."""
    kw_text = re.sub(r'\s+', ' ', kw_text).strip()
    # Tentar separadores em ordem de preferência
    if ';' in kw_text:
        keywords = [k.strip().rstrip('.') for k in kw_text.split(';') if k.strip()]
    elif ',' in kw_text:
        keywords = [k.strip().rstrip('.') for k in kw_text.split(',') if k.strip()]
    elif '. ' in kw_text:
        # Ponto como separador (ex: "Brutalismo. Triângulo Mineiro. Wagner")
        keywords = [k.strip().rstrip('.') for k in kw_text.split('. ') if k.strip()]
    else:
        keywords = [kw_text.strip().rstrip('.')]
    # Filtrar lixo
    keywords = [k for k in keywords if len(k) > 1 and len(k) < 100]
    return keywords if keywords else None


def extract_keywords_pt(text):
    """Extrai palavras-chave em português."""
    patterns = [
        r'[Pp]alavras[- ]?chave[s]?\s*[:;]\s*(.+?)(?:\n\s*\n|\n\s*(?:Abstract|ABSTRACT|Key))',
        r'[Pp]alavras[- ]?chave[s]?\s*[:;]\s*(.+?)$',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.MULTILINE | re.DOTALL)
        if m:
            kw_text = m.group(1).strip()
            # Limpar e separar
            kw_text = re.sub(r'\s+', ' ', kw_text)
            keywords = _split_keywords(kw_text)
            if keywords:
                return keywords
    return None


def extract_keywords_en(text):
    """Extrai keywords em inglês."""
    patterns = [
        r'[Kk]ey[- ]?words?\s*[:;]\s*(.+?)(?:\n\s*\n|\n\s*(?:Resumo|RESUMO|Palavras|[A-Z]{2,}))',
        r'[Kk]ey[- ]?words?\s*[:;]\s*(.+?)$',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.MULTILINE | re.DOTALL)
        if m:
            kw_text = m.group(1).strip()
            kw_text = re.sub(r'\s+', ' ', kw_text)
            keywords = _split_keywords(kw_text)
            if keywords:
                return keywords
    return None


def extract_references(text):
    """Extrai referências bibliográficas (seção final)."""
    # Procurar seção de referências no final do texto
    patterns = [
        r'(?:^|\n)\s*(?:Referências|REFERÊNCIAS|Referências [Bb]ibliográficas|REFERÊNCIAS BIBLIOGRÁFICAS|Bibliografia|BIBLIOGRAFIA)\s*\n(.+)',
        r'(?:^|\n)\s*(?:REFERENCES|References)\s*\n(.+)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL)
        if m:
            refs_block = m.group(1).strip()
            # Separar referências individuais
            # Padrão: cada ref começa com SOBRENOME, ou número, ou travessão
            refs = []
            current_ref = []
            for line in refs_block.split('\n'):
                stripped = line.strip()
                if not stripped:
                    if current_ref:
                        refs.append(' '.join(current_ref))
                        current_ref = []
                    continue
                # Nova referência se começa com maiúscula e parece nome de autor
                if re.match(r'^[A-ZÀ-Ú]{2,}', stripped) and current_ref:
                    refs.append(' '.join(current_ref))
                    current_ref = [stripped]
                elif re.match(r'^___', stripped) and current_ref:
                    refs.append(' '.join(current_ref))
                    current_ref = [stripped]
                else:
                    current_ref.append(stripped)
            if current_ref:
                refs.append(' '.join(current_ref))

            # Limpar referências
            clean_refs = []
            for ref in refs:
                ref = re.sub(r'\s+', ' ', ref).strip()
                if len(ref) > 20:
                    clean_refs.append(ref)

            if clean_refs:
                return clean_refs
    return None


def get_page_count(pdf_path):
    """Conta páginas do PDF."""
    result = subprocess.run(
        ['pdfinfo', pdf_path],
        capture_output=True, text=True, timeout=10
    )
    for line in result.stdout.split('\n'):
        if line.startswith('Pages:'):
            return int(line.split(':')[1].strip())
    return None


def extract_metadata(pdf_path, verbose=False):
    """Extrai todos os metadados de um PDF."""
    text = extract_text_raw(pdf_path)
    text = clean_text(text)

    if verbose:
        print(f"  Text length: {len(text)} chars")

    title = extract_title(text)
    authors = extract_authors_and_affiliations(text)
    abstract_pt = extract_abstract_pt(text)
    abstract_en = extract_abstract_en(text)
    keywords_pt = extract_keywords_pt(text)
    keywords_en = extract_keywords_en(text)
    references = extract_references(text)
    pages_count = get_page_count(pdf_path)

    return {
        'title': title,
        'authors': authors,
        'abstract_pt': abstract_pt,
        'abstract_en': abstract_en,
        'keywords_pt': keywords_pt,
        'keywords_en': keywords_en,
        'references': references,
        'pages_count': pages_count,
        'original_file': os.path.basename(pdf_path),
    }


def main():
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    all_results = []
    errors = []

    # Processar artigos
    print(f"{'='*60}")
    print("ARTIGOS (Apresentações Orais)")
    print(f"{'='*60}")

    for i, filename in enumerate(ARTIGOS_MAP, 1):
        pdf_path = os.path.join(ARTIGOS_DIR, filename)
        article_id = f"sdmg01-{i:03d}"

        if not os.path.isfile(pdf_path):
            print(f"  ERRO: {filename} não encontrado!")
            errors.append(filename)
            continue

        print(f"[{i:02d}/26] {article_id}: {filename}")

        try:
            meta = extract_metadata(pdf_path, verbose)
            meta['id'] = article_id
            meta['section'] = 'Apresentações Orais'
            meta['type'] = 'artigo'

            # Resumo de qualidade
            has_title = bool(meta['title'] and len(meta['title']) > 5)
            has_authors = len(meta['authors']) > 0
            has_abstract = bool(meta['abstract_pt'] or meta['abstract_en'])
            has_kw = bool(meta['keywords_pt'] or meta['keywords_en'])

            status = '✓' if (has_title and has_authors) else '⚠'
            print(f"  {status} Título: {meta['title'][:70]}...")
            print(f"    Autores: {len(meta['authors'])} | "
                  f"Resumo: {'PT' if meta['abstract_pt'] else '-'}"
                  f"{'EN' if meta['abstract_en'] else ''} | "
                  f"KW: {'PT' if meta['keywords_pt'] else '-'}"
                  f"{'EN' if meta['keywords_en'] else ''} | "
                  f"Refs: {len(meta['references']) if meta['references'] else 0} | "
                  f"Págs: {meta['pages_count']}")

            if verbose and meta['authors']:
                for au in meta['authors']:
                    print(f"    → {au['name']} <{au['email']}> [{au.get('affiliation', '-')}]")

            all_results.append(meta)

        except Exception as e:
            print(f"  ERRO: {e}")
            errors.append(filename)

    # Processar pôsteres
    print(f"\n{'='*60}")
    print("PÔSTERES")
    print(f"{'='*60}")

    for i, filename in enumerate(POSTERS_MAP, 17):
        pdf_path = os.path.join(POSTERS_DIR, filename)
        article_id = f"sdmg01-{i:03d}"

        if not os.path.isfile(pdf_path):
            print(f"  ERRO: {filename} não encontrado!")
            errors.append(filename)
            continue

        print(f"[{i:02d}/26] {article_id}: {filename}")

        try:
            meta = extract_metadata(pdf_path, verbose)
            meta['id'] = article_id
            meta['section'] = 'Pôsteres'
            meta['type'] = 'poster'

            has_title = bool(meta['title'] and len(meta['title']) > 5)
            has_authors = len(meta['authors']) > 0

            status = '✓' if (has_title and has_authors) else '⚠'
            print(f"  {status} Título: {meta['title'][:70]}...")
            print(f"    Autores: {len(meta['authors'])} | "
                  f"Resumo: {'PT' if meta['abstract_pt'] else '-'}"
                  f"{'EN' if meta['abstract_en'] else ''} | "
                  f"KW: {'PT' if meta['keywords_pt'] else '-'}"
                  f"{'EN' if meta['keywords_en'] else ''} | "
                  f"Refs: {len(meta['references']) if meta['references'] else 0} | "
                  f"Págs: {meta['pages_count']}")

            all_results.append(meta)

        except Exception as e:
            print(f"  ERRO: {e}")
            errors.append(filename)

    # Salvar resultados
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Extraídos: {len(all_results)}/26")
    print(f"Erros: {len(errors)}")
    if errors:
        for e in errors:
            print(f"  - {e}")
    print(f"Salvo em: {OUTPUT}")


if __name__ == '__main__':
    main()
