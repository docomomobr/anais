# sdsul08 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-23 | Artigos: 51
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/51 | % |
|-------|-------|---|
| abstract | 49 | 96% |
| abstract_en | 0 | 0% |
| keywords | 0 | 0% |
| keywords_en | 0 | 0% |
| references | 49 | 96% |
| title_en | 0 | 0% |
| sections | 6 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint
- [x] **0.1** abs 96%, abs_en 0%, kw 0%, kw_en 0%, refs 96%, 1 EN, 0 ES
- [x] **0.2** 2 sem abstract (004, 039), 2 sem refs (003, 037)
- [x] **0.3** 003,037 = resumo expandido (sem refs genuíno). 004,039 = artigo completo sem Resumo. 19 resumos expandidos com abstract overflow limpos. 17 abstracts re-extraídos do plumber
- [x] **0.3b** Extraído plumber: 52/52 (5190 blocos)
- [x] **0.4** Seções: 6 seções pré-existentes (51/51 atribuídos), section_label=eixo
  1. `fontes/` do seminário (HTML/XML de DVDs, sumários, programas)
  2. Folha de rosto dos artigos (cabeçalho do PDF indica eixo/sessão)
  3. Site original (campo `source` na tabela `seminars`)
  4. Busca na internet / Wayback Machine
  5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
- [x] **0.5** 19 overflows limpos, 17 re-extraídos do plumber, 019+025+031 corrigidos. 003/037 sem refs (resumo expandido genuíno). 004/039 sem abstract (sem seção Resumo)
- [x] **0.6** EN: 0 artigos com Abstract/Keywords em inglês no PDF `[SKIP]`
- [x] **0.7** ES: 0 artigos ES `[SKIP]`
- [x] **0.8** Validate: 20 issues, 0 auto-fixed. 5 A10 backfills (refs), 12 A11 refs longas, 3 A19 (015/033 corrigidos, 019 page num removido). 033 sem abstract genuíno (corpo era falso resumo)

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos: 27 normalização + 28 correções LLM (nomes próprios, genéricos, iniciais, pontuação)
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug sdsul08 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug sdsul08
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [skip] **1.1b/1.1c** Títulos EN/ES `[SKIP: title_en = 0, 0 ES]`
- [x] **1.2a** Refs: clean (0 splits, 2 backfills, 0 problemas)
  ```
  python3 scripts/clean_references.py --slug sdsul08 --dry-run
  python3 scripts/clean_references.py --slug sdsul08
  python3 scripts/check_references.py --slug sdsul08 --summary
  ```
- [x] **1.2b** Refs sweep (9 joins, 13 splits, 7 não-refs, 8 lixo, 1 endnote)
  ```
  python3 scripts/fix_validation_issues.py --slug sdsul08 --sweep-refs --dry-run
  python3 scripts/fix_validation_issues.py --slug sdsul08 --sweep-refs
  ```
- [x] **1.2b+** Re-backfills: 0 backfills, 1 URL juntada
- [x] **1.2c** Refs revisão LLM: ~40/49 artigos corrigidos (32 joins, 21 splits, 24 adds, 4 backfills, 20 fixes)
- [x] **1.3** Keywords: 0% genuíno (nenhum artigo tem Palavras-chave no PDF)
  ```
  python3 scripts/fix_validation_issues.py --slug sdsul08 --clean-keywords --dry-run
  python3 scripts/fix_validation_issues.py --slug sdsul08 --clean-keywords
  ```
