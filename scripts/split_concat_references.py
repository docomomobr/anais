#!/usr/bin/env python3
"""
Separa referências bibliográficas concatenadas no anais.db.

Problema: extração de PDF produziu múltiplas referências grudadas em uma
única string. Este script detecta pontos de separação e divide.

Heurísticas de split:
  1. "ano. SOBRENOME," — ABNT (família em CAPS, vírgula, nome)
  2. "ano. Sobrenome," — internacional (família em Titlecase, vírgula, nome)
  3. Espaço duplo/triplo + autor em CAPS
  4. Pipe (⏐) separando referência de notas de rodapé
  5. Sentence-end + CAPS author  (". SOBRENOME, Nome" ou ") SOBRENOME, Nome")

Proteções contra falsos positivos:
  - Não dividir em "ano. Disponível", "ano. Acesso", "ano. Tese", etc.
  - Não dividir em "ano. São Paulo", "ano. Rio de Janeiro", etc.
  - Não dividir em "ano. p.", "ano. v.", "ano. In:", "ano. s.n.", etc.
  - Validação: a palavra após o ano+ponto deve parecer um sobrenome real
    (não um substantivo comum, cidade, ou continuação de referência)

Uso:
    python3 scripts/split_concat_references.py --dry-run [--slug SLUG]
    python3 scripts/split_concat_references.py --apply [--slug SLUG]
    python3 scripts/split_concat_references.py --dry-run --verbose
"""

import argparse
import json
import os
import re
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')

# ── Words that are NOT author names after "year. Word" ──────────────────────
# These appear after year+period but are continuations, not new references.
NOT_AUTHOR_WORDS = {
    # Continuation words (Portuguese)
    'disponível', 'acesso', 'acessado', 'consultado', 'recuperado',
    'tese', 'dissertação', 'monografia', 'trabalho',
    'anais', 'atas', 'caderno', 'cadernos', 'revista', 'jornal',
    'in', 'p', 'pp', 'v', 'vol', 'n', 'nr', 'ed', 'org', 'orgs',
    's', 'sp',  # "s.n.", "s.l." etc.
    'são', 'rio', 'porto', 'belo', 'nova', 'new', 'buenos',
    'edição', 'tradução', 'adaptação', 'introdução', 'prefácio',
    'para', 'por', 'com', 'sem', 'sobre', 'entre',
    'doi', 'isbn', 'issn', 'http', 'https', 'www',
    'dispõe', 'regulamenta', 'estabelece', 'institui', 'altera',
    'brasil', 'decreto', 'lei', 'portaria', 'resolução',
    'o', 'a', 'os', 'as', 'um', 'uma', 'no', 'na', 'do', 'da',
    'e', 'ou', 'de', 'que', 'se', 'em',
    'entrevista', 'depoimento', 'palestra', 'conferência',
    'projeto', 'programa', 'plano',
    'figura', 'fig', 'foto', 'imagem', 'fonte', 'quadro', 'tabela',
    'arquivo', 'acervo', 'coleção', 'documentos',
    'apud',
    # Continuation words (English/Spanish)
    'available', 'accessed', 'retrieved', 'thesis', 'dissertation',
    'translated', 'edited', 'proceedings', 'journal',
    'barcelona', 'london', 'londres', 'paris', 'madrid', 'berlin',
    'cambridge', 'oxford', 'chicago', 'princeton', 'roma', 'rome',
    'buenos', 'bogotá', 'santiago', 'lisboa', 'coimbra',
    'brasília', 'curitiba', 'recife', 'salvador', 'fortaleza',
    'campinas', 'niterói', 'vitória', 'goiânia', 'florianópolis',
    'petrópolis',
    # Common nouns that look like names but aren't
    'le', 'la', 'el', 'il', 'die', 'der', 'das', 'the',
    'vol', 'n°', 'nº', 'cap', 'parte',
}

# Cities that commonly appear after year (2-word cities)
NOT_AUTHOR_BIGRAMS = {
    'são paulo', 'rio de', 'porto alegre', 'belo horizonte',
    'nova york', 'new york', 'new haven', 'buenos aires',
    'juiz de',
}

