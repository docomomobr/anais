#!/usr/bin/env python3
"""Check specific PDFs for EN title patterns."""

import sys
import pdfplumber

files = sys.argv[1:]
if not files:
    files = ['sdbr13-038.pdf', 'sdbr13-043.pdf', 'sdbr13-156.pdf', 'sdbr13-133.pdf', 'sdbr13-048.pdf']

for fname in files:
    path = f'nacionais/sdbr13/pdfs/{fname}'
    try:
        pdf = pdfplumber.open(path)
    except FileNotFoundError:
        print(f'{fname}: not found')
        continue

    try:
        for pi, page in enumerate(pdf.pages[:2]):
            text = page.extract_text()
            if text:
                print(f'=== {fname} Page {pi+1} ===')
                print(text[:2500])
                print()
    finally:
        pdf.close()
