#!/usr/bin/env python3
"""Deduplicação de autores em 5 fases.

Fase 0: Enriquecer nomes usando pilotis.db (match por email).
  - Se o Pilotis tem nome mais completo, atualiza givenname/familyname.
  - Não faz merge, apenas melhora a qualidade dos dados.

Fase 1: Merge por último sobrenome (detecta familyname mal separado).
  - Agrupa pelo último token do familyname normalizado.
  - Compara nome completo (givenname+familyname) concatenado.
  - Detecta: 'Ana | Carolina Bierrenbach' vs 'Ana Carolina de Souza | Bierrenbach'.
  - Corrige a partição (givenname/familyname) do registro mantido.

Fase 2: Merge por variantes (mesmo familyname, givenname é prefixo/abreviação).
  - Automático para alta confiança (nome curto → nome longo).
  - Pula casos onde givenname curto tem ≤1 palavra (ex: "Ana Lima" — ambíguo).

Fase 3: Relatório de casos ambíguos para revisão manual.

Uso:
    python3 scripts/dedup_authors.py           # Executa fases 0+1+2, relata fase 3
    python3 scripts/dedup_authors.py --report  # Apenas relatório (sem alterar DB)
    python3 scripts/dedup_authors.py --dry-run # Mostra o que faria (sem alterar DB)
"""

import sqlite3
import os
import sys
import re
import unicodedata
from collections import defaultdict

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE, 'anais.db')
PILOTIS_PATH = os.path.join(BASE, '..', 'financeiro', 'pilotis', 'dados', 'data', 'pilotis.db')

PARTICLES = {'de', 'da', 'do', 'das', 'dos', 'e', 'del', 'von'}


def strip_accents(s):
    """Remove acentos para comparação fuzzy."""
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def normalize_name(name):
    """Normaliza nome para comparação: minúscula, sem acentos, sem pontos."""
    name = strip_accents(name.lower())
    name = name.replace('.', '').replace(',', '')
    return re.sub(r'\s+', ' ', name).strip()


def is_abbreviation_of(short, long):
    """Verifica se 'short' é abreviação de 'long'."""
    short_n = normalize_name(short)
    long_n = normalize_name(long)

    if short_n == long_n:
        return True
    if long_n.startswith(short_n):
        return True

    short_parts = short_n.split()
    long_parts = long_n.split()

    if len(short_parts) > len(long_parts):
        return False

    for s, l in zip(short_parts, long_parts):
        if s == l:
            continue
        if len(s) == 1 and l.startswith(s):
            continue
        if l.startswith(s) and len(s) >= 2:
            continue
        return False

    return True


def is_variant(gn1, gn2, fn1, fn2):
    """Verifica se dois nomes são variantes do mesmo autor."""
    fn1_n = normalize_name(fn1)
    fn2_n = normalize_name(fn2)
    if fn1_n != fn2_n:
        return False
    return is_abbreviation_of(gn1, gn2) or is_abbreviation_of(gn2, gn1)


def longer_name(name1, name2):
    """Retorna o nome mais completo."""
    parts1 = name1.split()
    parts2 = name2.split()
    if len(parts1) != len(parts2):
        return name1 if len(parts1) > len(parts2) else name2
    if len(name1) != len(name2):
        return name1 if len(name1) > len(name2) else name2
    if strip_accents(name1) == strip_accents(name2):
        return name1 if name1 != strip_accents(name1) else name2
    return name1


def confidence(gn_short, gn_long):
    """Retorna confiança do merge (alta/baixa).

    Baixa: givenname curto tem ≤1 palavra real (ex: "Ana", "Carlos")
    — risco de falso positivo com sobrenomes comuns.
    """
    short_parts = normalize_name(gn_short).split()
    # Filtrar iniciais (1 char)
    real_parts = [p for p in short_parts if len(p) > 1]
    if len(real_parts) <= 1:
        return 'baixa'
    return 'alta'


def full_name_tokens(gn, fn):
    """Retorna tokens normalizados do nome completo, sem partículas."""
    full = normalize_name(f'{gn} {fn}')
    return [t for t in full.split() if t not in PARTICLES]


