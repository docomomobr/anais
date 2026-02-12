#!/usr/bin/env python3
"""Script pós-pipeline: aplica ORCIDs confirmados, backfill de checagem, dump.

Executar após o pipeline de busca (fetch_orcid.py --search) terminar.
"""

import json
import os
import sqlite3
from datetime import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE, 'anais.db')
RESULTS_PATH = os.path.join(BASE, 'orcid_results.json')
PIPELINE_VERSION = '2.0'
TODAY = datetime.now().strftime('%Y-%m-%d')


def main():
    if not os.path.exists(RESULTS_PATH):
        print(f'ERRO: {RESULTS_PATH} não encontrado')
        return

    with open(RESULTS_PATH, 'r') as f:
        results = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Garantir colunas existem
    cur.execute("PRAGMA table_info(authors)")
    cols = [r[1] for r in cur.fetchall()]
    if 'orcid_checked_at' not in cols:
        cur.execute('ALTER TABLE authors ADD COLUMN orcid_checked_at TEXT')
    if 'orcid_pipeline_version' not in cols:
        cur.execute('ALTER TABLE authors ADD COLUMN orcid_pipeline_version TEXT')
    conn.commit()

    # === 1. Aplicar ORCIDs confirmados ===
    confirmed = results.get('confirmed', [])
    applied = 0
    for entry in confirmed:
        aid = entry['author_id']
        orcid = entry['orcid']
        cur.execute("SELECT orcid FROM authors WHERE id = ?", (aid,))
        row = cur.fetchone()
        if row and row[0]:
            continue  # já tem
        cur.execute("UPDATE authors SET orcid = ? WHERE id = ?", (orcid, aid))
        applied += 1

    print(f'ORCIDs aplicados: {applied} (de {len(confirmed)} confirmados)')

    # === 2. Backfill checagem para todos os autores processados ===
    all_processed = set()
    for category in results.values():
        for entry in category:
            aid = entry.get('author_id')
            if aid:
                all_processed.add(aid)

    backfilled = 0
    for aid in all_processed:
        cur.execute(
            "UPDATE authors SET orcid_checked_at = ?, orcid_pipeline_version = ? WHERE id = ? AND orcid_checked_at IS NULL",
            (TODAY, PIPELINE_VERSION, aid))
        if cur.rowcount > 0:
            backfilled += 1

    print(f'Checagem registrada (backfill): {backfilled} autores')

    # === 3. Marcar autores que JÁ tinham ORCID (de etapas anteriores) ===
    cur.execute("""
        UPDATE authors SET orcid_checked_at = ?, orcid_pipeline_version = 'pre-2.0'
        WHERE orcid IS NOT NULL AND orcid != '' AND orcid_checked_at IS NULL
    """, (TODAY,))
    pre_marked = cur.rowcount
    print(f'Autores pré-existentes marcados: {pre_marked}')

    conn.commit()

    # === 4. Estatísticas finais ===
    cur.execute("SELECT COUNT(*) FROM authors WHERE orcid IS NOT NULL AND orcid != ''")
    total_orcid = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM authors")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM authors WHERE orcid_checked_at IS NOT NULL")
    checked = cur.fetchone()[0]

    print(f'\n{"="*50}')
    print(f'Total de autores:  {total}')
    print(f'Com ORCID:         {total_orcid} ({total_orcid*100/total:.1f}%)')
    print(f'Checados:          {checked} ({checked*100/total:.1f}%)')

    # Breakdown por fonte (do JSON)
    oa_count = sum(1 for c in confirmed if c.get('source', '').startswith('openalex'))
    cr_count = sum(1 for c in confirmed if c.get('source') == 'crossref')
    s2_count = sum(1 for c in confirmed if c.get('source') == 'semantic_scholar')
    orcid_count = len(confirmed) - oa_count - cr_count - s2_count

    print(f'\nConfirmados nesta execução: {len(confirmed)}')
    print(f'  OpenAlex:          {oa_count}')
    print(f'  Crossref:          {cr_count}')
    print(f'  Semantic Scholar:  {s2_count}')
    print(f'  ORCID API:         {orcid_count}')
    print(f'Candidatos (revisar): {len(results.get("candidates", []))}')
    print(f'Sem resultado:       {len(results.get("not_found", []))}')
    print(f'Muitos resultados:   {len(results.get("too_many", []))}')
    print(f'Pulados:             {len(results.get("skipped", []))}')

    conn.close()

    # === 5. Dump do banco ===
    print('\nGerando dump...')
    os.system(f'python3 {os.path.join(BASE, "scripts", "dump_anais_db.py")}')
    print('Concluído!')


if __name__ == '__main__':
    main()
