#!/usr/bin/env python3
"""
Gera dump SQL do dict.db para versionamento no git.

Uso:
    python3 dict/dump_db.py
"""

import os
import sqlite3

DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DIR, 'dict.db')
SQL_PATH = os.path.join(DIR, 'dict.sql')


def dump():
    if not os.path.exists(DB_PATH):
        print(f'ERRO: {DB_PATH} não existe.')
        return

    conn = sqlite3.connect(DB_PATH)

    with open(SQL_PATH, 'w', encoding='utf-8') as f:
        for line in conn.iterdump():
            f.write(line + '\n')

    conn.close()

    total = os.path.getsize(SQL_PATH)
    print(f'→ {SQL_PATH} ({total:,} bytes)')


if __name__ == '__main__':
    dump()
