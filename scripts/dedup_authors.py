#!/usr/bin/env python3
"""Deduplicação de autores em 9 etapas.

Etapa 0: Enriquecer nomes usando pilotis.db (match por email).
Etapa 1: Merge por último sobrenome (detecta familyname mal separado).
Etapa 2: Merge por variantes (mesmo familyname, givenname é prefixo/abreviação).
Etapa 3: Relatório de ambíguos da etapa 2 (baixa confiança).
Etapa 4: Familyname com/sem partícula ("Almeida" vs "de Almeida").
Etapa 5: Primeiro nome real + familyname (variantes de givenname, inclui typos).
Etapa 6: Iniciais → nome completo ("D. M. Macedo" → "Danilo Matoso Macedo").
Etapa 7: Cross-familyname (tokens de um são subset do outro).
Etapa 8: Coautores em comum (pares com ≥2 palavras em comum + coautor compartilhado).

Uso:
    python3 scripts/dedup_authors.py           # Executa etapas 0-8
    python3 scripts/dedup_authors.py --report  # Apenas relatório (sem alterar DB)
    python3 scripts/dedup_authors.py --dry-run # Mostra o que faria (sem alterar DB)
    python3 scripts/dedup_authors.py --phase N # Executa só a etapa N (0-8)
"""

import sqlite3
import os
import sys
import re
import json
import unicodedata
from collections import defaultdict

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE, 'anais.db')
PILOTIS_PATH = os.path.join(BASE, '..', 'financeiro', 'pilotis', 'dados', 'data', 'pilotis.db')

PARTICLES = {
    # Português
    'de', 'da', 'do', 'das', 'dos', 'e',
    # Espanhol
    'del', 'los', 'las', 'la', 'el',
    # Italiano
    'di', 'della', 'delle', 'dello', 'degli', 'dei',
    # Outros
    'von', 'van', 'le',
}
PARTICLES_PT = {'de', 'da', 'do', 'dos', 'das'}
SUFFIXES_ALL = {'filho', 'junior', 'júnior', 'neto', 'netto', 'sobrinho', 'segundo', 'terceiro', 'ii', 'iii'}

# Sobrenomes estrangeiros com partícula integrada (não separar)
FOREIGN_COMPOUND = {
    'De Bonis', 'De Izaga', 'De La Torre', 'De Paoli',
}


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
    """Verifica se 'short' é abreviação de 'long'.

    Testa prefixo (início→início) e sufixo (fim→fim).
    Ex: "J. Silva" abrevia "João Silva" (prefixo)
        "Salvador" abrevia "Luís Salvador" (sufixo — 2o nome usado sozinho)
    """
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

    # Match por prefixo (posição 0→0, 1→1, ...)
    if _parts_match(short_parts, long_parts):
        return True

    # Match por sufixo (últimas N palavras do longo)
    if len(short_parts) < len(long_parts):
        suffix = long_parts[-len(short_parts):]
        if _parts_match(short_parts, suffix):
            return True

    return False


def _parts_match(short_parts, long_parts):
    """Verifica se cada parte do curto casa com a parte correspondente do longo."""
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


def confidence(gn_short, gn_long, familyname=''):
    """Retorna confiança do merge (alta/baixa).

    Baixa: givenname curto tem ≤1 palavra real E sobrenome é ultra-comum
    — risco de falso positivo.

    Se o primeiro nome (não inicial) do curto casa com o do longo, é alta
    confiança — exceto para sobrenomes ultra-comuns com nomes comuns.
    """
    short_parts = normalize_name(gn_short).split()
    long_parts = normalize_name(gn_long).split()
    # Filtrar iniciais (1 char)
    real_parts = [p for p in short_parts if len(p) > 1]

    if len(real_parts) <= 1:
        # Sobrenomes ultra-comuns: risco alto de falso positivo
        COMMON_SURNAMES = {
            'silva', 'santos', 'oliveira', 'souza', 'sousa', 'lima',
            'pereira', 'costa', 'rodrigues', 'almeida', 'nascimento',
            'ferreira', 'araujo', 'araújo', 'carvalho', 'gomes',
            'martins', 'ribeiro', 'rocha', 'barros', 'dias',
            'mendes', 'vasconcellos', 'vieira',
        }
        fn_norm = normalize_name(familyname)
        if fn_norm in COMMON_SURNAMES:
            return 'baixa'

        # Primeiro nome real do curto deve ser >= 3 chars e casar com o longo
        if real_parts:
            first_short = real_parts[0]
            first_long = long_parts[0] if long_parts else ''
            if len(first_short) >= 3 and first_short == first_long:
                return 'alta'

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
    try:
        # 1. Registrar variante
        try:
            cur.execute('''
                INSERT OR IGNORE INTO author_variants (author_id, givenname, familyname, source)
                VALUES (?, ?, ?, ?)
            ''', (keep_id, remove_gn, remove_fn, source))
        except sqlite3.IntegrityError:
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
            _VALID_AUTHOR_UPDATE_COLS = {'email', 'orcid', 'givenname', 'familyname'}
            for k in updates:
                if k not in _VALID_AUTHOR_UPDATE_COLS:
                    raise ValueError(f"merge_authors: invalid column '{k}'")
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
    except Exception:
        cur.connection.rollback()
        raise


