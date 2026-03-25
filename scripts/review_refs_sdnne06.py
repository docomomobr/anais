#!/usr/bin/env python3
"""
Review references for sdnne06 articles by comparing DB with plumber files.

Detects and fixes:
- Missing references (in plumber but not in DB) → backfill
- Split references (one ref broken across two DB entries) → join
- Concatenated references (bullet-separated) → split
- Truncated references → fix
"""

import json
import os
import re
import sqlite3
import sys
from difflib import SequenceMatcher

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'anais.db')
PLUMBER_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'regionais', 'nne', 'sdnne06', 'fontes_plumber')


def normalize_text(text):
    """Normalize text for comparison: collapse whitespace, strip."""
    if not text:
        return ''
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_plumber_refs(filepath):
    """Parse a plumber JSONL file and extract individual references."""
    ref_blocks = []
    with open(filepath) as f:
        for line in f:
            obj = json.loads(line)
            if obj.get('role') == 'reference':
                ref_blocks.append(obj['text'])

    if not ref_blocks:
        return []

    full_text = '\n'.join(ref_blocks)

    # Remove header labels
    full_text = re.sub(r'^REFERÊNCIAS\s*BIBLIOGRÁFICAS\s*\n?', '', full_text, flags=re.IGNORECASE)
    full_text = re.sub(r'^REFERÊNCIAS\s*\n?', '', full_text, flags=re.IGNORECASE)
    full_text = re.sub(r'^BIBLIOGRAFIA\s*\n?', '', full_text, flags=re.IGNORECASE)
    full_text = re.sub(r'^REFERENCES\s*\n?', '', full_text, flags=re.IGNORECASE)

    if not full_text.strip():
        return []

    return split_refs_from_text(full_text)


