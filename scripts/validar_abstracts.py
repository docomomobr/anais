#!/usr/bin/env python3
"""Validação automática de abstracts — detecta erros sistemáticos de extração.

Regras aprendidas com a revisão humana dos seminários, especialmente sdbr08:
- Abstract PT preenchido com texto em inglês (swap PT↔EN)
- keywords_en presente mas abstract_en ausente (extração incompleta)
- Abstract que é trecho do corpo do texto (não é o resumo real)
- Abstract com lixo (títulos de seção, metadados, keywords vazados)
- Abstract truncado (não termina com pontuação)
- Abstract_en com markers em português
- Abstract ausente quando o padrão do seminário indica que deveria existir

Uso:
    python3 scripts/validar_abstracts.py --slug sdbr08
    python3 scripts/validar_abstracts.py --slug sdbr08 --fix-swap   # corrige swaps PT↔EN
    python3 scripts/validar_abstracts.py                             # todos os seminários
"""

import argparse
import os
import re
import sqlite3
import sys

DB_PATH = "anais.db"

# ── Detecção de idioma leve (sem dependência externa) ────────────────────────

# Palavras muito frequentes em PT que não existem em EN
PT_MARKERS = {
    'este', 'esta', 'artigo', 'trabalho', 'presente', 'pesquisa', 'estudo',
    'objetivo', 'objetivos', 'análise', 'através', 'partir', 'propõe',
    'busca', 'pretende', 'aborda', 'discute', 'investiga', 'apresenta',
    'verificar', 'compreender', 'identificar', 'analisar', 'contribuir',
    'arquitetura', 'patrimônio', 'edifício', 'cidade', 'projeto', 'obras',
    'também', 'além', 'dessa', 'desse', 'ainda', 'entre', 'sobre',
    'como', 'para', 'pela', 'pelo', 'pelos', 'pelas', 'seus', 'suas',
    'uma', 'umas', 'foram', 'sendo', 'será', 'seria', 'pode', 'podem',
    'não', 'são', 'está', 'têm', 'foi', 'havia', 'havia', 'houve',
    'neste', 'nesta', 'deste', 'desta', 'aqui', 'onde',
    'brasileiro', 'brasileira', 'moderno', 'moderna', 'modernista',
    'década', 'século', 'período', 'anos', 'construção', 'produção',
    'resultados', 'considerações', 'conclusão', 'metodologia',
    # Marcadores de início de abstract PT
    'palavras-chave', 'resumo',
}

# Palavras muito frequentes em EN que não existem em PT
EN_MARKERS = {
    'the', 'this', 'that', 'these', 'those', 'which', 'where', 'when',
    'paper', 'article', 'study', 'research', 'analysis', 'approach',
    'aims', 'seeks', 'discusses', 'investigates', 'presents', 'explores',
    'architecture', 'heritage', 'building', 'buildings', 'city', 'design',
    'also', 'between', 'through', 'within', 'however', 'therefore',
    'was', 'were', 'been', 'being', 'have', 'has', 'had', 'would',
    'could', 'should', 'might', 'their', 'them', 'they', 'with',
    'modern', 'modernist', 'brazilian', 'century', 'decade', 'years',
    'construction', 'production', 'results', 'conclusion', 'methodology',
    # Marcadores de início de abstract EN
    'keywords', 'abstract', 'key words',
}

# Palavras em espanhol que indicam idioma ES
ES_MARKERS = {
    'arquitectura', 'patrimonio', 'edificio', 'ciudad', 'proyecto',
    'análisis', 'estudio', 'investigación', 'presenta', 'objetivo',
    'moderno', 'moderna', 'modernista', 'brasileño', 'brasileña',
    'siglo', 'década', 'años', 'construcción', 'producción',
    'palabras', 'clave', 'resumen',
}


