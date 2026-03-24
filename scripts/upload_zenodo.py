#!/usr/bin/env python3
"""Upload artigos do anais.db para o Zenodo (ou sandbox) via API InvenioRDM.

Usa a API nova (/api/records) — NÃO a legacy (/api/deposit/depositions).

Uso:
    # Teste no sandbox
    python3 scripts/upload_zenodo.py --sandbox --seminar sdbr15 --limit 1

    # Dry run (mostra payload sem enviar)
    python3 scripts/upload_zenodo.py --dry-run --seminar sdbr15

    # Produção
    python3 scripts/upload_zenodo.py --seminar sdbr15

    # Upload do volume completo (anais em PDF único)
    python3 scripts/upload_zenodo.py --sandbox --seminar sdbr15 --upload-volume

Tokens em .env: ZENODO_SANDBOX_TOKEN, ZENODO_TOKEN
Requer: requests (pip install requests)
"""

import argparse
import json
import os
import sqlite3
import sys
import time

import requests
from requests.exceptions import ConnectionError, Timeout


class TimeoutSession(requests.Session):
    """Session that enforces a default timeout on all requests."""

    def __init__(self, timeout=(15, 120)):
        super().__init__()
        self.timeout = timeout

    def request(self, method, url, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        return super().request(method, url, **kwargs)


RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _retry(func, *args, max_attempts=3, backoff=2, **kwargs):
    """Retry wrapper with exponential backoff for network calls."""
    for attempt in range(1, max_attempts + 1):
        try:
            r = func(*args, **kwargs)
        except (ConnectionError, Timeout) as e:
            if attempt == max_attempts:
                raise
            wait = backoff ** attempt
            print(f"  Rede: tentativa {attempt}/{max_attempts} falhou ({e}), "
                  f"retentando em {wait}s...")
            time.sleep(wait)
            continue
        # Check for retryable HTTP status codes
        if r.status_code in RETRYABLE_STATUS:
            if attempt == max_attempts:
                return r
            if r.status_code == 429:
                wait = int(r.headers.get('Retry-After', backoff ** attempt))
            else:
                wait = backoff ** attempt
            print(f"  HTTP {r.status_code}: tentativa {attempt}/{max_attempts}, "
                  f"retentando em {wait}s...")
            time.sleep(wait)
            continue
        return r

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')
PDF_BASE = BASE_DIR

ZENODO_URL = 'https://zenodo.org'
SANDBOX_URL = 'https://sandbox.zenodo.org'
REQUEST_TIMEOUT = (15, 120)  # (connect, read) seconds

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
    'sdpr': 'sul',
}


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def fetch_articles(db, seminar_slug, limit=None):
    """Fetch articles with seminar and section metadata."""
    sql = """
        SELECT a.id, a.title, a.subtitle, a.abstract, a.keywords,
               a.abstract_en, a.abstract_es,
               a.keywords_en, a.keywords_es,
               a.title_en, a.subtitle_en,
               a.title_es, a.subtitle_es,
               a.file, a.locale, a.pages, a.doi, a.zenodo_record_id, a.document_type,
               s.title as section_title,
               sem.title as sem_title, sem.subtitle as sem_subtitle,
               sem.date_published, sem.location, sem.isbn, sem.publisher,
               sem.editors, sem.description as sem_description
        FROM articles a
        LEFT JOIN sections s ON s.id = a.section_id
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


def find_file(article):
    """Locate the file (PDF or video) for an article."""
    if not article['file']:
        return None
    slug = article['id'].rsplit('-', 1)[0]
    if slug.startswith('sdbr'):
        base = os.path.join(PDF_BASE, 'nacionais', slug)
    elif slug.startswith('sdnne'):
        base = os.path.join(PDF_BASE, 'regionais', 'nne', slug)
    elif slug.startswith('sdsul') or slug.startswith('sdpr'):
        base = os.path.join(PDF_BASE, 'regionais', 'sul', slug)
    elif slug.startswith(('sdsp', 'sdrj', 'sdmg')):
        base = os.path.join(PDF_BASE, 'regionais', 'se', slug)
    else:
        base = PDF_BASE
    # Try pdfs/ first, then videos/
    for subdir in ('pdfs', 'videos'):
        path = os.path.join(base, subdir, article['file'])
        if os.path.isfile(path):
            return path
    return None


# Backwards compatibility
find_pdf = find_file


def _slug_to_ambito(slug):
    """Map seminar slug to site path: sdnne08 → nne, sdsul03 → sul, etc."""
    for prefix, ambito in SLUG_TO_AMBITO.items():
        if slug.startswith(prefix):
            return ambito
    return slug


def _parse_keywords(raw):
    """Parse keywords from DB (JSON array string or comma-separated)."""
    if not raw:
        return []
    if raw.startswith('['):
        return json.loads(raw)
    return [k.strip() for k in raw.split(',') if k.strip()]


def _build_creators(authors):
    """Build InvenioRDM creators list from DB authors."""
    creators = []
    for au in authors:
        person = {
            'type': 'personal',
            'given_name': au['givenname'],
            'family_name': au['familyname'],
        }
        if au['orcid']:
            person['identifiers'] = [
                {'scheme': 'orcid', 'identifier': au['orcid']}
            ]
        creator = {'person_or_org': person}
        if au['affiliation']:
            creator['affiliations'] = [{'name': au['affiliation']}]
        creators.append(creator)
    return creators


def _build_editors(editors_json):
    """Build InvenioRDM contributors list from seminar editors.
    Não inclui ORCID nos editors para evitar spam de notificações
    no perfil ORCID dos editores (1 notificação por artigo)."""
    if not editors_json:
        return []
    editors_list = json.loads(editors_json) if editors_json.startswith('[') else [editors_json]
    contributors = []
    for name in editors_list:
        name = name.strip()
        if not name:
            continue
        parts = name.rsplit(' ', 1)
        if len(parts) == 2:
            person = {'type': 'personal', 'given_name': parts[0], 'family_name': parts[1]}
        else:
            person = {'type': 'personal', 'family_name': name, 'given_name': ''}
        contributors.append({
            'person_or_org': person,
            'role': {'id': 'editor'},
        })
    return contributors


def _build_description(article):
    """Build HTML description with abstracts in all available languages."""
    parts = []

    is_resumo = article['document_type'] == 'resumo'
    if is_resumo:
        parts.append('<p><em>Resumo de comunicação apresentada em evento.</em></p>')

    # Primary abstract (PT)
    if article['abstract']:
        parts.append(f"<p><strong>Resumo:</strong> {article['abstract']}</p>")

    # Abstract EN
    if article['abstract_en']:
        parts.append(f"<p><strong>Abstract:</strong> {article['abstract_en']}</p>")

    # Abstract ES
    if article['abstract_es']:
        parts.append(f"<p><strong>Resumen:</strong> {article['abstract_es']}</p>")

    if not parts:
        return '<p>(sem resumo)</p>'

    # Se só tem abstract num idioma, não precisa do label
    non_resumo = [p for p in parts if '<em>Resumo de comunicação' not in p]
    if len(non_resumo) == 1:
        # Remove o label (strong) quando é abstract único
        text = non_resumo[0]
        for label in ['<strong>Resumo:</strong> ', '<strong>Abstract:</strong> ', '<strong>Resumen:</strong> ']:
            text = text.replace(label, '')
        if is_resumo:
            return parts[0] + '\n' + text
        return text

    return '\n'.join(parts)


def build_record_payload(article, authors, seminar_slug, license_id='cc-by-4.0'):
    """Build InvenioRDM record payload from DB data."""
    is_resumo = article['document_type'] == 'resumo'

    # Title: combine title + subtitle
    title = article['title']
    if article['subtitle']:
        title += ': ' + article['subtitle']
    if is_resumo:
        title += ' [Resumo]'

    # Creators
    creators = _build_creators(authors)

    # Keywords → subjects (all languages, deduplicated)
    subjects = []
    seen = set()
    for kw_field in ['keywords', 'keywords_en', 'keywords_es']:
        for kw in _parse_keywords(article[kw_field]):
            kw_lower = kw.lower()
            if kw_lower not in seen:
                seen.add(kw_lower)
                subjects.append({'subject': kw})
    # Add seminar title for grouping
    sem_lower = article['sem_title'].lower()
    if sem_lower not in seen:
        subjects.append({'subject': article['sem_title']})

    # Language
    language = LOCALE_TO_ISO639.get(article['locale'], 'por')

    # Description (all abstracts)
    description = _build_description(article)

    # Conference URL
    ambito = _slug_to_ambito(seminar_slug)
    conference_url = f'https://anais.docomomobrasil.com/{ambito}/{seminar_slug}'

    # Additional titles (EN, ES)
    additional_titles = []
    if article['title_en']:
        t_en = article['title_en']
        if article['subtitle_en']:
            t_en += ': ' + article['subtitle_en']
        additional_titles.append({
            'title': t_en,
            'type': {'id': 'translated-title'},
            'lang': {'id': 'eng'},
        })
    if article['title_es']:
        t_es = article['title_es']
        if article['subtitle_es']:
            t_es += ': ' + article['subtitle_es']
        additional_titles.append({
            'title': t_es,
            'type': {'id': 'translated-title'},
            'lang': {'id': 'spa'},
        })

    payload = {
        'access': {
            'record': 'public',
            'files': 'public',
        },
        'files': {
            'enabled': True,
        },
        'metadata': {
            'title': title,
            'resource_type': {'id': 'video' if article['document_type'] == 'video' else 'publication-conferencepaper'},
            'publication_date': article['date_published'],
            'creators': creators,
            'description': description,
            'languages': [{'id': language}],
            # License: cc-by-4.0 by default; override via --license argument
            'rights': [{'id': license_id}],
            'publisher': article['publisher'] or 'Docomomo Brasil',
            'subjects': subjects,
            'related_identifiers': [
                {
                    'identifier': conference_url,
                    'scheme': 'url',
                    'relation_type': {'id': 'ispartof'},
                    'resource_type': {'id': 'publication-conferenceproceeding'},
                }
            ],
        },
        'custom_fields': {
            'meeting:meeting': {
                'title': article['sem_title'],
                'place': article['location'] or '',
                'url': conference_url,
            },
            'imprint:imprint': {
                'title': f"Anais do {article['sem_title']}",
            },
        },
    }

    # Additional titles
    if additional_titles:
        payload['metadata']['additional_titles'] = additional_titles

    # ISBN
    if article['isbn']:
        payload['metadata']['identifiers'] = [
            {'identifier': article['isbn'], 'scheme': 'isbn'}
        ]
        payload['custom_fields']['imprint:imprint']['isbn'] = article['isbn']

    # Pages
    if article['pages']:
        payload['custom_fields']['imprint:imprint']['pages'] = article['pages']

    # Editors as contributors
    contributors = _build_editors(article['editors'])
    if contributors:
        payload['metadata']['contributors'] = contributors

    # Notes (ficha catalográfica)
    if article['sem_description']:
        payload['metadata']['additional_descriptions'] = [
            {
                'description': article['sem_description'],
                'type': {'id': 'other'},
            }
        ]

    # Section title (eixo temático) in meeting session
    if article['section_title']:
        payload['custom_fields']['meeting:meeting']['session'] = article['section_title']

    return payload


def _upload_file(session, base_url, token, record_id, pdf_path):
    """Upload PDF via 3-step InvenioRDM file upload."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    filename = os.path.basename(pdf_path)

    # Step 1: Initiate
    r = _retry(session.post,
        f'{base_url}/api/records/{record_id}/draft/files',
        headers=headers,
        json=[{'key': filename}],
    )
    if r.status_code not in (200, 201):
        print(f"  ERRO initiate file: {r.status_code} {r.text[:300]}")
        return False

    # Step 2: Upload content (read into memory so retries work)
    with open(pdf_path, 'rb') as f:
        file_data = f.read()
    # Timeout proportional to file size: 120s base + 30s per MB
    upload_timeout = (15, max(120, 30 * len(file_data) // (1024 * 1024) + 120))
    r = _retry(session.put,
        f'{base_url}/api/records/{record_id}/draft/files/{filename}/content',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/octet-stream'},
        data=file_data,
        timeout=upload_timeout,
    )
    if r.status_code != 200:
        print(f"  ERRO upload content: {r.status_code} {r.text[:300]}")
        return False

    # Step 3: Commit
    r = _retry(session.post,
        f'{base_url}/api/records/{record_id}/draft/files/{filename}/commit',
        headers={'Authorization': f'Bearer {token}'},
    )
    if r.status_code != 200:
        print(f"  ERRO commit file: {r.status_code} {r.text[:300]}")
        return False

    size = r.json().get('size', 0)
    print(f"  PDF: {filename} ({size/1024:.0f} KB)")
    return True


def _resolve_community_id(session, base_url, token, community_slug):
    """Resolve community slug to UUID (production API requires UUID, not slug)."""
    r = session.get(
        f'{base_url}/api/communities/{community_slug}',
        headers={'Authorization': f'Bearer {token}'},
    )
    if r.status_code == 200:
        uuid = r.json().get('id')
        if uuid:
            return uuid
    return community_slug  # fallback to slug


def _submit_community(session, base_url, token, record_id, community_id):
    """Submit draft for community review (also publishes)."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    # Resolve slug to UUID (production API requires UUID)
    community_uuid = _resolve_community_id(session, base_url, token, community_id)

    # 1. Create review request
    r = session.put(
        f'{base_url}/api/records/{record_id}/draft/review',
        headers=headers,
        json={
            'receiver': {'community': community_uuid},
            'type': 'community-submission',
        },
    )
    if r.status_code not in (200, 201):
        print(f"  Community review: erro ao criar ({r.status_code} {r.text[:200]})")
        return None

    # 2. Submit (publishes + submits for review)
    r = session.post(
        f'{base_url}/api/records/{record_id}/draft/actions/submit-review',
        headers=headers,
        json={
            'payload': {
                'content': 'Artigo dos Anais Docomomo Brasil.',
                'format': 'html',
            }
        },
    )
    if r.status_code in (200, 202):
        request_id = r.json().get('id')
        print(f"  Community: submetido (request {request_id})")
        return request_id
    else:
        print(f"  Community submit-review: erro ({r.status_code} {r.text[:200]})")
        return None


def _accept_community_request(session, base_url, token, request_id):
    """Accept community request (if you are the community curator)."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    r = session.post(
        f'{base_url}/api/requests/{request_id}/actions/accept',
        headers=headers,
        json={},
    )
    if r.status_code == 200:
        print(f"  Community: aceito")
    else:
        print(f"  Community: erro ao aceitar ({r.status_code} {r.text[:200]})")


def upload_article(session, base_url, token, article, authors, seminar_slug,
                   dry_run=False, community_id=None, license_id='cc-by-4.0'):
    """Upload a single article to Zenodo via InvenioRDM API.
    Returns (doi, record_id) or (None, None)."""
    article_id = article['id']
    payload = build_record_payload(article, authors, seminar_slug, license_id=license_id)

    if dry_run:
        print(f"\n{'='*60}")
        print(f"[DRY RUN] {article_id}: {payload['metadata']['title'][:80]}")
        print(f"  Creators: {len(payload['metadata']['creators'])}")
        for c in payload['metadata']['creators']:
            p = c['person_or_org']
            orcid = ''
            if p.get('identifiers'):
                orcid = f" (ORCID: {p['identifiers'][0]['identifier']})"
            print(f"    {p.get('given_name', '')} {p.get('family_name', '')}{orcid}")
        print(f"  Language: {payload['metadata']['languages'][0]['id']}")
        print(f"  Subjects: {len(payload['metadata']['subjects'])}")
        if payload['metadata'].get('additional_titles'):
            for at in payload['metadata']['additional_titles']:
                print(f"  Title ({at['lang']['id']}): {at['title'][:70]}")
        print(f"  Meeting: {payload['custom_fields']['meeting:meeting']['title']}")
        if payload['custom_fields']['meeting:meeting'].get('session'):
            print(f"  Session: {payload['custom_fields']['meeting:meeting']['session']}")
        pdf = find_pdf(article)
        print(f"  PDF: {pdf or 'NÃO ENCONTRADO'}")
        print(f"\n  Payload JSON:")
        print(json.dumps(payload, indent=2, ensure_ascii=False)[:2000])
        return None, None

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    # 1. Create draft
    r = session.post(
        f'{base_url}/api/records',
        headers=headers,
        json=payload,
    )
    if r.status_code != 201:
        print(f"  ERRO ao criar draft: {r.status_code} {r.text[:500]}")
        return None, None

    record = r.json()
    record_id = record['id']
    print(f"  Draft criado: {record_id}")

    def _delete_draft():
        """Clean up orphan draft on error."""
        try:
            session.delete(
                f'{base_url}/api/records/{record_id}/draft',
                headers={'Authorization': f'Bearer {token}'},
            )
            print(f"  Draft {record_id} removido (cleanup)")
        except Exception as e:
            print(f"  AVISO: falha ao remover draft {record_id}: {e}")

    # 2. Upload PDF
    pdf_path = find_pdf(article)
    if not pdf_path:
        print(f"  ERRO: PDF não encontrado para {article_id}")
        _delete_draft()
        return None, None

    if not _upload_file(session, base_url, token, record_id, pdf_path):
        _delete_draft()
        return None, None

    # 3. Publish (or submit to community)
    if community_id:
        request_id = _submit_community(session, base_url, token, record_id, community_id)
        if not request_id:
            # Fallback: publish without community
            print(f"  Fallback: publicando sem community...")
            r = _retry(session.post,
                f'{base_url}/api/records/{record_id}/draft/actions/publish',
                headers={'Authorization': f'Bearer {token}'},
            )
            if r.status_code not in (200, 202):
                print(f"  ERRO ao publicar: {r.status_code} {r.text[:300]}")
                _delete_draft()
                return None, None
            record = r.json()
        else:
            # Auto-accept if we're the curator
            _accept_community_request(session, base_url, token, request_id)
            # Re-fetch the record to get DOI
            r = session.get(
                f'{base_url}/api/records/{record_id}',
                headers={'Authorization': f'Bearer {token}'},
            )
            record = r.json() if r.status_code == 200 else {}
    else:
        r = _retry(session.post,
            f'{base_url}/api/records/{record_id}/draft/actions/publish',
            headers={'Authorization': f'Bearer {token}'},
        )
        if r.status_code not in (200, 202):
            print(f"  ERRO ao publicar: {r.status_code} {r.text[:300]}")
            _delete_draft()
            return None, None
        record = r.json()

    # DOI: prefer concept DOI (always resolves to latest version)
    concept_doi = (record.get('conceptdoi')
                   or record.get('metadata', {}).get('relations', {}).get('version', [{}])[0].get('parent', {}).get('pid_value', ''))
    version_doi = (record.get('pids', {}).get('doi', {}).get('identifier')
                   or record.get('doi')
                   or record.get('metadata', {}).get('doi', ''))
    doi = concept_doi if concept_doi else version_doi
    zenodo_url = record.get('links', {}).get('self_html', '')

    print(f"  DOI: {doi}")
    if concept_doi and concept_doi != version_doi:
        print(f"  DOI versão: {version_doi}")
    if zenodo_url:
        print(f"  URL: {zenodo_url}")

    return doi, record_id


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
    elif slug.startswith('sdsul') or slug.startswith('sdpr'):
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


def upload_volume(session, base_url, token, seminar_slug, dry_run=False, community_id=None,
                  license_id='cc-by-4.0'):
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

    # Editors as creators (with ORCID lookup from authors table)
    editors_list = json.loads(sem['editors']) if sem['editors'] and sem['editors'].startswith('[') else []
    db2 = get_db()
    creators = []
    for name in editors_list:
        name = name.strip()
        if not name:
            continue
        parts = name.rsplit(' ', 1)
        if len(parts) == 2:
            given, family = parts[0], parts[1]
        else:
            given, family = '', name
        person = {'type': 'personal', 'given_name': given, 'family_name': family}
        # Lookup ORCID in authors table
        row = db2.execute(
            'SELECT orcid FROM authors WHERE givenname = ? AND familyname = ?',
            (given, family)
        ).fetchone()
        if row and row['orcid']:
            person['identifiers'] = [{'scheme': 'orcid', 'identifier': row['orcid']}]
        creators.append({'person_or_org': person})
    db2.close()
    if not creators:
        creators = [{'person_or_org': {'type': 'organizational', 'name': 'Docomomo Brasil'}}]

    ambito = _slug_to_ambito(seminar_slug)
    conference_url = f'https://anais.docomomobrasil.com/{ambito}/{seminar_slug}'

    payload = {
        'access': {'record': 'public', 'files': 'public'},
        'files': {'enabled': True},
        'metadata': {
            'title': title,
            'resource_type': {'id': 'publication-conferenceproceeding'},
            'publication_date': sem['date_published'],
            'creators': creators,
            'description': sem['description'] or title,
            'languages': [{'id': 'por'}],
            # License: cc-by-4.0 by default; override via --license argument
            'rights': [{'id': license_id}],
            'publisher': sem['publisher'] or 'Docomomo Brasil',
            'subjects': [
                {'subject': sem['title']},
                {'subject': 'Docomomo'},
                {'subject': 'Arquitetura Moderna'},
            ],
            'related_identifiers': [
                {
                    'identifier': conference_url,
                    'scheme': 'url',
                    'relation_type': {'id': 'isidenticalto'},
                    'resource_type': {'id': 'publication-conferenceproceeding'},
                }
            ],
        },
        'custom_fields': {
            'meeting:meeting': {
                'title': sem['title'],
                'place': sem['location'] or '',
                'url': conference_url,
            },
        },
    }

    if sem['isbn']:
        payload['metadata']['identifiers'] = [
            {'identifier': sem['isbn'], 'scheme': 'isbn'}
        ]
        payload['custom_fields']['imprint:imprint'] = {
            'title': title,
            'isbn': sem['isbn'],
        }

    # Não duplicar description em additional_descriptions

    if dry_run:
        print(f"\n[DRY RUN] Volume: {title}")
        print(f"  Creators: {len(creators)}")
        print(f"  PDF: {pdf_path or 'NÃO ENCONTRADO'}")
        if pdf_path:
            print(f"  Tamanho: {os.path.getsize(pdf_path)/1024/1024:.1f} MB")
        print(f"\n  Payload JSON:")
        print(json.dumps(payload, indent=2, ensure_ascii=False)[:2000])
        return None, None

    if not pdf_path:
        print(f"  PDF não encontrado: {sem['volume_pdf']}")
        return None, None

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    # 1. Create draft
    r = session.post(f'{base_url}/api/records', headers=headers, json=payload)
    if r.status_code != 201:
        print(f"  ERRO ao criar draft: {r.status_code} {r.text[:300]}")
        return None, None

    record = r.json()
    record_id = record['id']
    print(f"  Draft criado: {record_id}")

    def _delete_draft():
        """Clean up orphan draft on error."""
        try:
            session.delete(
                f'{base_url}/api/records/{record_id}/draft',
                headers={'Authorization': f'Bearer {token}'},
            )
            print(f"  Draft {record_id} removido (cleanup)")
        except Exception as e:
            print(f"  AVISO: falha ao remover draft {record_id}: {e}")

    # 2. Upload PDF
    if not _upload_file(session, base_url, token, record_id, pdf_path):
        _delete_draft()
        return None, None

    # 3. Publish
    if community_id:
        request_id = _submit_community(session, base_url, token, record_id, community_id)
        if request_id:
            _accept_community_request(session, base_url, token, request_id)
            r = session.get(f'{base_url}/api/records/{record_id}',
                            headers={'Authorization': f'Bearer {token}'})
            record = r.json() if r.status_code == 200 else {}
        else:
            r = session.post(f'{base_url}/api/records/{record_id}/draft/actions/publish',
                             headers={'Authorization': f'Bearer {token}'})
            if r.status_code not in (200, 202):
                print(f"  ERRO ao publicar: {r.status_code}")
                _delete_draft()
                return None, None
            record = r.json()
    else:
        r = session.post(f'{base_url}/api/records/{record_id}/draft/actions/publish',
                         headers={'Authorization': f'Bearer {token}'})
        if r.status_code not in (200, 202):
            print(f"  ERRO ao publicar: {r.status_code} {r.text[:300]}")
            _delete_draft()
            return None, None
        record = r.json()

    doi = (record.get('pids', {}).get('doi', {}).get('identifier')
           or record.get('doi')
           or record.get('metadata', {}).get('doi', ''))
    print(f"  DOI: {doi}")

    # Save DOI and record_id to seminars table
    if doi:
        db2 = get_db()
        try:
            db2.execute('ALTER TABLE seminars ADD COLUMN zenodo_doi TEXT')
        except Exception:
            pass  # column already exists
        try:
            db2.execute('ALTER TABLE seminars ADD COLUMN zenodo_record_id TEXT')
        except Exception:
            pass  # column already exists
        db2.execute('UPDATE seminars SET zenodo_doi=?, zenodo_record_id=? WHERE slug=?',
                    (doi, str(record_id), seminar_slug))
        db2.commit()
        db2.close()

    return doi, record_id


def main():
    parser = argparse.ArgumentParser(description='Upload artigos para Zenodo (API InvenioRDM)')
    parser.add_argument('--sandbox', action='store_true', help='Usar sandbox.zenodo.org')
    parser.add_argument('--token', help='API token (ou variável ZENODO_TOKEN / ZENODO_SANDBOX_TOKEN)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--seminar', help='Slug do seminário (ex: sdbr15)')
    group.add_argument('--all', action='store_true', help='Upload de todos os seminários')
    parser.add_argument('--limit', type=int, help='Limitar número de artigos')
    parser.add_argument('--dry-run', action='store_true', help='Apenas mostrar metadados')
    parser.add_argument('--no-skip-existing', action='store_false', dest='skip_existing',
                        help='Não pular artigos que já têm DOI (padrão: pula)')
    parser.add_argument('--license', default='cc-by-4.0',
                        help='Licença SPDX (padrão: cc-by-4.0)')
    parser.add_argument('--community', default=None,
                        help=f'Submeter à comunidade (default: sem community). Ex: {COMMUNITY_ID}')
    parser.add_argument('--upload-volume', action='store_true',
                        help='Upload do PDF da edição completa (em vez de artigos individuais)')
    args = parser.parse_args()

    base_url = SANDBOX_URL if args.sandbox else ZENODO_URL
    env_var = 'ZENODO_SANDBOX_TOKEN' if args.sandbox else 'ZENODO_TOKEN'

    # Load .env before checking token so env vars are available
    env_path = os.path.join(BASE_DIR, '.env')
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    token = args.token or os.environ.get(env_var)

    if not token and not args.dry_run:
        print(f"Erro: forneça --token ou defina {env_var}")
        sys.exit(1)

    # Modo volume: upload da edição completa
    if args.upload_volume:
        if not args.seminar:
            print("Erro: --upload-volume requer --seminar")
            sys.exit(1)
        session = TimeoutSession(REQUEST_TIMEOUT)
        doi, record_id = upload_volume(session, base_url, token, args.seminar,
                                       args.dry_run, args.community,
                                       license_id=args.license)
        if doi:
            print(f"\nVolume publicado: DOI {doi}")
        return

    db = get_db()

    # Determine which seminars to process
    if args.all:
        slugs = [r['slug'] for r in db.execute(
            "SELECT slug FROM seminars ORDER BY slug"
        ).fetchall()]
    else:
        slugs = [args.seminar]

    env_label = 'SANDBOX' if args.sandbox else 'PRODUÇÃO'
    print(f"Zenodo {env_label}: {base_url}")
    if args.all:
        print(f"Seminários: {len(slugs)}")
    print()

    session = TimeoutSession(REQUEST_TIMEOUT)
    total_uploaded = 0
    total_skipped = 0
    total_errors = 0
    all_results = []

    for sem_slug in slugs:
        articles = fetch_articles(db, sem_slug, args.limit)
        if not articles:
            print(f"[{sem_slug}] Nenhum artigo encontrado")
            continue

        # Pre-count uploadable articles for progress display
        uploadable = []
        for art in articles:
            if not art['file'] or not find_pdf(art):
                continue
            if art['document_type'] == 'resumo':
                continue
            if args.skip_existing and art['doi'] and not args.dry_run:
                continue
            if not fetch_authors(db, art['id']):
                continue
            uploadable.append(art['id'])
        total_to_upload = len(uploadable)

        print(f"--- {sem_slug}: {len(articles)} artigos ({total_to_upload} para upload) ---")

        current = 0
        for art in articles:
            article_id = art['id']

            if not art['file'] or not find_pdf(art):
                print(f"[SKIP] {article_id}: sem PDF")
                total_skipped += 1
                continue

            if art['document_type'] == 'resumo':
                print(f"[SKIP] {article_id}: resumo (sem texto completo)")
                total_skipped += 1
                continue

            if args.skip_existing and art['doi'] and not args.dry_run:
                print(f"[SKIP] {article_id}: já tem DOI {art['doi']}")
                total_skipped += 1
                continue

            authors = fetch_authors(db, article_id)
            if not authors:
                print(f"[SKIP] {article_id}: sem autores")
                total_skipped += 1
                continue

            current += 1
            print(f"  [{current}/{total_to_upload}] {article_id}: {art['title'][:60]}...")

            doi, record_id = upload_article(session, base_url, token, art, authors,
                                            sem_slug, args.dry_run, args.community,
                                            license_id=args.license)

            if args.dry_run:
                continue

            if doi:
                db.execute('UPDATE articles SET doi = ?, zenodo_record_id = ? WHERE id = ?',
                           (doi, str(record_id), article_id))
                db.commit()
                total_uploaded += 1
                all_results.append({'id': article_id, 'doi': doi, 'record_id': record_id})
            else:
                total_errors += 1

            # Rate limiting
            time.sleep(1.5)

    print(f"\n{'='*60}")
    print(f"Resultado: {total_uploaded} enviados, {total_skipped} pulados, {total_errors} erros")

    if all_results:
        label = slugs[0] if len(slugs) == 1 else 'all'
        log_path = f'/tmp/zenodo_{label}_results.json'
        with open(log_path, 'w') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"Log salvo em: {log_path}")

    db.close()


if __name__ == '__main__':
    main()