# ── Common first names that confirm a split point ───────────────────────────
# If the word after the comma is a known first name, we're more confident
COMMON_FIRST_NAMES = {
    'ana', 'antonio', 'antônio', 'carlos', 'cláudio', 'claudio',
    'danilo', 'edson', 'eduardo', 'fernando', 'flávia', 'flávio',
    'guilherme', 'hugo', 'joão', 'jorge', 'josé', 'júlio',
    'kenneth', 'lina', 'lucio', 'lúcio', 'luís', 'luis',
    'marcelo', 'marcos', 'maria', 'marlene', 'mário', 'mônica',
    'nelson', 'oscar', 'paulo', 'pedro', 'rafael', 'renato',
    'reyner', 'roberto', 'ruth', 'sérgio', 'sergio', 'silvio',
    'sylvia', 'yves', 'alberto', 'alcilia', 'aline', 'andré',
    'beatriz', 'cecília', 'celso', 'cristina', 'diego', 'elisabetta',
    'fábio', 'francisco', 'frederico', 'gabriel', 'giuseppe',
    'gustavo', 'helio', 'hélio', 'henrique', 'isabella', 'jacques',
    'jean', 'juliana', 'lauro', 'leonardo', 'letícia', 'luciana',
    'manfredo', 'marina', 'martin', 'matheus', 'miguel', 'nicolas',
    'otavio', 'otávio', 'patrícia', 'raul', 'regina', 'ricardo',
    'rodrigo', 'rosana', 'sandra', 'sigfried', 'simone', 'sonia',
    'tiago', 'vera', 'vicente', 'wagner', 'walter', 'wilson',
    # initials
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
    'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w',
}


def is_likely_author(word):
    """Check if a word looks like an author family name (not a common noun/city)."""
    w_lower = word.lower().rstrip('.,;:')
    if w_lower in NOT_AUTHOR_WORDS:
        return False
    # Must be at least 2 chars
    if len(w_lower) < 2:
        return False
    # Must start with a letter
    if not word[0].isalpha():
        return False
    return True


def is_abnt_author(text):
    """Check if text starts with ABNT-style author: 'SOBRENOME, Nome' or 'SOBRENOME, INICIAIS'."""
    # At least 2 uppercase letters in family name, then comma, then capital letter
    m = re.match(r'([A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ\s]+),\s*([A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ])', text)
    if not m:
        return False
    family = m.group(1).strip()
    # Discard if it's just a single short word (like "IN", "EM")
    if len(family) < 3:
        return False
    # Discard known non-author words
    if family.lower() in NOT_AUTHOR_WORDS:
        return False
    return True


def is_intl_author(text):
    """Check if text starts with international-style author: 'Sobrenome, Nome'."""
    m = re.match(r'([A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ][a-záàãâéêíóôõúüçñ]+(?:\s+[a-záàãâéêíóôõúüçñ]+)*),\s*([A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ])', text)
    if not m:
        return False
    family = m.group(1).strip()
    given_initial = m.group(2)
    # Check family name (full or first word) is not a common word
    first_word = family.split()[0].lower() if family else ''
    if family.lower() in NOT_AUTHOR_WORDS or first_word in NOT_AUTHOR_WORDS:
        return False
    # Family name should be at least 3 chars
    if len(family) < 3:
        return False
    return True


# ── Split patterns ──────────────────────────────────────────────────────────