def split_refs_from_text(text):
    """Split a block of text into individual references."""
    lines = text.split('\n')
    refs = []
    current = []

    # Pattern for start of a new reference
    ref_start = re.compile(
        r'^(?:'
        r'[A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ\s]{1,}[,.]'  # AUTHOR, or AUTHOR.
        r'|[_\-–—]{2,}'  # ABNT repeat
        r'|\d+[.\)]\s'   # numbered ref
        r'|[A-Z][a-záéíóúàâêôãõç]+\s*,'  # Author, (mixed case)
        r'|\uf0b7'  # bullet char
        r')'
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if ref_start.match(stripped) and current:
            ref_text = normalize_text(' '.join(current))
            if ref_text:
                refs.append(ref_text)
            current = [stripped]
        else:
            current.append(stripped)

    if current:
        ref_text = normalize_text(' '.join(current))
        if ref_text:
            refs.append(ref_text)

    return refs


def similarity(a, b):
    """Compute similarity ratio between two strings."""
    a_norm = normalize_text(a).lower()
    b_norm = normalize_text(b).lower()
    if not a_norm or not b_norm:
        return 0.0
    # Use first 100 chars for speed on long refs
    return SequenceMatcher(None, a_norm[:100], b_norm[:100]).ratio()


def is_in_db(ref, db_refs):
    """Check if a plumber ref is already present in DB (by start or similarity)."""
    ref_norm = normalize_text(ref).lower()
    if len(ref_norm) < 10:
        return True  # skip very short

    for d_ref in db_refs:
        d_norm = normalize_text(d_ref).lower()
        # Exact start match (first 50 chars for long refs)
        match_len = min(len(ref_norm), len(d_norm), 50)
        if match_len >= 30 and ref_norm[:match_len] == d_norm[:match_len]:
            return True
        # High similarity
        if similarity(ref, d_ref) > 0.75:
            return True
        # One contains the other's start (50+ chars)
        if len(ref_norm) >= 50 and ref_norm[:50] in d_norm:
            return True
        if len(d_norm) >= 50 and d_norm[:50] in ref_norm:
            return True

    return False


# Pattern for detecting a new reference start in extension text
# Catches: "AUTHOR, Name.", "LEVI-STRAUSS.", "SEMINÁRIO BRASILEIRO", etc.
REF_START_IN_EXT = re.compile(
    r'(?:\.\s+|^\s+)'  # After period+space or at start with space
    r'(?:'
    r'[A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ\-\s]{2,}[,.]\s+[A-Za-z]'  # AUTHOR, Name
    r'|[A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ]{3,}\s+[A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ]{3,}'  # TWO+ UPPERCASE WORDS (institution/event)
    r'|[A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ]{3,}\s+[a-záéíóúàâêôãõç]{3,}'  # UPPERCASE word + lowercase word (like "DESFILE estudantil")
    r'|[A-Z][a-záéíóúàâêôãõç]{2,}\s+[A-Z][a-záéíóúàâêôãõç]'  # Mixed case: "Nossa Pau"
    r'|In:\s*$'  # Ends with "In:" — incomplete
    r'|[_\-–—]{2,}'  # ABNT repeat
    r')'
)


def is_fragment(text):
    """Check if text looks like a fragment rather than a complete reference.

    Fragments are pieces of refs that got split by the plumber parser when
    a continuation line starts with a capitalized word (city, event, etc.).
    """
    t = normalize_text(text)
    if len(t) < 20:
        return True
    # Starts with lowercase
    if t[0].islower():
        return True
    # Starts with year/page/edition continuation
    if re.match(r'^\d', t):
        return True
    # Starts with known continuation words
    if re.match(r'^(et |de |da |do |em |no |na |del |la |p\.\s|v\.\s|n\.\s)', t, re.IGNORECASE):
        return True
    # Starts with event/proceedings name (not an author)
    if re.match(r'^(DOCOMOMO|MODERNO|ANAIS|PROCEEDINGS|PROPAR|SEMINÁRIO)', t):
        return True
    # Short fragments that look like publisher/location/pages (no comma after first word)
    # e.g., "Perspectiva, 1998. 813p." or "Municipal, 1992, p. 44."
    # or "Urbanismo, Salvador." or "Mackenzie, São Paulo, 2009."
    # These start with a capitalized word followed by comma, then short content
    if len(t) < 60 and re.match(r'^[A-Z][a-záéíóúàâêôãõç]+,\s', t):
        # Check: does it look like "Publisher, City, Year" pattern (no author structure)?
        # Real refs have "AUTHOR, Name." pattern (uppercase family name)
        first_word = t.split(',')[0].strip()
        if first_word[0].isupper() and not first_word.isupper():
            # Mixed case first word + short = likely fragment
            return True
    # City/location start followed by short content
    if re.match(r'^(Porto Alegre|São Paulo|Rio de Janeiro|Brasília|Recife|Salvador|Teresina|Fortaleza|'
                r'Londres|Manole|Mackenzie|Edufpi|Vitruvius|Paulo|Natal)', t):
        return True
    return False


def is_ref_header(text):
    """Check if text is a reference section header."""
    t = normalize_text(text).strip()
    return bool(re.match(
        r'^(REFERÊNCIAS|REFERENCIAS|REFERÊNCIAS BIBLIOGRÁFICAS|BIBLIOGRAFIA|REFERENCES)\s*$',
        t, re.IGNORECASE
    ))


def find_split_refs(db_refs):
    """Find DB refs that are one ref split across consecutive entries.

    Only flag clear cases:
    1. Current ends with "In:" or "e" (conjunction before editor/org)
    2. Next starts with lowercase or continuation pattern
    3. Next starts with "M.." (truncated author initial joined to next text)
    """
    splits = []

    for i in range(len(db_refs) - 1):
        curr = db_refs[i].strip()
        nxt = db_refs[i + 1].strip()
        if not nxt:
            continue

        # Case 1: Current ends with "In:" or similar (split at chapter/org reference)
        if re.search(r'\b(?:In|In:|e|et|and)\s*$', curr):
            splits.append((i, i + 1))
            continue

        # Case 2: Next starts with lowercase (clear continuation)
        # But NOT if it's a URL (URLs are standalone refs)
        if nxt[0].islower() and not nxt.startswith('http'):
            splits.append((i, i + 1))
            continue

        # Case 3: Next starts with "M.." or similar truncated pattern
        if re.match(r'^[A-Z]\.\.\w', nxt):
            splits.append((i, i + 1))
            continue

        # Case 4: Next starts with common continuation words
        if re.match(r'^(et |de |da |do |em |no |na |del |la |los |das |dos )', nxt):
            splits.append((i, i + 1))
            continue

        # Case 5: Bare URL continuation - only when previous ends with
        # "Disponível em:" or similar access-URL pattern (not just any ref)
        if re.match(r'^https?://', nxt):
            if re.search(r'(?:Disponível em|Available at|Acesso em|Acesso)\s*:?\s*$', curr, re.IGNORECASE):
                splits.append((i, i + 1))
                continue

    return splits


def find_bullet_concatenated(db_refs):
    """Find DB refs that have bullet markers (multiple refs as one entry)."""
    results = []
    for i, ref in enumerate(db_refs):
        if '\uf0b7' in ref:
            parts = re.split(r'\s*\uf0b7\s*', ref)
            parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]
            if len(parts) > 1:
                results.append((i, parts))
    return results


