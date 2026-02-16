#!/usr/bin/env python3
"""Upload artigos do anais.db para o Zenodo (ou sandbox) via REST API.

Uso:
    # Teste no sandbox (3 primeiros artigos do sdnne08)
    python3 scripts/upload_zenodo.py --sandbox --token TOKEN --seminar sdnne08 --limit 3

    # Seminário completo no sandbox
    python3 scripts/upload_zenodo.py --sandbox --token TOKEN --seminar sdnne08

    # Produção real
    python3 scripts/upload_zenodo.py --token TOKEN --seminar sdnne08

    # Dry run (mostra metadados sem enviar)
    python3 scripts/upload_zenodo.py --dry-run --seminar sdnne08

Requer: requests (pip install requests)
"""

import argparse
import json
import os
import sqlite3
import sys
import time

import requests

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'anais.db')
PDF_BASE = os.path.join(os.path.dirname(__file__), '..')

ZENODO_URL = 'https://zenodo.org'
SANDBOX_URL = 'https://sandbox.zenodo.org'

LOCALE_TO_ISO639 = {
    'pt-BR': 'por',
    'es': 'spa',
    'en': 'eng',
}

# Community identifier (must exist on the target Zenodo instance)
COMMUNITY_ID = 'docomomobr'

# Slug prefix → âmbito path for conference_url
SLUG_TO_AMBITO = {
    'sdbr': 'brasil',
    'sdnne': 'nne',
    'sdmg': 'se',
    'sdrj': 'se',
    'sdsp': 'se',
    'sdsul': 'sul',
}


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def fetch_articles(db, seminar_slug, limit=None):
    """Fetch articles with seminar and section metadata."""
    sql = """
        SELECT a.id, a.title, a.subtitle, a.abstract, a.keywords,
               a.file, a.locale, a.pages, a.doi,
               s.title as section_title,
               sem.title as sem_title, sem.subtitle as sem_subtitle,
               sem.date_published, sem.location, sem.isbn, sem.publisher,
               sem.editors, sem.description as sem_description
        FROM articles a
        JOIN sections s ON s.id = a.section_id
        JOIN seminars sem ON sem.slug = a.seminar_slug
        WHERE a.seminar_slug = ?
        ORDER BY a.id
    """
    if limit:
        sql += f' LIMIT {int(limit)}'
    return db.execute(sql, (seminar_slug,)).fetchall()


def fetch_authors(db, article_id):
    """Fetch authors for an article, ordered by seq."""
    sql = """
        SELECT au.givenname, au.familyname, aa.affiliation, au.orcid
        FROM article_author aa
        JOIN authors au ON au.id = aa.author_id
        WHERE aa.article_id = ?
        ORDER BY aa.seq
    """
    return db.execute(sql, (article_id,)).fetchall()


def find_pdf(article):
    """Locate the PDF file for an article."""
    if not article['file']:
        return None
    # Try seminar-specific paths
    slug = article['id'].rsplit('-', 1)[0]  # sdnne08-001 -> sdnne08
    # Map slug to directory
    if slug.startswith('sdbr'):
        base = os.path.join(PDF_BASE, 'nacionais', slug)
    elif slug.startswith('sdnne'):
        base = os.path.join(PDF_BASE, 'regionais', 'nne', slug)
    elif slug.startswith('sdsul'):
        base = os.path.join(PDF_BASE, 'regionais', 'sul', slug)
    elif slug.startswith(('sdsp', 'sdrj', 'sdmg')):
        base = os.path.join(PDF_BASE, 'regionais', 'se', slug)
    else:
        base = PDF_BASE

    pdf_path = os.path.join(base, 'pdfs', article['file'])
    if os.path.isfile(pdf_path):
        return pdf_path
    return None


def _slug_to_ambito(slug):
    """Map seminar slug to site path: sdnne08 → nne, sdsul03 → sul, etc."""
    for prefix, ambito in SLUG_TO_AMBITO.items():
        if slug.startswith(prefix):
            return ambito
    return slug