def find_split_points(ref):
    """Find all split points in a reference string.

    Returns list of (position, confidence, description) tuples.
    Position is the index where the NEW reference begins.
    """
    splits = []

    if len(ref) < 80:
        return splits  # too short to be concatenated

    # Pattern 1: Pipe character (⏐) — separates refs from footnotes
    # Split at pipe; keep the ref part, discard the footnote part if it's
    # clearly not a reference (running text, numbered footnotes)
    # Multiple pipe-like chars found in data: ⏐ (U+23D0), \uf8e6, \uf0bd (PUA), | (U+7C)
    # Only match PUA chars and ⏐ as pipe separators (regular | is too common)
    pipe_pattern = r'\s*[\u23d0\uf8e6\uf0bd]\s*'
    for m in re.finditer(pipe_pattern, ref):
        pos = m.start()
        if pos > 30:  # must have substantial ref before the pipe
            splits.append((pos, 'pipe', 'Pipe separator'))

    # Pattern 2: "year. AUTHOR," — ABNT style after year
    for m in re.finditer(r'(\d{4}[a-z]?)\.\s+', ref):
        after_pos = m.end()
        remaining = ref[after_pos:]
        year = m.group(1)

        # Skip if too close to start (likely the first ref's own year info)
        if m.start() < 30:
            continue

        # Check if what follows is an ABNT author
        if is_abnt_author(remaining):
            splits.append((after_pos, 'year_abnt', f'year({year}). + ABNT author'))
            continue

        # Check if what follows is an international author
        if is_intl_author(remaining):
            splits.append((after_pos, 'year_intl', f'year({year}). + intl author'))
            continue

    # Pattern 3: Double/triple space + ABNT author
    for m in re.finditer(r'\s{2,}', ref):
        after_pos = m.end()
        if after_pos >= len(ref):
            continue
        remaining = ref[after_pos:]

        # Skip if too close to start
        if m.start() < 20:
            continue

        if is_abnt_author(remaining):
            splits.append((after_pos, 'space_abnt', 'Double space + ABNT author'))
        elif is_intl_author(remaining):
            # Be more careful with intl style after double space
            # (could be just a formatting artifact)
            # Require longer text after
            if len(remaining) > 60:
                splits.append((after_pos, 'space_intl', 'Double space + intl author'))

    # Pattern 4: Sentence end + ABNT author (no year needed)
    # ". SOBRENOME, Nome" or ") SOBRENOME, Nome" or "> SOBRENOME, Nome"
    # This is the most aggressive pattern — require strong validation
    for m in re.finditer(r'[.>)]\s+', ref):
        after_pos = m.end()
        remaining = ref[after_pos:]

        # Skip early matches and short remainders
        if m.start() < 40 or len(remaining) < 80:
            continue

        if is_abnt_author(remaining):
            # Extra validation: the ABNT author should have a comma-separated given name
            # THEN a period, THEN what looks like a title (not just another author)
            am = re.match(
                r'([A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇÑ\s]+),\s*'
                r'([A-Za-záàãâéêíóôõúüçÁÉÍÓÚÀÂÊÔÃÕÇ][A-Za-záàãâéêíóôõúüçÁÉÍÓÚÀÂÊÔÃÕÇ\s.]+?)\.\s+'
                r'([A-Za-záàãâéêíóôõúüçÁÉÍÓÚÀÂÊÔÃÕÇ])',
                remaining
            )
            if am and len(remaining) > 80:
                family = am.group(1).strip()
                # Avoid splitting at ". In:" or similar
                before_text = ref[max(0, m.start()-5):m.start()+1]
                if re.search(r'\b[Ii]n\.$', before_text):
                    continue
                # Avoid false positives like "Vol. CSSV," — require family name >= 4 chars
                if len(family) < 4:
                    continue
                # Require that this isn't already covered by a year-based split nearby
                nearby_year = any(
                    abs(s[0] - after_pos) < 30 and s[1].startswith('year')
                    for s in splits
                )
                if not nearby_year:
                    splits.append((after_pos, 'sentence_abnt', 'Sentence end + ABNT author'))

    # Pattern 5: No period after year — "2007 SOBRENOME," or "2008 Sobrenome,"
    # More aggressive: handles both ABNT and intl style without period
    for m in re.finditer(r'(\d{4}[a-z]?)\s+', ref):
        after_pos = m.end()
        remaining = ref[after_pos:]
        year = m.group(1)

        if m.start() < 30:
            continue

        # Make sure it's not just a year in the middle of a title
        before = ref[max(0, m.start()-10):m.start()]
        # Skip if preceded by common preposition/conjunction or if year is part of title
        if re.search(r'\b(de|em|no|na|do|da|dos|das|ano|anos|entre|desde|até)\s*$', before, re.IGNORECASE):
            continue
        # Skip if this is already covered by a year+period split nearby
        already_covered = any(
            abs(s[0] - after_pos) < 20 and s[1].startswith('year')
            for s in splits
        )
        if already_covered:
            continue

        if is_abnt_author(remaining):
            splits.append((after_pos, 'year_nopunct_abnt', f'year({year}) + ABNT author (no punct)'))
        elif is_intl_author(remaining):
            # Require more context for intl style without period — the remaining
            # text should be long enough to be a complete reference
            if len(remaining) > 60:
                splits.append((after_pos, 'year_nopunct_intl', f'year({year}) + intl author (no punct)'))

    return splits


