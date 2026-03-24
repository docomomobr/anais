#!/usr/bin/env python3
"""Corrige metadados de artigos já publicados no Zenodo.

Lê os dados atualizados do anais.db e publica nova versão no Zenodo
com o payload completo reconstruído (PUT substitui tudo).

Uso:
    python3 scripts/fix_zenodo_metadata.py sdbr13-146
    python3 scripts/fix_zenodo_metadata.py sdbr13-146 sdbr08-042
    python3 scripts/fix_zenodo_metadata.py --dry-run sdbr13-146
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from upload_zenodo import (
    TimeoutSession, build_record_payload, fetch_articles,
    fetch_authors, get_db, REQUEST_TIMEOUT,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZENODO_URL = 'https://zenodo.org'


def load_token():
    env_path = os.path.join(BASE_DIR, '.env')
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return os.environ.get('ZENODO_TOKEN')


def fix_article(session, token, db, article_id, dry_run=False):
    """Create new Zenodo version with updated metadata from DB."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    # Get article from DB
    seminar_slug = article_id.rsplit('-', 1)[0]
    articles = fetch_articles(db, seminar_slug)
    article = next((a for a in articles if a['id'] == article_id), None)
    if not article:
        print(f"  ERRO: {article_id} não encontrado no banco")
        return False

    record_id = article['zenodo_record_id']
    if not record_id:
        print(f"  ERRO: {article_id} não tem zenodo_record_id")
        return False

    authors = fetch_authors(db, article_id)
    payload = build_record_payload(article, authors, seminar_slug, license_id='cc-by-4.0')

    print(f"\n{article_id}: {article['title'][:60]}")
    print(f"  Record: {record_id} | DOI: {article['doi']}")

    if dry_run:
        print(f"  [DRY RUN] Payload reconstruído, {len(authors)} autores")
        return True

    # 1. Create new version
    print(f"  Criando nova versão...")
    r = session.post(f'{ZENODO_URL}/api/records/{record_id}/versions', headers=headers)
    if r.status_code not in (200, 201):
        print(f"  ERRO ao criar versão: {r.status_code} {r.text[:300]}")
        return False
    new_id = r.json()['id']
    print(f"  Draft: {new_id}")

    # 2. Import files
    r = session.post(
        f'{ZENODO_URL}/api/records/{new_id}/draft/actions/files-import',
        headers=headers,
    )
    if r.status_code not in (200, 201):
        print(f"  ERRO ao importar arquivos: {r.status_code} {r.text[:300]}")
        return False

    # 3. PUT full metadata
    r = session.put(
        f'{ZENODO_URL}/api/records/{new_id}/draft',
        headers=headers,
        json=payload,
    )
    if r.status_code != 200:
        print(f"  ERRO ao atualizar metadata: {r.status_code} {r.text[:500]}")
        return False

    # 4. Publish
    r = session.post(
        f'{ZENODO_URL}/api/records/{new_id}/draft/actions/publish',
        headers=headers,
    )
    if r.status_code in (200, 202):
        print(f"  Publicado: https://zenodo.org/records/{new_id}")
        # Update record_id in DB (new version)
        db.execute(
            'UPDATE articles SET zenodo_record_id = ? WHERE id = ?',
            (str(new_id), article_id),
        )
        db.commit()
        return True
    else:
        print(f"  ERRO ao publicar: {r.status_code} {r.text[:500]}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Corrige metadados de artigos no Zenodo (nova versão)'
    )
    parser.add_argument('articles', nargs='+', help='IDs dos artigos (ex: sdbr13-146)')
    parser.add_argument('--dry-run', action='store_true', help='Apenas mostrar o que faria')
    args = parser.parse_args()

    token = load_token()
    if not token and not args.dry_run:
        print("Erro: ZENODO_TOKEN não encontrado em .env")
        sys.exit(1)

    session = TimeoutSession(REQUEST_TIMEOUT)
    db = get_db()

    ok, fail = 0, 0
    for article_id in args.articles:
        if fix_article(session, token, db, article_id, args.dry_run):
            ok += 1
        else:
            fail += 1

    print(f"\nResultado: {ok} OK, {fail} erro(s)")
    db.close()


if __name__ == '__main__':
    main()
