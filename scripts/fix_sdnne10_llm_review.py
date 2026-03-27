#!/usr/bin/env python3
"""Fix truncated abstracts for sdnne10 articles.

Compares DB values with plumber JSONL files and replaces truncated
or junk-contaminated abstracts with the complete text from plumber.

Articles affected:
  - sdnne10-002 (abstract, abstract_en)
  - sdnne10-004 (abstract, abstract_en)
  - sdnne10-024 (abstract, abstract_en)
  - sdnne10-030 (abstract_en)
  - sdnne10-032 (abstract_es)
  - sdnne10-037 (abstract, abstract_en)
  - sdnne10-058 (abstract_es)
  - sdnne10-060 (abstract)
  - sdnne10-062 (abstract, abstract_en)
  - sdnne10-063 (abstract_es)
  - sdnne10-067 (abstract)
  - sdnne10-076 (abstract_es)
  - sdnne10-078 (abstract_en)
  - sdnne10-082 (abstract, abstract_en)

Skipped (no plumber data for the needed language):
  - sdnne10-015 (abstract) -- no RESUMO in plumber
  - sdnne10-030 (abstract) -- no RESUMO in plumber
  - sdnne10-035 (abstract_es) -- DB matches plumber
  - sdnne10-043 (abstract_en) -- no ABSTRACT in plumber
  - sdnne10-046 (abstract_en) -- DB matches plumber
  - sdnne10-066 (abstract_es) -- DB matches plumber

Usage:
    python3 scripts/fix_sdnne10_llm_review.py --dry-run
    python3 scripts/fix_sdnne10_llm_review.py
"""

import argparse
import json
import os
import re
import sqlite3
from collections import Counter

DB_PATH = "anais.db"
PLUMBER_DIR = "regionais/nne/sdnne10/fontes_plumber"

_VALID_COLS = frozenset({"abstract", "abstract_en", "abstract_es"})

# Articles with email/header contamination in abstract (resumo expandido format)
EMAIL_CONTAMINATED = [
    "sdnne10-022", "sdnne10-023", "sdnne10-024", "sdnne10-027",
    "sdnne10-028", "sdnne10-039", "sdnne10-041", "sdnne10-073",
]

# Regex to match keyword lines in any of the three languages
KW_PATTERN = (
    r"\s*(?:Palavras[\s-]*chave|PALAVRA[\s-]*CHAVE"
    r"|KEYWORDS?|PALABRAS[\s-]*CLAVE)\w*\s*:.*$"
)

MARKER_MAP = {
    "abstract": "RESUMO",
    "abstract_en": "ABSTRACT",
    "abstract_es": "RESUMEN",
}


def get_filtered_blocks(filepath):
    """Read plumber JSONL, return abstract blocks with repeated headers removed."""
    blocks = []
    with open(filepath) as f:
        for line in f:
            obj = json.loads(line)
            if obj.get("role") == "abstract":
                text = obj.get("text", "").strip()
                if text:
                    blocks.append(text)

    # Count normalized blocks; those appearing 3+ times are page headers/footers
    block_counts = Counter()
    for b in blocks:
        norm = re.sub(r"\s+", " ", b).strip()
        block_counts[norm] += 1
    repeated = {norm for norm, count in block_counts.items() if count >= 3}

    TEMPLATE_NORM = (
        "Título do artigo: subtítulo do artigo Nome Completo dos Autores"
    )

    filtered = []
    for b in blocks:
        norm = re.sub(r"\s+", " ", b).strip()
        if norm in repeated or norm == TEMPLATE_NORM:
            continue
        filtered.append(b)

    return filtered


