#!/usr/bin/env python3
"""
Entity Resolution — reconhecimento de variantes de nome da mesma pessoa.

Trata a tipologia de erro #3 (ambiguidade de entidades) aplicada a nomes de
autores, conforme descrito em dict/documentacao/ner_fontes.md.

Identifica que "M.B. Cappello", "Maria Beatriz Cappello" e "Maria B. C. Cappello"
são a mesma pessoa. Técnicas:
  - Comparação de familyname exato (normalizado, sem acentos)
  - Jaro-Winkler no familyname (threshold >= 0.92) para variantes ortográficas
  - Análise de prefixos e abreviações no givenname
  - Coautoria: co-aparição no mesmo artigo = pessoas diferentes (sinal negativo)
  - Coautores compartilhados = sinal positivo (reforça match JW)

Uso como módulo:
    from dict.entity_resolution import is_variant, is_abbreviation_of, normalize_name

Uso standalone:
    python3 dict/entity_resolution.py "Maria Beatriz" "Cappello" "M.B." "Cappello"
    python3 dict/entity_resolution.py --test  # roda suite de testes
"""

import re
import unicodedata

try:
    from jellyfish import jaro_winkler_similarity
except ImportError:
    # Fallback puro Python (Jaro-Winkler)
    def jaro_winkler_similarity(s1, s2, p=0.1):
        """Jaro-Winkler similarity (fallback without jellyfish)."""
        if s1 == s2:
            return 1.0
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        search_range = max(len1, len2) // 2 - 1
        if search_range < 0:
            search_range = 0
        flags1 = [False] * len1
        flags2 = [False] * len2
        common = 0
        for i in range(len1):
            lo = max(0, i - search_range)
            hi = min(len2, i + search_range + 1)
            for j in range(lo, hi):
                if not flags2[j] and s1[i] == s2[j]:
                    flags1[i] = flags2[j] = True
                    common += 1
                    break
        if common == 0:
            return 0.0
        k = transpositions = 0
        for i in range(len1):
            if flags1[i]:
                while not flags2[k]:
                    k += 1
                if s1[i] != s2[k]:
                    transpositions += 1
                k += 1
        jaro = (common / len1 + common / len2 + (common - transpositions / 2) / common) / 3.0
        prefix = 0
        for i in range(min(4, len1, len2)):
            if s1[i] == s2[i]:
                prefix += 1
            else:
                break
        return jaro + prefix * p * (1.0 - jaro)


PARTICLES = {'de', 'da', 'do', 'das', 'dos', 'e', 'del', 'von', 'van', 'di'}

# Threshold para Jaro-Winkler no familyname (>= 0.92 = provável variante ortográfica)
JW_THRESHOLD = 0.92


def strip_accents(s):
    """Remove acentos para comparação fuzzy."""
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def normalize_name(name):
    """Normaliza nome para comparação: minúscula, sem acentos, pontos viram espaços."""
    name = strip_accents(name.lower())
    # Pontos entre iniciais viram espaços (M.B. → m b)
    name = name.replace('.', ' ').replace(',', ' ')
    return re.sub(r'\s+', ' ', name).strip()


