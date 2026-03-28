#!/usr/bin/env python3
"""Gera estrutura de conteúdo Hugo a partir do anais.db.

Uso:
    # Gerar conteúdo para um seminário
    python3 scripts/db2hugo.py --seminar sdnne08 --outdir site/content

    # Gerar para todos os regionais
    python3 scripts/db2hugo.py --all --outdir site/content
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import shutil

import yaml

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'anais.db')
FICHAS_PATH = os.path.join(os.path.dirname(__file__), '..', 'revisao', 'fichas_catalograficas.yaml')
REPO_ROOT = os.path.join(os.path.dirname(__file__), '..')

# Map slug prefix -> cover directories (relative to REPO_ROOT), in priority order.
# site/static/img/capas/ is tracked in git; nacionais/capas/ etc. are gitignored.
COVER_DIRS = {
    'sdbr': ['site/static/img/capas', 'nacionais/capas'],
    'sdmg': ['site/static/img/capas', 'regionais/se/capas'],
    'sdnne': ['site/static/img/capas', 'regionais/nne/capas'],
    'sdrj': ['site/static/img/capas', 'regionais/se/capas'],
    'sdsp': ['site/static/img/capas', 'regionais/se/capas'],
    'sdsul': ['site/static/img/capas', 'regionais/sul/capas'],
    'sdpr': ['site/static/img/capas', 'regionais/sul/capas'],
}

AMBITO_MAP = {
    'sdbr': ('brasil', 'Brasil'),
    'sdmg': ('se', 'Sudeste'),
    'sdnne': ('nne', 'Norte/Nordeste'),
    'sdrj': ('se', 'Sudeste'),
    'sdsp': ('se', 'Sudeste'),
    'sdsul': ('sul', 'Sul'),
    'sdpr': ('sul', 'Sul'),
}


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def load_fichas():
    """Load fichas catalográficas from YAML (repeated slug/ficha pairs)."""
    if not os.path.isfile(FICHAS_PATH):
        return {}
    result = {}
    with open(FICHAS_PATH, 'r', encoding='utf-8') as f:
        text = f.read()
    # Split into documents by adding --- between slug: entries
    docs_text = text.replace('\nslug:', '\n---\nslug:')
    for doc in yaml.safe_load_all(docs_text):
        if doc and isinstance(doc, dict) and 'slug' in doc:
            result[doc['slug']] = doc.get('ficha', '')
    return result


def find_cover(slug):
    """Find cover image (PNG) for a seminar slug. Returns absolute path or None."""
    for prefix, cover_dirs in COVER_DIRS.items():
        if slug.startswith(prefix):
            for cover_dir in cover_dirs:
                png = os.path.join(REPO_ROOT, cover_dir, f'{slug}.png')
                if os.path.isfile(png):
                    return png
    return None


def get_ambito(slug):
    """Return (ambito_slug, ambito_nome) for a seminar slug."""
    for prefix, (a_slug, a_name) in AMBITO_MAP.items():
        if slug.startswith(prefix):
            return a_slug, a_name
    return 'outros', 'Outros'


# City → (state abbrev, state name) for ABNT citation and state grouping
CITY_STATE = {
    'Belém': ('PA', 'Pará'),
    'Belo Horizonte': ('MG', 'Minas Gerais'),
    'Brasília': ('DF', 'Distrito Federal'),
    'Campina Grande': ('PB', 'Paraíba'),
    'Curitiba': ('PR', 'Paraná'),
    'Fortaleza': ('CE', 'Ceará'),
    'Manaus': ('AM', 'Amazonas'),
    'Niterói': ('RJ', 'Rio de Janeiro'),
    'Palmas': ('TO', 'Tocantins'),
    'Porto Alegre': ('RS', 'Rio Grande do Sul'),
    'Recife': ('PE', 'Pernambuco'),
    'Rio de Janeiro': ('RJ', 'Rio de Janeiro'),
    'Salvador': ('BA', 'Bahia'),
    'Santos': ('SP', 'São Paulo'),
    'São Carlos': ('SP', 'São Paulo'),
    'São Luís': ('MA', 'Maranhão'),
    'São Paulo': ('SP', 'São Paulo'),
    'Uberlândia': ('MG', 'Minas Gerais'),
    'Viçosa': ('MG', 'Minas Gerais'),
}


def parse_event_title(title):
    """Decompose event title into ABNT citation components.

    Input:  '4º Seminário Docomomo Rio, Rio de Janeiro, 2017'
    Output: {'event_name': 'Seminário Docomomo Rio',
             'event_edition': '4',
             'event_city': 'Rio de Janeiro',
             'event_year': '2017'}
    """
    m = re.match(
        r'(\d+)º\s+(Seminário|Encontro)\s+Docomomo\s+(.+?),\s+(.+),\s+(\d{4})$',
        title
    )
    if not m:
        return None
    return {
        'event_name': f'{m.group(2)} Docomomo {m.group(3)}',
        'event_edition': m.group(1),
        'event_city': m.group(4),
        'event_year': m.group(5),
    }


def yaml_escape(val):
    """Escape a string for YAML double-quoted scalar."""
    if val is None:
        return ''
    s = str(val)
    s = s.replace('\\', '\\\\').replace('"', '\\"')
    s = s.replace('\t', '\\t').replace('\r', '\\r')
    # Strip control characters (ord < 32) except \n
    s = ''.join(c if c == '\n' or ord(c) >= 32 else '' for c in s)
    s = s.replace('\n', '\\n')
    return s


def yaml_multiline(text, indent=2):
    """Format text as YAML literal block scalar."""
    if not text:
        return '""'
    prefix = ' ' * indent
    lines = text.rstrip().split('\n')
    return '|\n' + '\n'.join(prefix + line for line in lines)


def fetch_seminar(db, slug):
    return db.execute('SELECT * FROM seminars WHERE slug = ?', (slug,)).fetchone()


def fetch_articles(db, slug):
    return db.execute("""
        SELECT a.*, s.title as section_title, s.abbrev as section_abbrev,
               s.hide_title as section_hide_title, s.seq as section_seq
        FROM articles a
        LEFT JOIN sections s ON s.id = a.section_id
        WHERE a.seminar_slug = ?
        ORDER BY a.id
    """, (slug,)).fetchall()


def fetch_authors(db, article_id):
    return db.execute("""
        SELECT au.givenname, au.familyname, aa.affiliation, au.orcid
        FROM article_author aa
        JOIN authors au ON au.id = aa.author_id
        WHERE aa.article_id = ?
        ORDER BY aa.seq
    """, (article_id,)).fetchall()


def parse_json_field(val):
    """Parse a JSON array field, returning a list."""
    if not val:
        return []
    if val.startswith('['):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return []
    return [k.strip() for k in val.split(',') if k.strip()]


def doi_to_record_id(doi):
    """Extract Zenodo record ID from DOI: 10.5281/zenodo.XXXXXX -> XXXXXX"""
    if not doi:
        return None
    parts = doi.split('/')
    for p in reversed(parts):
        if p.startswith('zenodo.'):
            return p.replace('zenodo.', '')
    return None


def write_article_page(outdir, article, authors, seminar, ambito_slug, ambito_nome, ficha=None):
    """Write a Hugo content page for a single article."""
    article_id = article['id']
    article_dir = os.path.join(outdir, ambito_slug, seminar['slug'], article_id)
    os.makedirs(article_dir, exist_ok=True)

    doi = article['doi']
    record_id = article['zenodo_record_id'] or doi_to_record_id(doi)
    pdf_url = ''
    if record_id and article['file']:
        pdf_url = f"https://zenodo.org/records/{record_id}/files/{article['file']}"

    keywords = parse_json_field(article['keywords'])
    keywords_en = parse_json_field(article['keywords_en'])
    keywords_es = parse_json_field(article['keywords_es'])
    references = parse_json_field(article['references_'])

    # Build front matter
    lines = ['---']
    lines.append(f'title: "{yaml_escape(article["title"])}"')
    if article['subtitle']:
        lines.append(f'subtitle: "{yaml_escape(article["subtitle"])}"')
    if article['title_en']:
        lines.append(f'title_en: "{yaml_escape(article["title_en"])}"')
    if article['subtitle_en']:
        lines.append(f'subtitle_en: "{yaml_escape(article["subtitle_en"])}"')
    if article['title_es']:
        lines.append(f'title_es: "{yaml_escape(article["title_es"])}"')
    if article['subtitle_es']:
        lines.append(f'subtitle_es: "{yaml_escape(article["subtitle_es"])}"')
    lines.append(f'date: {seminar["date_published"]}')
    lines.append(f'slug: {article_id}')
    lines.append(f'type: artigo')
    if article['document_type'] and article['document_type'] != 'artigo':
        lines.append(f'document_type: {article["document_type"]}')
    # Mesas primeiro dentro de cada seção
    lines.append(f'weight: {0 if article["document_type"] == "mesa" else 10}')
    if article['section_title'] and not article['section_hide_title']:
        # Strip slug suffix from section title for display
        sec = article['section_title']
        # Remove " — sdnne08" suffix if present
        for suffix_marker in [' — sd', ' - sd']:
            idx = sec.find(suffix_marker)
            if idx > 0:
                sec = sec[:idx]
        lines.append(f'section_title: "{yaml_escape(sec)}"')
        if article['section_seq']:
            lines.append(f'section_seq: {article["section_seq"]}')
        # Emit section_label only if seq < 90 and the title doesn't already
        # start with the label (e.g. sdbr01 "Parte 01" already contains "parte")
        label = seminar['section_label'] or ''
        title_starts_with_label = label and sec.lower().startswith(label.lower())
        if article['section_seq'] and article['section_seq'] < 90 and label and not title_starts_with_label:
            lines.append(f'section_label: "{yaml_escape(label)}"')
    lines.append(f'event_title: "{yaml_escape(seminar["title"])}"')
    if seminar['location']:
        lines.append(f'event_location: "{yaml_escape(seminar["location"])}"')
    lines.append(f'event_date: "{seminar["date_published"]}"')
    if seminar['isbn']:
        lines.append(f'event_isbn: "{seminar["isbn"]}"')
    if seminar['publisher']:
        lines.append(f'event_publisher: "{yaml_escape(seminar["publisher"])}"')
    lines.append(f'event_slug: {seminar["slug"]}')
    lines.append(f'ambito: {ambito_slug}')
    lines.append(f'ambito_nome: "{ambito_nome}"')
    # ABNT citation components (parsed from event_title)
    cite = parse_event_title(seminar['title'])
    if cite:
        lines.append(f'event_name: "{yaml_escape(cite["event_name"])}"')
        lines.append(f'event_edition: {cite["event_edition"]}')
        lines.append(f'event_city: "{yaml_escape(cite["event_city"])}"')
        lines.append(f'event_year: {cite["event_year"]}')
    if article['locale']:
        lines.append(f'locale: "{article["locale"]}"')
    if article['pages']:
        lines.append(f'pages: "{article["pages"]}"')
    if article['file']:
        lines.append(f'pdf_file: "{article["file"]}"')

    # Abstract
    if article['abstract']:
        lines.append(f'abstract: {yaml_multiline(article["abstract"])}')

    # Keywords
    if keywords:
        lines.append('keywords:')
        for kw in keywords:
            lines.append(f'  - "{yaml_escape(kw)}"')

    # Abstract EN
    if article['abstract_en']:
        lines.append(f'abstract_en: {yaml_multiline(article["abstract_en"])}')
    if keywords_en:
        lines.append('keywords_en:')
        for kw in keywords_en:
            lines.append(f'  - "{yaml_escape(kw)}"')

    # Abstract ES
    if article['abstract_es']:
        lines.append(f'abstract_es: {yaml_multiline(article["abstract_es"])}')
    if keywords_es:
        lines.append('keywords_es:')
        for kw in keywords_es:
            lines.append(f'  - "{yaml_escape(kw)}"')

    # Authors (structured)
    if authors:
        lines.append('authors:')
        for au in authors:
            lines.append(f'  - givenname: "{yaml_escape(au["givenname"])}"')
            lines.append(f'    familyname: "{yaml_escape(au["familyname"])}"')
            if au['affiliation']:
                lines.append(f'    affiliation: "{yaml_escape(au["affiliation"])}"')
            if au['orcid']:
                lines.append(f'    orcid: "{au["orcid"]}"')

    # DOI and PDF
    if doi:
        lines.append(f'doi: "{doi}"')
    if pdf_url:
        lines.append(f'zenodo_pdf_url: "{pdf_url}"')

    lines.append(f'license_url: "https://creativecommons.org/licenses/by/4.0/"')

    # Ficha catalográfica
    if ficha:
        lines.append(f'ficha_catalografica: "{yaml_escape(ficha)}"')

    # Taxonomies for Hugo
    if authors:
        lines.append('autores:')
        for au in authors:
            lines.append(f'  - "{yaml_escape(au["familyname"])}, {yaml_escape(au["givenname"])}"')
    if keywords:
        lines.append('palavras-chave:')
        for kw in keywords:
            lines.append(f'  - "{yaml_escape(kw)}"')

    lines.append('---')

    # Body: references
    body_parts = []
    if references:
        body_parts.append('## Referências\n')
        for ref in references:
            safe_ref = ref.replace('<', '&lt;').replace('>', '&gt;')
            body_parts.append(f'- {safe_ref}')

    content = '\n'.join(lines) + '\n'
    if body_parts:
        content += '\n' + '\n'.join(body_parts) + '\n'

    filepath = os.path.join(article_dir, 'index.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    # Generate citation files with slug-based names
    write_citation_files(article_dir, article_id, article, authors, seminar)

    return filepath


def _bibtex_escape(s):
    """Escape special chars for BibTeX."""
    if not s:
        return ''
    return s.replace('&', '\\&').replace('_', '\\_').replace('%', '\\%')


def write_citation_files(outdir, slug, article, authors, seminar):
    """Write .bib, .ris, .json, .yaml citation files for an article."""
    title = article['title'] or ''
    subtitle = article['subtitle'] or ''
    full_title = f"{title}: {subtitle}" if subtitle else title
    year = seminar['date_published'][:4] if seminar['date_published'] else ''
    date_full = seminar['date_published'] or ''
    location = seminar['location'] or ''
    event_title = seminar['title'] or ''
    isbn = seminar['isbn'] or ''
    publisher = seminar['publisher'] or ''
    pages = article['pages'] or ''
    doi = article['doi'] or ''
    locale = article['locale'] or 'pt'
    record_id = article['zenodo_record_id'] or doi_to_record_id(doi)
    pdf_url = ''
    if record_id and article['file']:
        pdf_url = f"https://zenodo.org/records/{record_id}/files/{article['file']}"

    abstract = (article['abstract'] or '').strip()
    keywords = parse_json_field(article['keywords'])

    # BibTeX
    bib_key = slug.replace('-', '_')
    bib_authors = ' and '.join(
        f"{au['familyname']}, {au['givenname']}" for au in authors
    )
    bib_lines = [f'@inproceedings{{{bib_key},']
    bib_lines.append(f'  title     = {{{_bibtex_escape(full_title)}}},')
    bib_lines.append(f'  author    = {{{bib_authors}}},')
    bib_lines.append(f'  booktitle = {{{_bibtex_escape(event_title)}}},')
    bib_lines.append(f'  year      = {{{year}}},')
    if location:
        bib_lines.append(f'  address   = {{{location}}},')
    if pages:
        bib_lines.append(f'  pages     = {{{pages}}},')
    if doi:
        bib_lines.append(f'  doi       = {{{doi}}},')
    if isbn:
        bib_lines.append(f'  isbn      = {{{isbn}}},')
    if pdf_url:
        bib_lines.append(f'  url       = {{{pdf_url}}},')
    if abstract:
        bib_lines.append(f'  abstract  = {{{_bibtex_escape(abstract)}}},')
    if keywords:
        bib_lines.append(f'  keywords  = {{{", ".join(keywords)}}},')
    bib_lines.append('}')
    with open(os.path.join(outdir, f'{slug}.bib'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(bib_lines) + '\n')

    # RIS
    ris_lines = ['TY  - CPAPER']
    for au in authors:
        ris_lines.append(f"AU  - {au['familyname']}, {au['givenname']}")
    ris_lines.append(f'TI  - {full_title}')
    ris_lines.append(f'T2  - {event_title}')
    ris_lines.append(f'PY  - {year}')
    ris_lines.append(f'DA  - {date_full.replace("-", "/")}')
    if location:
        ris_lines.append(f'CY  - {location}')
    if pages:
        parts = pages.split('-')
        if len(parts) == 2:
            ris_lines.append(f'SP  - {parts[0]}')
            ris_lines.append(f'EP  - {parts[1]}')
        else:
            ris_lines.append(f'SP  - {pages}')
    if doi:
        ris_lines.append(f'DO  - {doi}')
    if isbn:
        ris_lines.append(f'SN  - {isbn}')
    if pdf_url:
        ris_lines.append(f'UR  - {pdf_url}')
    if abstract:
        ris_lines.append(f'AB  - {abstract}')
    for kw in keywords:
        ris_lines.append(f'KW  - {kw}')
    ris_lines.append(f'LA  - {locale}')
    ris_lines.append('ER  -')
    with open(os.path.join(outdir, f'{slug}.ris'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(ris_lines) + '\n')

    # CSL-JSON
    csl = {
        'id': slug,
        'type': 'paper-conference',
        'title': full_title,
        'container-title': event_title,
        'event-title': event_title,
        'issued': {'date-parts': [[int(year)]]} if year else {},
        'language': locale,
        'author': [
            {'family': au['familyname'], 'given': au['givenname'],
             **(({'ORCID': f"https://orcid.org/{au['orcid']}"}) if au['orcid'] else {})}
            for au in authors
        ],
    }
    if location:
        csl['event-place'] = location
        csl['publisher-place'] = location
    if doi:
        csl['DOI'] = doi
    if isbn:
        csl['ISBN'] = isbn
    if pages:
        csl['page'] = pages
    if pdf_url:
        csl['URL'] = pdf_url
    if abstract:
        csl['abstract'] = abstract
    if keywords:
        csl['keyword'] = ', '.join(keywords)
    with open(os.path.join(outdir, f'{slug}.json'), 'w', encoding='utf-8') as f:
        json.dump(csl, f, ensure_ascii=False, indent=2)
        f.write('\n')

    # YAML (CSL-YAML)
    yaml_csl = {
        'id': slug,
        'type': 'paper-conference',
        'title': full_title,
        'container-title': event_title,
        'event-title': event_title,
        'issued': {'date-parts': [[int(year)]]} if year else {},
        'language': locale,
        'author': [
            {'family': au['familyname'], 'given': au['givenname'],
             **(({'ORCID': f"https://orcid.org/{au['orcid']}"}) if au['orcid'] else {})}
            for au in authors
        ],
    }
    if location:
        yaml_csl['event-place'] = location
        yaml_csl['publisher-place'] = location
    if doi:
        yaml_csl['DOI'] = doi
    if isbn:
        yaml_csl['ISBN'] = isbn
    if pages:
        yaml_csl['page'] = pages
    if pdf_url:
        yaml_csl['URL'] = pdf_url
    if abstract:
        yaml_csl['abstract'] = abstract
    if keywords:
        yaml_csl['keyword'] = '; '.join(keywords)
    with open(os.path.join(outdir, f'{slug}.yaml'), 'w', encoding='utf-8') as f:
        yaml.dump(yaml_csl, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def write_seminar_citations(outdir, seminar, articles_data, ambito_slug):
    """Write combined citation files for an entire seminar."""
    slug = seminar['slug']
    event_dir = os.path.join(outdir, ambito_slug, slug)

    event_title = seminar['title'] or ''
    year = seminar['date_published'][:4] if seminar['date_published'] else ''
    date_full = seminar['date_published'] or ''
    location = seminar['location'] or ''
    isbn = seminar['isbn'] or ''

    bib_all, ris_all, csl_all, yaml_all = [], [], [], []

    for article, authors in articles_data:
        title = article['title'] or ''
        subtitle = article['subtitle'] or ''
        full_title = f"{title}: {subtitle}" if subtitle else title
        pages = article['pages'] or ''
        doi = article['doi'] or ''
        locale = article['locale'] or 'pt'
        record_id = article['zenodo_record_id'] or doi_to_record_id(doi)
        pdf_url = ''
        if record_id and article['file']:
            pdf_url = f"https://zenodo.org/records/{record_id}/files/{article['file']}"
        art_id = article['id']

        # BibTeX
        bib_key = art_id.replace('-', '_')
        bib_authors = ' and '.join(
            f"{au['familyname']}, {au['givenname']}" for au in authors
        )
        entry = [f'@inproceedings{{{bib_key},']
        entry.append(f'  title     = {{{_bibtex_escape(full_title)}}},')
        entry.append(f'  author    = {{{bib_authors}}},')
        entry.append(f'  booktitle = {{{_bibtex_escape(event_title)}}},')
        entry.append(f'  year      = {{{year}}},')
        if location:
            entry.append(f'  address   = {{{location}}},')
        if pages:
            entry.append(f'  pages     = {{{pages}}},')
        if doi:
            entry.append(f'  doi       = {{{doi}}},')
        if isbn:
            entry.append(f'  isbn      = {{{isbn}}},')
        if pdf_url:
            entry.append(f'  url       = {{{pdf_url}}},')
        entry.append('}')
        bib_all.append('\n'.join(entry))

        # RIS
        ris = ['TY  - CPAPER']
        for au in authors:
            ris.append(f"AU  - {au['familyname']}, {au['givenname']}")
        ris.append(f'TI  - {full_title}')
        ris.append(f'T2  - {event_title}')
        ris.append(f'PY  - {year}')
        ris.append(f'DA  - {date_full.replace("-", "/")}')
        if location:
            ris.append(f'CY  - {location}')
        if pages:
            parts = pages.split('-')
            if len(parts) == 2:
                ris.append(f'SP  - {parts[0]}')
                ris.append(f'EP  - {parts[1]}')
            else:
                ris.append(f'SP  - {pages}')
        if doi:
            ris.append(f'DO  - {doi}')
        if isbn:
            ris.append(f'SN  - {isbn}')
        if pdf_url:
            ris.append(f'UR  - {pdf_url}')
        ris.append(f'LA  - {locale}')
        ris.append('ER  -')
        ris_all.append('\n'.join(ris))

        # CSL-JSON
        csl = {
            'id': art_id,
            'type': 'paper-conference',
            'title': full_title,
            'container-title': event_title,
            'event-title': event_title,
            'issued': {'date-parts': [[int(year)]]} if year else {},
            'language': locale,
            'author': [
                {'family': au['familyname'], 'given': au['givenname'],
                 **(({'ORCID': f"https://orcid.org/{au['orcid']}"}) if au['orcid'] else {})}
                for au in authors
            ],
        }
        if location:
            csl['event-place'] = location
            csl['publisher-place'] = location
        if doi:
            csl['DOI'] = doi
        if isbn:
            csl['ISBN'] = isbn
        if pages:
            csl['page'] = pages
        if pdf_url:
            csl['URL'] = pdf_url
        csl_all.append(csl)

        # YAML entry
        yaml_all.append(csl.copy())

    with open(os.path.join(event_dir, f'{slug}.bib'), 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(bib_all) + '\n')
    with open(os.path.join(event_dir, f'{slug}.ris'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(ris_all) + '\n')
    with open(os.path.join(event_dir, f'{slug}.json'), 'w', encoding='utf-8') as f:
        json.dump(csl_all, f, ensure_ascii=False, indent=2)
        f.write('\n')
    with open(os.path.join(event_dir, f'{slug}.yaml'), 'w', encoding='utf-8') as f:
        yaml.dump(yaml_all, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def write_event_index(outdir, seminar, articles, ambito_slug, ambito_nome):
    """Write _index.md for an event (seminar)."""
    slug = seminar['slug']
    event_dir = os.path.join(outdir, ambito_slug, slug)
    os.makedirs(event_dir, exist_ok=True)

    # Copy cover image if available
    cover = find_cover(slug)
    has_cover = False
    if cover:
        dest = os.path.join(event_dir, f'{slug}.png')
        shutil.copy2(cover, dest)
        has_cover = True

    lines = ['---']
    lines.append(f'title: "{yaml_escape(seminar["title"])}"')
    if seminar['subtitle']:
        lines.append(f'subtitle: "{yaml_escape(seminar["subtitle"])}"')
    lines.append(f'date: {seminar["date_published"]}')
    lines.append(f'type: evento')
    lines.append(f'slug: {slug}')
    lines.append(f'ambito: {ambito_slug}')
    lines.append(f'ambito_nome: "{ambito_nome}"')
    if seminar['location']:
        lines.append(f'event_location: "{yaml_escape(seminar["location"])}"')
    if seminar['isbn']:
        lines.append(f'event_isbn: "{seminar["isbn"]}"')
    if seminar['publisher']:
        lines.append(f'event_publisher: "{yaml_escape(seminar["publisher"])}"')
    if seminar['editors']:
        editors_list = parse_json_field(seminar['editors'])
        if editors_list:
            lines.append(f'editors: "{yaml_escape(", ".join(editors_list))}"')
    if seminar['description']:
        lines.append(f'description: {yaml_multiline(seminar["description"])}')
    if has_cover:
        lines.append(f'cover: "{slug}.png"')
    if seminar['volume_pdf']:
        lines.append(f'volume_pdf: "{seminar["volume_pdf"]}"')
    if seminar['volume_pdf_label']:
        lines.append(f'volume_pdf_label: "{seminar["volume_pdf_label"]}"')
    lines.append(f'article_count: {len(articles)}')
    # State info (parsed from event title city)
    cite = parse_event_title(seminar['title'])
    if cite:
        city = cite['event_city']
        state_info = CITY_STATE.get(city)
        if state_info:
            lines.append(f'event_state: "{state_info[0]}"')
            lines.append(f'event_state_name: "{state_info[1]}"')
    lines.append('---')

    filepath = os.path.join(event_dir, '_index.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return filepath


AMBITO_WEIGHT = {'brasil': 1, 'se': 2, 'nne': 3, 'sul': 4}


def write_ambito_index(outdir, ambito_slug, ambito_nome):
    """Write _index.md for an âmbito (region)."""
    ambito_dir = os.path.join(outdir, ambito_slug)
    os.makedirs(ambito_dir, exist_ok=True)
    lines = ['---']
    lines.append(f'title: "Seminários Docomomo {ambito_nome}"')
    lines.append(f'type: ambito')
    lines.append(f'ambito: {ambito_slug}')
    lines.append(f'ambito_nome: "{ambito_nome}"')
    lines.append(f'weight: {AMBITO_WEIGHT.get(ambito_slug, 99)}')
    lines.append('---')
    filepath = os.path.join(ambito_dir, '_index.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return filepath


def write_homepage(outdir):
    """Write top-level _index.md."""
    lines = ['---']
    lines.append('title: "Anais Docomomo Brasil"')
    lines.append('type: homepage')
    lines.append('---')
    filepath = os.path.join(outdir, '_index.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return filepath


def generate_seminar(db, slug, outdir, fichas=None):
    """Generate all Hugo content for one seminar."""
    seminar = fetch_seminar(db, slug)
    if not seminar:
        print(f"Seminário '{slug}' não encontrado")
        return 0

    ambito_slug, ambito_nome = get_ambito(slug)
    articles = fetch_articles(db, slug)

    if not articles:
        print(f"Nenhum artigo para '{slug}'")
        return 0

    ficha = (fichas or {}).get(slug)

    # Write ambito index
    write_ambito_index(outdir, ambito_slug, ambito_nome)

    # Write event index
    write_event_index(outdir, seminar, articles, ambito_slug, ambito_nome)

    # Write article pages and collect data for seminar citations
    count = 0
    articles_data = []
    for art in articles:
        authors = fetch_authors(db, art['id'])
        write_article_page(outdir, art, authors, seminar, ambito_slug, ambito_nome, ficha=ficha)
        articles_data.append((art, authors))
        count += 1

    # Write combined citation files for the seminar
    write_seminar_citations(outdir, seminar, articles_data, ambito_slug)

    return count


def main():
    parser = argparse.ArgumentParser(description='Gera conteúdo Hugo a partir do anais.db')
    parser.add_argument('--seminar', help='Slug do seminário (ex: sdnne08)')
    parser.add_argument('--all', action='store_true', help='Gerar para todos os seminários (regionais + nacionais)')
    parser.add_argument('--outdir', default='site/content', help='Diretório de saída')
    args = parser.parse_args()

    if not args.seminar and not args.all:
        print("Erro: forneça --seminar SLUG ou --all")
        sys.exit(1)

    db = get_db()
    try:
        outdir = args.outdir
        os.makedirs(outdir, exist_ok=True)

        # Load fichas catalográficas
        fichas = load_fichas()

        # Write homepage
        write_homepage(outdir)

        if args.all:
            slugs = [r['slug'] for r in db.execute(
                "SELECT slug FROM seminars ORDER BY slug"
            ).fetchall()]
        else:
            slugs = [args.seminar]

        total = 0
        for slug in slugs:
            count = generate_seminar(db, slug, outdir, fichas=fichas)
            print(f"{slug}: {count} artigos")
            total += count

        print(f"\nTotal: {total} artigos em {outdir}/")
    finally:
        db.close()


if __name__ == '__main__':
    main()
