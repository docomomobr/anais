#!/usr/bin/env python3
"""Gera a mala direta da campanha de autores (agosto/2026).

Para cada autor com e-mail real: nome, e-mail, URL da página, nº e lista
de trabalhos, e os links assinados do worker de claims (conferência e
opt-out — token HMAC com o CLAIM_SECRET do .env, o MESMO do worker).

Dedup por e-mail: fichas que compartilham e-mail real (ex.: escritório)
viram UM destinatário com os nomes concatenados.

Saída: revisao/campanha-autores/mala-direta.csv — GITIGNORED (contém
e-mails pessoais; NUNCA commitar. Incidente de 2026-07-15 no devlog).

Uso:
    python3 scripts/gerar_campanha.py            # gera o CSV completo
    python3 scripts/gerar_campanha.py --amostra 5
"""

import argparse
import base64
import csv
import hashlib
import hmac
import json
import os
import re
import sqlite3
import sys
import unicodedata

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WORKER = 'https://claims-anais.tesouraria-docomomobr.workers.dev'
SITE = 'https://anais.docomomobrasil.com'
OUT = os.path.join(BASE, 'revisao', 'campanha-autores', 'mala-direta.csv')
PUBLIC_AUTORES = os.path.join(BASE, 'site', 'public', 'autores')


def secret():
    for l in open(os.path.join(BASE, '.env')):
        if l.startswith('CLAIM_SECRET='):
            return l.split('=', 1)[1].strip()
    sys.exit('CLAIM_SECRET ausente no .env')


def slugify(term):
    """Reproduz o urlize do Hugo: minúsculas, acentos PRESERVADOS,
    não-alfanuméricos viram hífen."""
    s = unicodedata.normalize('NFC', term).lower()
    s = re.sub(r"['\u2019\u00b4\u0060]", '', s)          # apóstrofos somem
    s = re.sub(r'[^\w.]+', '-', s, flags=re.UNICODE).replace('_', '-')
    return s.strip('-')


def token(sec, payload):
    corpo = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode()
    ).decode().rstrip('=')
    sig = hmac.new(sec.encode(), corpo.encode(), hashlib.sha256).hexdigest()[:32]
    return f'{corpo}.{sig}'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--amostra', type=int)
    args = ap.parse_args()

    sec = secret()
    db = sqlite3.connect(f"file:{os.path.join(BASE, 'anais.db')}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row

    autores = db.execute("""
        SELECT au.id, au.givenname, au.familyname, LOWER(TRIM(au.email)) email
        FROM authors au
        WHERE au.email IS NOT NULL AND au.email != ''
          AND au.email NOT LIKE '%example.com' AND au.email NOT LIKE '%exemplo.com'
          AND EXISTS (SELECT 1 FROM article_author aa WHERE aa.author_id = au.id)
        ORDER BY au.familyname, au.givenname""").fetchall()

    # dedup por e-mail
    por_email = {}
    for a in autores:
        por_email.setdefault(a['email'], []).append(a)

    linhas, sem_pagina = [], []
    for email, grupo in por_email.items():
        # um destinatário por e-mail; página/slug do primeiro (com mais artigos)
        grupo.sort(key=lambda a: -db.execute(
            "SELECT COUNT(*) FROM article_author WHERE author_id=?", (a['id'],)).fetchone()[0])
        a = grupo[0]
        termo = f"{a['familyname']}, {a['givenname']}"
        slug = slugify(termo)
        if not os.path.isdir(os.path.join(PUBLIC_AUTORES, slug)):
            sem_pagina.append((a['id'], termo, slug))
            continue
        arts = db.execute("""
            SELECT ar.title, s.title sem, s.year FROM article_author aa
            JOIN articles ar ON ar.id = aa.article_id
            JOIN seminars s ON s.slug = ar.seminar_slug
            WHERE aa.author_id = ? ORDER BY s.year DESC""", (a['id'],)).fetchall()
        lista = '\n'.join(f"• {r['title'][:80]} ({r['sem'].split(',')[0]}, {r['year']})"
                          for r in arts[:5])
        if len(arts) > 5:
            lista += f'\n• … e mais {len(arts) - 5} trabalho(s)'
        nomes = ' e '.join(f"{g['givenname']} {g['familyname']}" for g in grupo)
        payload = {'a': a['id'], 'e': email, 's': slug}
        t = token(sec, payload)
        linhas.append({
            'author_id': a['id'], 'nome': nomes, 'email': email,
            'n_trabalhos': len(arts),
            'url_pagina': f'{SITE}/autores/{slug}/',
            'lista_trabalhos': lista,
            'link_claim': f'{WORKER}/c/{t}',
            'link_optout': f'{WORKER}/o/{t}',
        })

    if args.amostra:
        linhas = linhas[:args.amostra]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    print(f'{len(linhas)} destinatários → {OUT}  (GITIGNORED — não commitar)')
    if sem_pagina:
        print(f'{len(sem_pagina)} autores SEM página no site (slug não bateu) — conferir:')
        for aid, termo, slug in sem_pagina[:10]:
            print(f'  id {aid}: "{termo}" → {slug}')


if __name__ == '__main__':
    main()
