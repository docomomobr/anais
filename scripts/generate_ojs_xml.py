#!/usr/bin/env python3
"""
Generate OJS 3.3 Native XML for importing all seminars into OJS.

Reads from:
  - anais.db (SQLite)
  - revisao/fichas_catalograficas.yaml (descriptions)

Two modes:
  - Default (metadata only): 1 XML per seminar, no PDFs. For test import.
  - --with-pdf: 1 XML per article with embedded PDF (base64). For production import.

Usage:
    python3 scripts/generate_ojs_xml.py [--slug SLUG] [--outdir DIR]
    python3 scripts/generate_ojs_xml.py --with-pdf [--slug SLUG] [--outdir DIR]
"""

import argparse
import base64
import html
import os
import re
import sqlite3
import sys
import yaml
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')
FICHAS_PATH = os.path.join(BASE_DIR, 'revisao', 'fichas_catalograficas.yaml')

# Map seminar slug prefix to regional directory
REGION_MAP = {
    'sdnne': 'regionais/nne',
    'sdmg': 'regionais/se',
    'sdrj': 'regionais/se',
    'sdsp': 'regionais/se',
    'sdsul': 'regionais/sul',
    'sdbr': 'nacionais',
}

# Volume name mapping (for OJS display)
VOLUME_NAMES = {
    1: 'Brasil',
    2: 'Sudeste',
    3: 'Norte/Nordeste',
    4: 'Sul',
}


def parse_fichas(path):
    """Parse fichas_catalograficas.yaml into {slug: ficha_text}."""
    with open(path, encoding='utf-8') as f:
        content = f.read()

    fichas = {}
    # Split on newline+slug: to separate entries
    entries = re.split(r'\nslug:', content)
    for entry in entries:
        text = entry if entry.startswith('slug:') else 'slug:' + entry
        text = text.strip()
        if not text:
            continue
        # Parse with yaml
        try:
            data = yaml.safe_load(text)
            if data and 'slug' in data and 'ficha' in data:
                fichas[data['slug']] = data['ficha']
        except yaml.YAMLError:
            # Fallback: manual parse
            lines = text.split('\n')
            slug = lines[0].split(':')[1].strip()
            ficha_lines = []
            for line in lines[1:]:
                if line.startswith('ficha:'):
                    line = line[6:].strip()
                    if line.startswith('>-'):
                        continue
                    ficha_lines.append(line)
                else:
                    ficha_lines.append(line.strip())
            fichas[slug] = ' '.join(ficha_lines).strip()

    return fichas


def linkify_ficha(text):
    """Convert plain URLs and DOIs in ficha text to HTML hyperlinks.

    Handles:
    - DOIs: 10.xxxxx/yyyy → <a href="https://doi.org/...">...</a>
    - URLs without protocol: www.xxx.yyy/... or domain.weebly.com/...
    """
    import re

    # Handle DOIs: "DOI: 10.xxxx/yyyy"
    def doi_replace(m):
        doi = m.group(1).rstrip('.')
        return f'DOI: <a href="https://doi.org/{doi}">{doi}</a>'

    text = re.sub(r'DOI:\s*(10\.\d{4,}/[^\s]+)', doi_replace, text)

    # Handle bare URLs (www.xxx or known domains without www)
    # Skip if already inside <a> tag
    def bare_url_replace(m):
        url = m.group(0).rstrip('.,;')
        return f'<a href="https://{url}">{url}</a>'

    text = re.sub(
        r'(?<!href=")(?<!">)\b(www\.[^\s<>]+|[a-z0-9]+\.(?:weebly|even3)\.com[^\s<>]*)',
        bare_url_replace, text
    )

    return text


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def xml_escape(text):
    """Escape text for XML."""
    if not text:
        return ''
    return html.escape(str(text), quote=True)


