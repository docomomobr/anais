#!/usr/bin/env python3
"""
Fix sdnne05 author issues found during plumber review.

Issues found:
1. sdnne05-028: Carolina Marques Chaves Galvão (author_id=91)
   - Affiliation "IAU-USP" → "IFS" (Instituto Federal de Sergipe)
   - Plumber bio: "Professora efetiva do IFS-Sergipe"

2. sdnne05-010: Eliane Ramos Cantuária (author_id=67)
   - Affiliation "UNIFAP" → "FAMA" (Faculdade de Macapá)
   - Plumber bio: "docente da Faculdade de Macapá"
   - UNIFAP is where she got her master's, not her teaching institution

Issues noted but NOT fixed (shared author in reviewed seminars):
- sdnne05-003: Nelcia Beatriz Fortes da Costa Pinheiro (author_id=1479)
  In this article she signs as "Costa Pinheiro" (familyname should be "Pinheiro"),
  but in sdbr08-038 (reviewed) she signs as "Costa". Changing the shared author
  record would affect reviewed seminars. Flagged for manual review.
"""

import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "anais.db")


def main():
    dry_run = "--dry-run" in sys.argv

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    fixes = [
        # (article_id, author_id, field, old_value, new_value, reason)
        (
            "sdnne05-028",
            91,
            "affiliation",
            "IAU-USP",
            "IFS",
            "Plumber bio: 'Professora efetiva do IFS-Sergipe'. IAU-USP is master's institution, not affiliation.",
        ),
        (
            "sdnne05-010",
            67,
            "affiliation",
            "UNIFAP",
            "FAMA",
            "Plumber bio: 'docente da Faculdade de Macapá'. UNIFAP is master's institution.",
        ),
    ]

    applied = 0
    for article_id, author_id, field, old_val, new_val, reason in fixes:
        # Verify current value
        cur.execute(
            f"SELECT {field} FROM article_author WHERE article_id = ? AND author_id = ?",
            (article_id, author_id),
        )
        row = cur.fetchone()
        if row is None:
            print(f"  SKIP {article_id} author {author_id}: record not found")
            continue

        current = row[field]
        if current != old_val:
            print(
                f"  SKIP {article_id} author {author_id}: "
                f"expected '{old_val}', found '{current}'"
            )
            continue

        if dry_run:
            print(f"  [DRY-RUN] {article_id} author {author_id}: {field} '{old_val}' → '{new_val}'")
            print(f"            Reason: {reason}")
        else:
            cur.execute(
                f"UPDATE article_author SET {field} = ? WHERE article_id = ? AND author_id = ?",
                (new_val, article_id, author_id),
            )
            print(f"  FIXED {article_id} author {author_id}: {field} '{old_val}' → '{new_val}'")
            applied += 1

    if not dry_run and applied > 0:
        conn.commit()
        print(f"\n{applied} fix(es) applied.")
    elif dry_run:
        print(f"\nDry run: {len(fixes)} fix(es) would be applied.")
    else:
        print("\nNo fixes needed.")

    conn.close()


if __name__ == "__main__":
    main()
