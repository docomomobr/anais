#!/usr/bin/env python3
"""Gera anais.sql a partir de anais.db (dump completo)."""

import sqlite3
import os
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE, 'anais.db')
SQL_PATH = os.path.join(BASE, 'anais.sql')


def main():
    if not os.path.exists(DB_PATH):
        print(f'Banco não encontrado: {DB_PATH}')
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    with open(SQL_PATH, 'w', encoding='utf-8') as f:
        for line in conn.iterdump():
            f.write(line + '\n')

    conn.close()

    size = os.path.getsize(SQL_PATH)
    if size > 1_000_000:
        print(f'Dump gerado: {SQL_PATH} ({size / 1_000_000:.1f} MB)')
    else:
        print(f'Dump gerado: {SQL_PATH} ({size / 1_000:.1f} KB)')


if __name__ == '__main__':
    main()
