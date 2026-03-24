#!/usr/bin/env python3
"""
Extract English titles (title_en, subtitle_en) from sdbr13 PDFs.

Scans PDFs for EN titles in the text between keyword section and Abstract section.
Only extracts titles that are clearly in English (not PT/ES titles).

Then applies Title Case normalization and writes to database.
"""

import os
import re
import sqlite3
import sys
import pdfplumber

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')
PDF_DIR = os.path.join(BASE_DIR, 'nacionais', 'sdbr13', 'pdfs')

sys.path.insert(0, BASE_DIR)

# Words that only appear in English, not Portuguese/Spanish
EN_ONLY_WORDS = {
    'the', 'and', 'between', 'from', 'with', 'that', 'this', 'which',
    'where', 'when', 'how', 'what', 'who', 'their', 'its', 'are',
    'was', 'were', 'has', 'have', 'had', 'been', 'being', 'will',
    'would', 'could', 'should', 'may', 'might', 'must', 'shall',
    'not', 'but', 'or', 'yet', 'so', 'because', 'since', 'while',
    'after', 'before', 'above', 'below', 'through', 'during', 'into',
    'about', 'against', 'upon', 'toward', 'towards', 'beyond',
    'architecture', 'building', 'heritage', 'house', 'museum',
    'bread', 'wall', 'bearing', 'load', 'structure', 'independent',
    'contrast', 'analogy', 'dialogues', 'interventions', 'built',
    'transformation', 'connections', 'culture', 'regional',
    'preservation', 'conservation', 'restoration', 'movement',
    'landscape', 'planning', 'design', 'space', 'identity',
    'memory', 'history', 'analysis', 'construction', 'housing',
    'contemporary', 'national', 'public', 'brazilian', 'brazil',
    'urban', 'city', 'school', 'church', 'hotel', 'hospital',
}


def is_clearly_english(text):
    """Check if text is clearly English (not PT/ES).
    Requires at least 2 English-only words."""
    words = text.lower().split()
    en_count = sum(1 for w in words if w.rstrip('.,;:()-') in EN_ONLY_WORDS)
    return en_count >= 2


def extract_text_pages(pdf_path, max_pages=3):
    try:
        pdf = pdfplumber.open(pdf_path)
        text = ''
        for p in pdf.pages[:max_pages]:
            t = p.extract_text()
            if t:
                text += t + '\n'
        pdf.close()
        return text
    except Exception:
        return ''