def detect_language(text):
    """Detecta idioma do texto (pt, en, es, unknown).

    Retorna (idioma, confiança) onde confiança é float 0-1.
    """
    if not text or len(text) < 30:
        return 'unknown', 0.0

    words = set(re.findall(r'[a-záàâãéêíóôõúüçñ]+', text.lower()))

    pt_count = len(words & PT_MARKERS)
    en_count = len(words & EN_MARKERS)
    es_count = len(words & ES_MARKERS)

    total = pt_count + en_count + es_count
    if total == 0:
        return 'unknown', 0.0

    # Diacríticos PT/ES como tiebreaker
    has_pt_diacritics = bool(re.search(r'[ãõç]', text.lower()))
    has_es_diacritics = bool(re.search(r'[ñ¿¡]', text.lower()))

    if has_pt_diacritics:
        pt_count += 2
    if has_es_diacritics:
        es_count += 2

    scores = {'pt': pt_count, 'en': en_count, 'es': es_count}
    best = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = scores[best] / total if total > 0 else 0

    return best, confidence


def validate_seminar(conn, slug, fix_swap=False):
    """Valida abstracts de um seminário. Retorna lista de issues."""
    cur = conn.cursor()

    articles = cur.execute("""
        SELECT id, title, locale, abstract, abstract_en, abstract_es,
               keywords, keywords_en, keywords_es
        FROM articles WHERE seminar_slug = ? ORDER BY id
    """, (slug,)).fetchall()

    if not articles:
        return []

    # Calcular padrão do seminário
    total = len(articles)
    has_abstract = sum(1 for a in articles if a[3] and a[3].strip())
    has_abstract_en = sum(1 for a in articles if a[4] and a[4].strip())
    has_kw_en = sum(1 for a in articles if a[7] and a[7].strip() and a[7] != '[]')

    pct_abstract = has_abstract / total * 100
    pct_abstract_en = has_abstract_en / total * 100
    pct_kw_en = has_kw_en / total * 100

    issues = []

    for art in articles:
        art_id, title, locale, abstract, abstract_en, abstract_es, kw, kw_en, kw_es = art
        art_issues = []

        # ── 1. Abstract PT preenchido com texto EN (swap) ──
        if abstract and abstract.strip():
            lang, conf = detect_language(abstract)
            if lang == 'en' and conf > 0.5:
                # Verificar se abstract_en está vazio ou tem PT
                if not abstract_en or not abstract_en.strip():
                    art_issues.append(('SWAP_PT_EN', f'abstract parece estar em inglês (conf={conf:.0%}), abstract_en vazio'))
                    if fix_swap:
                        cur.execute("UPDATE articles SET abstract_en = ?, abstract = '' WHERE id = ?",
                                   (abstract, art_id))
                        art_issues[-1] = ('SWAP_PT_EN_FIXED', art_issues[-1][1] + ' → corrigido')
                else:
                    # Ambos preenchidos mas abstract está em EN
                    en_lang, _ = detect_language(abstract_en)
                    if en_lang == 'pt':
                        art_issues.append(('SWAP_BOTH', f'abstract em EN, abstract_en em PT → provavelmente invertidos'))
                        if fix_swap:
                            cur.execute("UPDATE articles SET abstract = ?, abstract_en = ? WHERE id = ?",
                                       (abstract_en, abstract, art_id))
                            art_issues[-1] = ('SWAP_BOTH_FIXED', art_issues[-1][1] + ' → corrigido')

        # ── 2. keywords_en existe mas abstract_en não ──
        if kw_en and kw_en.strip() and kw_en != '[]':
            if not abstract_en or not abstract_en.strip():
                art_issues.append(('KW_EN_NO_ABSTRACT', 'tem keywords_en mas não tem abstract_en → provavelmente faltou extrair'))

        # ── 3. Abstract truncado ──
        for field_name, field_val in [('abstract', abstract), ('abstract_en', abstract_en)]:
            if field_val and field_val.strip():
                text = field_val.strip()
                if len(text) > 50 and text[-1] not in '.?!"\')»':
                    # Não flaggar se termina com keyword-like (já detectado em outro check)
                    if not re.search(r'(Palavras-chave|Keywords|Key words)\s*$', text, re.IGNORECASE):
                        art_issues.append(('TRUNCATED', f'{field_name}: possível truncamento (termina em "...{text[-30:]}")'))

        # ── 4. Keywords vazadas no abstract ──
        for field_name, field_val in [('abstract', abstract), ('abstract_en', abstract_en)]:
            if field_val and field_val.strip():
                if re.search(r'(Palavras[- ]chave|Keywords|Key\s*words)\s*[:.]', field_val, re.IGNORECASE):
                    art_issues.append(('KW_LEAKED', f'{field_name}: contém marcador de keywords'))

        # ── 5. abstract_en com texto PT ──
        if abstract_en and abstract_en.strip():
            lang, conf = detect_language(abstract_en)
            if lang == 'pt' and conf > 0.5:
                art_issues.append(('EN_IS_PT', f'abstract_en parece estar em português (conf={conf:.0%})'))

        # ── 6. Abstract muito curto ──
        if abstract and abstract.strip() and len(abstract.strip()) < 80:
            art_issues.append(('TOO_SHORT', f'abstract muito curto ({len(abstract.strip())} chars)'))
        if abstract_en and abstract_en.strip() and len(abstract_en.strip()) < 60:
            art_issues.append(('TOO_SHORT_EN', f'abstract_en muito curto ({len(abstract_en.strip())} chars)'))

        # ── 7. Abstract ausente quando padrão indica que deveria existir ──
        if pct_abstract >= 70 and (not abstract or not abstract.strip()):
            art_issues.append(('MISSING_PATTERN', f'abstract ausente (padrão do seminário: {pct_abstract:.0f}% têm)'))

        # ── 8. Abstract com título repetido no início ──
        if abstract and title:
            abs_start = abstract.strip()[:len(title) + 20].lower()
            title_lower = title.lower()
            if title_lower in abs_start:
                art_issues.append(('TITLE_IN_ABSTRACT', 'abstract começa com o título do artigo'))

        # ── 9. Abstract com caracteres de controle ──
        for field_name, field_val in [('abstract', abstract), ('abstract_en', abstract_en)]:
            if field_val:
                ctrl_chars = re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', field_val)
                if ctrl_chars:
                    codes = ', '.join(f'U+{ord(c):04X}' for c in set(ctrl_chars))
                    art_issues.append(('CONTROL_CHARS', f'{field_name}: contém caracteres de controle ({codes})'))

        if art_issues:
            issues.append((art_id, art_issues))

    if fix_swap:
        conn.commit()

    return issues


