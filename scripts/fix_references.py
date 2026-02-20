#!/usr/bin/env python3
"""
Fix real problems in references detected by check_references.py.

Categories of fixes:
1. Remove running text / figure captions / non-references (texto_corrido, nao_referencia)
2. Remove page headers/footers from sdsp06 (contamination from PDF extraction)
3. Remove other clearly non-reference entries (section headers from body text,
   descriptive captions, page numbers, etc.)
4. Clean sdsp06 refs that have headers prepended/appended

Does NOT split concatenated refs (those are legitimate in many cases).
"""

import json
import re
import sqlite3
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')

def clean_sdsp06_header(ref):
    """Remove sdsp06 page headers/footers from a reference string.

    Patterns:
    - "A ARQUITETURA MODERNA PAULISTA E A QUESTÃO SOCIAL NNN"
    - "NNN 6º SEMINÁRIO SP DOCOMOMO"
    - Combinations thereof
    """
    # Pattern for the header/footer text
    header_pat = r'\s*A ARQUITETURA MODERNA PAULISTA E A QUESTÃO SOCIAL\s*\d*\s*'
    seminar_pat = r'\s*\d*\s*6º SEMINÁRIO SP DOCOMOMO\s*'

    # Remove from beginning
    ref = re.sub(r'^(' + header_pat + r'|' + seminar_pat + r')+', '', ref)
    # Remove from end
    ref = re.sub(r'(' + header_pat + r'|' + seminar_pat + r')+$', '', ref)

    return ref.strip()


def is_sdsp06_header_only(ref):
    """Check if a ref consists only of sdsp06 page headers/footers."""
    cleaned = clean_sdsp06_header(ref)
    return len(cleaned) == 0 or len(cleaned) < 5