def is_abbreviation_of(short, long):
    """Verifica se 'short' é abreviação de 'long'.

    Exemplos:
        is_abbreviation_of("M.B.", "Maria Beatriz") → True
        is_abbreviation_of("Ana", "Ana Elísia") → True
        is_abbreviation_of("Maria", "Mariana") → False (parcial)
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

    for s, l in zip(short_parts, long_parts):
        if s == l:
            continue
        if len(s) == 1 and l.startswith(s):
            continue
        if l.startswith(s) and len(s) >= 2:
            continue
        return False

    return True


def familyname_similar(fn1, fn2):
    """Verifica se dois familynames são iguais ou variantes ortográficas.

    Retorna (match, score):
        match=True se iguais (normalizado) ou JW >= threshold.
        score: 1.0 se iguais, JW score se fuzzy.

    Detecta: Cappello/Capello, Villela/Vilella, etc.
    """
    fn1_n = normalize_name(fn1)
    fn2_n = normalize_name(fn2)
    if fn1_n == fn2_n:
        return True, 1.0
    score = jaro_winkler_similarity(fn1_n, fn2_n)
    return score >= JW_THRESHOLD, score


def is_variant(gn1, gn2, fn1, fn2):
    """Verifica se dois nomes são variantes do mesmo autor.

    Etapas:
    1. Familyname: match exato (normalizado) ou Jaro-Winkler >= 0.92
    2. Givenname: um é abreviação do outro

    Exemplos:
        is_variant("Maria Beatriz", "Cappello", "M.B.", "Cappello") → True
        is_variant("Maria Beatriz", "Cappello", "M.B.", "Capello") → True (JW)
        is_variant("Ana", "Lima", "Mariana", "Lima") → False
    """
    fn_match, fn_score = familyname_similar(fn1, fn2)
    if not fn_match:
        return False
    return is_abbreviation_of(gn1, gn2) or is_abbreviation_of(gn2, gn1)


def longer_name(name1, name2):
    """Retorna o nome mais completo entre dois candidatos."""
    parts1 = name1.split()
    parts2 = name2.split()
    if len(parts1) != len(parts2):
        return name1 if len(parts1) > len(parts2) else name2
    if len(name1) != len(name2):
        return name1 if len(name1) > len(name2) else name2
    # Preferir o que tem acentos (mais completo)
    if strip_accents(name1) == strip_accents(name2):
        return name1 if name1 != strip_accents(name1) else name2
    return name1


def confidence(gn_short, gn_long):
    """Retorna confiança do match ('alta' ou 'baixa').

    Baixa: givenname curto tem ≤1 palavra real (ex: "Ana", "Carlos")
    — risco de falso positivo com sobrenomes comuns (Silva, Santos).
    """
    short_parts = normalize_name(gn_short).split()
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
    - Último token deve ser igual
    - Tokens do meio devem aparecer em ordem
    """
    if not short_tokens or not long_tokens:
        return False

    s0, l0 = short_tokens[0], long_tokens[0]
    if s0 != l0:
        if len(s0) >= 1 and l0.startswith(s0):
            pass
        else:
            return False

    if short_tokens[-1] != long_tokens[-1]:
        return False

    if len(short_tokens) <= 2:
        return True

    short_middle = short_tokens[1:-1]
    long_middle = long_tokens[1:-1]
    j = 0
    for s in short_middle:
        found = False
        while j < len(long_middle):
            l = long_middle[j]
            j += 1
            if s == l or (len(s) >= 1 and l.startswith(s)):
                found = True
                break
        if not found:
            return False
    return True


def split_name_canonical(parts):
    """Separa lista de tokens em (givenname, familyname).

    Regra brasileira: familyname = último sobrenome.
    Sufixos (Filho, Júnior, Neto) ficam no familyname.
    Partículas (de, da, do) ficam no givenname.
    """
    suffixes = {'filho', 'junior', 'júnior', 'neto', 'sobrinho', 'segundo', 'terceiro'}
    if not parts:
        return '', ''
    last = parts[-1].lower()
    if last in suffixes and len(parts) >= 3:
        fn = f'{parts[-2]} {parts[-1]}'
        gn = ' '.join(parts[:-2])
    else:
        fn = parts[-1]
        gn = ' '.join(parts[:-1])
    return gn, fn


# ── Coautoria ─────────────────────────────────────────────────────────


def coauthors_of(conn, author_id):
    """Retorna set de author_ids que são coautores (co-aparecem em algum artigo)."""
    rows = conn.execute('''
        SELECT DISTINCT aa2.author_id
        FROM article_author aa1
        JOIN article_author aa2 ON aa1.article_id = aa2.article_id
        WHERE aa1.author_id = ? AND aa2.author_id != ?
    ''', (author_id, author_id)).fetchall()
    return {r[0] for r in rows}


def coappear_in_article(conn, id1, id2):
    """Verifica se dois autores aparecem juntos no mesmo artigo.

    Se sim, são DEFINITIVAMENTE pessoas diferentes (sinal negativo forte).
    """
    row = conn.execute('''
        SELECT COUNT(*) FROM article_author aa1
        JOIN article_author aa2 ON aa1.article_id = aa2.article_id
        WHERE aa1.author_id = ? AND aa2.author_id = ?
    ''', (id1, id2)).fetchone()
    return row[0] > 0


def shared_coauthors(conn, id1, id2):
    """Retorna coautores compartilhados entre dois autores (sem co-aparição direta).

    Coautores compartilhados = sinal positivo de mesma pessoa.
    Ex: se A e B nunca aparecem juntos, mas ambos coautoram com C,
    é mais provável que A e B sejam a mesma pessoa.
    """
    ca1 = coauthors_of(conn, id1)
    ca2 = coauthors_of(conn, id2)
    return ca1 & ca2


