#!/usr/bin/env python3
"""
Limpeza automatizada de referências bibliográficas no anais.db.

Operações:
  1. Split de refs concatenadas via convenção ABNT de underscores (______):
     - Quando o mesmo autor tem múltiplas obras, ABNT usa 6+ underscores
       em vez de repetir o nome. O pdftotext extrai tudo em uma única linha.
     - Detecta underscores no meio do texto e separa em refs individuais.
  2. Backfill de nomes de autores:
     - Refs que começam com ______ recebem o nome do autor da ref anterior.
  3. Join de URLs órfãs:
     - URLs soltas em linha separada são juntadas à ref anterior.

Uso:
    python3 scripts/clean_references.py [--slug SLUG] [--dry-run]
    python3 scripts/clean_references.py --slug sdnne01 --dry-run
"""

import argparse
import json
import os
import re
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')

# Regex para detectar underscores ABNT (3+ underscores)
UNDERSCORE_MID = re.compile(r'\s+(_{3,})')
UNDERSCORE_START = re.compile(r'^(_{3,})[.,]?\s*(.*)', re.DOTALL)

# URLs órfãs (ref é só URL ou começa com "Disponível em" / "Acesso em" / URL)
ORPHAN_URL = re.compile(r'^(https?://|www\.|Disponível\s+em\s*$|Acesso\s+em)', re.IGNORECASE)
BARE_URL = re.compile(r'^https?://\S+$')


def extract_author(ref):
    """Extrai nome do autor do início de uma ref ABNT.

    Retorna string como "SOBRENOME, Nome." ou "ORGANIZAÇÃO." ou None.
    """
    # SOBRENOME, Nome. ou SOBRENOME, INICIAIS.
    m = re.match(r'^([A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑA-záéíóúàâêôãõçñ\s,\.]+?)\.\s', ref)
    if m:
        candidate = m.group(1)
        if ',' in candidate:
            return candidate + '.'
    # ORGANIZAÇÃO.
    m = re.match(r'^([A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑA-záéíóúàâêôãõçñ\s]+?)\.\s', ref)
    if m:
        return m.group(1) + '.'
    return None


def split_underscores(refs):
    """Fase 1: separa refs concatenadas via underscores ABNT.

    Retorna (new_refs, split_count).
    """
    new_refs = []
    split_count = 0

    for ref in refs:
        ref = ref.strip()
        if not ref:
            continue

        parts = UNDERSCORE_MID.split(ref)

        if len(parts) > 1:
            # parts = [text_before, underscores, text_after, underscores, text_after, ...]
            first = parts[0].strip()
            if first:
                new_refs.append(first)

            for j in range(1, len(parts), 2):
                underscore = parts[j]
                text_after = parts[j + 1].strip() if j + 1 < len(parts) else ''
                if text_after:
                    new_refs.append(underscore + text_after)
                    split_count += 1
        else:
            new_refs.append(ref)

    return new_refs, split_count


def backfill_authors(refs):
    """Fase 2: substitui ______ iniciais pelo nome do autor da ref anterior.

    Retorna (new_refs, backfill_count).
    """
    new_refs = list(refs)
    backfill_count = 0

    for i in range(len(new_refs)):
        ref = new_refs[i].strip()
        m = UNDERSCORE_START.match(ref)
        if m and i > 0:
            # Busca autor na ref anterior (pode haver cadeia de ______)
            author = None
            for j in range(i - 1, -1, -1):
                prev = new_refs[j].strip()
                if not UNDERSCORE_START.match(prev):
                    author = extract_author(prev)
                    break
            if author:
                rest = m.group(2)
                new_refs[i] = author + ' ' + rest
                backfill_count += 1

    return new_refs, backfill_count


def join_orphan_urls(refs):
    """Fase 3: junta URLs órfãs à ref anterior.

    Retorna (new_refs, join_count).
    """
    new_refs = []
    join_count = 0

    for ref in refs:
        ref = ref.strip()
        if not ref:
            continue

        if new_refs and BARE_URL.match(ref):
            # URL solta → juntar à anterior
            prev = new_refs[-1].rstrip()
            if prev.endswith(('em', 'em:', 'in', 'in:')):
                new_refs[-1] = prev + ' ' + ref
            else:
                new_refs[-1] = prev + ' ' + ref
            join_count += 1
        elif new_refs and ref.startswith(('Disponível em', 'Acesso em', 'Available at')):
            # Continuação de "Disponível em..." → juntar
            new_refs[-1] = new_refs[-1].rstrip() + ' ' + ref
            join_count += 1
        else:
            new_refs.append(ref)

    return new_refs, join_count


def clean_article_refs(refs):
    """Aplica todas as fases de limpeza em sequência.

    Retorna (cleaned_refs, stats_dict).
    """
    stats = {'split': 0, 'backfill': 0, 'join': 0}

    refs, n = split_underscores(refs)
    stats['split'] = n

    refs, n = backfill_authors(refs)
    stats['backfill'] = n

    refs, n = join_orphan_urls(refs)
    stats['join'] = n

    return refs, stats


def main():
    parser = argparse.ArgumentParser(
        description='Limpeza automatizada de referências (underscores ABNT, URLs órfãs)')
    parser.add_argument('--slug', help='Processar apenas este seminário')
    parser.add_argument('--dry-run', action='store_true', help='Mostrar mudanças sem aplicar')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    where = "WHERE references_ IS NOT NULL AND references_ != '' AND references_ != '[]'"
    params = []
    if args.slug:
        where += " AND seminar_slug = ?"
        params.append(args.slug)

    cur.execute(
        f"SELECT id, file, seminar_slug, references_ FROM articles {where} ORDER BY file",
        params
    )
    articles = cur.fetchall()

    totals = {'articles': 0, 'split': 0, 'backfill': 0, 'join': 0,
              'refs_before': 0, 'refs_after': 0}

    for aid, fname, slug, refs_text in articles:
        refs = json.loads(refs_text)
        totals['refs_before'] += len(refs)

        cleaned, stats = clean_article_refs(refs)
        totals['refs_after'] += len(cleaned)

        changed = stats['split'] > 0 or stats['backfill'] > 0 or stats['join'] > 0

        if changed:
            totals['articles'] += 1
            totals['split'] += stats['split']
            totals['backfill'] += stats['backfill']
            totals['join'] += stats['join']

            if args.dry_run:
                changes = []
                if stats['split']:
                    changes.append(f"{stats['split']} splits")
                if stats['backfill']:
                    changes.append(f"{stats['backfill']} backfills")
                if stats['join']:
                    changes.append(f"{stats['join']} joins")
                print(f"  {fname}: {', '.join(changes)}")
            else:
                cur.execute("UPDATE articles SET references_ = ? WHERE id = ?",
                            (json.dumps(cleaned, ensure_ascii=False), aid))

    if not args.dry_run:
        conn.commit()

    print(f"\n=== Limpeza de referências ===")
    if args.slug:
        print(f"Seminário: {args.slug}")
    print(f"Artigos modificados: {totals['articles']}")
    print(f"Refs antes: {totals['refs_before']}")
    print(f"Refs depois: {totals['refs_after']}")
    print(f"Underscores split: {totals['split']}")
    print(f"Autores backfilled: {totals['backfill']}")
    print(f"URLs juntadas: {totals['join']}")
    print(f"{'DRY RUN' if args.dry_run else 'APLICADO'}")

    conn.close()


if __name__ == '__main__':
    main()