def full_name_compatible(short_tokens, long_tokens):
    """Verifica se dois nomes completos (sem partículas) são compatíveis.

    Regras:
    - Primeiro token do curto deve casar com primeiro do longo
      (curto pode ser abreviação do longo, mas NÃO o contrário)
    - Último token deve ser igual (garantido pelo agrupamento)
    - Tokens do meio do curto devem aparecer no meio do longo (em ordem)
    """
    if not short_tokens or not long_tokens:
        return False

    # Primeiro token: curto pode ser abreviação do longo, não o contrário
    s0, l0 = short_tokens[0], long_tokens[0]
    if s0 != l0:
        if len(s0) >= 1 and l0.startswith(s0):
            pass  # OK: curto abrevia longo (ex: "a" → "ana")
        else:
            return False  # Rejeita: "matheus" vs "m", "julia" vs "margarida"

    # Último token deve ser igual
    if short_tokens[-1] != long_tokens[-1]:
        return False

    # Se curto tem só 2 tokens (primeiro + último), já casou ambos
    if len(short_tokens) <= 2:
        return True

    # Tokens do meio do curto devem aparecer no meio do longo (em ordem)
    short_middle = short_tokens[1:-1]
    long_middle = long_tokens[1:-1]
    j = 0
    for s in short_middle:
        found = False
        while j < len(long_middle):
            l = long_middle[j]
            j += 1
            if s == l:
                found = True
                break
            # Abreviação: curto abrevia longo
            if len(s) >= 1 and l.startswith(s):
                found = True
                break
        if not found:
            return False
    return True


def get_author_articles(cur, author_id):
    """Retorna lista de (seminar_slug, article_title) do autor."""
    cur.execute('''
        SELECT a.seminar_slug, a.title
        FROM article_author aa
        JOIN articles a ON aa.article_id = a.id
        WHERE aa.author_id = ?
        ORDER BY a.seminar_slug
    ''', (author_id,))
    return cur.fetchall()


def merge_authors(cur, keep_id, remove_id, keep_gn, keep_fn, remove_gn, remove_fn, source='dedup'):
    """Faz merge de remove_id em keep_id."""
    # 1. Registrar variante
    try:
        cur.execute('''
            INSERT OR IGNORE INTO author_variants (author_id, givenname, familyname, source)
            VALUES (?, ?, ?, ?)
        ''', (keep_id, remove_gn, remove_fn, source))
    except Exception:
        pass

    # 2. Mover vínculos article_author
    cur.execute('''
        SELECT article_id, seq, primary_contact, affiliation, bio, country
        FROM article_author WHERE author_id = ?
    ''', (remove_id,))
    links = cur.fetchall()

    for article_id, seq, pc, affil, bio, country in links:
        cur.execute('''
            SELECT 1 FROM article_author
            WHERE article_id = ? AND author_id = ?
        ''', (article_id, keep_id))
        if cur.fetchone():
            cur.execute('DELETE FROM article_author WHERE article_id = ? AND author_id = ?',
                        (article_id, remove_id))
        else:
            cur.execute('''
                UPDATE article_author SET author_id = ?
                WHERE article_id = ? AND author_id = ?
            ''', (keep_id, article_id, remove_id))

    # 3. Mover email/orcid se keep não tem
    cur.execute('SELECT email, orcid FROM authors WHERE id = ?', (remove_id,))
    rem = cur.fetchone()
    cur.execute('SELECT email, orcid FROM authors WHERE id = ?', (keep_id,))
    kp = cur.fetchone()
    updates = {}
    if rem and kp:
        if rem[0] and not kp[0]:
            updates['email'] = rem[0]
        if rem[1] and not kp[1]:
            updates['orcid'] = rem[1]
    if updates:
        sets = ', '.join(f'{k} = ?' for k in updates)
        cur.execute(f'UPDATE authors SET {sets} WHERE id = ?',
                    list(updates.values()) + [keep_id])

    # 4. Atualizar givenname/familyname se remove é mais completo
    best_gn = longer_name(keep_gn, remove_gn)
    if best_gn != keep_gn:
        cur.execute('UPDATE authors SET givenname = ? WHERE id = ?', (best_gn, keep_id))

    # 5. Mover variantes que apontavam para remove
    cur.execute('UPDATE author_variants SET author_id = ? WHERE author_id = ?',
                (keep_id, remove_id))

    # 6. Deletar autor removido
    cur.execute('DELETE FROM authors WHERE id = ?', (remove_id,))