def make_section_ref(section_title, slug, section_id):
    """Generate a unique section ref/abbrev from section title, slug, and DB id."""
    title = section_title.strip()

    # Known patterns with number in title
    patterns = [
        (r'Eixo (\w+)', 'E'),
        (r'Mesa (\d+)', 'M'),
        (r'Sessão (\d+)\s+Mesa\s+(\d+)', 'SM'),
        (r'Sessão de comunicação (\d+)', 'SC'),
        (r'Sessão (\d+)', 'S'),
        (r'Painel (\d+)', 'P'),
        (r'Painéis', 'PN'),
        (r'Comunicações Orais', 'CO'),
        (r'Parte (\d+)', 'PT'),
    ]

    for pattern, prefix in patterns:
        m = re.match(pattern, title)
        if m:
            groups = m.groups()
            if groups:
                suffix = '-'.join(groups)
                return f'{prefix}{suffix}-{slug}'
            else:
                # No capture group - use section_id for uniqueness
                return f'{prefix}{section_id}-{slug}'

    # For compound types like "Artigos Completos — Documentação"
    if '—' in title:
        parts = title.split('—')
        type_part = parts[0].strip()
        theme_part = parts[1].strip() if len(parts) > 1 else ''

        type_abbr = {
            'Artigos Completos': 'AC',
            'Resumos Expandidos': 'RE',
            'Artigos': 'A',
        }.get(type_part, type_part[:2].upper())

        # Use section_id to guarantee uniqueness
        return f'{type_abbr}{section_id}-{slug}'

    # Generic: use section_id to guarantee uniqueness
    return f'SEC{section_id}-{slug}'


def find_pdf(slug, filename):
    """Find PDF file on disk given a seminar slug and filename.

    Searches in order:
      1. regionais/{region}/{slug}/pdfs/{filename}
      2. regionais/{region}/{slug}/{filename}  (sdnne10 uses Even3 IDs directly)
    Returns absolute path or None.
    """
    if not filename:
        return None

    for prefix, region_dir in REGION_MAP.items():
        if slug.startswith(prefix):
            base = os.path.join(BASE_DIR, region_dir, slug)
            # Try pdfs/ subdir first
            path = os.path.join(base, 'pdfs', filename)
            if os.path.isfile(path):
                return path
            # Try direct
            path = os.path.join(base, filename)
            if os.path.isfile(path):
                return path
            break

    return None


