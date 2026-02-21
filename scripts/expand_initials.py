#!/usr/bin/env python3
"""Expande iniciais abreviadas nos givennames dos autores.

Fontes de dados (em ordem de prioridade):
  1. Banco do Pilotis (match local instantâneo)
  2. Busca web via Escavador/Google (para os restantes)
  3. Revisão manual do relatório gerado

Uso:
    python3 scripts/expand_initials.py --report        # Gera relatório dos autores com iniciais
    python3 scripts/expand_initials.py --pilotis       # Aplica matches do Pilotis
    python3 scripts/expand_initials.py --web           # Busca na web (requer internet)
    python3 scripts/expand_initials.py --apply FILE    # Aplica correções de um JSON revisado

O JSON de saída fica em /tmp/initials_report.json
"""

import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE, 'anais.db')
PILOTIS_DB = os.path.expanduser(
    '~/Dropbox/docomomo/26-27/financeiro/pilotis/dados/data/pilotis.db'
)
REPORT_PATH = '/tmp/initials_report.json'


def normalize(s):
    """Remove accents and lowercase."""
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.lower().strip()


def has_initials(givenname):
    """Check if givenname contains abbreviated initials."""
    return '.' in givenname


def get_authors_with_initials(db):
    """Return authors whose givenname has periods (initials)."""
    return db.execute("""
        SELECT a.id, a.givenname, a.familyname,
               COUNT(aa.article_id) as article_count
        FROM authors a
        JOIN article_author aa ON a.id = aa.author_id
        WHERE a.givenname LIKE '%.%'
        GROUP BY a.id
        ORDER BY COUNT(aa.article_id) DESC, a.familyname
    """).fetchall()


# ---------------------------------------------------------------------------
# Phase 1: Pilotis match
# ---------------------------------------------------------------------------

def load_pilotis_names():
    """Load full names from Pilotis database, indexed by normalized last name."""
    if not os.path.exists(PILOTIS_DB):
        print(f"AVISO: Pilotis DB não encontrado: {PILOTIS_DB}")
        return {}

    pdb = sqlite3.connect(PILOTIS_DB)
    people = pdb.execute("SELECT id, nome FROM pessoas").fetchall()
    pdb.close()

    by_lastname = defaultdict(list)
    for pid, nome in people:
        parts = nome.split()
        if len(parts) >= 2:
            lastname = parts[-1]
            by_lastname[normalize(lastname)].append((pid, nome))
    return by_lastname


def match_pilotis(author, pilotis_by_lastname):
    """Try to match an author with initials against Pilotis full names.

    Returns (new_givenname, pilotis_name) or (None, None).
    """
    aid, given, family, _ = author
    candidates = pilotis_by_lastname.get(normalize(family), [])
    if not candidates:
        return None, None

    given_parts = given.replace('.', '. ').split()
    given_parts = [p.strip() for p in given_parts if p.strip()]
    if not given_parts:
        return None, None

    matches = []
    for pid, pilotis_name in candidates:
        pparts = pilotis_name.split()
        if len(pparts) < 2:
            continue

        # Given parts from pilotis (all but last name), without particles
        p_given = pparts[:-1]
        p_given_no_particles = [
            p for p in p_given
            if p.lower() not in ('de', 'da', 'do', 'dos', 'das', 'e')
        ]

        # Check first initial matches
        if not p_given_no_particles:
            continue
        first_init = given_parts[0].replace('.', '')
        if not first_init:
            continue
        if not normalize(p_given_no_particles[0]).startswith(normalize(first_init[0])):
            continue

        # Check all initials
        g_initials = [p.replace('.', '') for p in given_parts if p.replace('.', '')]
        all_match = True
        for i, init in enumerate(g_initials):
            if i >= len(p_given_no_particles):
                break
            if len(init) <= 2:  # initial
                if not normalize(p_given_no_particles[i]).startswith(
                    normalize(init[0])
                ):
                    all_match = False
                    break
            else:  # full name part — must match exactly
                if normalize(init) != normalize(p_given_no_particles[i]):
                    all_match = False
                    break

        if all_match:
            matches.append((pid, pilotis_name))

    if len(matches) == 1:
        pilotis_name = matches[0][1]
        pparts = pilotis_name.split()
        # Build new givenname: all parts except the last (familyname)
        new_given = ' '.join(pparts[:-1])
        return new_given, pilotis_name

    return None, None