def split_name_canonical(full_tokens_with_particles):
    """Dada lista de tokens (com partículas), separa em (givenname, familyname).

    Regra brasileira: familyname = último token (exceto sufixos).
    Partículas ficam no givenname, em minúscula.
    """
    if not full_tokens_with_particles:
        return '', ''
    parts = full_tokens_with_particles
    last = parts[-1].lower()
    if last in SUFFIXES_ALL and len(parts) >= 3:
        fn = f'{parts[-2]} {parts[-1]}'
        gn_parts = parts[:-2]
    else:
        fn = parts[-1]
        gn_parts = parts[:-1]
    # Normalizar casing de partículas no givenname
    gn_parts = [p.lower() if p.lower() in PARTICLES_PT else p for p in gn_parts]
    return ' '.join(gn_parts), fn


# ─── Normalização de partículas ────────────────────────────────

def normalize_particles(cur, dry_run=False):
    """Normaliza partição givenname/familyname e casing de partículas.

    Regra: familyname = último sobrenome. Partículas (de, da, do, dos, das)
    ficam no final do givenname, em minúscula.
    Sufixos (Júnior, Filho, Neto) ficam junto ao sobrenome.
    Sobrenomes estrangeiros compostos (De Bonis, De La Torre) são preservados.
    """
    print('=== Normalizar partículas ===')

    cur.execute('SELECT id, givenname, familyname FROM authors ORDER BY id')
    authors = cur.fetchall()

    fixes = 0
    for aid, gn, fn in authors:
        if not fn or not gn:
            continue

        # Skip known foreign compound surnames
        if fn.strip() in FOREIGN_COMPOUND:
            continue

        # Skip data with commas (needs manual fix)
        if ',' in fn:
            continue

        fn_words = fn.split()

        # Skip familynames that END with a particle (data corruption, not fixable here)
        if fn_words[-1].lower() in PARTICLES_PT:
            continue

        # Check if familyname needs fixing:
        # 1. Has Portuguese particle anywhere (multi-word familyname)
        # 2. Or givenname has capitalized particle
        has_fn_particle = len(fn_words) > 1 and any(w.lower() in PARTICLES_PT for w in fn_words)

        gn_words = gn.split()
        has_gn_cap_particle = any(
            w.lower() in PARTICLES_PT and w[0].isupper()
            for w in gn_words if w
        )

        if not has_fn_particle and not has_gn_cap_particle:
            continue

        # Recombine full name and re-split canonically
        full_parts = f'{gn} {fn}'.split()
        new_gn, new_fn = split_name_canonical(full_parts)

        if new_gn == gn and new_fn == fn:
            continue

        if dry_run:
            print(f'  "{gn} | {fn}" → "{new_gn} | {new_fn}"')
        else:
            # Register old name as variant
            try:
                cur.execute('''
                    INSERT OR IGNORE INTO author_variants (author_id, givenname, familyname, source)
                    VALUES (?, ?, ?, 'particle_norm')
                ''', (aid, gn, fn))
            except Exception:
                pass
            cur.execute('UPDATE authors SET givenname = ?, familyname = ? WHERE id = ?',
                        (new_gn, new_fn, aid))
        fixes += 1

    print(f'  Corrigidos: {fixes}\n')
    return fixes


# ─── Fase 0: Enriquecer com Pilotis ────────────────────────────

def load_pilotis():
    """Carrega nomes e emails do pilotis.db."""
    if not os.path.exists(PILOTIS_PATH):
        print(f'  Pilotis não encontrado: {PILOTIS_PATH}')
        return {}, {}

    pconn = sqlite3.connect(PILOTIS_PATH)
    try:
        pc = pconn.cursor()

        # nome por id
        pc.execute('SELECT id, nome FROM pessoas')
        nomes = {row[0]: row[1] for row in pc.fetchall()}

        # email → pessoa_id
        pc.execute('SELECT pessoa_id, email FROM emails')
        emails = {}
        for pid, em in pc.fetchall():
            emails[em.strip().lower()] = pid

        return nomes, emails
    finally:
        pconn.close()


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
        conf = confidence(shorter_gn, keep_gn if shorter_gn == remove_gn else remove_gn, familyname=keep_fn)

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
        conf = confidence(shorter_gn, longer_gn_val, familyname=fn1)

        if conf != 'baixa':
            continue

        arts1 = get_author_articles(cur, id1)
        arts2 = get_author_articles(cur, id2)

        # Evidências: coautores, afiliação, keywords
        coauth1 = get_coauthor_ids(cur, id1)
        coauth2 = get_coauthor_ids(cur, id2)
        shared_coauth = coauth1 & coauth2

        cur.execute('SELECT DISTINCT affiliation FROM article_author WHERE author_id = ? AND affiliation IS NOT NULL AND affiliation != ""', (id1,))
        affil1 = [r[0] for r in cur.fetchall()]
        cur.execute('SELECT DISTINCT affiliation FROM article_author WHERE author_id = ? AND affiliation IS NOT NULL AND affiliation != ""', (id2,))
        affil2 = [r[0] for r in cur.fetchall()]
        same_affil = bool(set(affil1) & set(affil2)) if affil1 and affil2 else None

        kw1 = get_author_keywords(cur, id1)
        kw2 = get_author_keywords(cur, id2)
        kw_common = kw1 & kw2

        ev = []
        if shared_coauth:
            ev.append(f'{len(shared_coauth)} coautores em comum')
        if same_affil is True:
            ev.append(f'mesma afiliação ({", ".join(set(affil1) & set(affil2))})')
        elif same_affil is False:
            ev.append(f'afil. diferentes ({", ".join(affil1)} vs {", ".join(affil2)})')
        elif not affil1 and not affil2:
            ev.append('sem afiliação')
        if kw_common:
            ev.append(f'{len(kw_common)} kw em comum ({", ".join(sorted(kw_common)[:5])}{"..." if len(kw_common) > 5 else ""})')

        ev_str = f' [{"; ".join(ev)}]' if ev else ''
        print(f'  ? "{gn1} {fn1}" ({len(arts1)} arts) vs "{gn2} {fn2}" ({len(arts2)} arts){ev_str}')
        for slug, title in arts1:
            print(f'      [{slug}] {title[:55]}')
        for slug, title in arts2:
            print(f'      [{slug}] {title[:55]}')
        print()
        count += 1

    print(f'  Total ambíguos: {count}\n')
    return count


