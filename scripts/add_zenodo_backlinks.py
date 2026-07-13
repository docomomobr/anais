#!/usr/bin/env python3
"""Adiciona backlink por artigo nos registros Zenodo já publicados.

Acrescenta em related_identifiers a URL da página HTML do próprio artigo
(isIdenticalTo → https://anais.docomomobrasil.com/{ambito}/{slug}/{id}/),
complementando o isPartOf existente (que aponta só para a edição).

Edição de metadados IN-PLACE via API InvenioRDM (sem nova versão, sem novo
DOI, sem files-import):
    1. GET  /api/records/{id}           → checa se o link já existe (idempotente)
    2. POST /api/records/{id}/draft     → draft da versão corrente
    3. PUT  /api/records/{id}/draft     → draft completo com o link acrescentado
    4. POST /api/records/{id}/draft/actions/publish

sdnne06 é pulado por padrão (ids numéricos no banco → URLs anômalas no site;
corrigir os slugs antes, depois rodar com --include-sdnne06).

Uso:
    python3 scripts/add_zenodo_backlinks.py --dry-run --limit 3
    python3 scripts/add_zenodo_backlinks.py sdbr13-146 sdbr08-042
    python3 scripts/add_zenodo_backlinks.py --slug sdsul06
    python3 scripts/add_zenodo_backlinks.py --all
"""

import argparse
import os
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from upload_zenodo import TimeoutSession, _slug_to_ambito
from fix_zenodo_metadata import load_token

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZENODO_URL = 'https://zenodo.org'
SITE_URL = 'https://anais.docomomobrasil.com'
PUBLIC_DIR = os.path.join(BASE_DIR, 'site', 'public')
THROTTLE = 0.7  # s entre registros (limite Zenodo: 100 req/min autenticado)


def article_url(seminar_slug, article_id):
    ambito = _slug_to_ambito(seminar_slug)
    return f'{SITE_URL}/{ambito}/{seminar_slug}/{article_id}/'


def page_exists_locally(seminar_slug, article_id):
    """Confere no site/public que a URL alvo existe (evita backlink para 404)."""
    ambito = _slug_to_ambito(seminar_slug)
    return os.path.isfile(
        os.path.join(PUBLIC_DIR, ambito, seminar_slug, article_id, 'index.html')
    )


def backlink_entry(url):
    return {
        'identifier': url,
        'scheme': 'url',
        'relation_type': {'id': 'isidenticalto'},
        'resource_type': {'id': 'publication-conferencepaper'},
    }


def has_backlink(metadata, url):
    return any(
        r.get('identifier', '').rstrip('/') == url.rstrip('/')
        for r in metadata.get('related_identifiers', [])
    )


def fix_broken_edition_link(metadata, seminar_slug):
    """Conserta isPartOf publicado com URL errada (bug SLUG_TO_AMBITO sem
    'idc': .../idc06/idc06 em vez de .../internacional/idc06). Retorna True
    se corrigiu algo."""
    ambito = _slug_to_ambito(seminar_slug)
    bad = f'{SITE_URL}/{seminar_slug}/{seminar_slug}'
    good = f'{SITE_URL}/{ambito}/{seminar_slug}'
    fixed = False
    for r in metadata.get('related_identifiers', []):
        if r.get('identifier', '').rstrip('/') == bad:
            r['identifier'] = good
            fixed = True
    return fixed


