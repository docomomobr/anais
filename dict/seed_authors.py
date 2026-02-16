#!/usr/bin/env python3
"""
Importa nomes dos autores de um banco SQLite como entradas 'nome' no dict.db.

Lê a tabela authors (givenname, familyname) e insere cada parte do nome
como entrada de capitalização. Não sobrescreve entradas manuais existentes.

Uso:
    python3 dict/seed_authors.py                        # usa anais.db
    python3 dict/seed_authors.py --source outro.db      # usa outro banco
    python3 dict/seed_authors.py --source anais.db --table authors
"""

import argparse
import os
import re
import sqlite3
import unicodedata

DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DB = os.path.join(DIR, 'dict.db')
DEFAULT_SOURCE = os.path.join(os.path.dirname(DIR), 'anais.db')

# Partículas que não são nomes próprios
PARTICULAS = {'de', 'da', 'do', 'dos', 'das', 'e', 'del', 'van', 'von', 'di'}

# Palavras curtas demais ou genéricas para serem nomes
SKIP = {'a', 'o', 'as', 'os', 'em', 'no', 'na', 'um', 'ao', 'se', 'que', 'com',
        'por', 'para', 'ou', 'mas', 'não', 'sem', 'seu', 'sua', 'mais', 'há',
        'já', 'até', 'entre', 'sobre', 'só', 'bem', 'mal', 'tão', 'nem', 'pois',
        'como', 'qual', 'cada', 'toda', 'todo', 'esse', 'essa', 'este', 'esta',
        # Adjetivos/substantivos comuns que aparecem em nomes compostos
        # mas não devem ser tratados como nomes próprios standalone
        'uma', 'cidade', 'verde', 'branco', 'negro', 'maior', 'menor',
        'discussão', 'intervenções', 'alguns', 'alto', 'baixo',
        'filho', 'neto', 'neta', 'sobrinho', 'sobrinha'}


def is_initial(word):
    """Detecta iniciais como M., A.B., M.B.C."""
    return bool(re.match(r'^[A-Z]\.?([A-Z]\.?)*$', word))


def extract_name_parts(givenname, familyname):
    """Extrai partes capitalizáveis de um nome completo."""
    parts = set()
    for field in [givenname, familyname]:
        if not field:
            continue
        for word in field.split():
            # Limpar pontuação
            clean = re.sub(r'[^\w]', '', word, flags=re.UNICODE)
            if not clean or len(clean) < 2:
                continue
            low = clean.lower()
            if low in PARTICULAS or low in SKIP:
                continue
            if is_initial(clean):
                continue
            # Manter capitalização original como canônica
            canonical = clean[0].upper() + clean[1:]
            parts.add((low, canonical))
    return parts


def seed(source_db, table='authors', gn_col='givenname', fn_col='familyname'):
    if not os.path.exists(DICT_DB):
        print(f'ERRO: {DICT_DB} não existe. Rode init_db.py primeiro.')
        return

    if not os.path.exists(source_db):
        print(f'ERRO: {source_db} não existe.')
        return

    src = sqlite3.connect(source_db)
    rows = src.execute(f'SELECT {gn_col}, {fn_col} FROM {table}').fetchall()
    src.close()

    all_parts = set()
    for gn, fn in rows:
        all_parts.update(extract_name_parts(gn, fn))

    dict_conn = sqlite3.connect(DICT_DB)

    # Não sobrescrever entradas manuais ou de outras categorias
    existing = set(
        r[0] for r in dict_conn.execute('SELECT word FROM dict_names').fetchall()
    )

    added = 0
    for word, canonical in sorted(all_parts):
        if word not in existing:
            dict_conn.execute(
                'INSERT INTO dict_names (word, category, canonical, source) '
                'VALUES (?, ?, ?, ?)',
                (word, 'nome', canonical, 'autores'))
            added += 1

    dict_conn.commit()
    total = dict_conn.execute("SELECT COUNT(*) FROM dict_names WHERE category='nome'").fetchone()[0]
    dict_conn.close()

    print(f'Autores lidos: {len(rows)}')
    print(f'Partes de nome extraídas: {len(all_parts)}')
    print(f'Já existentes: {len(all_parts) - added}')
    print(f'Adicionadas: {added}')
    print(f'Total nomes no dict: {total}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Importar nomes de autores para dict.db')
    parser.add_argument('--source', default=DEFAULT_SOURCE,
                        help=f'Banco fonte (default: {DEFAULT_SOURCE})')
    parser.add_argument('--table', default='authors', help='Tabela de autores')
    parser.add_argument('--givenname', default='givenname', help='Coluna do nome')
    parser.add_argument('--familyname', default='familyname', help='Coluna do sobrenome')
    args = parser.parse_args()
    seed(args.source, args.table, args.givenname, args.familyname)