# Pares conhecidamente diferentes (falsos positivos) — (id_menor, id_maior)
# Identificados por revisão humana. Ver docs/dedup_autores.md.
SKIP_PAIRS = {
    (20, 606),     # Andrey Rosenthal Schlee ↔ Andrey de Aspiazu Schlee (pai e filho)
    (6, 770),      # Ana Gabriela Godinho Lima ↔ Ana Laura Godinho Lima (irmãs)
    (6, 990),      # Ana Gabriela Godinho Lima ↔ Ana Carolina Gleria Lima
    (6, 2536),     # Ana Gabriela Godinho Lima ↔ Ana Lima (confirmado pela própria)
    (770, 2536),   # Ana Laura Godinho Lima ↔ Ana Lima
    (990, 2536),   # Ana Carolina Gleria Lima ↔ Ana Lima
    (2536, 3007),  # Ana Lima ↔ Ana Carla de Sousa Lima
    (782, 798),    # Candido Malta Campos Neto ↔ Candido Malta Campos (avô/neto)
    (1633, 2334),  # Maria Beatriz Pinheiro Machado ↔ Maria V. S. Machado
    (65, 67),      # Eloane ↔ Eliane Ramos Cantuária (coautoras no mesmo artigo)
    (2653, 3226),  # Aline Machado Vieira (UFRJ) ↔ Aline T. Machado (Mackenzie)
    (271, 1320),   # Carolina Vivas da Costa Milagre ↔ Carolina Costa (sem evidência)
    (2209, 3042),  # Erick Oliveira Silva ↔ Erick Oliveira (sem evidência)
    (1050, 2311),  # Felipe Moraes ↔ Felipe Moura Moraes Cardoso (sem evidência)
}

# Nomes genéricos que causam falsos positivos no cross-familyname
GENERIC_FIRST_NAMES = {
    'maria', 'ana', 'jose', 'joao', 'carlos', 'antonio', 'paulo', 'pedro',
    'luis', 'luiz', 'marcos', 'francisco', 'fernando',
}


def parse_keywords(raw):
    """Parseia keywords de um campo (JSON array ou texto separado por ;)."""
    if not raw:
        return set()
    try:
        kws = json.loads(raw)
        if isinstance(kws, list):
            return {kw.strip().lower() for kw in kws if kw.strip()}
    except (json.JSONDecodeError, TypeError):
        pass
    return {kw.strip().lower() for kw in raw.split(';') if kw.strip()}


def get_author_keywords(cur, author_id):
    """Retorna set de keywords (lowercase) dos artigos de um autor."""
    cur.execute('SELECT keywords FROM articles a JOIN article_author aa ON a.id = aa.article_id WHERE aa.author_id = ? AND keywords IS NOT NULL AND keywords != ""', (author_id,))
    kws = set()
    for r in cur.fetchall():
        kws |= parse_keywords(r[0])
    return kws


def real_tokens(gn, fn):
    """Extrai tokens 'reais' (sem partículas, sem iniciais de 1 char) do nome completo."""
    full = normalize_name(f'{gn} {fn}')
    return [t for t in full.split() if t not in PARTICLES and len(t) > 1]


def first_real_token(gn):
    """Primeiro token real (>1 char, não partícula) do givenname."""
    for t in normalize_name(gn).split():
        if t not in PARTICLES and len(t) > 1:
            return t
    return ''


def get_coauthor_ids(cur, author_id):
    """Retorna set de author_ids que são coautores (compartilham artigos)."""
    cur.execute('''
        SELECT DISTINCT aa2.author_id
        FROM article_author aa1
        JOIN article_author aa2 ON aa1.article_id = aa2.article_id
        WHERE aa1.author_id = ? AND aa2.author_id != ?
    ''', (author_id, author_id))
    return {row[0] for row in cur.fetchall()}


# ─── Etapa 4: Familyname com/sem partícula ─────────────────────

