#!/usr/bin/env python3
"""Verifica problemas comuns de qualidade nos dados do anais.db.

Detecta padrões aprendidos nas revisões humanas:
- Abreviações de estado (UF) em minúscula
- Intervalos de datas com hífen em vez de en-dash
- Nomes de edifícios/instituições que deveriam ser capitalizados
- Keywords com prefixos numéricos
- Familynames com múltiplas palavras (possível erro de parsing)
- Bios com whitespace excessivo

Uso:
    python3 scripts/check_quality.py                    # todos os regionais
    python3 scripts/check_quality.py --slug sdnne10     # um seminário
    python3 scripts/check_quality.py --all               # todos (inclui nacionais)
    python3 scripts/check_quality.py --fix               # aplica correções automáticas
"""

import argparse
import json
import os
import re
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')

STATES = frozenset({
    'ac', 'al', 'am', 'ap', 'ba', 'ce', 'df', 'es', 'go', 'ma', 'mg', 'ms',
    'mt', 'pa', 'pb', 'pe', 'pi', 'pr', 'rj', 'rn', 'ro', 'rr', 'rs', 'sc',
    'sp', 'to',
})

# Palavras que precedem nomes próprios → capitalizar
BUILDING_GENERICS = [
    'edifício', 'escola', 'parque', 'igreja', 'teatro', 'museu', 'palácio',
    'hospital', 'residência', 'casa', 'conjunto', 'centro', 'vila', 'praça',
    'avenida', 'terminal', 'estação', 'instituto',
]


def check_lowercase_uf(val):
    """Encontra UFs em minúscula após separador (-, /, parênteses)."""
    fixes = []
    # Padrão: separador + 2 letras minúsculas que sejam UF válida
    for m in re.finditer(r'([-–/]\s*)([a-z]{2})(\s*[)\s,;.!?\']|$)', val):
        if m.group(2) in STATES:
            fixes.append((m.start(2), m.end(2), m.group(2).upper()))
    for m in re.finditer(r'(\(\s*)([a-z]{2})(\s*\))', val):
        if m.group(2) in STATES:
            fixes.append((m.start(2), m.end(2), m.group(2).upper()))
    return fixes


def check_date_ranges(val):
    """Encontra intervalos YYYY-YYYY ou YYYY-YY com hífen em vez de en-dash."""
    fixes = []
    for m in re.finditer(r'(\d{4})-(\d{2,4})\b', val):
        year2 = int(m.group(2))
        # Verificar que é um intervalo de datas plausível
        if year2 >= 18 or (year2 >= 0 and year2 <= 99):
            fixes.append((m.start() + 4, m.start() + 5, '–'))
    return fixes


def check_building_names(val):
    """Encontra nomes de edifícios/instituições com genérico em minúscula."""
    issues = []
    for generic in BUILDING_GENERICS:
        pattern = re.compile(r'\b(' + re.escape(generic) + r')\s+([A-Z])', re.UNICODE)
        for m in pattern.finditer(val):
            # Verificar que não está no início da frase (já maiúscula)
            pos = m.start()
            if pos == 0:
                continue
            issues.append(f'{generic}→{generic.capitalize()} ({m.group()}...)')
    return issues


def check_numbered_keywords(val):
    """Encontra keywords com prefixos numéricos."""
    try:
        kws = json.loads(val)
        bad = [kw for kw in kws if kw and re.match(r'^\d+[.)\-]', kw.strip())]
        return bad
    except (json.JSONDecodeError, TypeError):
        return []


def check_multiword_familyname(givenname, familyname):
    """Verifica familynames com 3+ palavras (possível erro)."""
    words = familyname.split()
    if len(words) >= 3:
        return True
    return False


def check_bio_whitespace(bio):
    """Verifica bios com whitespace excessivo."""
    if bio and '  ' in bio:
        return True
    return False


def apply_text_fixes(val, fixes):
    """Aplica fixes (start, end, replacement) a um texto, do fim para o início."""
    result = val
    for start, end, repl in sorted(fixes, reverse=True):
        result = result[:start] + repl + result[end:]
    return result


