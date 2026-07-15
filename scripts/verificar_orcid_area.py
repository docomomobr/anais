#!/usr/bin/env python3
"""Verifica se os ORCIDs dos autores pertencem a pessoas da área de
arquitetura/urbanismo, cruzando o registro público do ORCID (empregos,
formação, keywords, títulos de obras) com termos da área — e confere o
nome. Não altera o banco: gera relatório para revisão humana.

Contexto: o pipeline de atribuição de ORCID cometeu erros (ex.: ORCID de
pesquisador de outra área com nome parecido; coautores com ORCID trocado
— casos corrigidos em 2026-07-14/15, cf. devlog).

Uso:
    python3 scripts/verificar_orcid_area.py            # todos (relatório)
    python3 scripts/verificar_orcid_area.py --limite 50
    python3 scripts/verificar_orcid_area.py --author-id 1720

Saída: revisao/orcid-verificacao-area.csv (pior suspeita primeiro) +
resumo no stdout. Idempotente: reaproveita linhas já verificadas.
"""

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
import socket
import urllib.request

socket.setdefaulttimeout(30)

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB = os.path.join(BASE, 'anais.db')
OUT = os.path.join(BASE, 'revisao', 'orcid-verificacao-area.csv')
THROTTLE = 0.35  # s entre chamadas à API pública

ARCH_TERMS = [
    # pt
    'arquitet', 'urbanis', 'urbano', 'urbana', 'patrimônio', 'patrimonio',
    'paisagis', 'edifício', 'edificio', 'construção', 'construcao',
    'restauro', 'projeto de arquitetura', 'cidade', 'habitação', 'habitacao',
    'modernismo', 'docomomo',
    # en/es
    'architect', 'urban', 'built environment', 'heritage', 'landscape',
    'city', 'housing', 'design',
    # instituições típicas
    'fau', 'iau', 'propar', 'mdu', 'ppgau',
]


def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', s.lower()).strip()


def tokens(s):
    return set(re.sub(r'[^a-z ]', '', norm(s)).split())


def fetch_record(orcid):
    req = urllib.request.Request(
        f'https://pub.orcid.org/v3.0/{orcid}/record',
        headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def avaliar(orcid, nome_db):
    d = fetch_record(orcid)
    person = d.get('person') or {}
    n = person.get('name') or {}
    nome_orcid = f"{(n.get('given-names') or {}).get('value', '')} " \
                 f"{(n.get('family-name') or {}).get('value', '')}".strip()

    partes = []
    partes += [(k.get('content') or '') for k in (person.get('keywords') or {}).get('keyword', [])]
    bio = ((person.get('biography') or {}) or {}).get('content') or ''
    partes.append(bio)
    acts = d.get('activities-summary') or {}
    for sec, key in (('employments', 'employment-summary'), ('educations', 'education-summary')):
        for g in ((acts.get(sec) or {}).get('affiliation-group') or []):
            for s in g.get('summaries', []):
                s = s.get(key) or {}
                partes.append(s.get('role-title') or '')
                partes.append(((s.get('organization') or {}) or {}).get('name') or '')
    for w in ((acts.get('works') or {}).get('group') or [])[:25]:
        try:
            partes.append(w['work-summary'][0]['title']['title']['value'])
        except (KeyError, IndexError):
            pass

    blob = norm(' '.join(partes))
    arch_hits = sorted({t for t in ARCH_TERMS if t in blob})
    tem_conteudo = len(blob.strip()) > 20

    t_db, t_oc = tokens(nome_db), tokens(nome_orcid)
    inter = len(t_db & t_oc)
    nome_ok = inter >= 2 or (inter >= 1 and min(len(t_db), len(t_oc)) == 1)

    if not tem_conteudo:
        veredito = 'sem_dados' if nome_ok else 'sem_dados_nome_divergente'
    elif arch_hits and nome_ok:
        veredito = 'ok'
    elif arch_hits:
        veredito = 'nome_divergente'
    elif nome_ok:
        veredito = 'area_suspeita'
    else:
        veredito = 'SUSPEITO'
    return veredito, nome_orcid, len(arch_hits), ', '.join(arch_hits[:6])


ORDEM = {'SUSPEITO': 0, 'area_suspeita': 1, 'nome_divergente': 2,
         'sem_dados_nome_divergente': 3, 'sem_dados': 4, 'erro': 5, 'ok': 9}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--limite', type=int)
    ap.add_argument('--author-id', type=int)
    args = ap.parse_args()

    feitos = {}
    for arq in (OUT, OUT + '.parcial'):
        if os.path.isfile(arq):
            with open(arq) as fh:
                for row in csv.DictReader(fh):
                    if row.get('veredito') != 'erro':
                        feitos[row['orcid']] = row

    db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    q = ("SELECT id, givenname || ' ' || familyname, orcid FROM authors "
         "WHERE orcid IS NOT NULL AND orcid != ''")
    if args.author_id:
        q += f' AND id = {args.author_id}'
    rows = db.execute(q + ' ORDER BY id').fetchall()
    if args.limite:
        rows = [r for r in rows if r[2] not in feitos][:args.limite] + \
               [r for r in rows if r[2] in feitos]

    resultados = []
    novas = 0
    for aid, nome, orcid in rows:
        if orcid in feitos:
            resultados.append(feitos[orcid])
            continue
        try:
            veredito, nome_orcid, n_hits, hits = avaliar(orcid, nome)
        except Exception as e:
            veredito, nome_orcid, n_hits, hits = 'erro', '', 0, str(e)[:60]
        linha = {'author_id': aid, 'nome_db': nome, 'orcid': orcid,
                 'nome_orcid': nome_orcid, 'veredito': veredito,
                 'sinais_arquitetura': n_hits, 'termos': hits}
        resultados.append(linha)
        novo_arquivo = not os.path.isfile(OUT + '.parcial')
        with open(OUT + '.parcial', 'a', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(linha))
            if novo_arquivo:
                w.writeheader()
            w.writerow(linha)
            fh.flush()
        novas += 1
        if novas % 50 == 0:
            print(f'  ...{novas} verificados')
        time.sleep(THROTTLE)

    resultados.sort(key=lambda r: (ORDEM.get(r['veredito'], 5), -int(r.get('sinais_arquitetura') or 0)))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['author_id', 'nome_db', 'orcid', 'nome_orcid',
                                           'veredito', 'sinais_arquitetura', 'termos'])
        w.writeheader()
        w.writerows(resultados)

    from collections import Counter
    print(f'\n{len(resultados)} ORCIDs | novos verificados: {novas}')
    for v, c in Counter(r['veredito'] for r in resultados).most_common():
        print(f'  {v}: {c}')
    print(f'→ {OUT}')


if __name__ == '__main__':
    main()