def phase4_particle_familyname(cur, dry_run=False):
    """Etapa 4: Merge autores cujo familyname difere só por partícula.

    Ex: "Caio Anderson da Silva | Almeida" vs "Caio Anderson da Silva de | Almeida"
    Ou: "João | Silva" vs "João da | Silva" (partícula no lugar errado)
    Ou: "Maria | Souza" vs "Maria de | Souza"

    Compara familyname após remover partículas. Exige que o primeiro
    nome real (>1 char) do givenname seja igual.
    """
    print('=== Etapa 4: Familyname com/sem partícula ===')

    cur.execute('SELECT id, givenname, familyname FROM authors ORDER BY id')
    authors = cur.fetchall()

    # Agrupar por familyname normalizado SEM partículas
    by_fn_nopart = defaultdict(list)
    for aid, gn, fn in authors:
        fn_tokens = [t for t in normalize_name(fn).split() if t not in PARTICLES]
        if fn_tokens:
            key = ' '.join(fn_tokens)
            by_fn_nopart[key].append((aid, gn, fn))

    merge_count = 0
    processed = set()

    for fn_key, group in sorted(by_fn_nopart.items()):
        if len(group) < 2:
            continue

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                id1, gn1, fn1 = group[i]
                id2, gn2, fn2 = group[j]

                # Se familyname já é idêntico, fase 2 já tratou
                if normalize_name(fn1) == normalize_name(fn2):
                    continue

                pair = (min(id1, id2), max(id1, id2))
                if pair in processed or pair in SKIP_PAIRS:
                    continue

                # Exigir primeiro nome real igual
                first1 = first_real_token(gn1)
                first2 = first_real_token(gn2)
                if not first1 or not first2 or first1 != first2:
                    continue

                # Verificar compatibilidade do nome completo (tokens sem partículas)
                tokens1 = real_tokens(gn1, fn1)
                tokens2 = real_tokens(gn2, fn2)

                if len(tokens1) <= len(tokens2):
                    short_t, long_t = tokens1, tokens2
                else:
                    short_t, long_t = tokens2, tokens1

                # Todos os tokens do curto devem estar no longo
                long_set = set(long_t)
                if not all(t in long_set for t in short_t):
                    # Tenta abreviação
                    if not full_name_compatible(short_t, long_t):
                        continue

                processed.add(pair)

                # Verificar existência
                cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (id1,))
                r1 = cur.fetchone()
                cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (id2,))
                r2 = cur.fetchone()
                if not r1 or not r2:
                    continue

                # Keep = nome mais completo
                t1 = real_tokens(gn1, fn1)
                t2 = real_tokens(gn2, fn2)
                if len(t2) > len(t1):
                    keep_id, keep_gn, keep_fn = id2, gn2, fn2
                    remove_id, remove_gn, remove_fn = id1, gn1, fn1
                else:
                    keep_id, keep_gn, keep_fn = id1, gn1, fn1
                    remove_id, remove_gn, remove_fn = id2, gn2, fn2

                arts_keep = get_author_articles(cur, keep_id)
                arts_remove = get_author_articles(cur, remove_id)

                if dry_run:
                    print(f'  MERGE: "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts)')
                else:
                    merge_authors(cur, keep_id, remove_id, keep_gn, keep_fn,
                                  remove_gn, remove_fn, 'dedup_phase4_particle')
                    print(f'  ⊕ "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts)')
                merge_count += 1

    print(f'  Merges: {merge_count}\n')
    return merge_count


# ─── Etapa 5: Primeiro nome + familyname ──────────────────────

def phase5_first_plus_family(cur, dry_run=False):
    """Etapa 5: Mesmo primeiro nome real + mesmo familyname, givenname diferente.

    Pega variantes que a etapa 2 não pegou (baixa confiança ou formatação diferente).
    Inclui typos no givenname intermediário (Beisl/Beisi, Fernandes/Fernandez).
    """
    print('=== Etapa 5: Primeiro nome + familyname ===')

    cur.execute('SELECT id, givenname, familyname FROM authors ORDER BY id')
    authors = cur.fetchall()

    # Agrupar por (primeiro nome real, familyname normalizado)
    by_key = defaultdict(list)
    for aid, gn, fn in authors:
        first = first_real_token(gn)
        fn_n = normalize_name(fn)
        if first and fn_n:
            by_key[(first, fn_n)].append((aid, gn, fn))

    merge_count = 0
    processed = set()

    for (first, fn_n), group in sorted(by_key.items()):
        if len(group) < 2:
            continue

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                id1, gn1, fn1 = group[i]
                id2, gn2, fn2 = group[j]

                if normalize_name(gn1) == normalize_name(gn2):
                    continue  # Já tratado

                pair = (min(id1, id2), max(id1, id2))
                if pair in processed or pair in SKIP_PAIRS:
                    continue

                # Tokens sem partículas
                t1 = real_tokens(gn1, fn1)
                t2 = real_tokens(gn2, fn2)

                # Um deve ser subset do outro (ou compatível por abreviação)
                if len(t1) <= len(t2):
                    short_t, long_t = t1, t2
                else:
                    short_t, long_t = t2, t1

                # Exigir ≥3 tokens reais no curto (≥2 é muito genérico: "Ana Lima")
                if len(short_t) < 3:
                    continue

                if not full_name_compatible(short_t, long_t):
                    # Tenta subset: todos os tokens do curto no longo
                    long_set = set(long_t)
                    if not all(t in long_set for t in short_t):
                        continue

                processed.add(pair)

                # Verificar existência
                cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (id1,))
                r1 = cur.fetchone()
                cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (id2,))
                r2 = cur.fetchone()
                if not r1 or not r2:
                    continue

                # Keep = mais artigos ou nome mais longo
                arts1 = get_author_articles(cur, id1)
                arts2 = get_author_articles(cur, id2)

                if len(t2) > len(t1) or (len(t2) == len(t1) and len(arts2) > len(arts1)):
                    keep_id, keep_gn, keep_fn = id2, gn2, fn2
                    remove_id, remove_gn, remove_fn = id1, gn1, fn1
                    arts_keep, arts_remove = arts2, arts1
                else:
                    keep_id, keep_gn, keep_fn = id1, gn1, fn1
                    remove_id, remove_gn, remove_fn = id2, gn2, fn2
                    arts_keep, arts_remove = arts1, arts2

                if dry_run:
                    print(f'  MERGE: "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts)')
                else:
                    merge_authors(cur, keep_id, remove_id, keep_gn, keep_fn,
                                  remove_gn, remove_fn, 'dedup_phase5_first_family')
                    print(f'  ⊕ "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts)')
                merge_count += 1

    print(f'  Merges: {merge_count}\n')
    return merge_count