def main():
    parser = argparse.ArgumentParser(description='Verificar qualidade dos dados')
    parser.add_argument('--slug', help='Verificar apenas este seminário')
    parser.add_argument('--all', action='store_true', help='Incluir nacionais')
    parser.add_argument('--fix', action='store_true', help='Aplicar correções automáticas (UF, en-dash)')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.slug:
        slugs = [args.slug]
    elif args.all:
        slugs = [r['slug'] for r in conn.execute('SELECT slug FROM seminars ORDER BY volume, number')]
    else:
        slugs = [r['slug'] for r in conn.execute(
            "SELECT slug FROM seminars WHERE slug NOT LIKE 'sdbr%' ORDER BY volume, number"
        )]

    total_issues = 0
    total_fixed = 0

    for slug in slugs:
        articles = conn.execute(
            'SELECT id, title, subtitle, keywords, keywords_en FROM articles WHERE seminar_slug=? ORDER BY id',
            (slug,)
        ).fetchall()

        slug_issues = 0

        for art in articles:
            for field in ['title', 'subtitle']:
                val = art[field]
                if not val:
                    continue

                # UFs minúsculas
                uf_fixes = check_lowercase_uf(val)
                if uf_fixes:
                    new_val = apply_text_fixes(val, uf_fixes)
                    ufs = ', '.join(f.upper() for _, _, f in uf_fixes)
                    print(f'  UF  {art["id"]} {field}: {ufs}')
                    print(f'       {val[:120]}')
                    slug_issues += 1
                    if args.fix:
                        conn.execute(f'UPDATE articles SET {field}=? WHERE id=?', (new_val, art['id']))
                        total_fixed += 1

                # En-dash
                dash_fixes = check_date_ranges(val)
                if dash_fixes:
                    new_val = apply_text_fixes(val, dash_fixes)
                    print(f'  DASH {art["id"]} {field}: {val[:120]}')
                    slug_issues += 1
                    if args.fix:
                        # Re-read in case UF fix already applied
                        current = conn.execute(f'SELECT {field} FROM articles WHERE id=?', (art['id'],)).fetchone()[0]
                        new_val = apply_text_fixes(current, check_date_ranges(current))
                        conn.execute(f'UPDATE articles SET {field}=? WHERE id=?', (new_val, art['id']))
                        total_fixed += 1

                # Nomes de edifícios (apenas alerta, não auto-fix)
                bldg = check_building_names(val)
                if bldg:
                    for b in bldg:
                        print(f'  BLDG {art["id"]} {field}: {b}')
                    slug_issues += len(bldg)

            # Keywords numeradas
            for kfield in ['keywords', 'keywords_en']:
                bad_kws = check_numbered_keywords(art[kfield])
                if bad_kws:
                    print(f'  KW#  {art["id"]} {kfield}: {bad_kws}')
                    slug_issues += 1

        # Autores com familyname multi-palavra
        authors = conn.execute('''
            SELECT DISTINCT au.id, au.givenname, au.familyname
            FROM authors au JOIN article_author aa ON aa.author_id=au.id
            JOIN articles a ON a.id=aa.article_id
            WHERE a.seminar_slug=?
        ''', (slug,)).fetchall()

        for au in authors:
            if check_multiword_familyname(au['givenname'], au['familyname']):
                print(f'  NAME {slug} author {au["id"]}: {au["givenname"]} | {au["familyname"]}')
                slug_issues += 1

        # Bios com whitespace
        bios = conn.execute('''
            SELECT aa.article_id, au.givenname, au.familyname, aa.bio
            FROM article_author aa JOIN authors au ON au.id=aa.author_id
            JOIN articles a ON a.id=aa.article_id
            WHERE a.seminar_slug=? AND aa.bio IS NOT NULL
        ''', (slug,)).fetchall()

        for b in bios:
            if check_bio_whitespace(b['bio']):
                print(f'  BIO  {b["article_id"]}: {b["givenname"]} {b["familyname"]} — whitespace excessivo')
                slug_issues += 1

        if slug_issues:
            print(f'  === {slug}: {slug_issues} problemas ===\n')
        total_issues += slug_issues

    if args.fix:
        conn.commit()
        print(f'\nTotal: {total_issues} problemas encontrados, {total_fixed} corrigidos automaticamente')
    else:
        print(f'\nTotal: {total_issues} problemas encontrados')
        if total_issues:
            print('Use --fix para aplicar correções automáticas (UF, en-dash)')

    conn.close()


if __name__ == '__main__':
    main()