def find_en_title(text):
    """Find English title in the PDF text.

    Returns (title, subtitle) or (None, None).
    """
    # Find keyword section end
    kw_match = re.search(
        r'(?:Palavras[- ]?chave[s]?|PALABRAS\s+CLAVE)\s*:?\s*(.+?\.)\s*\n',
        text, re.IGNORECASE | re.DOTALL
    )
    if not kw_match:
        return None, None

    after_kw = text[kw_match.end():]

    # Check if there's an Abstract label
    abs_match = re.search(r'\bAbstract\b', after_kw, re.IGNORECASE)

    if abs_match:
        # Pattern 1: EN title between keywords and Abstract
        between = after_kw[:abs_match.start()].strip()
        if between and len(between) > 10:
            lines = [l.strip() for l in between.split('\n') if l.strip()]
            title_lines = []
            for line in lines:
                if line.count(',') >= 3 and len(line) < 150:
                    continue
                if re.match(r'^\d+\s', line):
                    continue
                if len(line) < 5:
                    continue
                title_lines.append(line)

            if title_lines:
                candidate = ' '.join(title_lines)
                if 10 < len(candidate) < 500 and is_clearly_english(candidate):
                    return split_title_subtitle(candidate)
    else:
        # Pattern 2: No Abstract label - collect text until first lowercase paragraph
        title_lines = []
        for line in after_kw.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Stop at first line that looks like a paragraph (starts with uppercase,
            # then lowercase, and is long)
            if len(line) > 80 and line[0].isupper() and any(c.islower() for c in line[:20]):
                break
            title_lines.append(line)
            # Also stop if we've collected too many lines
            if len(title_lines) > 6:
                break

        if title_lines:
            candidate = ' '.join(title_lines)
            if 10 < len(candidate) < 500 and is_clearly_english(candidate):
                return split_title_subtitle(candidate)

    return None, None


def split_title_subtitle(text):
    """Split title:subtitle on colon or em-dash."""
    colon_m = re.match(r'^(.+?):\s+(.+)$', text)
    if colon_m:
        return colon_m.group(1).strip(), colon_m.group(2).strip()

    dash_m = re.match(r'^(.+?)\s*[—–]\s+(.+)$', text)
    if dash_m:
        return dash_m.group(1).strip(), dash_m.group(2).strip()

    return text, None


def apply_title_case(text):
    """Apply Title Case for English titles (Chicago/APA style)."""
    if not text:
        return text

    try:
        from titlecase import titlecase
        from dict.normalizar import load_dict, _SIGLAS, _NOMES, _LUGARES

        if not _SIGLAS:
            load_dict()

        EN_SMALL = {
            'to', 'am', 'al', 'se', 'go', 'ma', 'mg', 'mt', 'ms', 'pa', 'pi',
            'pr', 'pe', 'rj', 'rn', 'rs', 'ro', 'rr', 'sc', 'sp', 'ap', 'ac',
        }

        def callback(word, **kwargs):
            match = re.match(r'^([^\w]*)(\w+(?:[-/]\w+)*)([^\w]*)$', word, re.UNICODE)
            if not match:
                return None
            prefix, core, suffix = match.groups()
            core_lower = core.lower()

            if core_lower in _SIGLAS and core_lower not in EN_SMALL:
                return prefix + core.upper() + suffix
            if '-' in core:
                parts = core.split('-')
                if all(p.lower() in _SIGLAS for p in parts):
                    return prefix + '-'.join(p.upper() for p in parts) + suffix
            if core_lower in _NOMES:
                return prefix + _NOMES[core_lower] + suffix
            if core_lower in _LUGARES:
                return prefix + _LUGARES[core_lower] + suffix
            return None

        result = titlecase(text, callback=callback)
        return result
    except ImportError:
        return text.title()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--scan-only', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    rows = conn.execute(
        '''SELECT file, title, subtitle, abstract_en, title_en, subtitle_en
           FROM articles WHERE seminar_slug='sdbr13' AND abstract_en IS NOT NULL
           ORDER BY file'''
    ).fetchall()

    print(f'Total articles with abstract_en: {len(rows)}')
    print()

    extracted = []
    skipped_existing = 0
    no_title_found = 0

    for file, title_pt, subtitle_pt, abstract_en, existing_title_en, existing_subtitle_en in rows:
        if existing_title_en and existing_title_en.strip():
            skipped_existing += 1
            continue

        pdf_path = os.path.join(PDF_DIR, file)
        if not os.path.exists(pdf_path):
            continue

        text = extract_text_pages(pdf_path)
        if not text:
            continue

        title_en, subtitle_en = find_en_title(text)

        if title_en:
            title_en_norm = apply_title_case(title_en)
            subtitle_en_norm = apply_title_case(subtitle_en) if subtitle_en else None

            extracted.append((file, title_en, subtitle_en, title_en_norm, subtitle_en_norm))
            print(f'{file}:')
            print(f'  PT: {title_pt}')
            if subtitle_pt:
                print(f'  PT sub: {subtitle_pt}')
            print(f'  EN raw: {title_en}')
            if subtitle_en:
                print(f'  EN sub raw: {subtitle_en}')
            print(f'  EN norm: {title_en_norm}')
            if subtitle_en_norm:
                print(f'  EN sub norm: {subtitle_en_norm}')
            print()
        else:
            no_title_found += 1
            if args.verbose:
                print(f'{file}: no EN title found')

    print(f'=== Summary ===')
    print(f'Articles with abstract_en: {len(rows)}')
    print(f'Already had title_en: {skipped_existing}')
    print(f'EN titles extracted: {len(extracted)}')
    print(f'No EN title found: {no_title_found}')
    print()

    if args.scan_only:
        print('(scan-only mode)')
        return

    if not extracted:
        print('No titles to write.')
        return

    if args.dry_run:
        print('(dry-run mode)')
        return

    try:
        for file, _, _, title_en_norm, subtitle_en_norm in extracted:
            conn.execute(
                "UPDATE articles SET title_en=?, subtitle_en=? WHERE file=? AND seminar_slug='sdbr13'",
                (title_en_norm, subtitle_en_norm, file)
            )
        conn.commit()
        print(f'Wrote {len(extracted)} title_en to database.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