def generate_issue_xml(conn, slug, fichas, outdir, with_pdf=False):
    """Generate OJS Native XML for one seminar/issue.

    If with_pdf=True, generates 1 XML per article with embedded PDF (base64).
    Otherwise, generates 1 XML per seminar with metadata only.
    """

    # Fetch seminar data
    sem = conn.execute('SELECT * FROM seminars WHERE slug = ?', (slug,)).fetchone()
    if not sem:
        print(f'  ERROR: seminar {slug} not found')
        return None

    # Fetch sections
    sections = conn.execute(
        'SELECT * FROM sections WHERE seminar_slug = ? ORDER BY seq, id',
        (slug,)
    ).fetchall()

    # Fetch articles
    articles = conn.execute(
        'SELECT * FROM articles WHERE seminar_slug = ? ORDER BY section_id, id',
        (slug,)
    ).fetchall()

    if not articles:
        print(f'  SKIP: {slug} has no articles')
        return None

    # Create default section for articles without section
    null_section_arts = [a for a in articles if a['section_id'] is None]
    has_sections = len(sections) > 0

    # Build section map: section_id -> section_ref
    section_map = {}
    default_section_ref = f'ART-{slug}'

    # If we need a default section
    need_default = len(null_section_arts) > 0

    # --- Build XML ---
    NS = 'http://pkp.sfu.ca'
    XSI = 'http://www.w3.org/2001/XMLSchema-instance'

    issue = Element('issue')
    issue.set('xmlns', NS)
    issue.set('xmlns:xsi', XSI)
    issue.set('published', '1')
    issue.set('current', '0')
    issue.set('access_status', '1')
    issue.set('url_path', slug)
    issue.set('xsi:schemaLocation', f'{NS} native.xsd')

    # Issue identification
    SubElement(issue, 'id', type='internal', advice='ignore').text = slug

    # Description from fichas (with hyperlinked URLs and DOIs)
    ficha = fichas.get(slug, '')
    if ficha:
        desc_el = SubElement(issue, 'description', locale='pt_BR')
        desc_el.text = linkify_ficha(ficha)

    issue_ident = SubElement(issue, 'issue_identification')
    SubElement(issue_ident, 'volume').text = str(sem['volume'])
    SubElement(issue_ident, 'number').text = str(sem['number'])
    SubElement(issue_ident, 'year').text = str(sem['year'])
    SubElement(issue_ident, 'title', locale='pt_BR').text = sem['title']

    date_pub = sem['date_published'] or f"{sem['year']}-01-01"
    SubElement(issue, 'date_published').text = date_pub
    SubElement(issue, 'last_modified').text = date_pub

    # Sections
    sections_el = SubElement(issue, 'sections')

    if need_default:
        sec_el = SubElement(sections_el, 'section',
                           ref=default_section_ref, seq='0',
                           editor_restricted='0', meta_indexed='1',
                           meta_reviewed='1', abstracts_not_required='1',
                           hide_title='0', hide_author='0',
                           abstract_word_count='0')
        SubElement(sec_el, 'id', type='internal', advice='ignore').text = '0'
        SubElement(sec_el, 'abbrev', locale='pt_BR').text = default_section_ref
        # Título único para evitar colisão de seções journal-wide (pkp-lib #9755)
        SubElement(sec_el, 'title', locale='pt_BR').text = f'Artigos — {slug}'

    for idx, sec in enumerate(sections):
        sec_ref = sec['abbrev'] or make_section_ref(sec['title'], slug, sec['id'])
        section_map[sec['id']] = sec_ref

        ht = '1' if sec['hide_title'] else '0'
        sec_el = SubElement(sections_el, 'section',
                           ref=sec_ref, seq=str(idx + 1 if need_default else idx),
                           editor_restricted='0', meta_indexed='1',
                           meta_reviewed='1', abstracts_not_required='1',
                           hide_title=ht, hide_author='0',
                           abstract_word_count='0')
        SubElement(sec_el, 'id', type='internal', advice='ignore').text = str(sec['id'])
        SubElement(sec_el, 'abbrev', locale='pt_BR').text = sec_ref
        # Título único para evitar colisão de seções journal-wide (pkp-lib #9755).
        # OJS _sectionExist() busca por título; títulos iguais entre issues causam
        # crash fatal quando as abbreviations são diferentes.
        sec_title = sec['title']
        if not sec_title.endswith(slug):
            sec_title = f'{sec_title} — {slug}'
        SubElement(sec_el, 'title', locale='pt_BR').text = sec_title

    # Articles
    articles_el = SubElement(issue, 'articles')

    # When with_pdf, we build per-article XMLs later; collect article elements
    pdf_missing = []

    for art_idx, art in enumerate(articles):
        # Determine section ref
        if art['section_id'] and art['section_id'] in section_map:
            sec_ref = section_map[art['section_id']]
        else:
            sec_ref = default_section_ref

        art_el = SubElement(articles_el, 'article')
        art_el.set('xmlns:xsi', XSI)
        art_el.set('locale', 'pt_BR')
        art_el.set('date_submitted', date_pub)
        art_el.set('status', '3')
        art_el.set('submission_progress', '0')
        art_el.set('current_publication_id', str(art_idx + 1))
        art_el.set('stage', 'production')

        SubElement(art_el, 'id', type='internal', advice='ignore').text = art['id']

        # submission_file (before publication, only with PDF)
        pdf_path = None
        if with_pdf and art['file']:
            pdf_path = find_pdf(slug, art['file'])
            if pdf_path:
                pdf_size = os.path.getsize(pdf_path)
                sf_el = SubElement(art_el, 'submission_file',
                                  id=str(art_idx + 1),
                                  created_at=date_pub,
                                  date_created='',
                                  file_id=str(art_idx + 1),
                                  stage='proof',
                                  updated_at=date_pub,
                                  viewable='false',
                                  genre='Texto do artigo')
                sf_el.set('xsi:schemaLocation', f'{NS} native.xsd')
                SubElement(sf_el, 'name', locale='pt_BR').text = art['file']
                file_el = SubElement(sf_el, 'file',
                                    id=str(art_idx + 1),
                                    filesize=str(pdf_size),
                                    extension='pdf')
                with open(pdf_path, 'rb') as pf:
                    embed_el = SubElement(file_el, 'embed', encoding='base64')
                    embed_el.text = base64.b64encode(pf.read()).decode('ascii')
            else:
                pdf_missing.append(art['id'])

        # Publication
        pub_el = SubElement(art_el, 'publication')
        pub_el.set('xmlns:xsi', XSI)
        pub_el.set('locale', 'pt_BR')
        pub_el.set('version', '1')
        pub_el.set('status', '3')
        pub_el.set('url_path', '')
        pub_el.set('seq', str(art_idx))
        pub_el.set('date_published', date_pub)
        pub_el.set('section_ref', sec_ref)
        pub_el.set('access_status', '0')
        pub_el.set('xsi:schemaLocation', f'{NS} native.xsd')

        SubElement(pub_el, 'id', type='internal', advice='ignore').text = str(art_idx + 1)
        SubElement(pub_el, 'title', locale='pt_BR').text = art['title']

        if art['subtitle']:
            SubElement(pub_el, 'subtitle', locale='pt_BR').text = art['subtitle']

        if art['abstract']:
            SubElement(pub_el, 'abstract', locale='pt_BR').text = art['abstract']

        if art['abstract_en']:
            SubElement(pub_el, 'abstract', locale='en_US').text = art['abstract_en']

        # Keywords (only add element if there are actual keywords)
        if art['keywords']:
            kws = parse_keywords(art['keywords'])
            if kws:
                kw_el = SubElement(pub_el, 'keywords', locale='pt_BR')
                for kw in kws:
                    SubElement(kw_el, 'keyword').text = kw

        if art['keywords_en']:
            kws_en = parse_keywords(art['keywords_en'])
            if kws_en:
                kw_en_el = SubElement(pub_el, 'keywords', locale='en_US')
                for kw in kws_en:
                    SubElement(kw_en_el, 'keyword').text = kw

        # Authors
        art_authors = conn.execute('''
            SELECT au.givenname, au.familyname, au.email, au.orcid,
                   aa.affiliation, aa.bio, aa.country, aa.primary_contact, aa.seq
            FROM article_author aa
            JOIN authors au ON au.id = aa.author_id
            WHERE aa.article_id = ?
            ORDER BY aa.seq
        ''', (art['id'],)).fetchall()

        if art_authors:
            authors_el = SubElement(pub_el, 'authors')
            for aut_idx, aut in enumerate(art_authors):
                aut_el = SubElement(authors_el, 'author',
                                  include_in_browse='true',
                                  user_group_ref='Autor',
                                  seq=str(aut['seq']),
                                  id=str(aut_idx + 1))

                SubElement(aut_el, 'givenname', locale='pt_BR').text = aut['givenname']
                SubElement(aut_el, 'familyname', locale='pt_BR').text = aut['familyname']

                if aut['affiliation']:
                    SubElement(aut_el, 'affiliation', locale='pt_BR').text = aut['affiliation']

                country = aut['country'] or 'BR'
                SubElement(aut_el, 'country').text = country

                email = aut['email'] or f"autor{aut_idx+1}@example.com"
                SubElement(aut_el, 'email').text = email

                if aut['orcid']:
                    orcid_url = aut['orcid']
                    if not orcid_url.startswith('http'):
                        orcid_url = f'https://orcid.org/{orcid_url}'
                    SubElement(aut_el, 'orcid').text = orcid_url

                if aut['bio']:
                    SubElement(aut_el, 'biography', locale='pt_BR').text = aut['bio']

        # OJS 3.3 XSD order within <publication>:
        #   pkppublication base: id, title, prefix, subtitle, abstract,
        #     coverage, type, source, rights, licenseUrl, copyrightHolder,
        #     copyrightYear, keywords, agencies, languages, disciplines,
        #     subjects, authors, representation (=article_galley), citations
        #   OJS extension: issue_identification, pages, covers, issueId
        #
        # article_galley (representation) comes AFTER authors, BEFORE pages.
        # pages is in the OJS extension, after representation/citations.

        # article_galley (only with PDF)
        if pdf_path:
            galley_el = SubElement(pub_el, 'article_galley')
            galley_el.set('xmlns:xsi', XSI)
            galley_el.set('locale', 'pt_BR')
            galley_el.set('url_path', '')
            galley_el.set('approved', 'false')
            galley_el.set('xsi:schemaLocation', f'{NS} native.xsd')
            SubElement(galley_el, 'id', type='internal', advice='ignore').text = str(art_idx + 1)
            SubElement(galley_el, 'name', locale='pt_BR').text = 'PDF'
            SubElement(galley_el, 'seq').text = '0'
            SubElement(galley_el, 'submission_file_ref', id=str(art_idx + 1))

        # Citations (references) — after article_galley, before pages (XSD order)
        # OJS 3.3 native.xsd: <citations> contains <citation> child elements
        if art['references_']:
            refs_list = parse_keywords(art['references_'])  # JSON array → list
            if refs_list:
                citations_el = SubElement(pub_el, 'citations')
                for ref_text in refs_list:
                    SubElement(citations_el, 'citation').text = ref_text

        # Pages (OJS extension — must come AFTER citations)
        if art['pages']:
            SubElement(pub_el, 'pages').text = art['pages']

    if pdf_missing:
        print(f'  WARNING: {len(pdf_missing)} articles missing PDF: {pdf_missing[:5]}...')

    # --- Output ---
    if with_pdf:
        # 1 XML per article (PDFs make files too large for batch)
        outfiles = write_per_article_xmls(issue, articles_el, slug, outdir, NS)
        print(f'  {slug}: {len(articles)} articles → {len(outfiles)} XMLs in {outdir}/')
        return outfiles
    else:
        # 1 XML per seminar (metadata only)
        outfile = write_single_xml(issue, slug, outdir)
        print(f'  {slug}: {len(articles)} articles, {len(sections)} sections → {outfile}')
        return outfile