def build_metadata(article, authors, seminar_slug):
    """Build Zenodo metadata dict from DB data."""
    # Title: combine title + subtitle
    title = article['title']
    if article['subtitle']:
        title += ': ' + article['subtitle']

    # Creators
    creators = []
    for au in authors:
        creator = {'name': f"{au['familyname']}, {au['givenname']}"}
        if au['affiliation']:
            creator['affiliation'] = au['affiliation']
        if au['orcid']:
            creator['orcid'] = au['orcid']
        creators.append(creator)

    # Keywords (article keywords + seminar title for grouping)
    keywords = []
    if article['keywords']:
        kw = article['keywords']
        if kw.startswith('['):
            keywords = json.loads(kw)
        else:
            keywords = [k.strip() for k in kw.split(',') if k.strip()]
    keywords.append(article['sem_title'])

    # Language
    language = LOCALE_TO_ISO639.get(article['locale'], 'por')

    # Description (abstract or fallback)
    description = article['abstract'] or '(sem resumo)'

    metadata = {
        'title': title,
        'upload_type': 'publication',
        'publication_type': 'conferencepaper',
        'description': description,
        'creators': creators,
        'language': language,
        'access_right': 'open',
        'license': 'zenodo-freetoread-1.0',
        'publication_date': article['date_published'],
        'conference_title': article['sem_title'],
        'conference_place': article['location'] or '',
        'conference_url': f'https://anais.docomomobrasil.com/{_slug_to_ambito(seminar_slug)}/{seminar_slug}',
        'partof_title': f"Anais do {article['sem_title']}",
    }

    if article['isbn']:
        metadata['imprint_isbn'] = article['isbn']
    if article['pages']:
        metadata['partof_pages'] = article['pages']
    if keywords:
        metadata['keywords'] = keywords
    if article['publisher']:
        metadata['imprint_publisher'] = article['publisher']
    if article['sem_description']:
        metadata['notes'] = article['sem_description']

    # Contributors (editors/organizers from seminar)
    if article['editors']:
        editors_list = json.loads(article['editors']) if article['editors'].startswith('[') else [article['editors']]
        contributors = []
        for name in editors_list:
            name = name.strip()
            if not name:
                continue
            # Try to split "Givenname Familyname" → "Familyname, Givenname"
            parts = name.rsplit(' ', 1)
            if len(parts) == 2:
                formatted = f"{parts[1]}, {parts[0]}"
            else:
                formatted = name
            contributors.append({'name': formatted, 'type': 'Editor'})
        if contributors:
            metadata['contributors'] = contributors

    metadata['communities'] = [{'identifier': COMMUNITY_ID}]

    return metadata


def _accept_community_request(session, base_url, token, record_id):
    """Auto-accept pending community-inclusion request for a record."""
    headers = {'Authorization': f'Bearer {token}'}
    r = session.get(
        f'{base_url}/api/requests/',
        headers=headers,
        params={'sort': 'newest', 'size': 50, 'q': 'type:community-inclusion AND status:submitted'},
    )
    if r.status_code != 200:
        return
    for req in r.json().get('hits', {}).get('hits', []):
        topic = req.get('topic', {})
        if topic.get('record') == str(record_id):
            accept_url = req.get('links', {}).get('actions', {}).get('accept')
            if accept_url:
                r2 = session.post(accept_url, headers={**headers, 'Content-Type': 'application/json'}, json={})
                if r2.status_code == 200:
                    print(f"  Community: aceito")
                else:
                    print(f"  Community: erro ao aceitar ({r2.status_code})")
            return
    print(f"  Community: request não encontrado")


