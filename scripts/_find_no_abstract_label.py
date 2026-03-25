#!/usr/bin/env python3
"""Find sdbr13 articles that have abstract_en but no 'Abstract' label in PDF."""

import os
import re
import sqlite3
import pdfplumber

DB_PATH = 'anais.db'
PDF_DIR = 'nacionais/sdbr13/pdfs'

conn = sqlite3.connect(DB_PATH)
try:
    rows = conn.execute(
        "SELECT file FROM articles WHERE seminar_slug='sdbr13' AND abstract_en IS NOT NULL ORDER BY file"
    ).fetchall()
    files = [r[0] for r in rows]
finally:
    conn.close()

no_label = []
with_label = 0

for fname in files:
    try:
        pdf = pdfplumber.open(f'{PDF_DIR}/{fname}')
    except FileNotFoundError:
        continue
    try:
        text = ''
        for p in pdf.pages[:3]:
            t = p.extract_text()
            if t:
                text += t + '\n'
    finally:
        pdf.close()

    if not re.search(r'\bAbstract\b', text, re.IGNORECASE):
        no_label.append(fname)
        # Show what's after Palavras-chave
        m = re.search(r'Palavras[- ]?chave[s]?\s*:[^\n]*\n(.{0,500})', text, re.IGNORECASE | re.DOTALL)
        if m:
            after = m.group(1).strip()
            print(f'{fname}:')
            for line in after.split('\n')[:8]:
                print(f'  |{line}|')
            print()
    else:
        with_label += 1

print(f'=== {len(no_label)} articles without "Abstract" label, {with_label} with label ===')