def main():
    parser = argparse.ArgumentParser(description='Valida abstracts no anais.db')
    parser.add_argument('--slug', help='Seminário específico (ex: sdbr08)')
    parser.add_argument('--fix-swap', action='store_true',
                       help='Corrigir automaticamente swaps abstract PT↔EN')
    parser.add_argument('--summary', action='store_true',
                       help='Mostrar apenas contadores por categoria')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.slug:
        slugs = [args.slug]
    else:
        slugs = [row[0] for row in conn.execute(
            "SELECT DISTINCT seminar_slug FROM articles ORDER BY seminar_slug").fetchall()]

    grand_totals = {}

    for slug in slugs:
        issues = validate_seminar(conn, slug, fix_swap=args.fix_swap)

        if not issues:
            continue

        if args.summary:
            cats = {}
            for art_id, art_issues in issues:
                for cat, msg in art_issues:
                    cats[cat] = cats.get(cat, 0) + 1
            if cats:
                total_arts = conn.execute("SELECT COUNT(*) FROM articles WHERE seminar_slug=?", (slug,)).fetchone()[0]
                print(f"\n{slug} ({total_arts} artigos, {len(issues)} com problemas):")
                for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
                    print(f"  {cat}: {count}")
                    grand_totals[cat] = grand_totals.get(cat, 0) + count
        else:
            print(f"\n{'='*60}")
            print(f"{slug}")
            print(f"{'='*60}")
            for art_id, art_issues in issues:
                for cat, msg in art_issues:
                    print(f"  {art_id} [{cat}]: {msg}")

    if args.summary and grand_totals:
        print(f"\n{'='*60}")
        print("TOTAL")
        print(f"{'='*60}")
        for cat, count in sorted(grand_totals.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")

    conn.close()


if __name__ == '__main__':
    main()
