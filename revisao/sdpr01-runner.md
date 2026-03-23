# sdpr01 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-23 | Artigos: 26
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/26 | % |
|-------|-------|---|
| abstract | 18 | 69% |
| abstract_en | 0 | 0% |
| keywords | 17 | 65% |
| keywords_en | 0 | 0% |
| references | 18 | 69% |
| title_en | 0 | 0% |
| sections | 4 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint
- [x] **0.1** abs 69%, abs_en 0%, kw 65%, kw_en 0%, refs 69%, 0 EN, 0 ES
- [x] **0.2** 8 sem abstract (001, 008, 011, 012, 013, 017, 025, 026), 7 sem refs, 9 sem keywords
- [x] **0.3** Fonte primária: .doc originais (25 arquivos). Usado `extrair_metadados_doc.py` (novo script)
  - 6 campos novos extraídos: abstract_en (014), keywords_en (003, 005, 014, 023), refs (018)
  - LUSFOR~1.DOC = sdpr01-019 (filename 8.3 truncado)
  - "Conformação urbana" = sdpr01-013 (título diferente no filename vs conteúdo)
  - 026 = JPG (painel de imagens, sem .doc)
- [skip] **0.3b** Plumber não extraído — .doc é fonte primária
- [x] **0.4** Seções: 4 seções pré-existentes (26/26 atribuídos), section_label=seção temática
  - Conferência (1), Precursores do Moderno (11), As Cidades Assumem o Moderno (13), Painel (1)