def find_missing_refs(db_refs, plumber_refs):
    """Find plumber refs missing from DB."""
    missing = []
    for p_ref in plumber_refs:
        if is_ref_header(p_ref):
            continue
        p_norm = normalize_text(p_ref)
        if len(p_norm) < 15:
            continue
        if is_fragment(p_norm):
            continue
        if not is_in_db(p_ref, db_refs):
            missing.append(p_ref)
    return missing


def find_truncated_refs(db_refs, plumber_refs):
    """Find DB refs that are truncated vs plumber version.

    Only flag when:
    1. First 50 chars match exactly
    2. Plumber version is significantly longer
    3. The extension does NOT contain a new author/ref start (which would mean
       the plumber incorrectly concatenated two refs)
    """
    truncated = []
    for i, d_ref in enumerate(db_refs):
        d_norm = normalize_text(d_ref)
        if len(d_norm) < 30:
            continue

        for p_ref in plumber_refs:
            p_norm = normalize_text(p_ref)
            # Need at least 50 chars matching
            match_len = min(50, len(d_norm))
            if match_len < 30:
                continue
            if (d_norm[:match_len].lower() == p_norm[:match_len].lower() and
                    len(p_norm) > len(d_norm) + 20):
                # Check the extension part doesn't start a new ref
                extension = p_norm[len(d_norm):]
                # Look for new author pattern in extension (UPPERCASE, Name.)
                if REF_START_IN_EXT.search(extension):
                    continue  # Skip: plumber merged two refs
                # If extension is very long (>150 chars), likely contains merged refs
                if len(extension.strip()) > 150:
                    continue
                truncated.append((i, p_norm))
                break

    return truncated


def review_article(art_id, db_refs_json):
    """Review one article. Returns list of corrections."""
    corrections = []

    db_refs = json.loads(db_refs_json) if db_refs_json else []
    if not db_refs and not db_refs_json:
        return corrections

    fn = os.path.join(PLUMBER_DIR, f'sdnne06-{int(art_id):03d}.jsonl')
    if not os.path.exists(fn):
        return corrections

    plumber_refs = parse_plumber_refs(fn)

    # 1. Bullet-separated concatenated refs
    bullet_concats = find_bullet_concatenated(db_refs)
    for idx, parts in bullet_concats:
        corrections.append({
            'type': 'split_bullet',
            'index': idx,
            'old': db_refs[idx],
            'new_parts': parts
        })

    # 2. Split refs (broken across entries)
    splits = find_split_refs(db_refs)
    for idx1, idx2 in splits:
        joined = normalize_text(db_refs[idx1]) + ' ' + normalize_text(db_refs[idx2])
        corrections.append({
            'type': 'join',
            'index1': idx1,
            'index2': idx2,
            'old1': db_refs[idx1],
            'old2': db_refs[idx2],
            'new': joined
        })

    # 3. Truncated refs (if plumber available)
    if plumber_refs:
        truncated = find_truncated_refs(db_refs, plumber_refs)
        for idx, full_ref in truncated:
            # Skip if this index is involved in a split (will be handled there)
            if any(c['type'] == 'join' and (c['index1'] == idx or c['index2'] == idx) for c in corrections):
                continue
            corrections.append({
                'type': 'fix_truncated',
                'index': idx,
                'old': db_refs[idx],
                'new': full_ref
            })

        # 4. Missing refs
        missing = find_missing_refs(db_refs, plumber_refs)
        for m_ref in missing:
            corrections.append({
                'type': 'backfill',
                'new': normalize_text(m_ref)
            })

    return corrections