def main():
    dry_run = '--dry-run' in sys.argv

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute('''
        SELECT id, seminar_slug, references_
        FROM articles
        WHERE references_ IS NOT NULL AND references_ != ''
        ORDER BY id
    ''').fetchall()

    stats = {
        'removed_running_text': 0,      # texto corrido / narrative text
        'removed_sdsp06_headers': 0,     # standalone page headers
        'cleaned_sdsp06_headers': 0,     # headers stripped from actual refs
        'removed_non_ref': 0,            # other non-reference entries
        'removed_fragments': 0,          # orphan fragments
        'articles_modified': 0,
    }

    # ========================================================
    # DEFINE REMOVALS: (article_id, ref_indices_to_remove)
    # Based on manual review of all flagged entries
    # ========================================================

    # -- texto_corrido: running text that is NOT a reference --
    # These are narrative paragraphs that got mixed into reference lists.
    removals_texto_corrido = {
        # sdbr07-036 ref#4: "Nesse ponto de vista, interessa mais identificar..."
        'sdbr07-036': [3],
        # sdbr07-044 ref#11: "Segundo o engenheiro Rui Filgueiras Lima..."
        'sdbr07-044': [10],
        # sdbr08-004 ref#9: "28 No Hotel Pirâmide Blue Tree..."
        'sdbr08-004': [8],
        # sdbr08-138 ref#24: "Essa proposta gerou variações..." (nao_referencia)
        # sdbr08-138 ref#25: "iniciativa operária..."
        # sdbr08-138 ref#27: "5 O desligamento de Ferro..."
        # sdbr08-138 ref#29: "5.1 Outras experiências"
        # sdbr08-138 ref#30: "abstracionismo como fruto..."
        'sdbr08-138': [22, 23, 24, 26, 27, 28, 29],
        # sdbr09-053 ref#5: "confirmar que essa não aceitação..."
        'sdbr09-053': [4],
        # sdbr09-055 ref#6: "Um estudo mais aprofundado..."
        'sdbr09-055': [5],
        # sdrj04-015 ref#9: "Enquanto a matriz formal vem do MES..."
        # sdrj04-015 refs 10,12,19-26,30-31,33,35-36,38: fragments of body text
        # sdrj04-015 ref#50: "INICIATIVAS EM ANDAMENTO" (section header)
        # sdrj04-015 ref#55: "Na quase totalidade da edificação..."
        'sdrj04-015': [8, 9, 11, 18, 19, 21, 22, 23, 24, 25, 29, 30, 32, 34, 35, 37, 49, 54],
        # sdsp03-052 ref#4: "Resposta a afirmações..."
        'sdsp03-052': [3],
        # sdsul04-008 ref#1: ": seu modo de fazer..." (fragment, starts with colon)
        # sdsul04-008 ref#3: "o início de sua trajetória..."
        'sdsul04-008': [0, 2],
        # sdsul04-010 ref#1: "na natureza das dunas..."
        'sdsul04-010': [0],
        # sdsul05-001 ref#32: "Tanto as relações de parentesco..."
        'sdsul05-001': [31],
        # sdsul05-004 ref#56: "Para efeitos de simulação..."
        # sdsul05-004 ref#60: "Temos que ressaltar a possibilidade..."
        'sdsul05-004': [55, 59],
        # sdsul05-009 ref#11: "13 provável que tenha sido..."
        # sdsul05-009 ref#16: "Estamos em um segundo nível..."
        # sdsul05-009 ref#17: "17 incômodos por invadir..."
        'sdsul05-009': [10, 15, 16],
        # sdsul05-029 ref#7: "Setorização - grau de compartimentação..."
        # sdsul05-029 ref#11: "Na casa Varanda, a circulação..."
        # sdsul05-029 ref#14: "As duas composições..."
        # sdsul05-029 ref#19: "envidraçadas que se abriam..."
        'sdsul05-029': [6, 10, 13, 18],
        # sdsul07-022 ref#15: "No nível mais baixo do terreno..."
        # sdsul07-022 ref#25: "índice construtivo, além de outras razões..."
        # sdsul07-022 ref#27: "Estes patrimônios modernos..."
        'sdsul07-022': [14, 24, 26],
        # sdsul07-046 ref#4: "Formas de projetar associadas..."
        # sdsul07-046 ref#12: "Segawa que aborda a implementação..."
        # sdsul07-046 ref#35: "Expressão que se refere ao edifício..."
        'sdsul07-046': [3, 11, 34],
    }

    # -- sem_ano_ponto / other non-references --
    # These are clearly not bibliographic references:
    # page headers, section titles, figure captions, encoded strings, appendix titles, etc.
    removals_non_ref = {
        # sdbr08-120 ref#22: "Agradecemos pelas entrevistas os arquitetos e professores:"
        'sdbr08-120': [21],
        # sdbr12-043 ref#9: "Estrutura: CONSCAL – Engenheiro Civil Siguer Mitsutani"
        # sdbr12-043 ref#15: "CONSIDERAÇÕES FINAIS"
        'sdbr12-043': [8, 14],
        # sdbr12-058 ref#43: "LISTA DE FIGURAS"
        'sdbr12-058': [42],
        # sdbr13-066 ref#16: "CONSTRUÇÃO – Concrejato Engenharia engª Maria Aparecida Soukef Nasser"
        'sdbr13-066': [15],
        # sdnne08-009 ref#21: "APÊNDICES A: QUESTIONÁRIO APLICADO AOS FUNCIONÁRIOS"
        'sdnne08-009': [20],
        # sdnne08-010 ref#4: base64 encoded string "SI7czoxOiJoIjtzOjMyOiIzZTYyNjg5N..."
        # sdnne08-010 ref#21: URL-encoded string "IL_DA_MISS%C3%83O..."
        'sdnne08-010': [3, 20],
        # sdsul04-006 ref#4: "Rua V. Mário Pezzi" (address/caption)
        # sdsul04-006 ref#5: "Projeto Lunardi -" (caption)
        # sdsul04-006 ref#10: "pavilhão vertical" (caption)
        'sdsul04-006': [3, 4, 9],
        # sdsul04-007 ref#2: "Vista do terraço" (caption)
        # sdsul04-007 ref#3: "Entrada da residência" (caption)
        # sdsul04-007 ref#8: "Vista face norte" (caption)
        # sdsul04-007 ref#12: "casa projetada por" (fragment)
        # sdsul04-007 ref#13: "possu a estrutura" (fragment)
        # sdsul04-007 ref#15: "interessante notar que" (fragment)
        # sdsul04-007 ref#16: "ames, e tamb m com" (fragment)
        # sdsul04-007 ref#20: "asa ntenza não deixa dúvidas..." (fragment)
        # sdsul04-007 ref#22: "necess rio observar..." (fragment)
        'sdsul04-007': [1, 2, 7, 11, 12, 14, 15, 19, 21],
        # sdsul04-022 ref#2: "Pau, -edra, -fim, -inho, -esto..." (word fragments/poem)
        'sdsul04-022': [1],
        # sdsul04-031 ref#1-5: room descriptions (captions from floor plan)
        'sdsul04-031': [0, 1, 2, 3, 4],
        # sdsul04-033 ref#1: "de parentesco miesiano..." (fragment)
        'sdsul04-033': [0],
        # sdsul04-036 ref#1: "Por outro lado, essa nova espacialidade..." (text)
        # sdsul04-036 ref#2: "Figuras 11: Perspectiva e Planta Baixa..." (caption)
        'sdsul04-036': [0, 1],
        # sdsul05-004 refs 4,5,7,9,11,13,15,17,21,23,24,26,32,35,38,41,42,55:
        # These are table entries from a diagnostic table, not references
        'sdsul05-004+diag': [3, 4, 6, 8, 10, 12, 14, 16, 20, 22, 23, 25, 31, 34, 37, 40, 41, 54],
        # sdsul05-006 refs: "Considerações Finais", "13 | P á g i n a" etc.
        'sdsul05-006': [0, 1, 14, 41, 43],
        # sdsul07-022 ref#10: "DESENVOLVIMENTO" (section header)
        # sdsul07-022 ref#16: "REFERÊNCIAS EXTERNAS" (section header)
        # sdsul07-022 ref#21: "Fotos do autor." (credit)
        # sdsul07-022 ref#22: "ATUALMENTE/ DEMOLIÇÃO" (section header)
        'sdsul07-022+headers': [9, 15, 20, 21],
        # sdsul07-046 ref#2: "NOÇÕES EMERGENTES" (section header)
        # sdsul07-046 ref#9: "TRÊS CASOS BRASILEIROS" (section header)
        # sdsul07-046 ref#22: "HEUVEL, 2015). 9" (fragment)
        # sdsul07-046 ref#42: "CASTOR, 2013." (note ref)
        # sdsul07-046 ref#44: "CONSIDERAÇÕES FINAIS" (section header)
        'sdsul07-046+headers': [1, 8, 21, 41, 43],
        # sdsul05-022 ref#13: "Elementary Forms" (section header)
        # sdsul05-022 ref#23: "Industrial Baroquism" (section header)
        # sdsul05-022 ref#37: "And this was the" (fragment)
        'sdsul05-022': [12, 22, 36],
        # sdsul05-029 ref#21: "CONSIDERAÇÕES FINAIS"
        'sdsul05-029+header': [20],
        # sdsul05-009 ref#1: "Uma casa no Uruguai" (section title)
        'sdsul05-009+header': [0],
        # sdsp08-023 refs 9-43: These are project credits, not bibliographic references
        # "Equipe técnica:", "Leonardo Henrique", "Metro Arquitetos", etc.
        'sdsp08-023': list(range(8, 43)),
        # sdsp09-027 refs 21,24,27,30,31: email, institution names, address
        'sdsp09-027': [20, 23, 26, 29, 30],
        # sdsul04-005 ref#5: "Dois anos desta 'reflexão'..." (narrative)
        'sdsul04-005': [4],
    }

    # Merge both removal dicts
    all_removals = {}
    for d in [removals_texto_corrido, removals_non_ref]:
        for key, indices in d.items():
            # Handle keys with '+' suffix (for articles needing multiple removal sets)
            art_id = key.split('+')[0]
            if art_id in all_removals:
                all_removals[art_id] = sorted(set(all_removals[art_id] + indices))
            else:
                all_removals[art_id] = sorted(set(indices))

    # Process each article
    for row in rows:
        article_id = row['id']
        slug = row['seminar_slug']
        refs = json.loads(row['references_'])
        original_count = len(refs)
        modified = False

        # 1. Handle sdsp06 header/footer contamination
        if slug == 'sdsp06':
            new_refs = []
            for i, ref in enumerate(refs):
                if 'ARQUITETURA MODERNA PAULISTA' in ref or 'SEMINÁRIO SP DOCOMOMO' in ref:
                    cleaned = clean_sdsp06_header(ref)
                    if is_sdsp06_header_only(ref):
                        stats['removed_sdsp06_headers'] += 1
                        modified = True
                        continue  # Skip this ref entirely
                    elif cleaned != ref:
                        new_refs.append(cleaned)
                        stats['cleaned_sdsp06_headers'] += 1
                        modified = True
                        continue
                new_refs.append(ref)
            refs = new_refs

        # 2. Apply manual removals
        if article_id in all_removals:
            indices_to_remove = set(all_removals[article_id])
            new_refs = []
            for i, ref in enumerate(refs):
                if i in indices_to_remove:
                    # Categorize removal
                    if article_id in removals_texto_corrido and i in removals_texto_corrido.get(article_id, []):
                        stats['removed_running_text'] += 1
                    else:
                        stats['removed_non_ref'] += 1
                    modified = True
                else:
                    new_refs.append(ref)
            refs = new_refs

        # Save if modified
        if modified:
            stats['articles_modified'] += 1
            new_json = json.dumps(refs, ensure_ascii=False)
            if not dry_run:
                conn.execute(
                    'UPDATE articles SET references_ = ? WHERE id = ?',
                    (new_json, article_id)
                )
            removed = original_count - len(refs)
            print(f"  {article_id}: {original_count} → {len(refs)} refs ({removed} removed)")

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"\n{'DRY RUN - ' if dry_run else ''}Summary:")
    print(f"  Articles modified: {stats['articles_modified']}")
    print(f"  Running text removed: {stats['removed_running_text']}")
    print(f"  sdsp06 headers removed: {stats['removed_sdsp06_headers']}")
    print(f"  sdsp06 headers cleaned from refs: {stats['cleaned_sdsp06_headers']}")
    print(f"  Non-reference entries removed: {stats['removed_non_ref']}")
    total_removed = (stats['removed_running_text'] + stats['removed_sdsp06_headers'] +
                     stats['removed_non_ref'])
    print(f"  Total entries removed: {total_removed}")
    print(f"  sdsp06 refs cleaned (not removed): {stats['cleaned_sdsp06_headers']}")


if __name__ == '__main__':
    main()
