#!/usr/bin/env python3
"""
sdnne06 LLM review (step 1.10) — corrections found by comparing
plumber files with database fields.

Issues found and corrected:
1. Art 10: keywords wrong (DB has generic; PDF has specific)
2. Art 12: keywords wrong
3. Art 18: subtitle 'Currais novos' → 'Currais Novos' (proper noun)
4. Art 33: keywords wrong, title should be 'Conjunto Itararé'
5. Art 34: title 'Las plantas bajas' → 'La planta baja' (per PDF); 'Union' → 'Unión' (accent)
6. Art 36: keywords wrong
7. Art 39: keywords wrong
8. Art 41: subtitle 'Pólo' → 'Polo' (new spelling); 'na São Luís' → 'em São Luís'
9. Art 50: keywords wrong
10. Art 52: subtitle typo 'Gesamtkunswerk' → 'Gesamtkunstwerk'
11. Art 54: title typo 'Niemeyr' → 'Niemeyer'
12. Art 56: title missing 'a' — 'para paisagem' → 'para a paisagem' (per PDF)
13. Art 62: subtitle dates wrong per PDF (Castelão 1981 not 1980; 'Receita Federal' → 'Ministério da Fazenda', 1979 → 1983)
14. Art 66: keywords incomplete (only ["moderna"]); PDF has 3 keywords
15. Art 69: 'idearios' → 'ideários' (accent)
16. Art 79: subtitle typo 'edifífio' → 'edifício'
17. Art 88: keywords wrong
18. Art 89: keywords incomplete (only ["campinense"]); PDF has 3 keywords
19. Art 33: keywords_en missing — PDF has them
20. Art 10: keywords_en missing — PDF has them
21. Art 36: keywords_en missing — PDF has them
22. Art 50: keywords_en missing — PDF has them
23. Art 88: keywords_en missing — PDF has them
"""

import json
import sqlite3
import sys

DB = "/home/danilomacedo/Dropbox/docomomo/26-27/anais/anais.db"

_VALID_COLS = frozenset({
    'title', 'subtitle', 'title_es', 'subtitle_es',
    'abstract', 'abstract_en', 'abstract_es',
    'keywords', 'keywords_en', 'keywords_es',
    'references_',
})