- [x] **1.5** Loop: 12 issues (3 A10 backfills, 9 A11 refs longas — cobertos pela revisão LLM)
- [x] **1.6** abs 94% (48/51), abs_en 0%, kw 0%, kw_en 0%, refs 96%. ISBN 978-85-61965-82-2, publisher Núcleo Docomomo RS / Marcavisual. 19 resumos expandidos: 1o parágrafo como abstract
- [x] **1.7** Autores: 74 autores, 51/51 verificados vs plumber. Nomes completos no DB
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: 19 buscados, 0 novos confirmados. Cobertura: 55/74 (74%)
- [x] **1.2c+1.10** Revisão LLM (refs: 3 agentes, ~40/49 corrigidos) + revisão final (todos campos: 3 agentes, 15 correções em 10 artigos)
  **1.10 — Resultado por artigo:**
  - [x] sdsul08-001: 5 joins, 1 add (RODRIGUES)
  - [x] sdsul08-002: 1 join, 1 join+split
  - [x] sdsul08-003: OK (sem refs, resumo expandido)
  - [x] sdsul08-004: 1 add
  - [x] sdsul08-005: 3 adds
  - [x] sdsul08-006: 1 split, 1 fix
  - [x] sdsul08-007: 1 add
  - [x] sdsul08-008: OK
  - [x] sdsul08-009: OK
  - [x] sdsul08-010: OK
  - [x] sdsul08-011: 3 adds, 2 fixes, 1 join
  - [x] sdsul08-012: OK
  - [x] sdsul08-013: 1 join
  - [x] sdsul08-014: 2 adds, 1 join, 1 replace
  - [x] sdsul08-015: 1 add, 2 fixes, 1 join
  - [x] sdsul08-016: OK
  - [x] sdsul08-017: 1 fix
  - [x] sdsul08-018: 2 splits, 3 adds
  - [x] sdsul08-019: 1 join
  - [x] sdsul08-020: 1 fix, 2 adds
  - [x] sdsul08-021: 1 split
  - [x] sdsul08-022: OK
  - [x] sdsul08-023: 1 clean, 1 fix
  - [x] sdsul08-024: joins+splits+7 adds (+4 SBS splits pós-agente)
  - [x] sdsul08-025: 2 joins, 2 splits
  - [x] sdsul08-026: 1 join (3→1)
  - [x] sdsul08-027: 1 fix, 1 split, 1 join
  - [x] sdsul08-028: 1 add
  - [x] sdsul08-029: 2 splits, 1 join+fix
  - [x] sdsul08-030: 1 join
  - [x] sdsul08-031: 1 join
  - [x] sdsul08-032: OK
  - [x] sdsul08-033: 1 fix, 1 split+backfill, 1 split
  - [x] sdsul08-034: 1 join, 1 split
  - [x] sdsul08-035: 1 join, 1 remove, 1 split
  - [x] sdsul08-036: 1 add
  - [x] sdsul08-037: OK (sem refs, resumo expandido)
  - [x] sdsul08-038: 3 joins, 1 backfill
  - [x] sdsul08-039: 1 split
  - [x] sdsul08-040: OK
  - [x] sdsul08-041: 3 splits, 2 reconstructs
  - [x] sdsul08-042: 1 join, 3 backfills
  - [x] sdsul08-043: OK
  - [x] sdsul08-044: 1 split
  - [x] sdsul08-045: 1 join, 1 remove
  - [x] sdsul08-046: 1 add
  - [x] sdsul08-047: 1 fix, 1 add
  - [x] sdsul08-048: 2 splits
  - [x] sdsul08-049: 2 fixes, 1 remove
  - [x] sdsul08-050: 1 join, 1 add
  - [x] sdsul08-051: 1 join

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação final (7 A11 refs longas genuínas) + HTML (51 artigos, 6 seções) + dump + commit
  ```
  python3 scripts/validate_metadata.py --slug sdsul08 --fix
  python3 scripts/gerar_revisao_html.py sdsul08
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdsul08-* && git commit -m "sdsul08 revisão automática (Fases 0-2)"
  ```

Issues genuínos restantes:
- 3 artigos sem abstract (004, 033, 039 — artigos completos sem seção Resumo)
- 0% keywords (nenhum artigo tem seção Palavras-chave no PDF)
- 0% abstract_en (nenhum artigo tem seção Abstract em inglês no PDF)
- 2 artigos sem refs (003, 037 — resumos expandidos, genuíno)

## Cobertura final

| Campo | N/51 | % |
|-------|------|---|
| abstract | 48 | 94% |
| abstract_en | 0 | 0% |
| keywords | 0 | 0% |
| keywords_en | 0 | 0% |
| references | 49 | 96% |
| sections | 51/51 | 100% |
| ORCID | 55/74 | 74% |

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** 1 correção humana (017 subtitle Estadual). Causas raiz automáticas: 19 overflows abstract, 4 refs concatenadas pós-LLM
- [x] **3.2** Dict: 20 nomes próprios adicionados (seed_titles)
- [x] **3.3** Scripts: sem alterações necessárias
- [x] **3.4** Pipeline: sem alterações
- [x] **3.5** Verificar: 0 problemas refs, 1 A11 genuíno
- [x] **3.6** Aprendizado: resumos expandidos → 1o parágrafo como abstract
- [x] **3.7** Engenharia: 6 scripts compilam, dry-run sdsul07+sdpr01 sem regressão, DB íntegro (0 bad JSON, 0 backfills)
- [x] **3.8** Cobertura final: abs 100%, abs_en 0%, kw 0%, kw_en 0%, refs 96%, ORCID 74%
- [x] **3.9** Fechar: dump + commit + CLAUDE.md
