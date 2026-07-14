#!/usr/bin/env python3
"""Gera o catálogo OAI-PMH (oai_dc) a partir do anais.db.

Produz site/static/oai-data/catalog.json com um registro Dublin Core
trilíngue por artigo (fragmento XML pronto), consumido pelo Cloudflare
Worker em oai/worker.js, que implementa o protocolo.

Datestamps são preservados entre execuções: um registro só ganha datestamp
novo se seu conteúdo mudou (hash), permitindo colheita incremental
(from/until) pelos agregadores.

Uso:
    python3 scripts/gerar_oai.py            # gera/atualiza o catálogo
    python3 scripts/gerar_oai.py --dry-run  # só relata o que mudaria
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import date
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(__file__))
from upload_zenodo import _slug_to_ambito

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_URL = 'https://anais.docomomobrasil.com'
OUT_PATH = os.path.join(BASE_DIR, 'site', 'static', 'oai-data', 'catalog.json')
PUBLIC_DIR = os.path.join(BASE_DIR, 'site', 'public')
OAI_PREFIX = 'oai:anais.docomomobrasil.com:'

LOCALE_TO_ISO = {'pt': 'pt', 'pt_BR': 'pt', 'es': 'es', 'es_ES': 'es',
                 'en': 'en', 'en_US': 'en'}


def _lang(locale):
    return LOCALE_TO_ISO.get(locale or 'pt', 'pt')


def _dc_el(tag, value, lang=None):
    if not value:
        return ''
    attr = f' xml:lang="{lang}"' if lang else ''
    return f'      <dc:{tag}{attr}>{escape(value.strip())}</dc:{tag}>\n'


def _split_keywords(raw):
    """Keywords no banco: maioria em array JSON, minoria em texto com ';'."""
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith('['):
        try:
            return [str(k).strip() for k in json.loads(raw) if str(k).strip()]
        except (json.JSONDecodeError, TypeError):
            pass
    sep = ';' if ';' in raw else ','
    return [k.strip() for k in raw.split(sep) if k.strip()]


def _full_title(title, subtitle):
    if not title:
        return None
    return f'{title}: {subtitle}' if subtitle else title


def build_dc_xml(article, authors, seminar):
    """Fragmento <oai_dc:dc> trilíngue de um artigo."""
    main_lang = _lang(article['locale'])
    ambito = _slug_to_ambito(article['seminar_slug'])
    page_url = f"{SITE_URL}/{ambito}/{article['seminar_slug']}/{article['id']}/"

    x = ('    <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"\n'
         '        xmlns:dc="http://purl.org/dc/elements/1.1/"\n'
         '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
         '        xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/'
         ' http://www.openarchives.org/OAI/2.0/oai_dc.xsd">\n')

    x += _dc_el('title', _full_title(article['title'], article['subtitle']), main_lang)
    if main_lang != 'en':
        x += _dc_el('title', _full_title(article['title_en'], article['subtitle_en']), 'en')
    if main_lang != 'es':
        x += _dc_el('title', _full_title(article['title_es'], article['subtitle_es']), 'es')

    for a in authors:
        x += _dc_el('creator', f"{a['familyname']}, {a['givenname']}")

    for kw in _split_keywords(article['keywords']):
        x += _dc_el('subject', kw, main_lang)
    for kw in _split_keywords(article['keywords_en']):
        x += _dc_el('subject', kw, 'en')
    for kw in _split_keywords(article['keywords_es']):
        x += _dc_el('subject', kw, 'es')

    x += _dc_el('description', article['abstract'], main_lang)
    if main_lang != 'en':
        x += _dc_el('description', article['abstract_en'], 'en')
    if main_lang != 'es':
        x += _dc_el('description', article['abstract_es'], 'es')

    x += _dc_el('publisher', seminar['publisher'] or 'Docomomo Brasil')
    x += _dc_el('date', str(seminar['date_published'] or seminar['year']))
    x += _dc_el('type', 'info:eu-repo/semantics/conferenceObject')
    x += _dc_el('type', article['document_type'] or 'artigo')
    x += _dc_el('format', 'application/pdf')
    x += _dc_el('identifier', page_url)
    if article['doi']:
        x += _dc_el('identifier', f"https://doi.org/{article['doi']}")
    elif article['zenodo_record_id']:
        x += _dc_el('identifier',
                    f"https://doi.org/10.5281/zenodo.{article['zenodo_record_id']}")
    x += _dc_el('source', seminar['title'])
    if seminar['isbn']:
        x += _dc_el('source', f"ISBN {seminar['isbn']}")
    x += _dc_el('language', main_lang)
    x += _dc_el('rights', 'info:eu-repo/semantics/openAccess')

    x += '    </oai_dc:dc>'
    return x, page_url


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    db = sqlite3.connect(os.path.join(BASE_DIR, 'anais.db'))
    db.row_factory = sqlite3.Row

    # Datestamps anteriores (para preservação por hash)
    old = {}
    if os.path.isfile(OUT_PATH):
        with open(OUT_PATH) as f:
            for r in json.load(f).get('records', []):
                old[r['id']] = r

    today = date.today().isoformat()
    seminars = {s['slug']: s for s in db.execute('SELECT * FROM seminars')}
    articles = db.execute('SELECT * FROM articles ORDER BY id').fetchall()

    records, sets_seen = [], {}
    n_new = n_changed = n_kept = n_skipped = 0
    for art in articles:
        sem = seminars[art['seminar_slug']]
        authors = db.execute(
            'SELECT a.givenname, a.familyname FROM article_author aa '
            'JOIN authors a ON a.id = aa.author_id '
            'WHERE aa.article_id = ? ORDER BY aa.seq', (art['id'],)).fetchall()

        xml, page_url = build_dc_xml(art, authors, sem)

        # Só cataloga páginas que existem no site construído
        rel = page_url[len(SITE_URL) + 1:].rstrip('/')
        if not os.path.isfile(os.path.join(PUBLIC_DIR, *rel.split('/'), 'index.html')):
            n_skipped += 1
            continue

        content_hash = hashlib.sha256(xml.encode()).hexdigest()[:16]
        prev = old.get(art['id'])
        if prev and prev.get('hash') == content_hash:
            datestamp = prev['datestamp']
            n_kept += 1
        elif prev:
            datestamp = today
            n_changed += 1
        else:
            datestamp = today
            n_new += 1

        slug = art['seminar_slug']
        sets_seen[slug] = sem['title']
        records.append({
            'id': art['id'],
            'oai_id': OAI_PREFIX + art['id'],
            'datestamp': datestamp,
            'sets': [slug],
            'hash': content_hash,
            'xml': xml,
        })

    catalog = {
        'generated': today,
        'repository': {
            'name': 'Anais Docomomo Brasil',
            'earliest': min((r['datestamp'] for r in records), default=today),
            'admin_email': 'contato@docomomobrasil.com',
            'site': SITE_URL,
        },
        'sets': [{'spec': k, 'name': v} for k, v in sorted(sets_seen.items())],
        'records': records,
    }

    print(f"{len(records)} registros | novos: {n_new}, alterados: {n_changed}, "
          f"mantidos: {n_kept}, sem página no site (pulados): {n_skipped}")
    if args.dry_run:
        print('[DRY RUN] nada gravado')
        return

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump(catalog, f, ensure_ascii=False)
    print(f"Gravado: {OUT_PATH} ({os.path.getsize(OUT_PATH) // 1024} KB)")


if __name__ == '__main__':
    main()