- [x] **0.5** 8 artigos sem abstract = genuíno (sem seção Resumo no .doc). Mantidos sem abstract.
- [x] **0.6** EN: abs_en < 30% `[SKIP]`. Extraídos via .doc: abstract_en (014), keywords_en (003, 005, 014, 023)
- [x] **0.7** ES: 1 artigo (024) com abstract_es e keywords_es extraídos do .doc pelo agente LLM
- [x] **0.8** Validate: 7 issues, 1 auto-fixed (A17 ref duplicada 019). 3 A10 backfills, 3 A11 refs longas — cobertos pela revisão LLM

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos: 7 normalização + 6 correções manuais (carioca, Forte, COHAB-CT, Antônio, desenho, paisagem urbana, obra)
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug sdpr01 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug sdpr01
  ```
  → 4 erros do script corrigidos manualmente (gentílicos, subtítulos)
- [skip] **1.1b/1.1c** Títulos EN/ES `[SKIP: title_en = 0]`
- [x] **1.2a** Refs: clean (9 splits, 0 backfills, 0 problemas)
  ```
  python3 scripts/clean_references.py --slug sdpr01
  python3 scripts/check_references.py --slug sdpr01 --summary
  ```
- [x] **1.2b** Refs sweep (5 lixo, 4 joins, 2 não-refs)
  ```
  python3 scripts/fix_validation_issues.py --slug sdpr01 --sweep-refs
  ```
- [x] **1.2b+** Re-backfills: 0 backfills, 0 URLs
- [x] **1.2c+1.10** Revisão LLM (todos campos × todos artigos, 3 agentes, fonte: .doc→.txt)
  Resumo: 20/26 artigos corrigidos, 0 issues finais
  **1.10 — Resultado por artigo:**
  - [x] sdpr01-001: OK (sem abstract/kw/refs — genuíno, palestra)
  - [x] sdpr01-002: +6 refs (ARGAN, CIRNE-LIMA, etc.)
  - [x] sdpr01-003: 1 ref truncada completada
  - [x] sdpr01-004: 4 fixes (2 splits, 2 joins) → 16→17 refs
  - [x] sdpr01-005: 2 backfills + 2 joins → 18→16 refs
  - [x] sdpr01-006: 1 join → 8→7 refs
  - [x] sdpr01-007: 1 fix + 1 join → 4→3 refs
  - [x] sdpr01-008: refs reconstruídas (backfills FERREIRA/GNOATO, splits, joins) → 14 refs
  - [x] sdpr01-009: 1 backfill + 1 fix + 1 join → 5→4 refs
  - [x] sdpr01-010: acento "Antônio" corrigido
  - [x] sdpr01-011: OK
  - [x] sdpr01-012: OK
  - [x] sdpr01-013: OK
  - [x] sdpr01-014: 3 joins + 1 add → 25→24 refs
  - [x] sdpr01-015: +11 refs (eram 0)
  - [x] sdpr01-016: splits + joins + adds → 14→15 refs
  - [x] sdpr01-017: +14 refs (eram 0)
  - [x] sdpr01-018: 18→27 refs (splits massivos + normalização autores)
  - [x] sdpr01-019: 1 fix (DUQUEQUE→DUDEQUE)
  - [x] sdpr01-020: abstract fix (pósguerra→pós-guerra), 1 ref fix, 1 add → 23→24 refs
  - [x] sdpr01-021: +keywords_en, 2 joins + 1 add → 15→14 refs
  - [x] sdpr01-022: 9 backfills resolvidos, 5 joins, 3 adds → 43→42 refs
  - [x] sdpr01-023: 1 backfill + 1 join + truncamentos → 17→16 refs
  - [x] sdpr01-024: +22 refs (eram 0), +abstract_es, +keywords_es
  - [x] sdpr01-025: 1 join + 1 fix → 6→5 refs
  - [x] sdpr01-026: SKIP (JPG, sem .doc)
- [x] **1.3** Keywords: 0 alterações
- [x] **1.5** Loop: 0 issues
- [x] **1.6** abs 69% (18/26), abs_en 4% (1), abs_es 4% (1), kw 65% (17), kw_en 19% (5), kw_es 4% (1), refs 88% (23). Sem ISBN.
- [x] **1.7** Autores: 35 autores
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: 19 buscados, 1 novo confirmado. Cobertura: 17/35 (49%)

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação final (0 issues) + HTML (26 artigos, 4 seções) + dump + commit
  ```
  python3 scripts/validate_metadata.py --slug sdpr01 --fix
  python3 scripts/gerar_revisao_html.py sdpr01
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdpr01-* && git commit -m "sdpr01 revisão automática (Fases 0-2)"
  ```

Issues genuínos restantes:
- 8 artigos sem abstract (001, 008, 011, 012, 013, 017, 025, 026 — sem seção Resumo no .doc)
- 3 artigos sem refs (001, 010, 026 — genuíno)
- 0% keywords_en exceto 5 artigos com bilíngue no .doc
- 026 é JPG (painel de imagens)

## Cobertura final

| Campo | N/26 | % |
|-------|------|---|
| abstract | 18 | 69% |
| abstract_en | 1 | 4% |
| abstract_es | 1 | 4% |
| keywords | 17 | 65% |
| keywords_en | 5 | 19% |
| keywords_es | 1 | 4% |
| references | 23 | 88% |
| sections | 26/26 | 100% |
| ORCID | 17/35 | 49% |

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** 2 correções humanas (016 moderna, 022 brutalismo). Causas: normalização contextual (expressões em subtítulo)
- [x] **3.2** Dict: pós-modernismo→EXPRESSOES, argentina removida de TOPONIMICOS (duplicata), duplicatas campina grande/santo andré removidas
- [x] **3.3** Scripts: `dedup_authors.py` (suffix match), `extrair_metadados_doc.py` (5 fixes), + auditoria completa: 18 bugs em 5 scripts
- [x] **3.4** Pipeline: sem alterações necessárias
- [x] **3.5** Verificar: dry-runs sdpr01+sdbr08+sdbr13+dedup sem regressão
- [x] **3.6** Aprendizado: `revisao/sdpr01-aprendizado-revisao.json` + MEMORY.md (feedback_engineering_review)
- [x] **3.7** Revisão de engenharia completa (8 scripts auditados):
  - validate_metadata.py: 6 fixes (A23 boundary, A26 locale, A21 mutual exclusion, copy_field morto, refs sync, import morto)
  - clean_references.py: 4 fixes (json.loads crash, join_orphan_urls dead code, ORPHAN_URL morto, backfill warning)
  - fix_validation_issues.py: 3 fixes (block['text'] crash, json.loads ×5, fix_a10 chain-walk)
  - normalizar.py: 2 fixes (inicio_nova_frase reset+usage, \b UNICODE)
  - init_db.py: 3 fixes (pós-modernismo, argentina, duplicatas)
  - extrair_metadados_doc.py: 5 fixes (abstract_es, subdirs, threshold, try/finally, apply/report)
  - dedup_authors.py: 1 fix (suffix match)
- [x] **3.8** Cobertura final: abs 69%, abs_en 4%, kw 65%, kw_en 19%, refs 88%, ORCID 49%
- [x] **3.9** Fechar: dump + commit