def split_name_canonical(full_tokens_with_particles):
    """Dada lista de tokens (com partículas), separa em (givenname, familyname).

    Regra brasileira: familyname = último token (exceto sufixos).
    Partículas ficam no givenname.
    """
    suffixes = {'filho', 'junior', 'neto', 'sobrinho'}
    if not full_tokens_with_particles:
        return '', ''
    parts = full_tokens_with_particles
    last = parts[-1].lower()
    if last in suffixes and len(parts) >= 3:
        fn = f'{parts[-2]} {parts[-1]}'
        gn = ' '.join(parts[:-2])
    else:
        fn = parts[-1]
        gn = ' '.join(parts[:-1])
    return gn, fn


# ─── Fase 0: Enriquecer com Pilotis ────────────────────────────

def load_pilotis():
    """Carrega nomes e emails do pilotis.db."""
    if not os.path.exists(PILOTIS_PATH):
        print(f'  Pilotis não encontrado: {PILOTIS_PATH}')
        return {}, {}

    pconn = sqlite3.connect(PILOTIS_PATH)
    pc = pconn.cursor()

    # nome por id
    pc.execute('SELECT id, nome FROM pessoas')
    nomes = {row[0]: row[1] for row in pc.fetchall()}

    # email → pessoa_id
    pc.execute('SELECT pessoa_id, email FROM emails')
    emails = {}
    for pid, em in pc.fetchall():
        emails[em.strip().lower()] = pid

    pconn.close()
    return nomes, emails


def split_pilotis_name(full_name):
    """Separa nome completo do Pilotis em (givenname, familyname).

    Regra brasileira: familyname = último sobrenome, exceto sufixos
    (Filho, Junior, Neto, Sobrinho) que ficam no familyname.
    Partículas (de, da, do, das, dos, e) ficam no givenname.
    """
    parts = full_name.strip().split()
    if len(parts) <= 1:
        return full_name, ''

    # Sufixos que fazem parte do familyname
    suffixes = {'filho', 'junior', 'júnior', 'neto', 'sobrinho', 'segundo', 'terceiro'}

    last = parts[-1]
    if last.lower() in suffixes and len(parts) >= 3:
        fn = f'{parts[-2]} {parts[-1]}'
        gn = ' '.join(parts[:-2])
    else:
        fn = parts[-1]
        gn = ' '.join(parts[:-1])

    return gn, fn


def phase0_enrich(cur, dry_run=False):
    """Fase 0: Enriquecer nomes com dados do Pilotis (via email match)."""
    print('=== Fase 0: Enriquecer nomes via Pilotis ===')
    pilotis_nomes, pilotis_emails = load_pilotis()
    if not pilotis_emails:
        print('  Sem dados do Pilotis.\n')
        return 0

    print(f'  Pilotis: {len(pilotis_nomes)} pessoas, {len(pilotis_emails)} emails')

    cur.execute('SELECT id, givenname, familyname, email FROM authors WHERE email IS NOT NULL')
    authors = cur.fetchall()

    enriched = 0
    for aid, gn, fn, email in authors:
        if not email:
            continue
        email_low = email.strip().lower()
        if email_low not in pilotis_emails:
            continue

        pid = pilotis_emails[email_low]
        if pid not in pilotis_nomes:
            continue

        pilotis_full = pilotis_nomes[pid]
        p_gn, p_fn = split_pilotis_name(pilotis_full)

        if not p_gn or not p_fn:
            continue

        # Comparar: pilotis tem nome mais completo?
        anais_full = f'{gn} {fn}'
        anais_n = normalize_name(anais_full)
        pilotis_n = normalize_name(f'{p_gn} {p_fn}')

        if anais_n == pilotis_n:
            continue

        # Verificar se é a mesma pessoa (familyname compatível)
        fn_n = normalize_name(fn)
        pfn_n = normalize_name(p_fn)
        if fn_n != pfn_n:
            continue

        # Pilotis givenname é mais completo?
        best_gn = longer_name(p_gn, gn)
        if best_gn == gn:
            continue

        # Verificar se o nome-alvo já existe como outro autor
        cur.execute('SELECT id FROM authors WHERE givenname = ? AND familyname = ?',
                    (best_gn, fn))
        existing = cur.fetchone()

        if dry_run:
            if existing:
                print(f'  MERGE: "{gn} {fn}" (id={aid}) → existente "{best_gn} {fn}" (id={existing[0]}) [pilotis]')
            else:
                print(f'  ENRIQUECER: "{gn} {fn}" → "{best_gn} {fn}" (pilotis: {pilotis_full})')
        else:
            if existing:
                merge_authors(cur, existing[0], aid, best_gn, fn, gn, fn, 'pilotis_merge')
                print(f'  ⊕ "{gn} {fn}" (id={aid}) → merged em "{best_gn} {fn}" (id={existing[0]})')
            else:
                try:
                    cur.execute('''
                        INSERT OR IGNORE INTO author_variants (author_id, givenname, familyname, source)
                        VALUES (?, ?, ?, 'pilotis_enrich')
                    ''', (aid, gn, fn))
                except Exception:
                    pass
                cur.execute('UPDATE authors SET givenname = ? WHERE id = ?', (best_gn, aid))
                print(f'  ✓ "{gn} {fn}" → "{best_gn} {fn}"')
        enriched += 1

    print(f'  Enriquecidos: {enriched}\n')
    return enriched