def clean_text(text):
    """Remove keyword lines, template text, and normalize whitespace."""
    text = re.sub(KW_PATTERN, "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    text = re.sub(r"\s*Texto do resumo em espanhol.*$", "", text).strip()
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_marker_section(blocks, marker):
    """Extract text for a given language marker (RESUMO/ABSTRACT/RESUMEN).

    Follows these rules:
    - Start collecting after the marker
    - Skip template blocks ("Título do artigo...")
    - Stop at keyword lines, other language markers, or body text
    - Body text is detected when previous block ended with .?! and next
      block starts with uppercase (new paragraph = likely body text)
    - If previous block did NOT end with .?!, the next block is a
      continuation of the same sentence
    """
    parts = []
    in_section = False

    for b in blocks:
        first_word = b.split()[0] if b.split() else ""

        if first_word == marker:
            in_section = True
            text_after = b[len(marker) :].strip()
            if text_after:
                kw_match = re.search(KW_PATTERN, text_after, re.IGNORECASE)
                if kw_match:
                    text_after = text_after[: kw_match.start()].strip()
                    if text_after:
                        parts.append(text_after)
                    in_section = False
                else:
                    parts.append(text_after)
            continue

        if not in_section:
            continue

        # Stop conditions
        if first_word in ("RESUMO", "ABSTRACT", "RESUMEN"):
            break
        if re.match(
            r"^(?:PALABRA|KEYWORD|PALAVRA|Palavras[\s-]*chave)",
            b,
            re.IGNORECASE,
        ):
            break
        if "Título do artigo" in b:
            continue  # skip template, keep looking

        # Check for embedded keywords in this block
        kw_match = re.search(KW_PATTERN, b, re.IGNORECASE)

        if parts:
            prev_stripped = parts[-1].rstrip()
            prev_ends_sentence = prev_stripped and prev_stripped[-1] in ".?!"

            if prev_ends_sentence:
                first_real_char = b.lstrip()[:1]
                if first_real_char and first_real_char.islower():
                    # Lowercase start after sentence = still continuation
                    if kw_match:
                        text_before = b[: kw_match.start()].strip()
                        if text_before:
                            parts.append(text_before)
                        break
                    parts.append(b)
                else:
                    # Uppercase start after sentence end = likely body text
                    if kw_match:
                        text_before = b[: kw_match.start()].strip()
                        if text_before:
                            parts.append(text_before)
                    break
            else:
                # Previous block didn't end cleanly = continuation
                if kw_match:
                    text_before = b[: kw_match.start()].strip()
                    if text_before:
                        parts.append(text_before)
                    break
                parts.append(b)
        else:
            if kw_match:
                text_before = b[: kw_match.start()].strip()
                if text_before:
                    parts.append(text_before)
                break
            parts.append(b)

    if not parts:
        return None

    text = " ".join(p.strip() for p in parts)
    return clean_text(text)


def extract_nomarker_004(filepath):
    """sdnne10-004: no RESUMO/ABSTRACT markers; blocks split by page break.

    Block layout: [0]=pt_part1, [1]=pt_part2, [2]=en_part1, [3]=en_part2, [4]=es
    """
    blocks = get_filtered_blocks(filepath)
    pt = blocks[0] + " " + blocks[1]
    en = blocks[2] + " " + blocks[3]
    return {
        "abstract": clean_text(pt),
        "abstract_en": clean_text(en),
    }


def extract_nomarker_060(filepath):
    """sdnne10-060: no markers; blocks are: [0]=pt, [1]=pt_keywords, [2]=en, [3]=es."""
    blocks = get_filtered_blocks(filepath)
    result = {}
    for lang, idx in [("abstract", 0), ("abstract_en", 2), ("abstract_es", 3)]:
        if idx < len(blocks):
            result[lang] = clean_text(blocks[idx])
    return result


def add_final_period(text):
    """Add period if text doesn't end with punctuation."""
    if text and text[-1] not in ".?!":
        return text + "."
    return text


def build_email_fixes():
    """Build fixes for abstracts contaminated with email/header info."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    fixes = []

    for aid in EMAIL_CONTAMINATED:
        cur.execute("SELECT abstract FROM articles WHERE id=?", (aid,))
        row = cur.fetchone()
        if not row or not row[0]:
            continue
        abstract = row[0]

        # Find "RESUMO" marker and extract text after it
        # Pattern: everything before RESUMO is header/author info with emails
        match = re.search(r'\bRESUMO\b\s*', abstract)
        if match:
            clean = abstract[match.end():].strip()
            if clean and len(clean) < len(abstract):
                fixes.append((aid, "abstract", clean,
                              f"email contamination removed ({len(abstract) - len(clean)} chars header)"))

    conn.close()
    return fixes


def build_fixes():
    """Build list of (article_id, field, new_value, reason) tuples."""
    # Articles and fields to check
    articles_to_check = {
        "sdnne10-002": ["abstract", "abstract_en"],
        "sdnne10-004": ["abstract", "abstract_en"],
        "sdnne10-024": ["abstract", "abstract_en"],
        "sdnne10-030": ["abstract_en"],
        "sdnne10-032": ["abstract_es"],
        "sdnne10-037": ["abstract", "abstract_en"],
        "sdnne10-058": ["abstract_es"],
        "sdnne10-060": ["abstract"],
        "sdnne10-062": ["abstract", "abstract_en"],
        "sdnne10-063": ["abstract_es"],
        "sdnne10-067": ["abstract"],
        "sdnne10-076": ["abstract_es"],
        "sdnne10-078": ["abstract_en"],
        "sdnne10-082": ["abstract", "abstract_en"],
    }

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    fixes = []

    for aid, fields in sorted(articles_to_check.items()):
        fp = os.path.join(PLUMBER_DIR, f"{aid}.jsonl")

        # Extract abstracts from plumber
        if aid == "sdnne10-004":
            plumber = extract_nomarker_004(fp)
        elif aid == "sdnne10-060":
            plumber = extract_nomarker_060(fp)
        else:
            blocks = get_filtered_blocks(fp)
            plumber = {}
            for field in fields:
                marker = MARKER_MAP[field]
                val = extract_marker_section(blocks, marker)
                if val:
                    plumber[field] = val

        # Get current DB values
        cur.execute(
            "SELECT abstract, abstract_en, abstract_es FROM articles WHERE id=?",
            (aid,),
        )
        db_row = cur.fetchone()
        db_vals = {
            "abstract": db_row[0],
            "abstract_en": db_row[1],
            "abstract_es": db_row[2],
        }

        for field in fields:
            db_val = db_vals[field] or ""
            plumber_val = plumber.get(field, "")

            if not plumber_val:
                continue

            # Ensure final period
            plumber_val = add_final_period(plumber_val)

            # Check if fix is needed
            needs_fix = False
            reason = ""

            # Truncation check
            if len(db_val) < len(plumber_val) * 0.95:
                needs_fix = True
                reason = f"truncated (db={len(db_val)} < plumber={len(plumber_val)})"

            # Junk text check
            junk_markers = [
                "Nome Completo dos Autores",
                "Título do artigo",
                "Texto do resumo em espanhol",
                "Campina Grande-PB | 03 a 05 de outubro de 2024",
            ]
            for jm in junk_markers:
                if jm in db_val:
                    needs_fix = True
                    reason = f'junk text: "{jm[:40]}"'
                    break

            if needs_fix:
                fixes.append((aid, field, plumber_val, reason))

    conn.close()
    return fixes


def main():
    parser = argparse.ArgumentParser(
        description="Fix truncated sdnne10 abstracts from plumber JSONL files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without modifying the database",
    )
    args = parser.parse_args()

    email_fixes = build_email_fixes()
    fixes = build_fixes()
    fixes = email_fixes + fixes

    if not fixes:
        print("No fixes needed.")
        return

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Found {len(fixes)} fixes:\n")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for aid, field, new_val, reason in fixes:
        # Get current value for display
        if field not in _VALID_COLS:
            raise ValueError(f"Invalid column: {field}")
        cur.execute(f"SELECT {field} FROM articles WHERE id=?", (aid,))
        old_val = cur.fetchone()[0] or ""

        print(f"  {aid}.{field}: {reason}")
        print(f"    OLD ({len(old_val)}): ...{old_val[-70:]}")
        print(f"    NEW ({len(new_val)}): ...{new_val[-70:]}")

        if not args.dry_run:
            if field not in _VALID_COLS:
                raise ValueError(f"Invalid column: {field}")
            cur.execute(
                f"UPDATE articles SET {field}=? WHERE id=?",
                (new_val, aid),
            )

    if not args.dry_run:
        conn.commit()
        print(f"\n{len(fixes)} abstracts updated.")
    else:
        print(f"\n[DRY RUN] {len(fixes)} abstracts would be updated.")

    conn.close()


if __name__ == "__main__":
    main()
