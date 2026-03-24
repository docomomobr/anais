#!/usr/bin/env python3
"""Generate a single-page HTML review for a seminar.

Produces a self-contained HTML file that mirrors the Hugo site layout:
cover + metadata header, ficha catalográfica, TOC grouped by section,
and full article details grouped by section.
"""
import argparse
import base64
import re
import sqlite3
import json
import html
import os
import sys

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(SCRIPT_DIR, '..')
DB = os.path.join(REPO_ROOT, 'anais.db')
FICHAS_PATH = os.path.join(REPO_ROOT, 'revisao', 'fichas_catalograficas.yaml')

VALIDATION_PATH_TPL = os.path.join(REPO_ROOT, 'revisao', '{slug}-validation.json')

COVER_DIRS = {
    'sdbr': 'nacionais/capas',
    'sdmg': 'regionais/se/capas',
    'sdnne': 'regionais/nne/capas',
    'sdrj': 'regionais/se/capas',
    'sdsp': 'regionais/se/capas',
    'sdsul': 'regionais/sul/capas',
    'sdpr': 'regionais/sul/capas',
}

def _parse_args():
    parser = argparse.ArgumentParser(description='Gerar HTML de revisão por seminário')
    parser.add_argument('slug', help='Slug do seminário (ex: sdrj02)')
    parser.add_argument('--articles', help='Filtrar artigos específicos (ex: sdrj02-001,sdrj02-005)')
    return parser.parse_args()


# Module-level globals set by main() — avoids argparse crash on import
slug = None
FILTER_IDS = None
OUT_SUFFIX = ''
REVISAO_DIR = os.path.join(REPO_ROOT, 'revisao')
OUT = None


# ── helpers ──────────────────────────────────────────────────────────

def e(text):
    return html.escape(str(text)) if text else ''


_URL_RE = re.compile(r'(https?://[^\s<>&]+)')


def linkify(text):
    """HTML-escape text then convert URLs into clickable links."""
    escaped = e(text)
    return _URL_RE.sub(r'<a href="\1">\1</a>', escaped)


def fmt_keywords(kw_json):
    if not kw_json:
        return ''
    try:
        kws = json.loads(kw_json)
        return '; '.join(kws)
    except (json.JSONDecodeError, TypeError):
        return str(kw_json)


def fmt_refs(refs_json):
    if not refs_json:
        return ''
    try:
        refs = json.loads(refs_json)
    except (json.JSONDecodeError, TypeError):
        return ''
    return '\n'.join(f'<li>{e(r)}</li>' for r in refs)


def find_cover(slug):
    for prefix, cover_dir in COVER_DIRS.items():
        if slug.startswith(prefix):
            png = os.path.join(REPO_ROOT, cover_dir, f'{slug}.png')
            if os.path.isfile(png):
                return png
    return None


def cover_base64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')


def load_fichas():
    if not os.path.isfile(FICHAS_PATH):
        return {}
    result = {}
    with open(FICHAS_PATH, 'r', encoding='utf-8') as f:
        text = f.read()
    docs_text = text.replace('\nslug:', '\n---\nslug:')
    for doc in yaml.safe_load_all(docs_text):
        if doc and isinstance(doc, dict) and 'slug' in doc:
            result[doc['slug']] = doc.get('ficha', '')
    return result


def parse_editors(editors_json):
    if not editors_json:
        return []
    try:
        eds = json.loads(editors_json)
        if isinstance(eds, list):
            return eds
    except (json.JSONDecodeError, TypeError):
        pass
    return [s.strip() for s in str(editors_json).split(',') if s.strip()]


def load_validation(slug):
    """Load validation report and return dict of article_id → list of issues."""
    path = VALIDATION_PATH_TPL.format(slug=slug)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}
    by_article = {}
    for issue in report.get('issues', []):
        aid = issue.get('article_id', '')
        by_article.setdefault(aid, []).append(issue)
    return by_article