# ─── Fase 1: Merge por último sobrenome ──────────────────────────

def phase1_last_surname(cur, dry_run=False):
    """Fase 1: Merge por último token do familyname.

    Detecta familynames mal separados onde parte do nome ficou no familyname.
    Ex: 'Ana | Carolina Bierrenbach' vs 'Ana Carolina de Souza | Bierrenbach'.

    Compara nomes completos concatenados (sem partículas) como subsequência.
    Ao fazer merge, corrige a partição givenname/familyname do registro mantido.
    """
    print('=== Fase 1: Merge por último sobrenome ===')

    cur.execute('SELECT id, givenname, familyname FROM authors ORDER BY id')
    authors = cur.fetchall()

    # Agrupar pelo sobrenome-chave do familyname.
    # Se último token é sufixo (filho, junior, neto, etc.), usar penúltimo.
    suffixes = {'filho', 'fo', 'junior', 'jr', 'neto', 'sobrinho', 'segundo', 'terceiro'}
    by_last = defaultdict(list)
    for aid, gn, fn in authors:
        tokens = normalize_name(fn).split()
        if not tokens:
            continue
        key = tokens[-1]
        if key in suffixes and len(tokens) >= 2:
            key = tokens[-2]
        by_last[key].append((aid, gn, fn))

    merge_count = 0
    skip_count = 0
    processed = set()
    groups_checked = 0
    pairs_compared = 0
    pairs_same_fn = 0

    for last_token, group in sorted(by_last.items()):
        if len(group) < 2:
            continue
        groups_checked += 1

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                id1, gn1, fn1 = group[i]
                id2, gn2, fn2 = group[j]

                pairs_compared += 1

                # Pular se mesmo familyname (já tratado pela fase 2)
                if normalize_name(fn1) == normalize_name(fn2):
                    pairs_same_fn += 1
                    continue

                pair = (min(id1, id2), max(id1, id2))
                if pair in processed:
                    continue

                # Tokens do nome completo (sem partículas)
                tokens1 = full_name_tokens(gn1, fn1)
                tokens2 = full_name_tokens(gn2, fn2)

                if not tokens1 or not tokens2:
                    continue

                # Determinar curto e longo
                if len(tokens1) <= len(tokens2):
                    short_t, long_t = tokens1, tokens2
                    short_id, long_id = id1, id2
                    short_gn, short_fn = gn1, fn1
                    long_gn, long_fn = gn2, fn2
                else:
                    short_t, long_t = tokens2, tokens1
                    short_id, long_id = id2, id1
                    short_gn, short_fn = gn2, fn2
                    long_gn, long_fn = gn1, fn1

                # Verificar compatibilidade dos nomes completos
                if not full_name_compatible(short_t, long_t):
                    continue

                processed.add(pair)

                # Confiança: exigir ≥2 tokens reais no nome curto
                real_short = [t for t in short_t if len(t) > 1]
                if len(real_short) <= 1:
                    skip_count += 1
                    continue

                # Verificar se ambos ainda existem
                cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (short_id,))
                r1 = cur.fetchone()
                cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (long_id,))
                r2 = cur.fetchone()
                if not r1 or not r2:
                    continue

                # Keep = mais completo (long), remove = short
                keep_id, keep_gn, keep_fn = long_id, long_gn, long_fn
                remove_id, remove_gn, remove_fn = short_id, short_gn, short_fn

                arts_keep = get_author_articles(cur, keep_id)
                arts_remove = get_author_articles(cur, remove_id)

                if dry_run:
                    print(f'  MERGE: "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts)')
                else:
                    merge_authors(cur, keep_id, remove_id, keep_gn, keep_fn,
                                  remove_gn, remove_fn, 'dedup_phase1_lastsurname')

                    # Corrigir a partição do nome mantido:
                    # usar o nome completo mais longo para repartir corretamente
                    full_tokens_raw = normalize_name(f'{keep_gn} {keep_fn}').split()
                    # Reconstruir com casing original
                    orig_parts = f'{keep_gn} {keep_fn}'.split()
                    new_gn, new_fn = split_name_canonical(orig_parts)
                    if new_fn and normalize_name(new_fn) != normalize_name(keep_fn):
                        cur.execute('UPDATE authors SET givenname = ?, familyname = ? WHERE id = ?',
                                    (new_gn, new_fn, keep_id))

                    print(f'  ⊕ "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts)')
                    merge_count += 1

    print(f'  Grupos com ≥2 autores: {groups_checked}')
    print(f'  Pares comparados:      {pairs_compared} ({pairs_same_fn} mesmo familyname, {pairs_compared - pairs_same_fn} familyname diferente)')
    print(f'  Compatíveis:           {len(processed)}')
    if dry_run:
        print(f'  Merges previstos:      {len(processed) - skip_count}')
        print(f'  Baixa confiança:       {skip_count} (pulados)')
    else:
        print(f'  Merges executados:     {merge_count}')
        print(f'  Baixa confiança:       {skip_count} (pulados)')

    print()
    return merge_count