def deduplicate_splits(splits):
    """Remove splits that are too close together (within 10 chars)."""
    if not splits:
        return splits
    # Sort by position
    splits.sort(key=lambda x: x[0])
    result = [splits[0]]
    for s in splits[1:]:
        if s[0] - result[-1][0] > 10:
            result.append(s)
    return result


def split_reference(ref, splits):
    """Split a reference string at the given split points.

    Returns list of (text, from_pipe) tuples.
    from_pipe indicates if the split that created this part was a pipe split.
    """
    if not splits:
        return [(ref, False)]

    splits = deduplicate_splits(splits)
    parts = []
    prev = 0

    for pos, kind, desc in splits:
        part = ref[prev:pos].strip()
        if kind == 'pipe':
            # Trim trailing pipe chars
            part = part.rstrip('\u23d0\uf8e6\uf0bd').strip()
        if part and len(part) > 10:  # don't keep tiny fragments
            parts.append((part, False))
        prev = pos

    # Last part — mark as from_pipe if the split that created it was a pipe split
    last = ref[prev:].strip()
    last_from_pipe = splits[-1][1] == 'pipe' if splits else False
    if last and len(last) > 10:
        parts.append((last, last_from_pipe))

    # Also mark parts that immediately follow a pipe split
    for i in range(len(splits)):
        if splits[i][1] == 'pipe':
            # The part AFTER this pipe split should be marked
            # Find which part index corresponds to this split
            target_idx = i + 1  # +1 because parts[0] is before splits[0]
            if target_idx < len(parts):
                text, _ = parts[target_idx]
                parts[target_idx] = (text, True)

    return parts if parts else [(ref, False)]


def is_footnote_text(text):
    """Check if text looks like footnote/running text rather than a reference.

    Used specifically for content after a pipe (⏐) separator.
    Conservative: only returns True when very confident it's NOT a reference.
    """
    text = text.strip()
    # Strip leading pipe chars and footnote numbers
    text = re.sub(r'^[\u23d0\uf8e6\uf0bd]\s*', '', text)
    text = re.sub(r'^\d+\s+', '', text).strip()

    if not text:
        return True
    if len(text) < 15:
        return True

    # If it starts with an ABNT or intl author, it's likely a reference
    if is_abnt_author(text):
        return False
    if is_intl_author(text):
        return False
    # If it contains a year and author pattern, it's likely a reference
    if re.search(r'[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]{2,},\s*[A-Z]', text[:150]):
        return False
    if re.search(r'[A-Z][a-z]+,\s*[A-Z][a-z]', text[:150]):
        return False

    # Running text with lots of common words
    words = text.split()
    if len(words) > 8:
        common = {'o', 'a', 'os', 'as', 'de', 'do', 'da', 'dos', 'das',
                  'um', 'uma', 'que', 'se', 'em', 'no', 'na', 'por', 'com',
                  'é', 'foi', 'são', 'ser', 'como', 'mais', 'não', 'ou',
                  'para', 'entre', 'este', 'esta', 'esse', 'essa',
                  'the', 'of', 'and', 'in', 'to', 'is', 'was', 'a', 'an'}
        ratio = sum(1 for w in words if w.lower() in common) / len(words)
        if ratio > 0.30:
            return True

    return False