# Descrições curtas dos checks de validação
VALIDATION_CHECK_DESC = {
    'A01': 'abs_en sem kw_en', 'A02': 'kw_en sem abs_en',
    'A03': 'abs_es sem kw_es', 'A04': 'kw_es sem abs_es',
    'A05': 'locale_es→abs_es', 'A06': 'locale_es→kw_es',
    'A07': 'fontes: Abstract', 'A08': 'fontes: Keywords',
    'A09': 'fontes: Resumen', 'A10': 'backfill pendente',
    'A11': 'ref longa', 'A12': 'não-ref em refs',
    'A13': 'URL órfã', 'A14': 'abstract contaminado',
    'A15': 'locale mismatch', 'A16': 'control chars',
    'A17': 'refs duplicadas', 'A18': 'sem autores',
    'A19': 'abstract truncado?',
    'A20': 'abstract overflow',
}


def strip_section_suffix(sec_title):
    """Remove slug suffix like ' — sdnne08' from section title."""
    if not sec_title:
        return sec_title
    for marker in [' — sd', ' - sd']:
        idx = sec_title.find(marker)
        if idx > 0:
            return sec_title[:idx]
    return sec_title


# ── main ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    args = _parse_args()
    slug = args.slug
    FILTER_IDS = None
    OUT_SUFFIX = ''
    if args.articles:
        FILTER_IDS = set(args.articles.split(','))
        OUT_SUFFIX = '-novos'
    OUT = os.path.join(REVISAO_DIR, f'revisao-{slug}{OUT_SUFFIX}.html')

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    sem = conn.execute('SELECT * FROM seminars WHERE slug=?', (slug,)).fetchone()
    if not sem:
        conn.close()
        print(f'Seminário "{slug}" não encontrado.')
        sys.exit(1)

    try:
        sections = conn.execute(
            'SELECT * FROM sections WHERE seminar_slug=? ORDER BY seq, id', (slug,)
        ).fetchall()

        articles = conn.execute('''
            SELECT a.*, s.title as section_title, s.seq as section_seq
            FROM articles a
            LEFT JOIN sections s ON a.section_id = s.id
            WHERE a.seminar_slug=?
            ORDER BY s.seq, s.id, a.id
        ''', (slug,)).fetchall()

        # Filter articles if --articles was given
        if FILTER_IDS:
            articles = [a for a in articles if a['id'] in FILTER_IDS]

        # Group articles by section
        section_map = {}  # section_title -> list of articles
        for art in articles:
            sec = strip_section_suffix(art['section_title']) or 'Sem seção'
            section_map.setdefault(sec, []).append(art)

        # Cover + ficha + validation
        cover_path = find_cover(slug)
        fichas = load_fichas()
        ficha = fichas.get(slug, '')
        editors = parse_editors(sem['editors'])
        n_articles = len(articles)
        n_sections = len(section_map)
        validation_issues = load_validation(slug)
        n_issues = sum(len(v) for v in validation_issues.values())
        n_articles_with_issues = len(validation_issues)


        # ── HTML generation ──────────────────────────────────────────────────

        lines = []

        # --- <head> ---
        lines.append(f'''<!DOCTYPE html>
        <html lang="pt-BR">
        <head>
        <meta charset="utf-8">
        <title>Revisão — {e(sem["title"])}</title>
        <style>
        :root {{
          --color-text: #222;
          --color-muted: #777;
          --color-label: #555;
          --color-missing: #c44;
          --color-orcid: #a6ce39;
          --color-pdf-yes: #2a7;
          --color-pdf-no: #bbb;
          --color-section-bg: #e8edf5;
          --color-section-text: #335;
          --color-abstract-bg: #f8f8f5;
          --color-abstract-border: #ccc;
          --color-author-bg: #eee;
          --color-toc-bg: #f5f5f5;
        }}
        body {{
          font-family: Georgia, serif;
          max-width: 900px; margin: 2em auto; padding: 0 1em;
          color: var(--color-text); line-height: 1.6;
        }}
        a {{ color: #336; }}

        /* ── Header ── */
        .event-header {{
          display: flex; gap: 1.5em; align-items: flex-start;
          margin-bottom: 1.5em; padding-bottom: 1.5em;
          border-bottom: 2px solid #333;
        }}
        .event-cover {{
          width: 220px; min-width: 220px;
          border: 1px solid #ccc; border-radius: 3px;
        }}
        .cover-placeholder {{
          width: 220px; min-width: 220px; height: 300px;
          background: #eee; border: 1px dashed #bbb; border-radius: 3px;
          display: flex; align-items: center; justify-content: center;
          color: #999; font-size: 0.9em;
        }}
        .event-header-info h1 {{
          font-size: 1.4em; margin: 0 0 0.3em 0; border: none; padding: 0;
        }}
        .event-header-info .subtitle {{
          font-size: 1.05em; color: #555; margin: 0 0 0.6em 0; font-style: italic;
        }}
        .event-header-info .meta-line {{
          font-size: 0.9em; color: var(--color-muted); margin: 0.15em 0;
        }}
        .event-header-info .stats {{
          font-size: 0.9em; margin-top: 0.6em; font-weight: bold;
        }}
        .volume-pdf-badge {{
          display: inline-block; margin-top: 0.5em;
          padding: 3px 10px; border-radius: 3px;
          background: #e0e8f0; color: #335; font-size: 0.85em;
        }}

        /* ── Ficha ── */
        .ficha {{
          background: #fafaf8; border: 1px solid #ddd; border-radius: 4px;
          padding: 0.8em 1em; margin-bottom: 2em; font-size: 0.88em;
          color: #444; line-height: 1.6;
        }}
        .ficha-title {{
          font-weight: bold; text-transform: uppercase; font-size: 0.8em;
          letter-spacing: 0.05em; color: var(--color-label); margin-bottom: 0.3em;
        }}

        /* ── TOC ── */
        .toc {{
          background: var(--color-toc-bg); padding: 1em 1.2em;
          border-radius: 5px; margin-bottom: 2em;
        }}
        .toc-title {{ font-weight: bold; margin-bottom: 0.5em; }}
        .toc-section {{ font-weight: bold; margin-top: 0.6em; color: var(--color-section-text); }}
        .toc ol {{ padding-left: 1.5em; margin: 0.2em 0; }}
        .toc li {{ margin: 0.15em 0; font-size: 0.9em; }}
        .toc a {{ text-decoration: none; color: #336; }}
        .toc a:hover {{ text-decoration: underline; }}
        .toc .id {{ font-family: monospace; font-size: 0.85em; color: #888; }}
        .toc .pdf-dot {{ font-size: 0.75em; }}
        .toc .pdf-yes {{ color: var(--color-pdf-yes); }}
        .toc .pdf-no {{ color: var(--color-pdf-no); }}
        .toc .toc-authors {{ color: var(--color-muted); font-size: 0.88em; }}

        /* ── Section headings ── */
        .section-heading {{
          background: var(--color-section-bg); color: var(--color-section-text);
          padding: 0.5em 0.8em; border-radius: 4px;
          font-size: 1.15em; margin-top: 2.5em; margin-bottom: 0.5em;
        }}

        /* ── Article ── */
        .article-divider {{
          display: flex; align-items: center; gap: 0.5em;
          margin-top: 2.5em; border-top: 1px solid #bbb; padding-top: 0.8em;
        }}
        .article-divider .id {{
          font-family: monospace; font-size: 0.9em; color: #888;
          white-space: nowrap;
        }}
        .article-divider .pdf-badge {{
          margin-left: auto; font-size: 0.8em; padding: 2px 8px;
          border-radius: 3px; white-space: nowrap;
        }}
        .pdf-badge.yes {{ background: #dff5ea; color: #1a6; }}
        .pdf-badge.no {{ background: #f0f0f0; color: #999; }}
        .article-title {{
          font-size: 1.15em; font-weight: bold; margin: 0.3em 0 0.1em 0;
        }}
        .article-subtitle {{
          font-size: 0.95em; color: #555; font-style: italic; margin: 0 0 0.3em 0;
        }}
        .article-title-en {{
          font-size: 0.9em; color: #666; margin: 0.2em 0 0;
        }}
        .article-subtitle-en {{
          font-size: 0.85em; color: #888; font-style: italic; margin: 0 0 0.2em 0;
        }}

        /* ── Fields ── */
        .field {{ margin: 0.3em 0; }}
        .label {{
          font-weight: bold; color: var(--color-label);
          font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.05em;
        }}
        .meta-bar {{
          font-size: 0.85em; color: var(--color-muted); margin: 0.3em 0;
        }}
        .meta-bar .section-tag {{
          background: #dde; padding: 2px 6px; border-radius: 3px;
          font-size: 0.9em; color: #446;
        }}
        .meta-bar .file {{ font-family: monospace; color: #668; }}
        .locale-tag {{
          background: #fde; padding: 1px 5px; border-radius: 3px;
          font-size: 0.8em; color: #844;
        }}

        .authors {{ margin: 0.4em 0; }}
        .author {{
          display: inline-block; background: var(--color-author-bg);
          padding: 2px 8px; border-radius: 3px; margin: 2px; font-size: 0.9em;
        }}
        .author .affil {{ color: #777; font-size: 0.85em; }}
        .author .orcid {{ color: var(--color-orcid); font-size: 0.8em; }}

        .abstract {{
          background: var(--color-abstract-bg); padding: 0.8em 1em;
          border-left: 3px solid var(--color-abstract-border);
          margin: 0.5em 0; font-size: 0.95em;
        }}
        .abstract-en {{
          border-left-color: #b0c4de;
        }}
        .keywords {{ font-style: italic; color: #555; }}

        .refs {{ font-size: 0.85em; color: #444; }}
        .refs ol {{ padding-left: 1.5em; }}
        .refs li {{ margin-bottom: 0.3em; }}

        .missing {{ color: var(--color-missing); font-style: italic; }}

        /* ── Validation warnings ── */
        .validation-summary {{
          background: #fff8e1; border: 1px solid #ffc107; border-radius: 4px;
          padding: 0.8em 1em; margin-bottom: 1.5em; font-size: 0.88em;
        }}
        .validation-summary-title {{
          font-weight: bold; color: #856404; margin-bottom: 0.3em;
        }}
        .validation-badges {{
          display: flex; flex-wrap: wrap; gap: 3px; margin-top: 0.3em;
        }}
        .validation-badge {{
          display: inline-block; padding: 1px 6px; border-radius: 3px;
          font-size: 0.8em; font-family: monospace;
        }}
        .validation-badge.warning {{ background: #fff3cd; color: #856404; }}
        .validation-badge.error {{ background: #f8d7da; color: #721c24; }}
        .validation-badge.info {{ background: #d1ecf1; color: #0c5460; }}
        .article-warnings {{
          margin: 0.3em 0; font-size: 0.82em;
        }}

        @media print {{
          .toc {{ page-break-after: always; }}
          .article-divider {{ page-break-before: always; border-top: none; }}
        }}
        </style>
        </head>
        <body>
        ''')

        # --- Header (flex: cover + info) ---
        lines.append('<div class="event-header">')

        if cover_path:
            b64 = cover_base64(cover_path)
            lines.append(f'  <img class="event-cover" src="data:image/png;base64,{b64}" alt="Capa">')
        else:
            lines.append('  <div class="cover-placeholder">sem capa</div>')

        lines.append('  <div class="event-header-info">')
        lines.append(f'    <h1>{e(sem["title"])}</h1>')
        if sem['subtitle']:
            lines.append(f'    <p class="subtitle">{e(sem["subtitle"])}</p>')

        # Location — Publisher · ISBN
        loc_parts = []
        if sem['location']:
            loc_parts.append(e(sem['location']))
        if sem['publisher']:
            loc_parts.append(e(sem['publisher']))
        loc_line = ' — '.join(loc_parts)
        if sem['isbn']:
            loc_line += f' · ISBN {e(sem["isbn"])}'
        elif loc_parts:
            loc_line += ' · <span class="missing">sem ISBN</span>'
        if loc_line:
            lines.append(f'    <p class="meta-line">{loc_line}</p>')

        # Editors
        if editors:
            lines.append(f'    <p class="meta-line">Org.: {e(", ".join(editors))}</p>')

        # Stats
        lines.append(f'    <p class="stats">{n_articles} artigos · {n_sections} {"seção" if n_sections == 1 else "seções"}</p>')

        # Volume PDF
        if sem['volume_pdf']:
            lines.append(f'    <span class="volume-pdf-badge">PDF da edição: {e(sem["volume_pdf"])}</span>')

        lines.append('  </div>')
        lines.append('</div>')

        # --- Ficha catalográfica ---
        # Preferir description do banco; fallback para YAML
        ficha_text = sem['description'] or ficha or ''
        if ficha_text:
            lines.append('<div class="ficha">')
            lines.append('  <div class="ficha-title">Ficha catalográfica</div>')
            lines.append(f'  {linkify(ficha_text)}')
            lines.append('</div>')

        # --- Validation summary ---
        if validation_issues:
            lines.append('<div class="validation-summary">')
            lines.append(f'  <div class="validation-summary-title">Validação: {n_issues} issues em {n_articles_with_issues} artigos</div>')
            # Count by check
            check_counts = {}
            for issues_list in validation_issues.values():
                for issue in issues_list:
                    c = issue.get('check', '?')
                    check_counts[c] = check_counts.get(c, 0) + 1
            lines.append('  <div class="validation-badges">')
            for c in sorted(check_counts.keys()):
                desc = VALIDATION_CHECK_DESC.get(c, c)
                lines.append(f'    <span class="validation-badge warning">{c} {desc}: {check_counts[c]}</span>')
            lines.append('  </div>')
            lines.append('</div>')

        # --- TOC (grouped by section) ---
        lines.append('<div class="toc">')
        lines.append('  <div class="toc-title">Sumário</div>')
        for sec_title, sec_articles in section_map.items():
            lines.append(f'  <div class="toc-section">{e(sec_title)} ({len(sec_articles)})</div>')
            lines.append('  <ol>')
            for art in sec_articles:
                title = art['title']
                if art['subtitle']:
                    title += f': {art["subtitle"]}'
                # Compact authors
                authors = conn.execute('''
                    SELECT au.givenname, au.familyname
                    FROM article_author aa JOIN authors au ON aa.author_id = au.id
                    WHERE aa.article_id = ? ORDER BY aa.seq
                ''', (art['id'],)).fetchall()
                authors_str = '; '.join(f'{a["givenname"]} {a["familyname"]}' for a in authors)
                # PDF indicator
                pdf_cls = 'pdf-yes' if art['file'] else 'pdf-no'
                pdf_icon = '&#x25CF;' if art['file'] else '&#x25CB;'
                lines.append(
                    f'  <li>'
                    f'<a href="#{art["id"]}">'
                    f'<span class="id">{art["id"]}</span> '
                    f'{e(title)}</a> '
                    f'<span class="toc-authors">{e(authors_str)}</span> '
                    f'<span class="pdf-dot {pdf_cls}">{pdf_icon}</span>'
                    f'</li>'
                )
            lines.append('  </ol>')
        lines.append('</div>')

        # --- Articles (grouped by section) ---
        for sec_title, sec_articles in section_map.items():
            lines.append(f'<h2 class="section-heading">{e(sec_title)} ({len(sec_articles)})</h2>')

            for art in sec_articles:
                # Divider with ID and PDF badge
                if art['file']:
                    pdf_badge = f'<span class="pdf-badge yes">PDF {e(art["file"])}</span>'
                else:
                    pdf_badge = '<span class="pdf-badge no">sem PDF</span>'

                lines.append(f'<div class="article-divider" id="{art["id"]}">')
                lines.append(f'  <span class="id">{art["id"]}</span>')
                lines.append(f'  {pdf_badge}')
                lines.append('</div>')

                # Title
                lines.append(f'<div class="article-title">{e(art["title"])}</div>')
                if art['subtitle']:
                    lines.append(f'<div class="article-subtitle">{e(art["subtitle"])}</div>')

                # Title EN / Subtitle EN
                if art['title_en']:
                    lines.append(f'<div class="article-title-en">[EN] {e(art["title_en"])}</div>')
                    if art['subtitle_en']:
                        lines.append(f'<div class="article-subtitle-en">{e(art["subtitle_en"])}</div>')

                # Title ES / Subtitle ES
                if art['title_es']:
                    lines.append(f'<div class="article-title-en">[ES] {e(art["title_es"])}</div>')
                    if art['subtitle_es']:
                        lines.append(f'<div class="article-subtitle-en">{e(art["subtitle_es"])}</div>')

                # Authors
                authors = conn.execute('''
                    SELECT au.givenname, au.familyname, aa.affiliation, au.orcid
                    FROM article_author aa
                    JOIN authors au ON aa.author_id = au.id
                    WHERE aa.article_id = ?
                    ORDER BY aa.seq
                ''', (art['id'],)).fetchall()

                lines.append('<div class="authors">')
                for au in authors:
                    name = f'{au["givenname"]} {au["familyname"]}'
                    parts = [e(name)]
                    if au['affiliation']:
                        parts.append(f'<span class="affil">({e(au["affiliation"])})</span>')
                    if au['orcid']:
                        parts.append(f'<span class="orcid">&#x2B21; {au["orcid"]}</span>')
                    lines.append(f'  <span class="author">{" ".join(parts)}</span>')
                lines.append('</div>')

                # Meta bar: section · file · pages · locale
                meta_parts = []
                sec_display = strip_section_suffix(art['section_title'])
                if sec_display:
                    meta_parts.append(f'<span class="section-tag">{e(sec_display)}</span>')
                if art['file']:
                    meta_parts.append(f'<span class="file">{e(art["file"])}</span>')
                if art['pages_count']:
                    meta_parts.append(f'{art["pages_count"]} p.')
                if art['locale'] and art['locale'] != 'pt-BR':
                    meta_parts.append(f'<span class="locale-tag">{e(art["locale"])}</span>')
                if meta_parts:
                    lines.append(f'<div class="meta-bar">{" · ".join(meta_parts)}</div>')

                # Validation warnings for this article
                art_issues = validation_issues.get(art['id'], [])
                if art_issues:
                    lines.append('<div class="article-warnings">')
                    for issue in art_issues:
                        sev = issue.get('severity', 'warning')
                        check = issue.get('check', '?')
                        detail = issue.get('detail', '')
                        lines.append(f'  <span class="validation-badge {sev}">{check}</span> <small>{e(detail)}</small><br>')
                    lines.append('</div>')

                # Abstracts e keywords — labels fixos, mostra o que existe
                # abstract=PT (Resumo), abstract_en=EN (Abstract), abstract_es=ES (Resumen)

                # Resumo (PT)
                if art['abstract']:
                    lines.append('<div class="field"><span class="label">Resumo</span></div>')
                    lines.append(f'<div class="abstract">{e(art["abstract"])}</div>')

                # Palavras-chave (PT)
                kw = fmt_keywords(art['keywords'])
                if kw:
                    lines.append(f'<div class="field"><span class="label">Palavras-chave</span> <span class="keywords">{e(kw)}</span></div>')

                # Abstract (EN)
                if art['abstract_en']:
                    lines.append('<div class="field"><span class="label">Abstract</span></div>')
                    lines.append(f'<div class="abstract abstract-en">{e(art["abstract_en"])}</div>')

                # Keywords (EN)
                kw_en = fmt_keywords(art['keywords_en'])
                if kw_en:
                    lines.append(f'<div class="field"><span class="label">Keywords</span> <span class="keywords">{e(kw_en)}</span></div>')

                # Resumen (ES)
                if art['abstract_es']:
                    lines.append('<div class="field"><span class="label">Resumen</span></div>')
                    lines.append(f'<div class="abstract abstract-es">{e(art["abstract_es"])}</div>')

                # Palabras clave (ES)
                kw_es = fmt_keywords(art['keywords_es'])
                if kw_es:
                    lines.append(f'<div class="field"><span class="label">Palabras clave</span> <span class="keywords">{e(kw_es)}</span></div>')

                # Sem nenhum abstract
                if not art['abstract'] and not art['abstract_en'] and not art['abstract_es']:
                    lines.append('<div class="field"><span class="missing">Sem resumo</span></div>')
                if not kw and not kw_en and not kw_es:
                    lines.append('<div class="field"><span class="missing">Sem palavras-chave</span></div>')

                # References
                refs_html = fmt_refs(art['references_'])
                if refs_html:
                    try:
                        n = len(json.loads(art['references_']))
                    except (json.JSONDecodeError, TypeError):
                        n = 0
                    lines.append(f'<div class="refs"><span class="label">Referências ({n})</span><ol>{refs_html}</ol></div>')
                else:
                    lines.append('<div class="field"><span class="missing">Sem referências</span></div>')

        lines.append('</body></html>')

    finally:
        conn.close()

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'{os.path.relpath(OUT)} ({n_articles} artigos, {n_sections} seções)')