def main():
    dry_run = '--dry-run' in sys.argv
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    updates = []

    # 1. Art 10: keywords — PDF: "Arquitetura moderna, estratégias bioclimáticas, arquitetura residencial"
    updates.append(("10", "keywords",
        json.dumps(["arquitetura moderna", "estratégias bioclimáticas", "arquitetura residencial"], ensure_ascii=False),
        '["arquitetura moderna", "soluções bioclimáticas", "eficiência energética"]',
        "keywords differ from PDF"))

    # 1b. Art 10: keywords_en — PDF: "Modern architecture; bioclimatic solutions; residential architecture"
    updates.append(("10", "keywords_en",
        json.dumps(["modern architecture", "bioclimatic solutions", "residential architecture"], ensure_ascii=False),
        None,
        "keywords_en present in PDF but missing in DB"))

    # 2. Art 12: keywords — PDF: "arquitetura moderna, análise projetual, patrimônio moderno"
    updates.append(("12", "keywords",
        json.dumps(["arquitetura moderna", "análise projetual", "patrimônio moderno"], ensure_ascii=False),
        '["complexo arquitetônico", "construção moderna", "análise projetual"]',
        "keywords differ from PDF"))

    # 3. Art 18: subtitle 'Currais novos' → 'Currais Novos'
    updates.append(("18", "subtitle",
        "os projetos do Engenheiro-Arquiteto Otávio Roscoe no contexto de modernização urbana de Currais Novos/RN (década de 1950)",
        "os projetos do Engenheiro-Arquiteto Otávio Roscoe no contexto de modernização urbana de Currais novos/RN (década de 1950)",
        "proper noun: Currais Novos"))

    # 4. Art 33: title 'Itararé' → 'Conjunto Itararé' (per PDF heading)
    updates.append(("33", "title",
        "Conjunto Itararé",
        "Itararé",
        "PDF heading says 'CONJUNTO ITARARÉ'"))

    # 4b. Art 33: subtitle per PDF heading
    updates.append(("33", "subtitle",
        "análise morfológica e reflexos do Urbanismo de Teresina",
        "análise morfológica e influência no Urbanismo de Teresina",
        "PDF subtitle is 'análise morfológica e reflexos do urbanismo'"))

    # 4c. Art 33: keywords — PDF: "História do Urbanismo; Morfologia; Conjunto Habitacional Itararé"
    updates.append(("33", "keywords",
        json.dumps(["história do urbanismo", "morfologia", "Conjunto Habitacional Itararé"], ensure_ascii=False),
        '["Itararé", "morfologia", "urbanismo"]',
        "keywords differ from PDF"))

    # 4d. Art 33: keywords_en — PDF: "History of Urbanism; Morphology; Housing Development Itararé"
    updates.append(("33", "keywords_en",
        json.dumps(["history of urbanism", "morphology", "Housing Development Itararé"], ensure_ascii=False),
        None,
        "keywords_en present in PDF but missing in DB"))

    # 5. Art 34: title correction per PDF
    updates.append(("34", "title",
        "La planta baja, Unión de diferencias",
        "Las plantas bajas, Union de diferencias",
        "PDF heading: 'LA PLANTA BAJA UNIÓN DE DIFERENCIAS' (singular, accent)"))

    # 6. Art 36: keywords — PDF: "modernidade; regionalismo; madeira"
    updates.append(("36", "keywords",
        json.dumps(["modernidade", "regionalismo", "madeira"], ensure_ascii=False),
        '["arquitetura moderna", "madeira", "Zanine Caldas"]',
        "keywords differ from PDF"))

    # 6b. Art 36: keywords_en — PDF: "modern architecture; regionalism; timber construction"
    updates.append(("36", "keywords_en",
        json.dumps(["modern architecture", "regionalism", "timber construction"], ensure_ascii=False),
        None,
        "keywords_en present in PDF but missing in DB"))

    # 7. Art 39: keywords — PDF: "Severiano Porto, processo de projeto, Aldeia SOS do Amazonas"
    updates.append(("39", "keywords",
        json.dumps(["Severiano Porto", "processo de projeto", "Aldeia SOS do Amazonas"], ensure_ascii=False),
        '["Severiano Mário Porto", "tectônica", "solução de design"]',
        "keywords differ from PDF"))

    # 7b. Art 39: keywords_en — PDF: "Severiano Porto, Design Solution, Children's Village Amazonas"
    updates.append(("39", "keywords_en",
        json.dumps(["Severiano Porto", "design solution", "Children's Village Amazonas"], ensure_ascii=False),
        None,
        "keywords_en present in PDF but missing in DB"))

    # 8. Art 41: subtitle corrections
    updates.append(("41", "subtitle",
        "análise da proposta não executada de Lúcio Costa para o Novo Polo Urbano em São Luís-MA, anos 70",
        "análise da proposta não executada de Lúcio Costa para o novo Pólo urbano na São Luís- MA, anos 70",
        "PDF: 'Novo Polo Urbano em São Luís-MA' (Polo sem acento, em not na)"))

    # 9. Art 50: keywords — PDF: "Belém, Arquitetura Moderna, trajetórias"
    updates.append(("50", "keywords",
        json.dumps(["Belém", "arquitetura moderna", "trajetórias"], ensure_ascii=False),
        '["Amazônia", "experiência", "modernidade"]',
        "keywords differ from PDF"))

    # 9b. Art 50: keywords_en — PDF: "Belém, Modern Architecture, trajectories"
    updates.append(("50", "keywords_en",
        json.dumps(["Belém", "modern architecture", "trajectories"], ensure_ascii=False),
        None,
        "keywords_en present in PDF but missing in DB"))

    # 10. Art 52: subtitle typo
    updates.append(("52", "subtitle",
        "João Filgueiras Lima e sua Gesamtkunstwerk",
        "João Filgueiras Lima e sua Gesamtkunswerk",
        "typo: Gesamtkunswerk → Gesamtkunstwerk"))

    # 11. Art 54: title typo
    updates.append(("54", "title",
        "Uma reflexão sobre Acessibilidade na obra de Oscar Niemeyer",
        "Uma reflexão sobre Acessibilidade na obra de Oscar Niemeyr",
        "typo: Niemeyr → Niemeyer"))

    # 12. Art 56: title missing article
    updates.append(("56", "title",
        "A Arquitetura de Miguel Caddah para a paisagem moderna teresinense",
        "A Arquitetura de Miguel Caddah para paisagem moderna teresinense",
        "PDF: 'PARA A PAISAGEM' (missing 'a')"))

    # 13. Art 62: subtitle — PDF says different building names and dates
    updates.append(("62", "subtitle",
        "análise de três edifícios — Estádio Castelão (1981), Ministério da Fazenda (1983) e Memorial Bandeira Tribuzzi (1985)",
        "análise de três edifícios — Receita Federal (1979), Estádio Castelão (1980) e Memorial Bandeira Tribuzzi (1985)",
        "PDF has different buildings/dates: Castelão 1981, Ministério da Fazenda 1983"))

    # 14. Art 66: keywords incomplete — PDF: "Arquitetura Moderna, Significância cultural, Análise tipológica"
    updates.append(("66", "keywords",
        json.dumps(["arquitetura moderna", "significância cultural", "análise tipológica"], ensure_ascii=False),
        '["moderna"]',
        "keywords incomplete in DB; PDF has 3"))

    # 14b. Art 66: keywords_en — PDF: "Modern architecture, cultural significance, typological analysis"
    updates.append(("66", "keywords_en",
        json.dumps(["modern architecture", "cultural significance", "typological analysis"], ensure_ascii=False),
        None,
        "keywords_en present in PDF but missing in DB"))

    # 15. Art 69: keyword missing accent
    updates.append(("69", "keywords",
        json.dumps(["urbanismo moderno", "planos urbanos", "ideários urbanos"], ensure_ascii=False),
        '["urbanismo moderno", "planos urbanos", "idearios urbanos"]',
        "missing accent: idearios → ideários"))

    # 16. Art 79: subtitle typo
    updates.append(("79", "subtitle",
        "edifício Holiday, Recife",
        "edifífio Holiday, Recife",
        "typo: edifífio → edifício"))

    # 17. Art 88: keywords — PDF: "Conforto ambiental, brutalismo, Armando de Holanda"
    updates.append(("88", "keywords",
        json.dumps(["conforto ambiental", "brutalismo", "Armando de Holanda"], ensure_ascii=False),
        '["conforto ambiental", "modernismo", "eficiência"]',
        "keywords differ from PDF"))

    # 17b. Art 88: keywords_en — PDF: "Environmental comfort system, brutalism, Armando de Holanda"
    updates.append(("88", "keywords_en",
        json.dumps(["environmental comfort system", "brutalism", "Armando de Holanda"], ensure_ascii=False),
        None,
        "keywords_en present in PDF but missing in DB"))

    # 18. Art 89: keywords incomplete — PDF: "arquitetura moderna, análise projetual, arquitetura campinense"
    updates.append(("89", "keywords",
        json.dumps(["arquitetura moderna", "análise projetual", "arquitetura campinense"], ensure_ascii=False),
        '["campinense"]',
        "keywords incomplete in DB; PDF has 3"))

    # 18b. Art 89: keywords_en — PDF: "modern architecture, projetual analysis, campina grande architecture"
    updates.append(("89", "keywords_en",
        json.dumps(["modern architecture", "projetual analysis", "Campina Grande architecture"], ensure_ascii=False),
        None,
        "keywords_en present in PDF but missing in DB"))

    # Execute updates
    count = 0
    for art_id, field, new_val, old_val, reason in updates:
        if field not in _VALID_COLS:
            raise ValueError(f"Invalid column: {field}")
        # Verify current value matches expected
        cur.execute(f"SELECT {field} FROM articles WHERE seminar_slug='sdnne06' AND id=?", (art_id,))
        row = cur.fetchone()
        current = row[0] if row else None

        if old_val is not None and current != old_val:
            # Check if already fixed
            if current == new_val:
                print(f"  SKIP Art {art_id} {field}: already correct")
                continue
            print(f"  WARNING Art {art_id} {field}: expected '{old_val[:60]}...' but got '{(current or '')[:60]}...'")
            # Still apply the fix since the new value is from the PDF
        elif old_val is None and current is not None and current != '' and current != new_val:
            print(f"  WARNING Art {art_id} {field}: has value '{(current or '')[:60]}...' but expected empty")
            # Still apply since PDF is authoritative

        if current == new_val:
            print(f"  SKIP Art {art_id} {field}: already correct")
            continue

        if dry_run:
            print(f"  DRY-RUN Art {art_id} {field}: {reason}")
            print(f"    OLD: {(current or '')[:100]}")
            print(f"    NEW: {new_val[:100]}")
        else:
            cur.execute(f"UPDATE articles SET {field}=? WHERE seminar_slug='sdnne06' AND id=?",
                        (new_val, art_id))
            print(f"  FIXED Art {art_id} {field}: {reason}")
        count += 1

    if not dry_run:
        conn.commit()
        print(f"\n=== {count} corrections applied ===")
    else:
        print(f"\n=== {count} corrections would be applied (dry-run) ===")

    conn.close()

if __name__ == '__main__':
    main()
