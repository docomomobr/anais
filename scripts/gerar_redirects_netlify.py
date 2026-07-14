#!/usr/bin/env python3
"""Gera _redirects (Netlify) e redirects.json (Cloudflare Pages _worker.js)
para publicacoes.docomomobrasil.com.

Fontes:
  1. Clone do repo docomomobr/publicacoes (meta refresh atual) — autoridade
     para o conjunto de URLs e destinos, incluindo /revista/*.
  2. docs/ojs_article_mapping.json — validação cruzada dos artigos.

Regras:
  - 1 linha exata por página existente no repo de meta refresh (301).
  - Para cada artigo: linhas splat cobrindo galley e download
    (/anais/article/view/{id}/* e /anais/article/download/{id}/*).
  - URL desconhecida → 404 honesto (página de cortesia), NUNCA redirect
    para a home (Google trata redirect-para-home em massa como soft-404).

Uso:
    python3 scripts/gerar_redirects_netlify.py CLONE_DIR SAIDA_DIR
"""

import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPING = os.path.join(BASE_DIR, 'docs', 'ojs_article_mapping.json')

REFRESH_RE = re.compile(r'http-equiv="refresh"[^>]*url=([^">]+)"', re.I)
CANONICAL_RE = re.compile(r'rel="canonical" href="([^"]+)"', re.I)


def extract_target(html_path):
    html = open(html_path, encoding='utf-8', errors='replace').read()
    m = REFRESH_RE.search(html) or CANONICAL_RE.search(html)
    return m.group(1).rstrip() if m else None


def main():
    clone, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)

    # 1. Varredura do clone: (rota, destino)
    routes = []
    for root, _dirs, files in os.walk(clone):
        if '.git' in root:
            continue
        if 'index.html' not in files:
            continue
        rel = os.path.relpath(root, clone)
        path = '/' if rel == '.' else '/' + rel.replace(os.sep, '/')
        target = extract_target(os.path.join(root, 'index.html'))
        if target:
            routes.append((path, target))
    routes.sort()

    # 2. Validação cruzada dos artigos contra o mapeamento canônico
    mapping = {str(m['ojs_id']): m for m in json.load(open(MAPPING))}
    art_re = re.compile(r'^/anais/article/view/(\d+)$')
    divergentes, sem_pagina = [], []
    ids_no_clone = set()
    for path, target in routes:
        m = art_re.match(path)
        if not m:
            continue
        ojs_id = m.group(1)
        ids_no_clone.add(ojs_id)
        canon = mapping.get(ojs_id)
        if canon and f"/{canon['article_id']}/" not in target:
            divergentes.append((ojs_id, target, canon['article_id']))
    for ojs_id in mapping:
        if ojs_id not in ids_no_clone:
            sem_pagina.append(ojs_id)

    # 3. Emissão do _redirects
    lines = [
        '# Redirects 301: publicacoes.docomomobrasil.com -> destinos atuais',
        '# Gerado por scripts/gerar_redirects_netlify.py — NAO editar a mao.',
        '# Fallback: URL desconhecida cai no 404.html (sem redirect p/ home).',
        '',
    ]
    for path, target in routes:
        lines.append(f'{path} {target} 301')
        m = art_re.match(path)
        if m:
            # galley (view/{id}/{galley}) e download (download/{id}/...)
            lines.append(f'{path}/* {target} 301')
            lines.append(f'/anais/article/download/{m.group(1)}/* {target} 301')

    # 3b. Entradas do mapping sem página no clone (ex.: front matter):
    # redirecionar para a página da edição correspondente.
    AMBITO = {'sdbr': 'brasil', 'sdnne': 'nne', 'sdsul': 'sul', 'sdpr': 'sul',
              'sdmg': 'se', 'sdrj': 'se', 'sdsp': 'se', 'idc': 'internacional'}
    for ojs_id in sorted(sem_pagina, key=int):
        entry = mapping[ojs_id]
        slug = entry['seminar_slug']
        ambito = next(v for k, v in AMBITO.items() if slug.startswith(k))
        if entry.get('article_id'):
            target = f"https://anais.docomomobrasil.com/{ambito}/{slug}/{entry['article_id']}/"
        else:
            target = f'https://anais.docomomobrasil.com/{ambito}/{slug}/'
        for prefix in (f'/anais/article/view/{ojs_id}',):
            lines.append(f'{prefix} {target} 301')
            lines.append(f'{prefix}/* {target} 301')
        lines.append(f'/anais/article/download/{ojs_id}/* {target} 301')

    out = os.path.join(outdir, '_redirects')
    with open(out, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    # redirects.json para o _worker.js (Cloudflare Pages):
    # exact: rota exata → destino; article: ojs_id → destino (cobre
    # view/{id}/qualquer-galley e download/{id}/qualquer-coisa)
    exact, article = {}, {}
    for ln in lines:
        if not ln or ln.startswith('#'):
            continue
        path, target, _ = ln.rsplit(' ', 2)[0], ln.split(' ')[1], None
        path, target = ln.split(' ')[0], ln.split(' ')[1]
        if path.endswith('/*'):
            import re as _re
            m = _re.match(r'/anais/article/(?:view|download)/(\d+)/\*$', path)
            if m:
                article[m.group(1)] = target
            continue
        exact[path] = target
    jout = os.path.join(outdir, 'redirects.json')
    with open(jout, 'w') as f:
        json.dump({'exact': exact, 'article': article}, f, ensure_ascii=False)
    print(f'{len(exact)} rotas exatas + {len(article)} artigos → {jout}')

    print(f'{len(routes)} rotas no clone → {len(lines) - 4} linhas em {out}')
    print(f'artigos no clone: {len(ids_no_clone)} | no mapping canônico: {len(mapping)}')
    if divergentes:
        print(f'DIVERGENTES ({len(divergentes)}):')
        for d in divergentes[:10]:
            print('  ', d)
    if sem_pagina:
        print(f'no mapping mas SEM página no clone ({len(sem_pagina)}): {sem_pagina[:10]}')
    if not divergentes and not sem_pagina:
        print('validação cruzada: OK (0 divergências)')


if __name__ == '__main__':
    main()