def is_variant_with_coauthorship(gn1, gn2, fn1, fn2, conn, id1, id2):
    """is_variant() enriquecido com análise de coautoria.

    Retorna (is_match, reason):
        (False, 'coappear') — aparecem juntos no mesmo artigo = pessoas diferentes
        (False, 'name_mismatch') — nomes não compatíveis
        (True, 'exact') — familyname exato + givenname compatível
        (True, 'jw') — familyname Jaro-Winkler + givenname compatível
        (True, 'jw+coauthors') — JW + coautores compartilhados reforçam
    """
    # 1. Coautoria negativa: co-aparição = pessoas diferentes
    if coappear_in_article(conn, id1, id2):
        return False, 'coappear'

    # 2. Familyname
    fn_match, fn_score = familyname_similar(fn1, fn2)
    if not fn_match:
        return False, 'name_mismatch'

    # 3. Givenname
    gn_ok = is_abbreviation_of(gn1, gn2) or is_abbreviation_of(gn2, gn1)
    if not gn_ok:
        return False, 'name_mismatch'

    # 4. Determinar razão
    if fn_score == 1.0:
        return True, 'exact'

    # Familyname é JW fuzzy — coautores compartilhados reforçam
    shared = shared_coauthors(conn, id1, id2)
    if shared:
        return True, 'jw+coauthors'

    return True, 'jw'


# ── CLI ────────────────────────────────────────────────────────────────

def _run_tests():
    """Suite de testes básicos."""
    tests = [
        # (gn1, fn1, gn2, fn2, expected)
        # Abreviação de givenname
        ("Maria Beatriz", "Cappello", "M.B.", "Cappello", True),
        ("Ana Elísia da", "Costa", "Ana Elísia", "Costa", True),
        ("João Carlos da Silva", "Neto", "J.C.", "Neto", True),
        ("Ana", "Lima", "Mariana", "Lima", False),
        ("Fernando", "Vázquez Ramos", "Fernando Guillermo", "Vázquez Ramos", True),
        ("Ruth Verde", "Zein", "Ruth", "Zein", True),
        # Jaro-Winkler no familyname (variantes ortográficas)
        ("Maria Beatriz", "Cappello", "Maria Beatriz", "Capello", True),
        ("Fábio", "Villela", "Fábio", "Vilella", True),
        ("M.B.", "Cappello", "M.B.", "Capello", True),
        # Familynames diferentes demais (JW < threshold)
        ("Ana", "Silva", "Ana", "Souza", False),
        ("Carlos", "Costa", "Carlos", "Castro", False),
    ]

    passed = 0
    for gn1, fn1, gn2, fn2, expected in tests:
        result = is_variant(gn1, gn2, fn1, fn2)
        status = 'OK' if result == expected else 'FAIL'
        if status == 'FAIL':
            print(f'  {status}: is_variant("{gn1} {fn1}", "{gn2} {fn2}") = {result}, expected {expected}')
        else:
            passed += 1

    # Testes de familyname_similar
    jw_tests = [
        ("Cappello", "Capello", True),
        ("Villela", "Vilella", True),
        ("Silva", "Souza", False),
        ("Costa", "Costa", True),
    ]
    for fn1, fn2, expected in jw_tests:
        match, score = familyname_similar(fn1, fn2)
        status = 'OK' if match == expected else 'FAIL'
        if status == 'FAIL':
            print(f'  {status}: familyname_similar("{fn1}", "{fn2}") = {match} (score={score:.3f}), expected {expected}')
        else:
            passed += 1

    total = len(tests) + len(jw_tests)
    print(f'  {passed}/{total} testes passaram')


if __name__ == '__main__':
    import sys

    if '--test' in sys.argv:
        _run_tests()
    elif len(sys.argv) == 5:
        gn1, fn1, gn2, fn2 = sys.argv[1:5]
        result = is_variant(gn1, gn2, fn1, fn2)
        print(f'is_variant("{gn1} {fn1}", "{gn2} {fn2}") = {result}')
        if result:
            best = longer_name(f'{gn1}', f'{gn2}')
            conf = confidence(gn1 if gn1 != best else gn2, best)
            print(f'  nome mais completo: {best} {fn1}')
            print(f'  confiança: {conf}')
    else:
        print('Uso:')
        print('  python3 dict/entity_resolution.py "givenname1" "familyname1" "givenname2" "familyname2"')
        print('  python3 dict/entity_resolution.py --test')
