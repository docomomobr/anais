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
import sqlite3
import sys
import textwrap

import shutil

import yaml

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'anais.db')
FICHAS_PATH = os.path.join(os.path.dirname(__file__), '..', 'revisao', 'fichas_catalograficas.yaml')
REPO_ROOT = os.path.join(os.path.dirname(__file__), '..')

# Map slug prefix -> cover directory (relative to REPO_ROOT)
COVER_DIRS = {
    'sdbr': 'nacionais/capas',
    'sdmg': 'regionais/se/capas',
    'sdnne': 'regionais/nne/capas',
    'sdrj': 'regionais/se/capas',
    'sdsp': 'regionais/se/capas',
    'sdsul': 'regionais/sul/capas',
}

AMBITO_MAP = {
    'sdbr': ('brasil', 'Brasil'),
    'sdmg': ('se', 'Sudeste'),
    'sdnne': ('nne', 'Norte/Nordeste'),
    'sdrj': ('se', 'Sudeste'),
    'sdsp': ('se', 'Sudeste'),
    'sdsul': ('sul', 'Sul'),
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
    for prefix, cover_dir in COVER_DIRS.items():
        if slug.startswith(prefix):
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


def yaml_escape(val):
    """Escape a string for YAML double-quoted scalar."""
    if val is None:
        return ''
    s = str(val)
    s = s.replace('\\', '\\\\').replace('"', '\\"')
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


def fetch_sections(db, slug):
    return db.execute(
        'SELECT * FROM sections WHERE seminar_slug = ? ORDER BY seq',
        (slug,)
    ).fetchall()


def fetch_articles(db, slug):
    return db.execute("""
        SELECT a.*, s.title as section_title, s.abbrev as section_abbrev
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
    record_id = doi_to_record_id(doi)
    pdf_url = ''
    if record_id and article['file']:
        pdf_url = f"https://zenodo.org/records/{record_id}/files/{article['file']}"

    keywords = parse_json_field(article['keywords'])
    references = parse_json_field(article['references_'])

    # Build front matter
    lines = ['---']
    lines.append(f'title: "{yaml_escape(article["title"])}"')
    if article['subtitle']:
        lines.append(f'subtitle: "{yaml_escape(article["subtitle"])}"')
    lines.append(f'date: {seminar["date_published"]}')
    lines.append(f'slug: {article_id}')
    lines.append(f'type: artigo')
    if article['section_title']:
        # Strip slug suffix from section title for display
        sec = article['section_title']
        # Remove " — sdnne08" suffix if present
        for suffix_marker in [' — sd', ' - sd']:
            idx = sec.find(suffix_marker)
            if idx > 0:
                sec = sec[:idx]
        lines.append(f'section_title: "{yaml_escape(sec)}"')
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

    lines.append(f'license_url: "https://creativecommons.org/licenses/by-nc-nd/4.0/"')

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
            body_parts.append(f'- {ref}')

    content = '\n'.join(lines) + '\n'
    if body_parts:
        content += '\n' + '\n'.join(body_parts) + '\n'

    filepath = os.path.join(article_dir, 'index.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath


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
    lines.append(f'article_count: {len(articles)}')
    lines.append('---')

    filepath = os.path.join(event_dir, '_index.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return filepath


def write_ambito_index(outdir, ambito_slug, ambito_nome):
    """Write _index.md for an âmbito (region)."""
    ambito_dir = os.path.join(outdir, ambito_slug)
    os.makedirs(ambito_dir, exist_ok=True)
    lines = ['---']
    lines.append(f'title: "Seminários Docomomo {ambito_nome}"')
    lines.append(f'type: ambito')
    lines.append(f'ambito: {ambito_slug}')
    lines.append(f'ambito_nome: "{ambito_nome}"')
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

    # Write article pages
    count = 0
    for art in articles:
        authors = fetch_authors(db, art['id'])
        write_article_page(outdir, art, authors, seminar, ambito_slug, ambito_nome, ficha=ficha)
        count += 1

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
    db.close()


if __name__ == '__main__':
    main()