def upload_article(session, base_url, token, article, authors, seminar_slug, dry_run=False):
    """Upload a single article to Zenodo. Returns (doi, deposition_id) or (None, None)."""
    article_id = article['id']
    metadata = build_metadata(article, authors, seminar_slug)

    if dry_run:
        print(f"\n{'='*60}")
        print(f"[DRY RUN] {article_id}: {metadata['title'][:80]}")
        print(f"  Creators: {', '.join(c['name'] for c in metadata['creators'])}")
        print(f"  Language: {metadata['language']}")
        print(f"  Keywords: {metadata.get('keywords', [])}")
        if 'contributors' in metadata:
            print(f"  Editors: {', '.join(c['name'] for c in metadata['contributors'])}")
        pdf = find_pdf(article)
        print(f"  PDF: {pdf or 'NÃO ENCONTRADO'}")
        return None, None

    headers = {'Authorization': f'Bearer {token}'}

    # 1. Create empty deposition
    r = session.post(
        f'{base_url}/api/deposit/depositions',
        headers={**headers, 'Content-Type': 'application/json'},
        json={},
    )
    if r.status_code != 201:
        print(f"  ERRO ao criar deposition: {r.status_code} {r.text[:200]}")
        return None, None

    depo = r.json()
    depo_id = depo['id']
    bucket_url = depo['links']['bucket']

    # 2. Upload PDF (obrigatório — artigos sem PDF devem ser filtrados antes)
    pdf_path = find_pdf(article)
    if not pdf_path:
        print(f"  ERRO: PDF não encontrado para {article_id}")
        return None, None
    else:
        filename = os.path.basename(pdf_path)
        with open(pdf_path, 'rb') as f:
            r = session.put(
                f'{bucket_url}/{filename}',
                headers=headers,
                data=f,
            )
        if r.status_code not in (200, 201):
            print(f"  ERRO upload PDF: {r.status_code} {r.text[:200]}")
            return None, None

    # 3. Set metadata
    r = session.put(
        f'{base_url}/api/deposit/depositions/{depo_id}',
        headers={**headers, 'Content-Type': 'application/json'},
        json={'metadata': metadata},
    )
    if r.status_code != 200:
        print(f"  ERRO ao definir metadados: {r.status_code} {r.text[:300]}")
        return None, None

    # 4. Publish
    r = session.post(
        f'{base_url}/api/deposit/depositions/{depo_id}/actions/publish',
        headers=headers,
    )
    if r.status_code != 202:
        print(f"  ERRO ao publicar: {r.status_code} {r.text[:300]}")
        return None, None

    result = r.json()
    doi = result.get('doi', result.get('metadata', {}).get('doi'))
    record_id = result.get('record_id', result.get('id'))
    print(f"  DOI: {doi}")

    # 5. Auto-accept community inclusion request (owner of community)
    if record_id:
        _accept_community_request(session, base_url, token, record_id)

    return doi, depo_id


def find_volume_pdf(seminar_slug):
    """Locate the complete volume PDF for a seminar."""
    db = get_db()
    row = db.execute('SELECT volume_pdf FROM seminars WHERE slug = ?', (seminar_slug,)).fetchone()
    db.close()
    if not row or not row['volume_pdf']:
        return None
    filename = row['volume_pdf']
    slug = seminar_slug
    if slug.startswith('sdbr'):
        base = os.path.join(PDF_BASE, 'nacionais', slug)
    elif slug.startswith('sdnne'):
        base = os.path.join(PDF_BASE, 'regionais', 'nne', slug)
    elif slug.startswith('sdsul'):
        base = os.path.join(PDF_BASE, 'regionais', 'sul', slug)
    elif slug.startswith(('sdsp', 'sdrj', 'sdmg')):
        base = os.path.join(PDF_BASE, 'regionais', 'se', slug)
    else:
        base = PDF_BASE
    for subdir in ['pdfs', '.', '..']:
        path = os.path.join(base, subdir, filename)
        if os.path.isfile(path):
            return os.path.abspath(path)
    return None