# ─── Etapa 6: Iniciais → nome completo ──────────────────────

def phase6_initials(cur, dry_run=False):
    """Etapa 6: Merge quando um autor usa iniciais e outro tem nome completo.

    Ex: "D. M. | Macedo" → "Danilo Matoso | Macedo"
    Primeira inicial DEVE bater com primeiro nome (sem pular).
    """
    print('=== Etapa 6: Iniciais → nome completo ===')

    cur.execute('SELECT id, givenname, familyname FROM authors ORDER BY id')
    authors = cur.fetchall()

    # Agrupar por familyname normalizado (sem partículas)
    by_fn = defaultdict(list)
    for aid, gn, fn in authors:
        fn_tokens = [t for t in normalize_name(fn).split() if t not in PARTICLES]
        if fn_tokens:
            by_fn[' '.join(fn_tokens)].append((aid, gn, fn))

    merge_count = 0
    processed = set()

    for fn_key, group in sorted(by_fn.items()):
        if len(group) < 2:
            continue

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                id1, gn1, fn1 = group[i]
                id2, gn2, fn2 = group[j]

                pair = (min(id1, id2), max(id1, id2))
                if pair in processed or pair in SKIP_PAIRS:
                    continue

                gn1_parts = [t for t in normalize_name(gn1).split() if t not in PARTICLES]
                gn2_parts = [t for t in normalize_name(gn2).split() if t not in PARTICLES]

                if not gn1_parts or not gn2_parts:
                    continue

                # Identificar qual tem iniciais e qual tem nomes completos
                has_initials_1 = any(len(p) <= 2 for p in gn1_parts)
                has_initials_2 = any(len(p) <= 2 for p in gn2_parts)

                if has_initials_1 == has_initials_2:
                    continue  # Ambos têm ou nenhum tem iniciais

                if has_initials_1:
                    short_parts, long_parts = gn1_parts, gn2_parts
                    short_id, long_id = id1, id2
                    short_gn, short_fn = gn1, fn1
                    long_gn, long_fn = gn2, fn2
                else:
                    short_parts, long_parts = gn2_parts, gn1_parts
                    short_id, long_id = id2, id1
                    short_gn, short_fn = gn2, fn2
                    long_gn, long_fn = gn1, fn1

                # Primeira inicial DEVE bater com primeiro nome
                if not long_parts[0].startswith(short_parts[0]):
                    continue

                # Verificar demais iniciais em ordem
                li = 0
                match = True
                for sp in short_parts:
                    if li >= len(long_parts):
                        match = False
                        break
                    if len(sp) <= 2:
                        # Inicial: buscar match em long_parts a partir de li
                        found = False
                        while li < len(long_parts):
                            if long_parts[li].startswith(sp):
                                li += 1
                                found = True
                                break
                            li += 1
                        if not found:
                            match = False
                            break
                    else:
                        # Nome completo: deve bater exatamente
                        if long_parts[li] != sp:
                            match = False
                            break
                        li += 1

                if not match:
                    continue

                processed.add(pair)

                # Verificar existência
                cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (short_id,))
                r1 = cur.fetchone()
                cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (long_id,))
                r2 = cur.fetchone()
                if not r1 or not r2:
                    continue

                keep_id, keep_gn, keep_fn = long_id, long_gn, long_fn
                remove_id, remove_gn, remove_fn = short_id, short_gn, short_fn
                arts_keep = get_author_articles(cur, keep_id)
                arts_remove = get_author_articles(cur, remove_id)

                if dry_run:
                    print(f'  MERGE: "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts)')
                else:
                    merge_authors(cur, keep_id, remove_id, keep_gn, keep_fn,
                                  remove_gn, remove_fn, 'dedup_phase6_initials')
                    print(f'  ⊕ "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts)')
                merge_count += 1

    print(f'  Merges: {merge_count}\n')
    return merge_count


# ─── Etapa 7: Cross-familyname (subset de tokens) ──────────────