# ---------------------------------------------------------------------------
# Phase 2: Web search
# ---------------------------------------------------------------------------

def search_web_name(given, family):
    """Search Escavador for the full name, return candidates."""
    full_abbrev = f"{given} {family}".replace('.', '')
    query = f'"{full_abbrev}" site:escavador.com'
    url = (
        'https://www.google.com/search?'
        + urllib.parse.urlencode({'q': query, 'num': 5})
    )
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        # Extract names from Escavador results
        # Pattern: "Nome Completo - Escavador"
        names = re.findall(
            r'(?:>|")([A-ZÀ-Ý][a-zà-ý]+(?: (?:de |da |do |dos |das |e )?'
            r'[A-ZÀ-Ý][a-zà-ý]+)+)(?:\s*[-–—]\s*Escavador)',
            html,
        )
        return list(set(names))
    except Exception as e:
        return []


def search_lattes_name(given, family):
    """Search Lattes/Google for the full name."""
    # Build query with family name and first initial
    first_init = given.replace('.', '').strip().split()[0] if given.strip() else ''
    if not first_init:
        return []

    query = f'"{first_init}" "{family}" site:lattes.cnpq.br'
    url = (
        'https://www.google.com/search?'
        + urllib.parse.urlencode({'q': query, 'num': 5})
    )
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        # Lattes results often show full name
        names = re.findall(
            r'(?:>|")([A-ZÀ-Ý][a-zà-ý]+(?: (?:de |da |do |dos |das |e )?'
            r'[A-ZÀ-Ý][a-zà-ý]+)+)(?:\s*[-–—]\s*Currículo)',
            html,
        )
        return list(set(names))
    except Exception as e:
        return []


# ---------------------------------------------------------------------------
# Phase 3: Apply corrections
# ---------------------------------------------------------------------------