def upload_volume(session, base_url, token, seminar_slug, dry_run=False):
    """Upload the complete volume PDF as a Zenodo proceedings record."""
    db = get_db()
    sem = db.execute('SELECT * FROM seminars WHERE slug = ?', (seminar_slug,)).fetchone()
    db.close()
    if not sem:
        print(f"Seminário '{seminar_slug}' não encontrado")
        return None, None
    if not sem['volume_pdf']:
        print(f"Seminário '{seminar_slug}' não tem volume_pdf")
        return None, None

    pdf_path = find_volume_pdf(seminar_slug)
    title = f"Anais do {sem['title']}"
    if sem['subtitle']:
        title += f": {sem['subtitle']}"

    # Editors as creators
    editors_list = json.loads(sem['editors']) if sem['editors'] and sem['editors'].startswith('[') else []
    creators = []
    for name in editors_list:
        name = name.strip()
        if not name:
            continue
        parts = name.rsplit(' ', 1)
        if len(parts) == 2:
            creators.append({'name': f"{parts[1]}, {parts[0]}"})
        else:
            creators.append({'name': name})
    if not creators:
        creators = [{'name': 'Docomomo Brasil'}]

    metadata = {
        'title': title,
        'upload_type': 'publication',
        'publication_type': 'conferencepaper',
        'description': sem['description'] or title,
        'creators': creators,
        'language': 'por',
        'access_right': 'open',
        'license': 'zenodo-freetoread-1.0',
        'publication_date': sem['date_published'],
        'conference_title': sem['title'],
        'conference_place': sem['location'] or '',
        'conference_url': f'https://anais.docomomobrasil.com/{_slug_to_ambito(seminar_slug)}/{seminar_slug}',
        'keywords': [sem['title'], 'Docomomo', 'Arquitetura Moderna'],
        'communities': [{'identifier': COMMUNITY_ID}],
    }
    if sem['isbn']:
        metadata['imprint_isbn'] = sem['isbn']
    if sem['publisher']:
        metadata['imprint_publisher'] = sem['publisher']
    if sem['description']:
        metadata['notes'] = sem['description']

    if dry_run:
        print(f"\n[DRY RUN] Volume: {title}")
        print(f"  Creators: {', '.join(c['name'] for c in creators)}")
        print(f"  PDF: {pdf_path or 'NÃO ENCONTRADO'}")
        if pdf_path:
            print(f"  Tamanho: {os.path.getsize(pdf_path)/1024/1024:.1f} MB")
        return None, None

    if not pdf_path:
        print(f"  PDF não encontrado: {sem['volume_pdf']}")
        return None, None

    headers = {'Authorization': f'Bearer {token}'}

    # 1. Create deposition
    r = session.post(
        f'{base_url}/api/deposit/depositions',
        headers={**headers, 'Content-Type': 'application/json'},
        json={},
    )
    if r.status_code != 201:
        print(f"  ERRO ao criar deposition: {r.status_code}")
        return None, None
    depo = r.json()
    depo_id = depo['id']
    bucket_url = depo['links']['bucket']

    # 2. Upload PDF
    filename = os.path.basename(pdf_path)
    size_mb = os.path.getsize(pdf_path) / 1024 / 1024
    print(f"  Uploading {filename} ({size_mb:.1f} MB)...")
    with open(pdf_path, 'rb') as f:
        r = session.put(
            f'{bucket_url}/{filename}',
            headers=headers,
            data=f,
        )
    if r.status_code not in (200, 201):
        print(f"  ERRO upload: {r.status_code}")
        return None, None

    # 3. Set metadata
    r = session.put(
        f'{base_url}/api/deposit/depositions/{depo_id}',
        headers={**headers, 'Content-Type': 'application/json'},
        json={'metadata': metadata},
    )
    if r.status_code != 200:
        print(f"  ERRO metadados: {r.status_code} {r.text[:200]}")
        return None, None

    # 4. Publish
    r = session.post(
        f'{base_url}/api/deposit/depositions/{depo_id}/actions/publish',
        headers=headers,
    )
    if r.status_code != 202:
        print(f"  ERRO publicar: {r.status_code}")
        return None, None

    result = r.json()
    doi = result.get('doi', result.get('metadata', {}).get('doi'))
    print(f"  DOI: {doi}")
    return doi, depo_id