def phase7_cross_familyname(cur, dry_run=False):
    """Etapa 7: Merge autores com familyname diferente quando um nome é subset do outro.

    Ex: "Luciana | Saboia" vs "Luciana Cristina Saboia Ormonda de Almeida | Cruz"
    → tokens(Luciana Saboia) ⊂ tokens(Luciana Cristina Saboia Ormonda Almeida Cruz)

    Agrupa pelo primeiro nome real (>3 chars). Para cada par com familyname diferente,
    verifica se os tokens reais do menor estão todos contidos no maior.
    Exige ≥2 tokens reais em comum.

    CUIDADO: nomes genéricos (Maria, Ana, José) + sobrenome comum = falso positivo.
    """
    print('=== Etapa 7: Cross-familyname (subset de tokens) ===')

    cur.execute('SELECT id, givenname, familyname FROM authors ORDER BY id')
    authors = cur.fetchall()

    # Agrupar pelo primeiro nome real (>3 chars para evitar iniciais/partículas)
    by_first = defaultdict(list)
    for aid, gn, fn in authors:
        first = first_real_token(gn)
        if first and len(first) > 3:
            by_first[first].append((aid, gn, fn))

    merge_count = 0
    report_count = 0
    processed = set()

    for first, group in sorted(by_first.items()):
        if len(group) < 2:
            continue

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                id1, gn1, fn1 = group[i]
                id2, gn2, fn2 = group[j]

                # Só interessam familynames DIFERENTES
                if normalize_name(fn1) == normalize_name(fn2):
                    continue

                pair = (min(id1, id2), max(id1, id2))
                if pair in processed or pair in SKIP_PAIRS:
                    continue

                t1 = real_tokens(gn1, fn1)
                t2 = real_tokens(gn2, fn2)

                if len(t1) <= len(t2):
                    short_t, long_t = t1, t2
                    short_id, long_id = id1, id2
                    short_gn, short_fn = gn1, fn1
                    long_gn, long_fn = gn2, fn2
                else:
                    short_t, long_t = t2, t1
                    short_id, long_id = id2, id1
                    short_gn, short_fn = gn2, fn2
                    long_gn, long_fn = gn1, fn1

                # Exigir ≥2 tokens reais no curto
                if len(short_t) < 2:
                    continue

                # Todos os tokens do curto devem estar no longo
                long_set = set(long_t)
                if not all(t in long_set for t in short_t):
                    continue

                # Contar tokens em comum
                common = set(short_t) & long_set
                if len(common) < 2:
                    continue

                # O familyname (tokens reais) do curto DEVE estar entre os
                # tokens do longo. Sem isso, pega falsos positivos como
                # "Erick Oliveira" ≠ "Erick Oliveira Silva"
                short_fn_tokens = [t for t in normalize_name(short_fn).split() if t not in PARTICLES and len(t) > 1]
                long_fn_tokens = [t for t in normalize_name(long_fn).split() if t not in PARTICLES and len(t) > 1]
                # O familyname do curto deve estar presente no nome completo do longo
                if short_fn_tokens and not all(t in long_set for t in short_fn_tokens):
                    continue

                # Rejeitar se os familynames não têm NENHUM token em comum
                # (ex: "Oliveira" vs "Silva" — nenhum overlap no sobrenome)
                fn_common = set(short_fn_tokens) & set(long_fn_tokens)
                if not fn_common and short_fn_tokens and long_fn_tokens:
                    # O familyname do curto deve pelo menos aparecer no givenname do longo
                    long_gn_tokens = [t for t in normalize_name(long_gn).split() if t not in PARTICLES and len(t) > 1]
                    if not any(t in long_gn_tokens for t in short_fn_tokens):
                        continue

                processed.add(pair)

                # Reportar (não auto-merge) quando:
                # - nome genérico com poucos tokens
                # - só 2 tokens em comum (pouca evidência)
                is_generic = first in GENERIC_FIRST_NAMES and len(short_t) == 2
                is_low_evidence = len(common) <= 2

                # Verificar existência
                cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (short_id,))
                r1 = cur.fetchone()
                cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (long_id,))
                r2 = cur.fetchone()
                if not r1 or not r2:
                    continue

                arts_short = get_author_articles(cur, short_id)
                arts_long = get_author_articles(cur, long_id)

                # Keep = mais artigos, ou nome mais longo se empate
                if len(arts_long) > len(arts_short) or (len(arts_long) == len(arts_short) and len(long_t) >= len(short_t)):
                    keep_id, keep_gn, keep_fn = long_id, long_gn, long_fn
                    remove_id, remove_gn, remove_fn = short_id, short_gn, short_fn
                    arts_keep, arts_remove = arts_long, arts_short
                else:
                    keep_id, keep_gn, keep_fn = short_id, short_gn, short_fn
                    remove_id, remove_gn, remove_fn = long_id, long_gn, long_fn
                    arts_keep, arts_remove = arts_short, arts_long

                if is_generic or is_low_evidence:
                    # Apenas reportar com contexto (coautores + afiliação)
                    coauth_keep = get_coauthor_ids(cur, keep_id)
                    coauth_remove = get_coauthor_ids(cur, remove_id)
                    shared_coauth = coauth_keep & coauth_remove

                    # Afiliações
                    cur.execute('SELECT DISTINCT affiliation FROM article_author WHERE author_id = ? AND affiliation IS NOT NULL AND affiliation != ""', (keep_id,))
                    affil_keep = [r[0] for r in cur.fetchall()]
                    cur.execute('SELECT DISTINCT affiliation FROM article_author WHERE author_id = ? AND affiliation IS NOT NULL AND affiliation != ""', (remove_id,))
                    affil_remove = [r[0] for r in cur.fetchall()]
                    same_affil = bool(set(affil_keep) & set(affil_remove)) if affil_keep and affil_remove else None

                    # Keywords em comum (universo temático)
                    kw_keep = get_author_keywords(cur, keep_id)
                    kw_remove = get_author_keywords(cur, remove_id)
                    kw_common = kw_keep & kw_remove

                    evidence = []
                    if shared_coauth:
                        evidence.append(f'{len(shared_coauth)} coautores em comum')
                    if same_affil is True:
                        evidence.append(f'mesma afiliação ({", ".join(set(affil_keep) & set(affil_remove))})')
                    elif same_affil is False:
                        evidence.append(f'afil. diferentes ({", ".join(affil_keep)} vs {", ".join(affil_remove)})')
                    elif not affil_keep and not affil_remove:
                        evidence.append('sem afiliação')
                    if kw_common:
                        evidence.append(f'{len(kw_common)} keywords em comum ({", ".join(sorted(kw_common)[:5])}{"..." if len(kw_common) > 5 else ""})')

                    ev_str = f' [{"; ".join(evidence)}]' if evidence else ''
                    print(f'  ? REVIEW ({len(common)} tokens): "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) vs "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts){ev_str}')
                    for slug, title in arts_keep:
                        print(f'      [{slug}] {title[:55]}')
                    for slug, title in arts_remove:
                        print(f'      [{slug}] {title[:55]}')
                    print()
                    report_count += 1
                elif dry_run:
                    print(f'  MERGE: "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts)')
                    for slug, title in arts_keep:
                        print(f'      [{slug}] {title[:55]}')
                    for slug, title in arts_remove:
                        print(f'      [{slug}] {title[:55]}')
                    print()
                else:
                    merge_authors(cur, keep_id, remove_id, keep_gn, keep_fn,
                                  remove_gn, remove_fn, 'dedup_phase7_cross')
                    print(f'  ⊕ "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts)')
                merge_count += 1

    print(f'  Merges: {merge_count} ({report_count} pendentes de revisão)\n')
    return merge_count


