#!/usr/bin/env python3
"""Scan sdbr13 PDFs for bold/italic EN titles using font info."""

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

found = []

for fname in files:
    try:
        pdf = pdfplumber.open(f'{PDF_DIR}/{fname}')
    except FileNotFoundError:
        continue

    try:
        abstract_page = None
        abstract_y = None

        # Find Abstract position
        for pi, page in enumerate(pdf.pages[:3]):
            words = page.extract_words(extra_attrs=['fontname', 'size'])
            for w in words:
                if w['text'].lower() in ('abstract', 'abstract:'):
                    abstract_page = pi
                    abstract_y = w['top']
                    break
            if abstract_y is not None:
                break

        if abstract_page is None:
            continue

        # Look for bold/italic EN text before Abstract on that page
        page = pdf.pages[abstract_page]
        words = page.extract_words(extra_attrs=['fontname', 'size'])

        title_candidates = []
        for w in words:
            if w['top'] >= abstract_y:
                break
            fontname = w.get('fontname', '')
            size = w.get('size', 10)

            # Bold-italic or large bold text
            is_bold_italic = 'BoldItalic' in fontname
            is_large = size >= 12

            if (is_bold_italic or is_large) and 'Bold' in fontname:
                title_candidates.append((w['top'], size, fontname, w['text']))
    finally:
        pdf.close()

    if not title_candidates:
        continue

    # Group by y-position into lines
    lines = []
    current = [title_candidates[0]]
    for w in title_candidates[1:]:
        if abs(w[0] - current[-1][0]) < 5:
            current.append(w)
        else:
            lines.append(current)
            current = [w]
    lines.append(current)

    # Check each line for English content
    for line_words in lines:
        text = ' '.join(w[3] for w in line_words)
        size = line_words[0][1]
        fontname = line_words[0][2]
        y = line_words[0][0]

        # Skip PT labels
        if any(pt in text.lower() for pt in ['resumo', 'palavras', 'chave', 'doutora', 'doutor', 'mestra', 'mestranda', 'professor']):
            continue

        # Check if English (has common EN words)
        en_words = {'the', 'of', 'and', 'in', 'for', 'to', 'a', 'an',
                    'between', 'from', 'with', 'on', 'at', 'by', 'is',
                    'modern', 'architecture', 'heritage', 'urban', 'house',
                    'building', 'design', 'cultural', 'national', 'public',
                    'local', 'culture', 'connections', 'international',
                    'contrast', 'analogy', 'regional', 'dialogues',
                    'structure', 'wall', 'independent', 'load', 'bearing'}
        text_words = text.lower().split()
        en_count = sum(1 for w in text_words if w.rstrip('.,;:()') in en_words)

        if en_count >= 1:
            found.append((fname, f'y={y:.0f} size={size:.0f} font={fontname}: {text}'))

print(f'Font-based candidates: {len(found)}')
for fname, info in found:
    print(f'  {fname}: {info}')