def apply_corrections(db, corrections):
    """Apply a list of (author_id, new_givenname) to the database.
    If the expanded name already exists as another author, merge instead of update."""
    cur = db.cursor()
    applied = 0
    merged = 0
    for aid, new_gn in corrections:
        old = cur.execute(
            "SELECT givenname, familyname FROM authors WHERE id = ?", (aid,)
        ).fetchone()
        if not old:
            continue
        old_gn, fn = old
        # Check if expanded name already exists as a different author
        existing = cur.execute(
            "SELECT id FROM authors WHERE givenname = ? AND familyname = ? AND id != ?",
            (new_gn, fn, aid)
        ).fetchone()
        if existing:
            canonical_id = existing[0]
            print(f"  [{aid}] {old_gn} {fn}  →  MERGE into [{canonical_id}] {new_gn} {fn}")
            # Move articles from dupe to canonical (skip duplicates)
            cur.execute(
                "UPDATE OR IGNORE article_author SET author_id = ? WHERE author_id = ?",
                (canonical_id, aid)
            )
            # Clean up any remaining (duplicates that were ignored)
            cur.execute("DELETE FROM article_author WHERE author_id = ?", (aid,))
            # Register variant
            cur.execute(
                "INSERT OR IGNORE INTO author_variants (author_id, givenname, familyname, source) VALUES (?, ?, ?, 'expand-merge')",
                (canonical_id, old_gn, fn)
            )
            # Delete dupe author
            cur.execute("DELETE FROM authors WHERE id = ?", (aid,))
            merged += 1
        else:
            print(f"  [{aid}] {old_gn} {fn}  →  {new_gn} {fn}")
            cur.execute(
                "UPDATE authors SET givenname = ? WHERE id = ?", (new_gn, aid)
            )
            applied += 1
    db.commit()
    print(f"\nAtualizados: {applied} autores, merges: {merged}")
    remaining = cur.execute(
        "SELECT COUNT(*) FROM authors WHERE givenname LIKE '%.%'"
    ).fetchone()[0]
    print(f"Restantes com iniciais: {remaining}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def cmd_report():
    """Generate a report of all authors with initials."""
    db = sqlite3.connect(DB_PATH)
    authors = get_authors_with_initials(db)
    db.close()

    report = []
    for aid, gn, fn, cnt in authors:
        report.append({
            'author_id': aid,
            'givenname': gn,
            'familyname': fn,
            'article_count': cnt,
            'status': 'pending',
        })

    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Relatório: {len(report)} autores com iniciais")
    print(f"Salvo em: {REPORT_PATH}")


def cmd_pilotis():
    """Match authors with initials against Pilotis and apply."""
    db = sqlite3.connect(DB_PATH)
    authors = get_authors_with_initials(db)

    pilotis = load_pilotis_names()
    if not pilotis:
        db.close()
        return

    corrections = []
    for author in authors:
        new_gn, pilotis_name = match_pilotis(author, pilotis)
        if new_gn:
            corrections.append((author[0], new_gn))
            print(
                f"  MATCH: [{author[0]}] {author[1]} {author[2]}  →  "
                f"{new_gn} {author[2]}  (Pilotis: {pilotis_name})"
            )

    if corrections:
        print(f"\n{len(corrections)} matches encontrados. Aplicando...")
        apply_corrections(db, corrections)
    else:
        print("Nenhum match do Pilotis encontrado.")

    db.close()


def cmd_web():
    """Search the web for full names of authors with initials."""
    db = sqlite3.connect(DB_PATH)
    authors = get_authors_with_initials(db)
    db.close()

    results = []
    total = len(authors)
    for i, (aid, gn, fn, cnt) in enumerate(authors):
        print(f"  [{i+1}/{total}] {gn} {fn}...", end=' ', flush=True)

        web_names = search_web_name(gn, fn)
        time.sleep(2)  # Respect rate limits

        if not web_names:
            web_names = search_lattes_name(gn, fn)
            time.sleep(2)

        # Filter by matching family name
        matching = [
            n for n in web_names
            if normalize(n.split()[-1]) == normalize(fn)
        ]

        if matching:
            print(f"→ {matching}")
        else:
            print("sem resultado")

        results.append({
            'author_id': aid,
            'givenname': gn,
            'familyname': fn,
            'article_count': cnt,
            'web_candidates': matching,
            'status': 'found' if matching else 'not_found',
        })

    out_path = '/tmp/initials_web_results.json'
    with open(out_path, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    found = sum(1 for r in results if r['status'] == 'found')
    print(f"\nResultados: {found}/{total} encontrados")
    print(f"Salvo em: {out_path}")


def cmd_apply(filepath):
    """Apply corrections from a reviewed JSON file.

    Expected format: list of objects with 'author_id' and 'new_givenname'.
    """
    with open(filepath) as f:
        data = json.load(f)

    corrections = [
        (item['author_id'], item['new_givenname'])
        for item in data
        if item.get('new_givenname')
    ]

    if not corrections:
        print("Nenhuma correção encontrada no arquivo.")
        return

    db = sqlite3.connect(DB_PATH)
    apply_corrections(db, corrections)
    db.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == '--report':
        cmd_report()
    elif cmd == '--pilotis':
        cmd_pilotis()
    elif cmd == '--web':
        cmd_web()
    elif cmd == '--apply':
        if len(sys.argv) < 3:
            print("Uso: --apply <arquivo.json>")
            sys.exit(1)
        cmd_apply(sys.argv[2])
    else:
        print(f"Comando desconhecido: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
