#!/usr/bin/env python3
"""
Normaliza maiúsculas/minúsculas nos títulos e subtítulos conforme norma brasileira.
Usa o módulo dict/ (dict.db) como dicionário de nomes próprios.

ATENÇÃO: Todos os dados de dicionário (nomes, siglas, lugares, movimentos,
toponímicos, expressões) residem no dict.db. NUNCA adicionar listas de
palavras diretamente neste script. Para adicionar entradas: editar
dict/init_db.py e rodar --reset, ou inserir direto no dict.db.

Uso:
    python3 scripts/normalizar_maiusculas.py [--slug SLUG] [--dry-run]
"""

import argparse
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')

# Importar módulo dict/
sys.path.insert(0, BASE_DIR)
from dict.normalizar import normalizar_texto, load_dict, stats


def normalizar_seminario(conn, slug, dry_run=False):
    """Normaliza títulos/subtítulos de um seminário no banco."""
    rows = conn.execute(
        'SELECT id, title, subtitle FROM articles WHERE seminar_slug = ? ORDER BY id',
        (slug,)
    ).fetchall()

    alterados = 0
    for art_id, old_t, old_s in rows:
        new_t = normalizar_texto(old_t, eh_subtitulo=False)
        new_s = normalizar_texto(old_s, eh_subtitulo=True) if old_s else old_s

        if new_t != old_t or new_s != old_s:
            alterados += 1
            if new_t != old_t:
                print(f'  T: {old_t}')
                print(f'  →  {new_t}')
            if old_s and new_s != old_s:
                print(f'  S: {old_s}')
                print(f'  →  {new_s}')
            print()

            if not dry_run:
                conn.execute(
                    'UPDATE articles SET title = ?, subtitle = ? WHERE id = ?',
                    (new_t, new_s, art_id))

    if not dry_run:
        conn.commit()

    status = '(dry-run)' if dry_run else ''
    print(f'=== {slug}: {alterados}/{len(rows)} artigos alterados {status} ===\n')
    return alterados


def main():
    parser = argparse.ArgumentParser(description='Normalizar maiúsculas/minúsculas')
    parser.add_argument('--slug', help='Normalizar apenas este seminário')
    parser.add_argument('--dry-run', action='store_true', help='Apenas mostrar, não alterar')
    args = parser.parse_args()

    load_dict()
    s = stats()
    print(f'Dicionário: {s["siglas"]} siglas, {s["nomes"]} nomes, '
          f'{s["lugares"]} lugares, {s["areas"]} áreas, '
          f'{s["movimentos"]} movimentos, {s["toponimicos"]} toponímicos, '
          f'{s["expressoes"]} expressões\n')

    conn = sqlite3.connect(DB_PATH)

    if args.slug:
        slugs = [args.slug]
    else:
        # Apenas regionais
        rows = conn.execute(
            "SELECT slug FROM seminars WHERE slug NOT LIKE 'sdbr%' ORDER BY volume, number"
        ).fetchall()
        slugs = [r[0] for r in rows]

    total = 0
    for slug in slugs:
        n = normalizar_seminario(conn, slug, dry_run=args.dry_run)
        total += n

    print(f'Total: {total} artigos alterados em {len(slugs)} seminários')
    conn.close()


if __name__ == '__main__':
    main()
