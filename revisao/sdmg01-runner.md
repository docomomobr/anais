# sdmg01 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-23 | Artigos: 26
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/26 | % |
|-------|-------|---|
| abstract | 17 | 65% |
| abstract_en | 18 | 69% |
| keywords | 18 | 69% |
| keywords_en | 15 | 58% |
| references | 20 | 77% |
| title_en | 0 | 0% |
| sections | 2 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint
- [x] **0.1** abs 65% (17/26), abs_en 69% (18), kw 69% (18), kw_en 58% (15), refs 77% (20), title_en 0%, 2 seções
- [x] **0.2** 9 sem abs, 8 sem abs_en, 8 sem kw, 11 sem kw_en, 6 sem refs
- [x] **0.3** Fonte primária: DVD com PPT interativo + PDFs individuais. Sem doc/docx.
- [x] **0.3b** Plumber extraído (26 artigos, 2526 blocos)
- [x] **0.4** Seções: 2 (Apresentações Orais hide_title=1, Pôsteres). Sem eixos temáticos. PPT confirma: só "apresentações orais | posters". fontes_secoes.md já documenta.
- [x] **0.5** Lacunas preenchidas do plumber:
  - 006: abstract PT (p3-p4, 9.8pt) + 46 refs
  - 019: abstract PT (small p1) + keywords PT
  - 024: abstract PT (resumo p1) + keywords PT/EN (bilingual)
  - 004: abstract_en (Abstract p1)
  - 011: keywords PT (embedded no abstract)
  - 022: keywords PT + EN, refs (2-col mangled, 70 entries)
  - 023: keywords PT/EN (bilingual)
  - 005: keywords_en
  - 016: refs (37, split de 2 blocos concatenados)
  - 021: refs (22, reference + footnote blocks)
  - Genuinamente ausentes: 009 abs/kw/refs, 010/012/026 abs PT, 007/008/018-020 abs_en
- [skip] **0.6** EN: 1 abs_en extraído, 19 title_en falharam (sem seção EN nos PDFs)
- [skip] **0.7** ES: 0 artigos com locale=es `[SKIP]`
- [x] **0.8** Validate --fix: 4 auto-fixed (A17 dedup refs, A20 overflow), 16 issues para Fase 1

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 9 normalização + 7 correções LLM (engenheiro, presente, materiais, complexo, nacionais/internacionais, jardim, arquitetônica, desenvolvimento)
- [skip] **1.1b/1.1c** Títulos EN/ES `[SKIP: title_en = 0]`
- [x] **1.2a** Refs: clean (4 splits, 5 backfills, 1 join URL)
- [x] **1.2b** Refs sweep (9 arts alterados: 12 joins, 12 endnotes, 8 non-refs removidas)
- [x] **1.2b+** Re-backfills: 2 backfills
- [x] **1.2c+1.10** Revisão LLM (todos campos × todos artigos, 3 agentes, fonte: plumber)
  Resumo: 18/26 artigos corrigidos, 3 issues genuínos finais
  **1.10 — Resultado por artigo:**
  - [x] sdmg01-001: OK
  - [x] sdmg01-002: +14 refs (bibliografia body block)
  - [x] sdmg01-003: OK
  - [x] sdmg01-004: abstract_en limpo (cid garbage), +1 ref GAZETA
  - [x] sdmg01-005: OK
  - [x] sdmg01-006: abstract PT completado (p3-p4), abstract_en completado
  - [x] sdmg01-007: OK (abs_en genuinamente ausente)
  - [x] sdmg01-008: +1 ref Minas Gerais/EMBRATUR (abs_en genuinamente ausente)
  - [x] sdmg01-009: subtítulo corrigido (vilas operadoras Furnas), refs reconstruídas (7→5)
  - [x] sdmg01-010: abstract_en limpo (contaminação footnote), refs split CAVALCANTI (13→14)
  - [x] sdmg01-011: refs limpas — joins, splits, fragments (20→18)
  - [x] sdmg01-012: refs corrigidas — PIRES join, backfill incorreto removido (13→14)
  - [x] sdmg01-013: OK
  - [x] sdmg01-014: refs limpas (footnote removida do PAPADAKI)
  - [x] sdmg01-015: refs juntadas — MALARD, VASCONCELLOS x2 (20→17)
  - [x] sdmg01-016: refs reconstruídas — splits BRUAND/GOODWIN/GUEGEN/MARTINS (25→34)
  - [x] sdmg01-017: refs reconstruídas — joins ASTOS/LARA, MALARD completado (8→5)
  - [x] sdmg01-018: OK (abs_en genuinamente ausente)
  - [x] sdmg01-019: abstract removido (body text sem RESUMO), keywords mantidas
  - [x] sdmg01-020: OK (abs/kw genuinamente ausentes, sem RESUMO)
  - [x] sdmg01-021: abstract_en trimmed (PT kw removidas), keywords split PT/EN
  - [x] sdmg01-022: abstract_en limpo (footnote contaminação), refs reconstruídas 2-col (2→30)
  - [x] sdmg01-023: OK
  - [x] sdmg01-024: abstract trimmed (body text removido, só Resumo)
  - [x] sdmg01-025: +1 ref FICHER, abstract_en typo corrigido
  - [x] sdmg01-026: refs joins (CHRYSOSTOMO, REZENDE)
- [x] **1.3** Keywords: 1 art alterado (2 splits) + 9 keywords convertidas para JSON array
- [x] **1.5** Loop: 11→3 issues (A01×2 genuíno, A10×1 genuíno)
- [x] **1.6** abs 73% (19/26), abs_en 76% (20), kw 80% (21), kw_en 69% (18), refs 100% (26)
- [x] **1.7** Autores: 40 autores, todos verificados vs plumber. 2 corrigidos:
  - Anita Regina Di Marco: familyname "Marco" → "Di Marco" (sobrenome composto)
  - Lisandra Mara Silva: familyname "Mara" → "Silva" (era Lisandra|Mara)
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: 20 buscados, 1 confirmado + 3 candidatos aceitos. Cobertura: 23/40 (57%)

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação final (3 issues genuínos) + HTML (26 artigos, 2 seções) + dump + commit

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** 1 correção humana (012 subtitle typo "mg1"→"MG"). Causa: dado de origem, não pipeline.
  37 correções automáticas: 7 títulos, 18 artigos refs, 6 abstracts, 4 keywords, 2 autores
- [x] **3.2** Dict: "Vilas Operadoras" adicionado por seed_titles. MG já era sigla. Sem alterações manuais.
- [x] **3.3** Scripts: 1 bug corrigido (fix_validation_issues.py:523, aid→art_id em clean_keywords)
- [x] **3.4** Pipeline: sem alterações necessárias
- [x] **3.5** Verificar: dry-run normalizar (7 regressões esperadas = correções LLM), validate 3 issues genuínos, dedup 0 merges
- [x] **3.6** Aprendizado: `revisao/sdmg01-aprendizado-revisao.json`
- [x] **3.7** Revisão de engenharia: 15 scripts auditados (Opus), 4 bugs corrigidos:
  - fix_validation_issues.py:523 — aid→art_id (clean_keywords crash)
  - gerar_revisao_html.py:75 — fmt_refs json.loads sem try/except (crash HTML)
  - fix_validation_issues.py:1440 — sweep_all_refs json.loads sem guard (abort sweep)
  - check_references.py:199 — WHERE não excluía '[]' (processamento desnecessário)
- [x] **3.8** Cobertura final: abs 73%, abs_en 76%, kw 80%, kw_en 69%, refs 100%, ORCID 60%
- [x] **3.9** Fechar: dump + commit
