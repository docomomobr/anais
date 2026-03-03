#!/usr/bin/env python3
"""
Normaliza capitalização de title_en e subtitle_en para Title Case inglês
(Chicago Manual of Style / APA).

Usa a biblioteca `titlecase` com callback para preservar acrônimos (IPHAN,
UNESCO, CIAM) e nomes próprios (Brasília, Niemeyer, Le Corbusier) do dict.db.

Uso:
    python3 scripts/normalizar_titulos_en.py --slug sdbr08 --dry-run
    python3 scripts/normalizar_titulos_en.py --slug sdbr08
"""

import argparse
import os
import re
import sqlite3
import sys

from titlecase import titlecase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')

# Importar módulo dict/ para carregar acrônimos e nomes próprios
sys.path.insert(0, BASE_DIR)
from dict.normalizar import load_dict, stats, _SIGLAS, _NOMES, _LUGARES, _EXPRESSOES


# Palavras curtas em inglês que coincidem com siglas PT do dict.db
# Devem ser tratadas como preposições/artigos, não como siglas
EN_SMALL_WORDS = {
    'to', 'am', 'al', 'se', 'go', 'ma', 'mg', 'mt', 'ms', 'pa', 'pi',
    'pr', 'pe', 'rj', 'rn', 'rs', 'ro', 'rr', 'sc', 'sp', 'ap', 'ac',
}


def make_titlecase_callback():
    """Cria callback para a biblioteca titlecase que preserva formas canônicas do dict.db."""

    def callback(word, **kwargs):
        # Remover pontuação ao redor para lookup
        match = re.match(r'^([^\w]*)(\w+(?:[-/]\w+)*)([^\w]*)$', word, re.UNICODE)
        if not match:
            return None

        prefix, core, suffix = match.groups()
        core_lower = core.lower()
        core_upper = core.upper()

        # Siglas: preservar ALL CAPS (IPHAN, UNESCO, FAU-USP, CIAM)
        # Mas excluir palavras curtas que coincidem com siglas de estados PT
        if core_lower in _SIGLAS and core_lower not in EN_SMALL_WORDS:
            return prefix + core_upper + suffix

        # Para palavras hifenizadas (FAU-USP), verificar cada parte
        if '-' in core:
            parts = core.split('-')
            parts_lower = [p.lower() for p in parts]
            # Se todas as partes são siglas, preservar como sigla
            if all(p in _SIGLAS for p in parts_lower):
                return prefix + '-'.join(p.upper() for p in parts) + suffix
            # Se alguma parte é sigla, preservar essa parte e titlecase as outras
            result_parts = []
            for p in parts:
                if p.lower() in _SIGLAS:
                    result_parts.append(p.upper())
                elif p.lower() in _NOMES:
                    result_parts.append(_NOMES[p.lower()])
                elif p.lower() in _LUGARES:
                    result_parts.append(_LUGARES[p.lower()])
                else:
                    result_parts.append(None)  # let titlecase handle it
            if any(r is not None for r in result_parts):
                # Fill in Nones with titlecase's default
                for i, r in enumerate(result_parts):
                    if r is None:
                        result_parts[i] = parts[i].capitalize()
                return prefix + '-'.join(result_parts) + suffix

        # Nomes próprios: preservar forma canônica (Niemeyer, Corbusier)
        if core_lower in _NOMES:
            return prefix + _NOMES[core_lower] + suffix

        # Lugares: preservar forma canônica (Brasília, São Paulo)
        if core_lower in _LUGARES:
            return prefix + _LUGARES[core_lower] + suffix

        # Retornar None para deixar titlecase decidir
        return None

    return callback


def apply_expressions(text):
    """Aplica expressões consolidadas do dict.db após o titlecase."""
    for expr, canonical in _EXPRESSOES.items():
        # Só aplicar expressões que façam sentido em inglês (nomes compostos)
        # Pular expressões puramente em português
        pattern = re.compile(r'\b' + re.escape(expr) + r'\b', re.IGNORECASE)
        text = pattern.sub(canonical, text)
    return text


def normalizar_titulo_en(text):
    """Normaliza um título EN para Title Case."""
    if not text:
        return text

    callback = make_titlecase_callback()
    result = titlecase(text, callback=callback)

    # Aplicar expressões consolidadas
    result = apply_expressions(result)

    return result


def normalizar_subtitulo_en(text):
    """Normaliza um subtítulo EN para Title Case.

    Mesmo tratamento do título — em inglês, subtítulos também usam Title Case
    (diferente do português, onde subtítulo começa com minúscula).
    """
    if not text:
        return text
    return normalizar_titulo_en(text)


def normalizar_seminario(conn, slug, dry_run=False):
    """Normaliza title_en/subtitle_en de um seminário no banco."""
    rows = conn.execute(
        '''SELECT id, title_en, subtitle_en FROM articles
           WHERE seminar_slug = ? AND (title_en IS NOT NULL AND title_en != '')
           ORDER BY id''',
        (slug,)
    ).fetchall()

    alterados = 0
    total = len(rows)

    for art_id, old_t, old_s in rows:
        new_t = normalizar_titulo_en(old_t)
        new_s = normalizar_subtitulo_en(old_s) if old_s else old_s

        if new_t != old_t or new_s != old_s:
            alterados += 1
            if new_t != old_t:
                print(f'  {art_id}')
                print(f'    T: {old_t}')
                print(f'    →  {new_t}')
            if old_s and new_s != old_s:
                print(f'    S: {old_s}')
                print(f'    →  {new_s}')
            print()

            if not dry_run:
                conn.execute(
                    'UPDATE articles SET title_en = ?, subtitle_en = ? WHERE id = ?',
                    (new_t, new_s, art_id))

    if not dry_run:
        conn.commit()

    status = '(dry-run)' if dry_run else ''
    print(f'=== {slug}: {alterados}/{total} títulos EN alterados {status} ===\n')
    return alterados


def main():
    parser = argparse.ArgumentParser(description='Normalizar títulos EN para Title Case')
    parser.add_argument('--slug', help='Normalizar apenas este seminário')
    parser.add_argument('--dry-run', action='store_true', help='Apenas mostrar, não alterar')
    args = parser.parse_args()

    load_dict()
    s = stats()
    print(f'Dicionário: {s["siglas"]} siglas, {s["nomes"]} nomes, '
          f'{s["lugares"]} lugares, {s["expressoes"]} expressões\n')

    conn = sqlite3.connect(DB_PATH)

    if args.slug:
        slugs = [args.slug]
    else:
        rows = conn.execute(
            "SELECT slug FROM seminars ORDER BY volume, number"
        ).fetchall()
        slugs = [r[0] for r in rows]

    total = 0
    for slug in slugs:
        n = normalizar_seminario(conn, slug, dry_run=args.dry_run)
        total += n

    print(f'Total: {total} títulos EN alterados em {len(slugs)} seminários')
    conn.close()


if __name__ == '__main__':
    main()