# ─── Etapa 8: Coautores em comum ──────────────────────────────

def phase8_coauthors(cur, dry_run=False):
    """Etapa 8: Pares com ≥2 palavras em comum no nome + coautor compartilhado.

    Sinal mais poderoso: se dois autores com nomes parecidos compartilham
    coautores, provavelmente são a mesma pessoa.
    Cuidado: coautores no MESMO artigo são pessoas DIFERENTES.
    """
    print('=== Etapa 8: Coautores em comum ===')

    cur.execute('SELECT id, givenname, familyname FROM authors ORDER BY id')
    authors = cur.fetchall()

    merge_count = 0
    processed = set()

    # Pré-computar tokens reais de cada autor
    author_info = {}  # aid -> (gn, fn)
    author_tokens = {}
    for aid, gn, fn in authors:
        author_info[aid] = (gn, fn)
        author_tokens[aid] = set(real_tokens(gn, fn))

    # Build inverted index: article -> set of author_ids
    cur.execute('SELECT article_id, author_id FROM article_author')
    article_to_authors = defaultdict(set)
    author_to_articles = defaultdict(set)
    for art_id, auth_id in cur.fetchall():
        article_to_authors[art_id].add(auth_id)
        author_to_articles[auth_id].add(art_id)

    # Build coauthor sets from inverted index (no per-pair DB queries)
    coauthor_sets = {}
    for aid in author_info:
        coauths = set()
        for art_id in author_to_articles.get(aid, set()):
            coauths.update(article_to_authors[art_id])
        coauths.discard(aid)
        if coauths:
            coauthor_sets[aid] = coauths

    # Build candidate pairs: only authors that share at least one coauthor
    # (i.e., author A has coauthor C, and author B also has coauthor C)
    coauth_to_authors = defaultdict(set)
    for aid, coauths in coauthor_sets.items():
        for c in coauths:
            coauth_to_authors[c].add(aid)

    candidate_pairs = set()
    for coauth_id, connected in coauth_to_authors.items():
        connected_list = sorted(connected)
        for i in range(len(connected_list)):
            for j in range(i + 1, len(connected_list)):
                candidate_pairs.add((connected_list[i], connected_list[j]))

    # Pre-compute same-article pairs (coauthors on same paper = different people)
    same_article_pairs = set()
    for art_id, auth_ids in article_to_authors.items():
        auth_list = sorted(auth_ids)
        for i in range(len(auth_list)):
            for j in range(i + 1, len(auth_list)):
                same_article_pairs.add((auth_list[i], auth_list[j]))

    # Only compare candidate pairs
    for id1, id2 in sorted(candidate_pairs):
        pair = (id1, id2)
        if pair in processed or pair in SKIP_PAIRS:
            continue

        if id1 not in author_info or id2 not in author_info:
            continue

        gn1, fn1 = author_info[id1]
        gn2, fn2 = author_info[id2]

        t1 = author_tokens.get(id1, set())
        t2 = author_tokens.get(id2, set())

        # ≥3 palavras reais em comum (≥2 é muito frouxo)
        common = t1 & t2
        if len(common) < 3:
            continue

        # Primeiro nome real deve bater
        first1 = first_real_token(gn1)
        first2 = first_real_token(gn2)
        if first1 != first2:
            continue

        # Já foi tratado por fases anteriores? (familyname idêntico)
        if normalize_name(fn1) == normalize_name(fn2):
            continue

        # Familyname tokens devem ter overlap (evita "Ana Carolina Holanda" ↔ "Ana Carolina Freire")
        fn1_tokens = set(t for t in normalize_name(fn1).split() if t not in PARTICLES and len(t) > 1)
        fn2_tokens = set(t for t in normalize_name(fn2).split() if t not in PARTICLES and len(t) > 1)
        if fn1_tokens and fn2_tokens and not (fn1_tokens & fn2_tokens):
            # Verificar se familyname de um aparece no givenname do outro
            gn1_tokens = set(t for t in normalize_name(gn1).split() if t not in PARTICLES and len(t) > 1)
            gn2_tokens = set(t for t in normalize_name(gn2).split() if t not in PARTICLES and len(t) > 1)
            if not (fn1_tokens & gn2_tokens) and not (fn2_tokens & gn1_tokens):
                continue

        processed.add(pair)

        # NÃO contar se estão no MESMO artigo (seriam coautores = pessoas diferentes)
        if pair in same_article_pairs:
            continue  # Coautores no mesmo artigo = pessoas diferentes

        # Verificar coautores em comum (from pre-computed sets)
        shared = coauthor_sets.get(id1, set()) & coauthor_sets.get(id2, set())

        if not shared:
            continue

        # Verificar existência (pode ter sido mergeado em fase anterior)
        cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (id1,))
        r1 = cur.fetchone()
        cur.execute('SELECT id, givenname, familyname FROM authors WHERE id = ?', (id2,))
        r2 = cur.fetchone()
        if not r1 or not r2:
            continue

        arts1 = get_author_articles(cur, id1)
        arts2 = get_author_articles(cur, id2)

        # Keep = mais artigos
        if len(arts2) > len(arts1) or (len(arts2) == len(arts1) and len(t2) >= len(t1)):
            keep_id, keep_gn, keep_fn = id2, gn2, fn2
            remove_id, remove_gn, remove_fn = id1, gn1, fn1
            arts_keep, arts_remove = arts2, arts1
        else:
            keep_id, keep_gn, keep_fn = id1, gn1, fn1
            remove_id, remove_gn, remove_fn = id2, gn2, fn2
            arts_keep, arts_remove = arts1, arts2

        if dry_run:
            print(f'  MERGE: "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts) [{len(shared)} coautores em comum]')
        else:
            merge_authors(cur, keep_id, remove_id, keep_gn, keep_fn,
                          remove_gn, remove_fn, 'dedup_phase8_coauthors')
            print(f'  ⊕ "{keep_gn} | {keep_fn}" ({len(arts_keep)} arts) << "{remove_gn} | {remove_fn}" ({len(arts_remove)} arts) [{len(shared)} coautores em comum]')
        merge_count += 1

    print(f'  Merges: {merge_count}\n')
    return merge_count