# ─── Fase 2: Merge por variantes ────────────────────────────────

def phase2_merge(cur, dry_run=False):
    """Fase 2: Merge automático de variantes de nome (mesmo familyname)."""
    print('=== Fase 2: Merge de variantes de nome ===')

    cur.execute('SELECT COUNT(*) FROM authors')
    before = cur.fetchone()[0]
    print(f'  Autores antes: {before}')

    cur.execute('''
        SELECT a1.id, a1.givenname, a1.familyname,
               a2.id, a2.givenname, a2.familyname
        FROM authors a1
        JOIN authors a2 ON a1.familyname = a2.familyname AND a1.id < a2.id
        WHERE a1.givenname != a2.givenname
        ORDER BY a1.familyname, a1.givenname
    ''')
    candidates = cur.fetchall()

    merge_count = 0
    skip_low = 0
    processed = set()

    for id1, gn1, fn1, id2, gn2, fn2 in candidates:
        if not is_variant(gn1, gn2, fn1, fn2):
            continue

        pair = (min(id1, id2), max(id1, id2))
        if pair in processed:
            continue
        processed.add(pair)

        # Verificar se ambos ainda existem
        cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (id1,))
        r1 = cur.fetchone()
        cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (id2,))
        r2 = cur.fetchone()
        if not r1 or not r2:
            continue

        id1, gn1, fn1 = r1
        id2, gn2, fn2 = r2
        if gn1 == gn2:
            continue
        if not is_variant(gn1, gn2, fn1, fn2):
            continue

        # Decidir quem manter
        best_gn = longer_name(gn1, gn2)
        if best_gn == gn1:
            keep_id, keep_gn, keep_fn = id1, gn1, fn1
            remove_id, remove_gn, remove_fn = id2, gn2, fn2
        else:
            keep_id, keep_gn, keep_fn = id2, gn2, fn2
            remove_id, remove_gn, remove_fn = id1, gn1, fn1

        # Checar confiança
        shorter_gn = remove_gn if len(normalize_name(remove_gn)) <= len(normalize_name(keep_gn)) else keep_gn
        conf = confidence(shorter_gn, keep_gn if shorter_gn == remove_gn else remove_gn)

        if conf == 'baixa':
            skip_low += 1
            continue

        arts_keep = get_author_articles(cur, keep_id)
        arts_remove = get_author_articles(cur, remove_id)

        if dry_run:
            print(f'  MERGE: "{keep_gn} {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} {remove_fn}" ({len(arts_remove)} arts)')
        else:
            merge_authors(cur, keep_id, remove_id, keep_gn, keep_fn, remove_gn, remove_fn, 'dedup_phase2')
            merge_count += 1

    if dry_run:
        print(f'\n  Merges previstos: {merge_count + skip_low}')
        print(f'  Alta confiança:   {len(processed) - skip_low}')
        print(f'  Baixa confiança:  {skip_low} (pulados)')
    else:
        cur.execute('SELECT COUNT(*) FROM authors')
        after = cur.fetchone()[0]
        print(f'  Merges executados: {merge_count}')
        print(f'  Baixa confiança:   {skip_low} (pulados → fase 3)')
        print(f'  Autores depois:    {after}')

    print()
    return merge_count, skip_low