def process_article(article_id, refs, verbose=False):
    """Process all references for an article.

    Returns (new_refs, changes) where changes is a list of descriptions.
    """
    new_refs = []
    changes = []

    for i, ref in enumerate(refs):
        ref = ref.strip()
        if not ref:
            continue

        splits = find_split_points(ref)

        if not splits:
            new_refs.append(ref)
            continue

        parts_with_flags = split_reference(ref, splits)

        if len(parts_with_flags) > 1:
            # Filter out footnote text that came from pipe splits
            filtered_parts = []
            for j, (part, from_pipe) in enumerate(parts_with_flags):
                if from_pipe and is_footnote_text(part):
                    if verbose:
                        preview = part[:80] + '...' if len(part) > 80 else part
                        changes.append(f'  ref#{i}: DISCARDED footnote: {preview}')
                else:
                    # Clean pipe chars from the text
                    cleaned = re.sub(r'\s*[\u23d0\uf8e6\uf0bd]\s*', '', part).strip()
                    # Strip leading footnote numbers from pipe parts
                    if from_pipe:
                        cleaned = re.sub(r'^\d+\s+', '', cleaned).strip()
                    if cleaned and len(cleaned) > 10:
                        filtered_parts.append(cleaned)

            if len(filtered_parts) > 1 or len(filtered_parts) != len(parts_with_flags):
                split_desc = ', '.join(f'{s[2]}' for s in splits[:3])
                if len(splits) > 3:
                    split_desc += f' (+{len(splits)-3} more)'
                changes.append(
                    f'  ref#{i}: {len(ref)} chars → {len(filtered_parts)} parts '
                    f'[{split_desc}]'
                )
                if verbose:
                    for j, part in enumerate(filtered_parts):
                        changes.append(f'    part {j}: {part[:120]}...' if len(part) > 120 else f'    part {j}: {part}')
                new_refs.extend(filtered_parts)
            else:
                new_refs.extend(filtered_parts)
        else:
            part_text = parts_with_flags[0][0]
            new_refs.append(part_text)

    return new_refs, changes


def remove_non_references(refs, verbose=False):
    """Remove entries that are clearly not bibliographic references.

    Returns (cleaned_refs, removals) where removals is a list of descriptions.
    """
    cleaned = []
    removals = []

    # Patterns for non-references
    non_ref_patterns = [
        # Figure captions
        re.compile(r'^\(?\s*(Fig\.|Figura|Foto|Imagem|Fonte:)\s', re.IGNORECASE),
        # Just URL without context
        re.compile(r'^(https?://|www\.)\S+$', re.IGNORECASE),
        # Bullet points or lists
        re.compile(r'^[•\-–—]\s'),
        # Just punctuation/symbols
        re.compile(r'^[\s•\-–—·.,;:\u23d0\uf8e6\uf0bd]+$'),
        # Very short fragments that are just noise
        re.compile(r'^.{0,10}$'),
    ]

    for i, ref in enumerate(refs):
        ref_stripped = ref.strip()

        if not ref_stripped:
            removals.append(f'  ref#{i}: REMOVED empty')
            continue

        # Very short and no year = likely fragment
        if len(ref_stripped) < 15 and not re.search(r'\d{4}', ref_stripped):
            removals.append(f'  ref#{i}: REMOVED short fragment ({len(ref_stripped)} chars): {ref_stripped}')
            continue

        removed = False
        for pattern in non_ref_patterns:
            if pattern.search(ref_stripped):
                removals.append(f'  ref#{i}: REMOVED non-ref: {ref_stripped[:80]}')
                removed = True
                break

        if not removed:
            cleaned.append(ref)

    return cleaned, removals


