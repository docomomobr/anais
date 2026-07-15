#!/usr/bin/env python3
"""Generate a single-page HTML review for a seminar."""
import sqlite3
import json
import html
import sys

slug = sys.argv[1] if len(sys.argv) > 1 else 'sdpr02'
DB = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/anais.db'
OUT = f'/tmp/revisao-{slug}.html'

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

sem = conn.execute('SELECT * FROM seminars WHERE slug=?', (slug,)).fetchone()
sections = conn.execute('SELECT * FROM sections WHERE seminar_slug=? ORDER BY id', (slug,)).fetchall()
articles = conn.execute('''
    SELECT a.*, s.title as section_title
    FROM articles a
    LEFT JOIN sections s ON a.section_id = s.id
    WHERE a.seminar_slug=?
    ORDER BY a.id
''', (slug,)).fetchall()

def e(text):
    return html.escape(str(text)) if text else ''

def fmt_keywords(kw_json):
    if not kw_json:
        return ''
    kws = json.loads(kw_json)
    return '; '.join(kws)

def fmt_refs(refs_json):
    if not refs_json:
        return ''
    refs = json.loads(refs_json)
    lines = []
    for i, r in enumerate(refs, 1):
        lines.append(f'<li>{e(r)}</li>')
    return '\n'.join(lines)

lines = []
lines.append(f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Revisão — {e(sem["title"])}</title>
<style>
body {{ font-family: Georgia, serif; max-width: 900px; margin: 2em auto; padding: 0 1em; color: #222; line-height: 1.5; }}
h1 {{ font-size: 1.4em; border-bottom: 2px solid #333; padding-bottom: 0.3em; }}
h2 {{ font-size: 1.1em; margin-top: 2.5em; border-bottom: 1px solid #999; padding-bottom: 0.2em; color: #444; }}
.id {{ font-family: monospace; font-size: 0.85em; color: #888; }}
.field {{ margin: 0.3em 0; }}
.label {{ font-weight: bold; color: #555; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.05em; }}
.abstract {{ background: #f8f8f5; padding: 0.8em 1em; border-left: 3px solid #ccc; margin: 0.5em 0; font-size: 0.95em; }}
.keywords {{ font-style: italic; color: #555; }}
.authors {{ margin: 0.4em 0; }}
.author {{ display: inline-block; background: #eee; padding: 2px 8px; border-radius: 3px; margin: 2px 2px; font-size: 0.9em; }}
.author .affil {{ color: #777; font-size: 0.85em; }}
.author .orcid {{ color: #a6ce39; font-size: 0.8em; }}
.refs {{ font-size: 0.85em; color: #444; }}
.refs ol {{ padding-left: 1.5em; }}
.refs li {{ margin-bottom: 0.3em; }}
.missing {{ color: #c44; font-style: italic; }}
.section-tag {{ background: #dde; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; color: #446; }}
.file {{ font-family: monospace; font-size: 0.85em; color: #668; }}
.meta {{ font-size: 0.85em; color: #777; }}
.toc {{ background: #f5f5f5; padding: 1em; border-radius: 5px; margin-bottom: 2em; }}
.toc a {{ text-decoration: none; color: #336; }}
.toc a:hover {{ text-decoration: underline; }}
.toc ol {{ padding-left: 1.5em; }}
.toc li {{ margin: 0.2em 0; }}
</style>
</head>
<body>
<h1>{e(sem["title"])}</h1>
<div class="meta">
{e(sem["subtitle"] or "")}<br>
{e(sem["location"])} — {sem["year"]}<br>
Publisher: {e(sem["publisher"])} | ISBN: {e(sem["isbn"]) or '<span class="missing">sem ISBN</span>'}
</div>
''')

# TOC
lines.append('<div class="toc"><strong>Sumário</strong><ol>')
for art in articles:
    title = art["title"]
    if art["subtitle"]:
        title += f': {art["subtitle"]}'
    lines.append(f'<li><a href="#{art["id"]}"><span class="id">{art["id"]}</span> {e(title)}</a></li>')
lines.append('</ol></div>')

# Articles
for art in articles:
    title = e(art["title"])
    if art["subtitle"]:
        title += f': <span style="font-weight:normal">{e(art["subtitle"])}</span>'

    lines.append(f'<h2 id="{art["id"]}"><span class="id">{art["id"]}</span> — {title}</h2>')

    # Section, file, pages
    meta_parts = []
    if art["section_title"]:
        meta_parts.append(f'<span class="section-tag">{e(art["section_title"])}</span>')
    if art["file"]:
        meta_parts.append(f'<span class="file">{e(art["file"])}</span>')
    if art["pages_count"]:
        meta_parts.append(f'{art["pages_count"]} p.')
    if meta_parts:
        lines.append(f'<div class="meta">{" · ".join(meta_parts)}</div>')

    # Authors
    authors = conn.execute('''
        SELECT au.givenname, au.familyname, aa.affiliation, au.orcid, au.email
        FROM article_author aa
        JOIN authors au ON aa.author_id = au.id
        WHERE aa.article_id = ?
        ORDER BY aa.seq
    ''', (art["id"],)).fetchall()

    lines.append('<div class="authors">')
    for au in authors:
        name = f'{au["givenname"]} {au["familyname"]}'
        parts = [e(name)]
        if au["affiliation"]:
            parts.append(f'<span class="affil">({e(au["affiliation"])})</span>')
        if au["orcid"]:
            parts.append(f'<span class="orcid">⬡ {au["orcid"]}</span>')
        lines.append(f'  <span class="author">{" ".join(parts)}</span>')
    lines.append('</div>')

    # Abstract
    if art["abstract"]:
        lines.append(f'<div class="field"><span class="label">Resumo</span></div>')
        lines.append(f'<div class="abstract">{e(art["abstract"])}</div>')
    else:
        lines.append(f'<div class="field"><span class="missing">Sem resumo</span></div>')

    # Keywords
    kw = fmt_keywords(art["keywords"])
    if kw:
        lines.append(f'<div class="field"><span class="label">Palavras-chave</span> <span class="keywords">{e(kw)}</span></div>')
    else:
        lines.append(f'<div class="field"><span class="missing">Sem palavras-chave</span></div>')

    # References
    refs_html = fmt_refs(art["references_"])
    if refs_html:
        n = len(json.loads(art["references_"]))
        lines.append(f'<div class="refs"><span class="label">Referências ({n})</span><ol>{refs_html}</ol></div>')
    else:
        lines.append(f'<div class="field"><span class="missing">Sem referências</span></div>')

lines.append('</body></html>')

with open(OUT, 'w') as f:
    f.write('\n'.join(lines))

print(f'{OUT} ({len(articles)} artigos)')
