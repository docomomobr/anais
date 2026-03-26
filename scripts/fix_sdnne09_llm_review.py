#!/usr/bin/env python3
"""
sdnne09 LLM review — corrections found by comparing
plumber files with database fields (50 articles reviewed).

Systematic issues:
1. Footer "9° Seminário Docomomo Norte e Nordeste São Luís, 2022" in abstract_en (10 arts)
2. Footer "São Luís, 2022" appended to references (42 arts)
3. Subtitle truncations and capitalization errors
4. Keywords: splits, spurious entries, capitalization of proper nouns
"""

import json
import re
import sqlite3
import sys

DB = "/home/danilomacedo/Dropbox/docomomo/26-27/anais/anais.db"

FOOTER_PATTERN = r'\s*9° Seminário Docomomo Norte e Nordeste\s*São Luís,?\s*2022\s*'


def main():
    dry_run = '--dry-run' in sys.argv
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    total = 0

    # ═══════════════════════════════════════════════════════════════
    # Phase 1: Clean footer from abstract_en (systematic)
    # ═══════════════════════════════════════════════════════════════
    print("── Phase 1: Footer in abstract_en ──")
    arts = cur.execute(
        "SELECT id, abstract_en FROM articles "
        "WHERE seminar_slug='sdnne09' AND abstract_en LIKE '%Seminário Docomomo%'"
    ).fetchall()

    for art in arts:
        cleaned = re.sub(FOOTER_PATTERN, ' ', art['abstract_en']).strip()
        # normalize double spaces
        cleaned = re.sub(r'  +', ' ', cleaned)
        if cleaned != art['abstract_en']:
            if dry_run:
                print(f"  DRY-RUN {art['id']}: would clean footer from abstract_en")
            else:
                cur.execute("UPDATE articles SET abstract_en=? WHERE id=?",
                            (cleaned, art['id']))
                print(f"  FIXED {art['id']}: cleaned footer from abstract_en")
            total += 1

    # ═══════════════════════════════════════════════════════════════
    # Phase 2: Clean footer from references (systematic)
    # ═══════════════════════════════════════════════════════════════
    print("\n── Phase 2: Footer in references ──")
    arts = cur.execute(
        "SELECT id, references_ FROM articles "
        "WHERE seminar_slug='sdnne09' AND references_ LIKE '%São Luís, 2022%'"
    ).fetchall()

    for art in arts:
        refs = json.loads(art['references_'])
        changed = False
        new_refs = []
        for r in refs:
            # Remove footer patterns
            cleaned = re.sub(r'\s*São Luís,?\s*2022\s*$', '', r).strip()
            # Also clean mid-ref footer
            cleaned = re.sub(FOOTER_PATTERN, ' ', cleaned).strip()
            cleaned = re.sub(r'  +', ' ', cleaned)
            # Remove entries that are ONLY the footer
            if cleaned and cleaned not in ('São Luís, 2022', 'São Luís,2022', '2022'):
                new_refs.append(cleaned)
                if cleaned != r:
                    changed = True
            else:
                changed = True
        if changed:
            new_val = json.dumps(new_refs, ensure_ascii=False)
            if dry_run:
                print(f"  DRY-RUN {art['id']}: would clean footer from {len(refs)} refs → {len(new_refs)} refs")
            else:
                cur.execute("UPDATE articles SET references_=? WHERE id=?",
                            (new_val, art['id']))
                print(f"  FIXED {art['id']}: cleaned footer from refs ({len(refs)} → {len(new_refs)})")
            total += 1

    # ═══════════════════════════════════════════════════════════════
    # Phase 3: Title/subtitle corrections (per article)
    # ═══════════════════════════════════════════════════════════════
    print("\n── Phase 3: Title/subtitle corrections ──")

    title_fixes = [
        # (id, field, old_value, new_value, reason)
        ("sdnne09-003", "title",
         "Adaptabilidade de soluções projetuais trazidas por imigrantes japoneses à Amazônia amapaense no período moderno",
         "Adaptabilidade de soluções projetuais trazidas por imigrantes japoneses à Amazônia amapaense no período moderno-janarista",
         "truncated: missing '-janarista'"),

        ("sdnne09-005", "subtitle",
         "construindo uma narrativa histórica sobre Teresina através de imagens do século XX",
         "construindo uma narrativa histórica sobre Teresina e a obra do Eng. Cícero Ferraz de Sousa Martins no século XX, através de imagens",
         "rewritten: missing engineer's name"),

        ("sdnne09-006", "subtitle",
         "uma análise sobre sua produção arquitetônica",
         "uma análise sobre sua produção arquitetônica aliada aos respectivos contextos",
         "truncated: missing final clause"),

        ("sdnne09-010", "subtitle",
         "a Arquitetura antiga da escola industrial de Cuiabá, MT",
         "a arquitetura antiga da Escola Industrial de Cuiabá, MT",
         "capitalization: 'Arquitetura' lowercase, 'Escola Industrial' is proper noun"),

        ("sdnne09-011", "subtitle",
         None,  # currently NULL
         "uma análise de Vers une Architecture",
         "subtitle missing: present in PDF after colon"),

        ("sdnne09-013", "subtitle",
         "estudo da habitação moderna Rural no Maranhão",
         "estudo da habitação moderna rural no Maranhão",
         "'Rural' should be lowercase"),

        ("sdnne09-014", "subtitle",
         "um estudo sobre a iluminação natural na sede do ministério da Fazenda em Fortaleza",
         "um estudo sobre a iluminação natural na sede do Ministério da Fazenda em Fortaleza",
         "'Ministério da Fazenda' is a proper noun"),

        ("sdnne09-015", "subtitle",
         "quem São as arquitetas de formação moderna em São Luís, MA?",
         "quem são as arquitetas de formação moderna em São Luís, MA?",
         "'São' here is the verb 'ser', not place name"),

        ("sdnne09-020", "subtitle",
         "Modernidade, cultura técnica e Sociedade",
         "modernidade, cultura técnica e sociedade",
         "subtitle starts lowercase; 'Sociedade' not a proper noun"),

        ("sdnne09-022", "subtitle",
         "o edifício do SESI em Crato, CE",
         "o edifício do SESI em Crato – Ceará, Brasil",
         "PDF has 'CEARÁ, BRASIL', not 'CE'"),

        ("sdnne09-023", "subtitle",
         "a residência José Macedo de Acácio Gil Borsoi",
         "a residência José Macedo (⁕1957 - †2000) de Acácio Gil Borsoi",
         "dates missing from subtitle"),

        ("sdnne09-026", "subtitle",
         "Modernidade e tradição na obra de Nícia Paes Bormann",
         "modernidade e tradição na obra de Nícia Paes Bormann",
         "subtitle starts lowercase"),

        ("sdnne09-028", "subtitle",
         "análise do Patrimônio Moderno de Campina Grande",
         "análise do patrimônio moderno de Campina Grande",
         "'Patrimônio Moderno' not a consolidated expression"),

        ("sdnne09-029", "subtitle",
         "a Modernidade tradicionalista em obras de Mato Grosso",
         "a modernidade tradicionalista em obras de Mato Grosso",
         "'Modernidade' not a consolidated expression"),

        ("sdnne09-030", "title",
         "Arquitetura Escolar moderna e saúde",
         "Arquitetura Escolar Moderna e Saúde",
         "'Moderna' part of 'Arquitetura Moderna'; 'Saúde' main title word"),

        ("sdnne09-030", "subtitle",
         "estratégias projetuais de edifícios escolares paulistas (anos 1930)",
         "estratégias projetuais de edifícios escolares paulistas (anos 1930) para prevenção de epidemias e sua relação com as prescrições contra a Covid-19",
         "subtitle truncated: missing second half"),

        ("sdnne09-033", "subtitle",
         "produção arquitetônica feminina no século XX e XXI em São Luís, MA",
         "produção arquitetônica feminina no século XX em São Luís, MA",
         "PDF heading says 'NO SÉCULO XX' without 'e XXI'"),

        ("sdnne09-036", "title",
         "Análise da funcionalidade, tipologia e topologia dos projetos arquitetônicos dos conjuntos habitacionais populares do programa Minha Casa Minha Vida (PMCMV) na cidade de São Luís no Maranhão",
         "Análise da funcionalidade, tipologia e topologia dos projetos arquitetônicos dos conjuntos habitacionais populares do Programa Minha Casa Minha Vida (PMCMV) na cidade de São Luís no Maranhão",
         "'Programa Minha Casa Minha Vida' is a proper name"),

        ("sdnne09-037", "subtitle",
         "o Memorial Padre Cícero em Juazeiro do Norte Ceará",
         "o Memorial Padre Cícero em Juazeiro do Norte, Ceará",
         "missing comma before 'Ceará'"),

        ("sdnne09-039", "title",
         "Edifício colonial e o Modernismo no Centro Histórico de São Luís",
         "Edifício Colonial e o Modernismo no Centro Histórico de São Luís",
         "'Edifício Colonial' is the building's proper name"),

        ("sdnne09-040", "title",
         "Mural de concreto policromado da fachada do edifício Oscar Pereira",
         "Mural de concreto policromado da fachada do Edifício Oscar Pereira",
         "'Edifício Oscar Pereira' is a proper name"),

        ("sdnne09-041", "title",
         "O Cine teatro municipal de Barbalha – CE",
         "O Cine Teatro Municipal de Barbalha – CE",
         "'Cine Teatro Municipal' is a proper name"),

        ("sdnne09-047", "title",
         "Arte, Arquitetura e paisagem",
         "Arte, Arquitetura e Paisagem",
         "'Paisagem' is a main title word"),

        ("sdnne09-047", "subtitle",
         "o Rural de Minas Gerais pelos olhos de Tarsila do Amaral",
         "o rural de Minas Gerais pelos olhos de Tarsila do Amaral",
         "'Rural' should be lowercase"),

        ("sdnne09-048", "subtitle",
         "ponte governador José Sarney e os ecos da Modernidade",
         "ponte Governador José Sarney e os ecos da modernidade",
         "'Governador' is part of proper name; 'Modernidade' lowercase"),

        ("sdnne09-049", "title",
         "O Recôncavo e o reconvexo",
         "O Recôncavo e o Reconvexo",
         "'Reconvexo' parallels 'Recôncavo' in title"),
    ]

    for art_id, field, old_val, new_val, reason in title_fixes:
        cur.execute(f"SELECT {field} FROM articles WHERE id=?", (art_id,))
        row = cur.fetchone()
        current = row[0] if row else None

        if old_val is not None and current != old_val:
            if current == new_val:
                print(f"  SKIP {art_id} {field}: already correct")
                continue
            print(f"  WARNING {art_id} {field}: expected '{(old_val or '')[:60]}' but got '{(current or '')[:60]}'")
        elif old_val is None and current is not None and current.strip():
            if current == new_val:
                print(f"  SKIP {art_id} {field}: already correct")
                continue
            print(f"  WARNING {art_id} {field}: expected empty but has '{(current or '')[:60]}'")

        if current == new_val:
            print(f"  SKIP {art_id} {field}: already correct")
            continue

        if dry_run:
            print(f"  DRY-RUN {art_id} {field}: {reason}")
        else:
            cur.execute(f"UPDATE articles SET {field}=? WHERE id=?", (new_val, art_id))
            print(f"  FIXED {art_id} {field}: {reason}")
        total += 1

    # ═══════════════════════════════════════════════════════════════
    # Phase 4: Keywords corrections
    # ═══════════════════════════════════════════════════════════════
    print("\n── Phase 4: Keywords corrections ──")

    kw_fixes = [
        ("sdnne09-007", "keywords_en",
         json.dumps(["Clorindo Testa", "Centro Cívico de Santa Rosa", "Banco de Londres", "Biblioteca Nacional"], ensure_ascii=False),
         "remove spurious '2022' keyword"),

        ("sdnne09-014", "keywords",
         json.dumps(["iluminação natural", "arquitetura moderna", "Acácio Gil Borsoi", "conforto térmico", "Fortaleza"], ensure_ascii=False),
         "capitalize proper nouns: Acácio Gil Borsoi, Fortaleza"),

        ("sdnne09-014", "keywords_en",
         json.dumps(["natural lighting", "modern architecture", "Acácio Gil Borsoi", "thermal comfort", "Fortaleza"], ensure_ascii=False),
         "capitalize proper nouns; split 'thermal comfort, fortaleza'"),

        ("sdnne09-021", "keywords_en",
         json.dumps(["women architects", "Nélia Romero", "Ceará architecture", "modernism"], ensure_ascii=False),
         "split compound keyword; capitalize proper nouns"),

        ("sdnne09-031", "keywords",
         json.dumps(["Moderno", "São Luís", "Braga Diniz"], ensure_ascii=False),
         "split 'São Luís, Braga Diniz' into 2 keywords"),

        ("sdnne09-033", "keywords",
         json.dumps(["Arquitetura moderna", "feminina", "São Luís"], ensure_ascii=False),
         "'Feminina' → 'feminina' (not a proper noun)"),

        ("sdnne09-035", "keywords_en",
         json.dumps(["brises", "modern architecture", "Fortaleza"], ensure_ascii=False),
         "remove spurious '2022' keyword"),

        ("sdnne09-037", "keywords_en",
         json.dumps(["Padre Cícero Memorial", "conservation", "modern movement"], ensure_ascii=False),
         "fix typo 'moviment' → 'movement'; remove '. 1' contamination"),

        ("sdnne09-041", "keywords",
         json.dumps(["patrimônio", "cine teatro", "requalificação", "Barbalha"], ensure_ascii=False),
         "split 'requalificação, Barbalha' into 2 keywords"),

        ("sdnne09-041", "keywords_en",
         json.dumps(["heritage", "cine theater", "requalification", "Barbalha"], ensure_ascii=False),
         "split 'requalification, Barbalha' into 2 keywords"),

        ("sdnne09-042", "keywords_en",
         json.dumps(["Smart Heritage", "Laser Scanner", "UAV", "Preservation"], ensure_ascii=False),
         "remove '. 1' contamination from 'Preservation'"),

        ("sdnne09-043", "keywords",
         json.dumps(["Banco do Nordeste", "centro cultural", "modernismo", "Juazeiro do Norte"], ensure_ascii=False),
         "split compound keyword"),

        ("sdnne09-043", "keywords_en",
         json.dumps(["Banco do Nordeste", "cultural center", "modernism", "Juazeiro do Norte"], ensure_ascii=False),
         "split compound keyword"),
    ]

    for art_id, field, new_val, reason in kw_fixes:
        cur.execute(f"SELECT {field} FROM articles WHERE id=?", (art_id,))
        row = cur.fetchone()
        current = row[0] if row else None

        if current == new_val:
            print(f"  SKIP {art_id} {field}: already correct")
            continue

        if dry_run:
            print(f"  DRY-RUN {art_id} {field}: {reason}")
            print(f"    OLD: {(current or '')[:100]}")
            print(f"    NEW: {new_val[:100]}")
        else:
            cur.execute(f"UPDATE articles SET {field}=? WHERE id=?", (new_val, art_id))
            print(f"  FIXED {art_id} {field}: {reason}")
        total += 1

    # ═══════════════════════════════════════════════════════════════
    # COMMIT
    # ═══════════════════════════════════════════════════════════════
    if not dry_run:
        conn.commit()
        print(f"\n=== {total} corrections applied ===")
    else:
        print(f"\n=== {total} corrections would be applied (dry-run) ===")

    conn.close()


if __name__ == '__main__':
    main()