def write_single_xml(issue, slug, outdir):
    """Write the complete issue as a single XML file."""
    xml_str = tostring(issue, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty = dom.toprettyxml(indent='  ', encoding='UTF-8').decode('utf-8')
    pretty = pretty.replace("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n", '', 1)
    final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty.lstrip()

    outfile = os.path.join(outdir, f'{slug}.xml')
    with open(outfile, 'w', encoding='utf-8') as f:
        f.write(final_xml)
    return outfile


def write_per_article_xmls(issue_el, articles_el, slug, outdir, NS):
    """Write 1 XML per article, each containing the full issue structure.

    Each XML has the same issue/sections but only 1 article.
    This keeps file size manageable with embedded PDFs.
    """
    all_articles = list(articles_el)
    outfiles = []

    for i, art_el in enumerate(all_articles):
        # Clone issue without articles
        single_issue = Element(issue_el.tag, issue_el.attrib)
        for child in issue_el:
            if child.tag == f'{{{NS}}}articles' or child.tag == 'articles':
                # Replace with single-article container
                single_arts = SubElement(single_issue, 'articles')
                single_arts.append(art_el)
            else:
                single_issue.append(child)

        # Get article id for filename
        art_id_el = art_el.find(f'{{{NS}}}id') or art_el.find('id')
        art_id = art_id_el.text if art_id_el is not None else f'{i+1:03d}'

        xml_str = tostring(single_issue, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty = dom.toprettyxml(indent='  ', encoding='UTF-8').decode('utf-8')
        pretty = pretty.replace("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n", '', 1)
        final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty.lstrip()

        outfile = os.path.join(outdir, f'{art_id}.xml')
        with open(outfile, 'w', encoding='utf-8') as f:
            f.write(final_xml)
        outfiles.append(outfile)

    return outfiles


def parse_keywords(kw_str):
    """Parse keywords from DB string (YAML list or newline-separated)."""
    if not kw_str:
        return []
    kw_str = kw_str.strip()

    # Try YAML list first
    if kw_str.startswith('[') or kw_str.startswith('-'):
        try:
            parsed = yaml.safe_load(kw_str)
            if isinstance(parsed, list):
                return [str(k).strip() for k in parsed if k]
        except yaml.YAMLError:
            pass

    # Newline-separated
    if '\n' in kw_str:
        return [k.strip().lstrip('- ') for k in kw_str.split('\n') if k.strip()]

    # Semicolon-separated
    if ';' in kw_str:
        return [k.strip() for k in kw_str.split(';') if k.strip()]

    # Comma-separated (but careful with commas inside keywords)
    # Only split on comma if result has 2+ items
    parts = [k.strip() for k in kw_str.split(',') if k.strip()]
    if len(parts) > 1:
        return parts

    return [kw_str] if kw_str else []


def main():
    parser = argparse.ArgumentParser(description='Generate OJS Native XML for import')
    parser.add_argument('--slug', help='Generate only for this seminar slug')
    parser.add_argument('--outdir', default=None,
                       help='Output directory (default: xml_test/ or xml_prod/)')
    parser.add_argument('--with-pdf', action='store_true',
                       help='Embed PDFs in base64 (1 XML per article, for production)')
    args = parser.parse_args()

    # Default output dir
    if args.outdir is None:
        args.outdir = os.path.join(BASE_DIR, 'xml_prod' if args.with_pdf else 'xml_test')

    # Create output dir
    os.makedirs(args.outdir, exist_ok=True)

    # Load fichas
    fichas = parse_fichas(FICHAS_PATH)
    print(f'Loaded {len(fichas)} fichas catalográficas')

    # Connect to DB
    conn = get_db()

    if args.slug:
        slugs = [args.slug]
    else:
        # Only regionals (never import nationals — they're already published)
        rows = conn.execute(
            "SELECT slug FROM seminars WHERE slug NOT LIKE 'sdbr%' ORDER BY volume, number"
        ).fetchall()
        slugs = [r['slug'] for r in rows]

    mode = 'with PDF (1 per article)' if args.with_pdf else 'metadata only (1 per seminar)'
    print(f'Generating XML for {len(slugs)} seminars ({mode})...\n')

    total_files = 0
    for slug in slugs:
        result = generate_issue_xml(conn, slug, fichas, args.outdir, with_pdf=args.with_pdf)
        if result:
            if isinstance(result, list):
                total_files += len(result)
            else:
                total_files += 1

    print(f'\nDone: {total_files} XML files in {args.outdir}/')

    conn.close()


if __name__ == '__main__':
    main()