def add_backlink(session, headers, article_id, seminar_slug, record_id, dry_run=False):
    url = article_url(seminar_slug, article_id)

    if not page_exists_locally(seminar_slug, article_id):
        print(f"  SKIP {article_id}: página não existe em site/public ({url})")
        return 'skipped'

    # 1. GET registro publicado — checagem idempotente
    r = session.get(f'{ZENODO_URL}/api/records/{record_id}', headers=headers)
    if r.status_code != 200:
        print(f"  ERRO {article_id}: GET record {record_id} → {r.status_code}")
        return 'error'
    record = r.json()
    needs_fix = fix_broken_edition_link(record['metadata'], seminar_slug)
    if has_backlink(record['metadata'], url) and not needs_fix:
        print(f"  OK   {article_id}: backlink já presente")
        return 'present'

    if dry_run:
        rel = [x.get('identifier') for x in record['metadata'].get('related_identifiers', [])]
        print(f"  DRY  {article_id} (record {record_id})")
        print(f"       related atuais{' (isPartOf corrigido)' if needs_fix else ''}: {rel}")
        if not has_backlink(record['metadata'], url):
            print(f"       + isIdenticalTo → {url}")
        return 'would_add'

    # 2. Draft da versão corrente (in-place, sem nova versão)
    r = session.post(f'{ZENODO_URL}/api/records/{record_id}/draft', headers=headers)
    if r.status_code not in (200, 201):
        print(f"  ERRO {article_id}: criar draft → {r.status_code} {r.text[:200]}")
        return 'error'
    draft = r.json()

    # 3. PUT do draft completo com o link acrescentado.
    # Usa o próprio corpo do draft (preserva metadata, custom_fields, access).
    fix_broken_edition_link(draft['metadata'], seminar_slug)
    if not has_backlink(draft['metadata'], url):
        draft['metadata'].setdefault('related_identifiers', []).append(backlink_entry(url))
    body = {k: draft[k] for k in ('metadata', 'custom_fields', 'access') if k in draft}
    r = session.put(
        f'{ZENODO_URL}/api/records/{record_id}/draft', headers=headers, json=body
    )
    if r.status_code != 200:
        print(f"  ERRO {article_id}: PUT draft → {r.status_code} {r.text[:300]}")
        return 'error'

    # 4. Publish (mesma versão, mesmo DOI)
    r = session.post(
        f'{ZENODO_URL}/api/records/{record_id}/draft/actions/publish', headers=headers
    )
    if r.status_code in (200, 202):
        print(f"  ADD  {article_id}: {url}")
        return 'added'
    print(f"  ERRO {article_id}: publish → {r.status_code} {r.text[:300]}")
    return 'error'


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('article_ids', nargs='*', help='IDs específicos (ex: sdbr13-146)')
    parser.add_argument('--slug', help='Só artigos de um seminário')
    parser.add_argument('--all', action='store_true', help='Todos com zenodo_record_id')
    parser.add_argument('--limit', type=int, help='Máximo de registros a processar')
    parser.add_argument('--include-sdnne06', action='store_true',
                        help='Inclui sdnne06 (URLs numéricas anômalas)')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    if not (args.article_ids or args.slug or args.all):
        parser.error('informe IDs, --slug ou --all')

    token = load_token()
    if not token and not args.dry_run:
        sys.exit('ZENODO_TOKEN ausente (.env)')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        # CRÍTICO: sem este Accept, /api/records devolve a serialização LEGADA
        # (API velho) — que, reenviada no PUT, apaga os metadados do draft.
        'Accept': 'application/vnd.inveniordm.v1+json',
    }

    db = sqlite3.connect(os.path.join(BASE_DIR, 'anais.db'))
    db.row_factory = sqlite3.Row
    q = ("SELECT id, seminar_slug, zenodo_record_id FROM articles "
         "WHERE zenodo_record_id IS NOT NULL")
    params = []
    if args.article_ids:
        q += f" AND id IN ({','.join('?' * len(args.article_ids))})"
        params += args.article_ids
    if args.slug:
        q += " AND seminar_slug = ?"
        params.append(args.slug)
    if not args.include_sdnne06:
        q += " AND seminar_slug != 'sdnne06'"
    q += " ORDER BY id"
    rows = db.execute(q, params).fetchall()
    if args.limit:
        rows = rows[:args.limit]

    print(f"{len(rows)} registros a processar{' [DRY RUN]' if args.dry_run else ''}\n")
    session = TimeoutSession(timeout=(15, 120))
    tally = {}
    for i, row in enumerate(rows):
        result = add_backlink(
            session, headers, row['id'], row['seminar_slug'],
            row['zenodo_record_id'], dry_run=args.dry_run,
        )
        tally[result] = tally.get(result, 0) + 1
        if not args.dry_run and i < len(rows) - 1:
            time.sleep(THROTTLE)

    print(f"\nResumo: {dict(sorted(tally.items()))}")
    if tally.get('error'):
        sys.exit(1)


if __name__ == '__main__':
    main()