# ─── Fase 3: Relatório de ambíguos ──────────────────────────────

def phase3_report(cur):
    """Fase 3: Lista casos ambíguos (baixa confiança) para revisão manual."""
    print('=== Fase 3: Casos ambíguos (revisão manual) ===')

    cur.execute('''
        SELECT a1.id, a1.givenname, a1.familyname,
               a2.id, a2.givenname, a2.familyname
        FROM authors a1
        JOIN authors a2 ON a1.familyname = a2.familyname AND a1.id < a2.id
        WHERE a1.givenname != a2.givenname
        ORDER BY a1.familyname, a1.givenname
    ''')
    candidates = cur.fetchall()

    count = 0
    processed = set()
    for id1, gn1, fn1, id2, gn2, fn2 in candidates:
        if not is_variant(gn1, gn2, fn1, fn2):
            continue

        pair = (min(id1, id2), max(id1, id2))
        if pair in processed:
            continue
        processed.add(pair)

        shorter_gn = gn2 if len(normalize_name(gn2)) <= len(normalize_name(gn1)) else gn1
        longer_gn_val = gn1 if shorter_gn == gn2 else gn2
        conf = confidence(shorter_gn, longer_gn_val)

        if conf != 'baixa':
            continue

        arts1 = get_author_articles(cur, id1)
        arts2 = get_author_articles(cur, id2)

        print(f'  ? "{gn1} {fn1}" ({len(arts1)} arts) vs "{gn2} {fn2}" ({len(arts2)} arts)')
        for slug, title in arts1:
            print(f'      [{slug}] {title[:55]}')
        for slug, title in arts2:
            print(f'      [{slug}] {title[:55]}')
        print()
        count += 1

    print(f'  Total ambíguos: {count}\n')
    return count


def main():
    dry_run = '--dry-run' in sys.argv
    report_only = '--report' in sys.argv

    if not os.path.exists(DB_PATH):
        print(f'Banco não encontrado: {DB_PATH}')
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM authors')
    total_before = cur.fetchone()[0]
    print(f'Autores no banco: {total_before}\n')

    # Fase 0
    enriched = phase0_enrich(cur, dry_run=dry_run or report_only)

    # Fase 1 — merge por último sobrenome (corrige partição errada)
    merges_p1 = phase1_last_surname(cur, dry_run=dry_run or report_only)

    # Fase 2 — merge por variantes (mesmo familyname)
    merges_p2, low_conf = phase2_merge(cur, dry_run=dry_run or report_only)

    if not dry_run and not report_only:
        conn.commit()

    # Fase 3
    ambiguous = phase3_report(cur)

    # Resumo final
    cur.execute('SELECT COUNT(*) FROM authors')
    total_after = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM author_variants')
    variants = cur.fetchone()[0]

    print(f'{"="*50}')
    print(f'Autores antes:    {total_before}')
    if not dry_run and not report_only:
        print(f'Enriquecidos:     {enriched}')
        print(f'Merges fase 1:    {merges_p1} (último sobrenome)')
        print(f'Merges fase 2:    {merges_p2} (variantes)')
        print(f'Autores depois:   {total_after}')
        print(f'Variantes reg.:   {variants}')
    print(f'Ambíguos:         {ambiguous} (revisão manual)')

    # Top autores
    if not dry_run and not report_only:
        print(f'\nTop 15 autores por nº de artigos:')
        cur.execute('''
            SELECT a.givenname, a.familyname, COUNT(*) as n
            FROM article_author aa JOIN authors a ON aa.author_id = a.id
            GROUP BY a.id ORDER BY n DESC LIMIT 15
        ''')
        for gn, fn, n in cur.fetchall():
            print(f'  {n:3d} artigos — {gn} {fn}')

    conn.close()


if __name__ == '__main__':
    main()
