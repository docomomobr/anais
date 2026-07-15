#!/usr/bin/env python3
"""Sincroniza o bloco `creators` dos registros Zenodo com o anais.db.

Motivação (2026-07-15): a auditoria de identidade corrigiu 285 autores
(265 ORCIDs de terceiros removidos, fusões de fichas, grafias) — mas os
registros Zenodo publicados ainda carregam os creators antigos, e o
DataCite continua empurrando os papers para os perfis ORCID errados.

Edição de metadados IN-PLACE (padrão de add_zenodo_backlinks.py: draft
da versão corrente → PUT → publish; sem nova versão/DOI). Troca APENAS
`metadata.creators`, preservando o resto do registro vivo. Idempotente:
compara antes de editar.

Uso:
    python3 scripts/sincronizar_creators_zenodo.py --dry-run [ids...]
    python3 scripts/sincronizar_creators_zenodo.py --all
    python3 scripts/sincronizar_creators_zenodo.py --auditados   # só os 402 afetados
"""

import argparse
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from upload_zenodo import (TimeoutSession, _retry, _build_creators,
                           fetch_authors, get_db)
from fix_zenodo_metadata import load_token

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z = 'https://zenodo.org'
AUDIT = os.path.join(BASE, 'revisao', 'campanha-autores', 'dedup-identidade-externa.csv')
THROTTLE = 0.7


def _norm_creators(creators):
    """Forma canônica p/ comparação: (given, family, orcid, afiliação)."""
    out = []
    for c in creators or []:
        p = c.get('person_or_org') or {}
        orcid = ''
        for i in p.get('identifiers') or []:
            if i.get('scheme') == 'orcid':
                orcid = i.get('identifier') or ''
        af = ((c.get('affiliations') or [{}])[0] or {}).get('name') or ''
        out.append((p.get('given_name') or '', p.get('family_name') or '', orcid, af))
    return out


def ids_auditados(db):
    tocados = set()
    with open(AUDIT) as fh:
        for row in csv.reader(fh):
            if row and row[0] != 'acao' and row[1].isdigit():
                tocados.add(int(row[1]))
    q = (f"SELECT DISTINCT a.id FROM articles a "
         f"JOIN article_author aa ON aa.article_id=a.id "
         f"WHERE aa.author_id IN ({','.join(map(str, tocados))}) "
         f"AND a.zenodo_record_id IS NOT NULL ORDER BY a.id")
    return [r[0] for r in db.execute(q)]


def sincronizar(session, headers, db, art_id, dry_run):
    rid, = db.execute("SELECT zenodo_record_id FROM articles WHERE id=?", (art_id,)).fetchone()
    if not rid:
        return 'sem_zenodo'
    novos = _build_creators(fetch_authors(db, art_id))

    r = _retry(session.get, f'{Z}/api/records/{rid}', headers=headers)
    if r.status_code != 200:
        print(f"  ERRO {art_id}: GET {rid} → {r.status_code}")
        return 'error'
    record = r.json()
    if _norm_creators(record['metadata'].get('creators')) == _norm_creators(novos):
        return 'igual'

    if dry_run:
        antes = _norm_creators(record['metadata'].get('creators'))
        depois = _norm_creators(novos)
        print(f"  DRY {art_id} (record {rid}):")
        for a, d in zip(antes + [None] * (len(depois) - len(antes)),
                        depois + [None] * (len(antes) - len(depois))):
            if a != d:
                print(f"    - {a}\n    + {d}")
        return 'would_fix'

    r = _retry(session.post, f'{Z}/api/records/{rid}/draft', headers=headers)
    if r.status_code not in (200, 201):
        print(f"  ERRO {art_id}: draft → {r.status_code} {r.text[:200]}")
        return 'error'
    draft = r.json()
    draft['metadata']['creators'] = novos
    body = {k: draft[k] for k in ('metadata', 'custom_fields', 'access') if k in draft}
    r = _retry(session.put, f'{Z}/api/records/{rid}/draft', headers=headers, json=body)
    if r.status_code != 200:
        print(f"  ERRO {art_id}: PUT → {r.status_code} {r.text[:300]}")
        return 'error'
    r = _retry(session.post, f'{Z}/api/records/{rid}/draft/actions/publish', headers=headers)
    if r.status_code in (200, 202):
        print(f"  FIX  {art_id} (record {rid})")
        return 'fixed'
    if r.status_code == 404:
        print(f"  AVISO {art_id}: publish 404 (provável timeout+sucesso) — verificar")
        return 'verificar'
    print(f"  ERRO {art_id}: publish → {r.status_code} {r.text[:300]}")
    return 'error'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('article_ids', nargs='*')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--auditados', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limite', type=int)
    args = ap.parse_args()

    token = load_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.inveniordm.v1+json',
    }
    session = TimeoutSession(timeout=(15, 120))
    db = get_db()

    if args.article_ids:
        ids = args.article_ids
    elif args.auditados:
        ids = ids_auditados(db)
    elif args.all:
        ids = [r[0] for r in db.execute(
            "SELECT id FROM articles WHERE zenodo_record_id IS NOT NULL ORDER BY id")]
    else:
        ap.error('informe IDs, --auditados ou --all')
    if args.limite:
        ids = ids[:args.limite]

    print(f"{len(ids)} artigos{' [DRY RUN]' if args.dry_run else ''}\n")
    tally = {}
    for i, art_id in enumerate(ids):
        try:
            res = sincronizar(session, headers, db, art_id, args.dry_run)
        except Exception as e:
            print(f"  ERRO {art_id}: {type(e).__name__}: {e}")
            res = 'error'
        tally[res] = tally.get(res, 0) + 1
        if not args.dry_run and i < len(ids) - 1:
            time.sleep(THROTTLE)
    print(f"\nResumo: {dict(sorted(tally.items()))}")
    sys.exit(1 if tally.get('error') else 0)


if __name__ == '__main__':
    main()