def main():
    parser = argparse.ArgumentParser(description='Upload artigos para Zenodo')
    parser.add_argument('--sandbox', action='store_true', help='Usar sandbox.zenodo.org')
    parser.add_argument('--token', help='API token (ou variável ZENODO_TOKEN / ZENODO_SANDBOX_TOKEN)')
    parser.add_argument('--seminar', required=True, help='Slug do seminário (ex: sdnne08)')
    parser.add_argument('--limit', type=int, help='Limitar número de artigos')
    parser.add_argument('--dry-run', action='store_true', help='Apenas mostrar metadados')
    parser.add_argument('--skip-existing', action='store_true', default=True,
                        help='Pular artigos que já têm DOI (padrão: sim)')
    parser.add_argument('--upload-volume', action='store_true',
                        help='Upload do PDF da edição completa (em vez de artigos individuais)')
    args = parser.parse_args()

    base_url = SANDBOX_URL if args.sandbox else ZENODO_URL
    env_var = 'ZENODO_SANDBOX_TOKEN' if args.sandbox else 'ZENODO_TOKEN'
    token = args.token or os.environ.get(env_var)

    if not token and not args.dry_run:
        print(f"Erro: forneça --token ou defina {env_var}")
        sys.exit(1)

    # Modo volume: upload da edição completa
    if args.upload_volume:
        session = requests.Session()
        doi, depo_id = upload_volume(session, base_url, token, args.seminar, args.dry_run)
        if doi:
            print(f"\nVolume publicado: DOI {doi}")
        return

    db = get_db()
    articles = fetch_articles(db, args.seminar, args.limit)

    if not articles:
        print(f"Nenhum artigo encontrado para '{args.seminar}'")
        sys.exit(1)

    env_label = 'SANDBOX' if args.sandbox else 'PRODUÇÃO'
    print(f"Zenodo {env_label}: {base_url}")
    print(f"Seminário: {args.seminar}")
    print(f"Artigos: {len(articles)}")
    print()

    session = requests.Session()
    uploaded = 0
    skipped = 0
    errors = 0
    current = 0
    results = []

    for art in articles:
        article_id = art['id']

        # Verificar PDF antes de tudo — sem PDF, não sobe para o Zenodo
        if not art['file'] or not find_pdf(art):
            print(f"[SKIP] {article_id}: sem PDF")
            skipped += 1
            continue

        if args.skip_existing and art['doi'] and not args.dry_run:
            print(f"[SKIP] {article_id}: já tem DOI {art['doi']}")
            skipped += 1
            continue

        authors = fetch_authors(db, article_id)
        if not authors:
            print(f"[SKIP] {article_id}: sem autores")
            skipped += 1
            continue

        current += 1
        print(f"[{current}/{len(articles)}] {article_id}: {art['title'][:60]}...")

        doi, depo_id = upload_article(session, base_url, token, art, authors, args.seminar, args.dry_run)

        if args.dry_run:
            continue

        if doi:
            # Save DOI to database
            db.execute('UPDATE articles SET doi = ? WHERE id = ?', (doi, article_id))
            db.commit()
            uploaded += 1
            results.append({'id': article_id, 'doi': doi, 'deposition_id': depo_id})
        else:
            errors += 1

        # Rate limiting
        time.sleep(1.5)

    print(f"\n{'='*60}")
    print(f"Resultado: {uploaded} enviados, {skipped} pulados, {errors} erros")

    if results:
        # Save results log
        log_path = f'/tmp/zenodo_{args.seminar}_results.json'
        with open(log_path, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Log salvo em: {log_path}")

    db.close()


if __name__ == '__main__':
    main()