def main():
    dry_run = '--dry-run' in sys.argv
    report_only = '--report' in sys.argv
    phase_only = None
    if '--phase' in sys.argv:
        idx = sys.argv.index('--phase')
        if idx + 1 < len(sys.argv):
            phase_only = int(sys.argv[idx + 1])

    if not os.path.exists(DB_PATH):
        print(f'Banco não encontrado: {DB_PATH}')
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    try:
        cur = conn.cursor()

        cur.execute('SELECT COUNT(*) FROM authors')
        total_before = cur.fetchone()[0]
        print(f'Autores no banco: {total_before}\n')

        def should_run(phase_num):
            return phase_only is None or phase_only == phase_num

        # Normalizar partículas (antes de tudo)
        particle_fixes = 0
        if should_run(-1):
            particle_fixes = normalize_particles(cur, dry_run=dry_run or report_only)

        # Etapa 0
        enriched = 0
        if should_run(0):
            enriched = phase0_enrich(cur, dry_run=dry_run or report_only)

        # Etapa 1 — merge por último sobrenome (corrige partição errada)
        merges_p1 = 0
        if should_run(1):
            merges_p1 = phase1_last_surname(cur, dry_run=dry_run or report_only)

        # Etapa 2 — merge por variantes (mesmo familyname)
        merges_p2 = 0
        low_conf = 0
        if should_run(2):
            merges_p2, low_conf = phase2_merge(cur, dry_run=dry_run or report_only)

        if not dry_run and not report_only:
            conn.commit()

        # Etapa 3 — relatório de ambíguos
        ambiguous = 0
        if should_run(3):
            ambiguous = phase3_report(cur)

        # Etapa 4 — familyname com/sem partícula
        merges_p4 = 0
        if should_run(4):
            merges_p4 = phase4_particle_familyname(cur, dry_run=dry_run or report_only)

        # Etapa 5 — primeiro nome + familyname
        merges_p5 = 0
        if should_run(5):
            merges_p5 = phase5_first_plus_family(cur, dry_run=dry_run or report_only)

        # Etapa 6 — iniciais → nome completo
        merges_p6 = 0
        if should_run(6):
            merges_p6 = phase6_initials(cur, dry_run=dry_run or report_only)

        # Etapa 7 — cross-familyname (subset de tokens)
        merges_p7 = 0
        if should_run(7):
            merges_p7 = phase7_cross_familyname(cur, dry_run=dry_run or report_only)

        # Etapa 8 — coautores em comum
        merges_p8 = 0
        if should_run(8):
            merges_p8 = phase8_coauthors(cur, dry_run=dry_run or report_only)

        if not dry_run and not report_only:
            conn.commit()

        # Resumo final
        cur.execute('SELECT COUNT(*) FROM authors')
        total_after = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM author_variants')
        variants = cur.fetchone()[0]

        print(f'{"="*50}')
        print(f'Autores antes:    {total_before}')
        if not dry_run and not report_only:
            print(f'Partículas fix.:  {particle_fixes}')
            print(f'Enriquecidos:     {enriched}')
            print(f'Merges etapa 1:   {merges_p1} (último sobrenome)')
            print(f'Merges etapa 2:   {merges_p2} (variantes)')
            print(f'Merges etapa 4:   {merges_p4} (partícula familyname)')
            print(f'Merges etapa 5:   {merges_p5} (primeiro nome + familyname)')
            print(f'Merges etapa 6:   {merges_p6} (iniciais)')
            print(f'Merges etapa 7:   {merges_p7} (cross-familyname)')
            print(f'Merges etapa 8:   {merges_p8} (coautores em comum)')
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
    finally:
        conn.close()


if __name__ == '__main__':
    main()