def apply_corrections(conn, art_id, corrections):
    """Apply all corrections for one article."""
    db_refs = json.loads(conn.execute(
        "SELECT references_ FROM articles WHERE seminar_slug='sdnne06' AND id=?",
        (art_id,)
    ).fetchone()[0] or '[]')

    new_refs = list(db_refs)
    applied = []

    # 1. Apply joins (reverse order to preserve indices)
    joins = sorted([c for c in corrections if c['type'] == 'join'],
                   key=lambda c: c['index2'], reverse=True)
    for j in joins:
        idx1, idx2 = j['index1'], j['index2']
        if idx2 < len(new_refs):
            joined = normalize_text(new_refs[idx1]) + ' ' + normalize_text(new_refs[idx2])
            new_refs[idx1] = joined
            new_refs.pop(idx2)
            applied.append(j)

    # 2. Apply bullet splits (reverse order)
    bsplits = sorted([c for c in corrections if c['type'] == 'split_bullet'],
                     key=lambda c: c['index'], reverse=True)
    for bs in bsplits:
        idx = bs['index']
        if idx < len(new_refs):
            new_refs[idx:idx + 1] = bs['new_parts']
            applied.append(bs)

    # 3. Apply truncated fixes (match by content since indices may have shifted)
    for fix in corrections:
        if fix['type'] == 'fix_truncated':
            old_norm = normalize_text(fix['old']).lower()
            for i, r in enumerate(new_refs):
                if normalize_text(r).lower()[:35] == old_norm[:35]:
                    if len(fix['new']) > len(normalize_text(r)):
                        new_refs[i] = fix['new']
                        applied.append(fix)
                    break

    # 4. Apply backfills (replace truncated entries or append new)
    for bf in corrections:
        if bf['type'] == 'backfill':
            new_ref = bf['new']
            new_norm = normalize_text(new_ref).lower()

            # Check if there's a truncated version in DB to replace
            replaced = False
            for i, r in enumerate(new_refs):
                r_norm = normalize_text(r).lower()
                # If DB entry is shorter and is a prefix of the backfill ref
                if (len(r_norm) < len(new_norm) - 10 and
                        len(r_norm) >= 10 and
                        new_norm.startswith(r_norm.rstrip('. '))):
                    new_refs[i] = new_ref
                    bf['replaced_index'] = i
                    applied.append(bf)
                    replaced = True
                    break

            if not replaced:
                # Double-check not already present
                if not is_in_db(new_ref, new_refs):
                    new_refs.append(new_ref)
                    applied.append(bf)

    if applied:
        conn.execute(
            "UPDATE articles SET references_=? WHERE seminar_slug='sdnne06' AND id=?",
            (json.dumps(new_refs, ensure_ascii=False), art_id)
        )

    return applied


def main():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, references_ FROM articles WHERE seminar_slug='sdnne06' "
        "AND file IS NOT NULL AND file != '' ORDER BY CAST(id AS INTEGER)"
    ).fetchall()

    print(f"Reviewing {len(rows)} articles with PDF files...")
    print()

    all_corrections = {}
    total_by_type = {}
    total_applied = 0

    for art_id, db_refs_json in rows:
        corrections = review_article(art_id, db_refs_json)
        if corrections:
            applied = apply_corrections(conn, art_id, corrections)
            if applied:
                all_corrections[art_id] = applied
                for a in applied:
                    t = a['type']
                    total_by_type[t] = total_by_type.get(t, 0) + 1
                    total_applied += 1

    conn.commit()
    conn.close()

    # Report
    print(f"Total articles reviewed: {len(rows)}")
    print(f"Total corrections applied: {total_applied}")
    print(f"Corrections by type:")
    for t, count in sorted(total_by_type.items()):
        print(f"  {t}: {count}")
    print()

    for art_id in sorted(all_corrections.keys(), key=lambda x: int(x)):
        corrs = all_corrections[art_id]
        print(f"--- Article {art_id} ({len(corrs)} corrections) ---")
        for c in corrs:
            if c['type'] == 'join':
                print(f"  JOIN [{c['index1']}]+[{c['index2']}]:")
                print(f"    [{c['index1']}]: {normalize_text(c['old1'])[:100]}")
                print(f"    [{c['index2']}]: {normalize_text(c['old2'])[:100]}")
            elif c['type'] == 'split_bullet':
                print(f"  SPLIT_BULLET [{c['index']}] into {len(c['new_parts'])} parts")
                for j, p in enumerate(c['new_parts']):
                    print(f"    Part {j}: {p[:80]}")
            elif c['type'] == 'backfill':
                print(f"  BACKFILL: {c['new'][:120]}")
            elif c['type'] == 'fix_truncated':
                print(f"  FIX_TRUNCATED [{c['index']}]:")
                print(f"    Old: {normalize_text(c['old'])[:100]}")
                print(f"    New: {normalize_text(c['new'])[:100]}")
        print()


if __name__ == '__main__':
    main()