def main():
    parser = argparse.ArgumentParser(
        description='Separar referências concatenadas no anais.db')
    parser.add_argument('--slug', help='Processar apenas este seminário')
    parser.add_argument('--dry-run', action='store_true',
                        help='Mostrar mudanças sem aplicar')
    parser.add_argument('--apply', action='store_true',
                        help='Aplicar mudanças ao banco')
    parser.add_argument('--verbose', action='store_true',
                        help='Mostrar detalhes de cada split')
    parser.add_argument('--remove-non-refs', action='store_true',
                        help='Também remover entradas que não são referências')
    parser.add_argument('--only-sdbr', action='store_true',
                        help='Processar apenas seminários nacionais (sdbr*)')
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("Erro: especifique --dry-run ou --apply", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    where_clauses = ["references_ IS NOT NULL", "references_ != ''", "references_ != '[]'"]
    params = []

    if args.slug:
        where_clauses.append("seminar_slug = ?")
        params.append(args.slug)
    elif args.only_sdbr:
        where_clauses.append("seminar_slug LIKE 'sdbr%'")

    where = "WHERE " + " AND ".join(where_clauses)

    cur.execute(
        f"SELECT id, file, seminar_slug, references_ FROM articles {where} ORDER BY id",
        params
    )
    articles = cur.fetchall()

    totals = {
        'articles_changed': 0,
        'refs_before': 0,
        'refs_after': 0,
        'splits': 0,
        'non_refs_removed': 0,
        'by_slug': {},
    }

    for aid, fname, slug, refs_text in articles:
        try:
            refs = json.loads(refs_text)
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(refs, list):
            continue

        totals['refs_before'] += len(refs)

        if slug not in totals['by_slug']:
            totals['by_slug'][slug] = {'before': 0, 'after': 0, 'splits': 0, 'removed': 0}
        totals['by_slug'][slug]['before'] += len(refs)

        # Phase 1: Split concatenated references
        new_refs, split_changes = process_article(aid, refs, verbose=args.verbose)

        # Phase 2: Remove non-references (if requested)
        removal_changes = []
        if args.remove_non_refs:
            new_refs, removal_changes = remove_non_references(new_refs, verbose=args.verbose)

        changed = len(new_refs) != len(refs) or any(
            a.strip() != b.strip() for a, b in zip(refs, new_refs) if len(refs) == len(new_refs)
        )

        if changed:
            totals['articles_changed'] += 1
            n_splits = len(new_refs) - len(refs) + len(removal_changes)
            totals['splits'] += max(0, len(new_refs) - len(refs) + len(removal_changes))
            totals['non_refs_removed'] += len(removal_changes)
            totals['by_slug'][slug]['splits'] += max(0, len(new_refs) - len(refs) + len(removal_changes))
            totals['by_slug'][slug]['removed'] += len(removal_changes)

            if args.dry_run:
                if split_changes or removal_changes:
                    print(f"\n{aid} ({fname}): {len(refs)} refs → {len(new_refs)} refs")
                    for ch in split_changes:
                        print(ch)
                    for ch in removal_changes:
                        print(ch)

            if args.apply:
                cur.execute(
                    "UPDATE articles SET references_ = ? WHERE id = ?",
                    (json.dumps(new_refs, ensure_ascii=False), aid)
                )

        totals['refs_after'] += len(new_refs)
        totals['by_slug'][slug]['after'] += len(new_refs)

    if args.apply:
        conn.commit()

    # Print summary
    print(f"\n{'='*60}")
    print(f"{'RESUMO':^60}")
    print(f"{'='*60}")

    if args.slug:
        print(f"Seminário: {args.slug}")
    elif args.only_sdbr:
        print(f"Seminários: sdbr* (nacionais)")
    else:
        print(f"Seminários: todos")

    print(f"\nArtigos modificados: {totals['articles_changed']}")
    print(f"Refs antes:  {totals['refs_before']}")
    print(f"Refs depois: {totals['refs_after']}")
    print(f"Refs novas (splits):    +{totals['refs_after'] - totals['refs_before'] + totals['non_refs_removed']}")
    if args.remove_non_refs:
        print(f"Não-refs removidas:     -{totals['non_refs_removed']}")
    print(f"Diferença líquida:      {totals['refs_after'] - totals['refs_before']:+d}")

    if len(totals['by_slug']) > 1:
        print(f"\n{'Slug':<12} {'Antes':>6} {'Depois':>7} {'Splits':>7} {'Removidas':>10}")
        print('-' * 50)
        for slug in sorted(totals['by_slug']):
            s = totals['by_slug'][slug]
            diff = s['after'] - s['before']
            if diff != 0:
                print(f"{slug:<12} {s['before']:>6} {s['after']:>7} {s['splits']:>7} {s['removed']:>10}")

    mode = 'DRY RUN' if args.dry_run else 'APLICADO'
    print(f"\nModo: {mode}")

    conn.close()


if __name__ == '__main__':
    main()
