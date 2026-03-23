# sdsul07 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-22 | Artigos: 46
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/46 | % |
|-------|-------|---|
| abstract | 39 | 85% |
| abstract_en | 0 | 0% |
| keywords | 0 | 0% |
| keywords_en | 0 | 0% |
| references | 45 | 98% |
| title_en | 0 | 0% |
| sections | 8 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint
- [x] **0.1** abs 85%, abs_en 0%, kw 0%, kw_en 0%, refs 98%, 0 EN, 0 ES
- [x] **0.2** 7 sem abstract (001,002,024,033,035,041,044), 1 sem refs (008)
- [x] **0.3** 7 sem abstract genuíno (nenhum "Resumo" no PDF — legendas de figuras). 008 refs no plumber
- [x] **0.3b** Extraído plumber: 47/47 (5326 blocos)
- [x] **0.4** Seções: 8 sessões pré-existentes (46/46 atribuídos)
- [x] **0.5** 008: 10 refs extraídas do plumber. 17 abstracts overflow corrigidos (re-extraídos do plumber). 2 truncados completados (012, 025 — blocos adjacentes). 037 truncado completado
- [x] **0.6** EN: 0 artigos com seção EN (nenhum tem Abstract/Keywords em inglês no PDF) `[SKIP]`
- [x] **0.7** ES: 0 artigos ES `[SKIP]`
- [x] **0.8** Validate: 20 issues, 1 auto-fixed (A25). 19 restantes: 16 A10 backfills (refs), 1 A12 não-ref (046), 2 A19 (já corrigidos)

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos: 23 normalização + 31 correções LLM (B/b, nomes próprios, genéricos, EMEIs, CIAMs, Taba Guaianases, Cine Marrocos, etc.)
- [skip] **1.1b/1.1c** Títulos EN/ES `[SKIP: title_en = 0, 0 ES]`
- [x] **1.2a** Refs: clean (0 splits, 2 backfills, 0 problemas)
- [x] **1.2b** Refs sweep (142 joins, 1 split, 20 não-refs, 14 lixo, 5 dedup, 1 body truncado)
- [x] **1.2b+** Re-backfills: 1
- [x] **1.2c** Refs revisão LLM: 43/46 artigos corrigidos (joins, splits, não-refs, backfills)
- [x] **1.3** Keywords: 0% genuíno (nenhum artigo tem Palavras-chave no PDF)
- [x] **1.5** Loop: 15 issues (13 A10 backfills, 1 A11 ref longa, 1 A19 — todos cobertos pela revisão LLM)
- [x] **1.6** abs 85%, abs_en 0%, kw 0%, kw_en 0%, refs 100%. ISBN 978-65-89263-60-9, publisher Núcleo Docomomo RS / Marcavisual
- [x] **1.7** Autores: 56 autores, 46/46 verificados vs sumário anais. Nomes completos no DB (sumário abrevia)
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: 16 buscados, 2 novos confirmados (Andrey de Aspiazu Schlee, Larissa Nogueira Agnelo). Cobertura: 47/56 (84%)
- [x] **1.10** Revisão LLM final — 3 agentes paralelos (46 artigos)
  Correções 1.10:
  - 001: 4 joins (12→8 refs)
  - 002: 2 joins (7→5 refs)
  - 003: 8 joins + 1 ref faltante (25→16 refs)
  - 004: 2 joins (10→8 refs)
  - 005: 4 joins (16→11 refs)
  - 006: 4 joins (21→17 refs)
  - 007: joins + backfills + 1 ref faltante (34→25 refs)
  - 009: 3 joins (16→13 refs)
  - 010: 3 joins (16→13 refs)
  - 011: 5 joins (19→14 refs)
  - 013: 2 joins (14→12 refs)
  - 014: 4 joins (9→5 refs)
  - 015: splits + 1 ref faltante (16→21 refs)
  - 016: 2 joins (11→9 refs)
  - 017: abstract overflow cortado (4293→3353c) + 3 joins (9→6 refs)
  - 018: 2 joins (16→14 refs)
  - 019: splits + joins (25→23 refs)
  - 020: 14 joins + 1 ref faltante (61→55 refs)
  - 021: backfill + 2 joins (8→6 refs)
  - 022: 10 body text removidos + 4 joins (22→8 refs)
  - 023: 21 body text removidos + 5 joins (48→22 refs)
  - 024: 7 joins (15→8 refs)
  - 026: 5 joins (16→11 refs)
  - 027: 3 joins (22→19 refs)
  - 028: 4 backfills + joins (32→22 refs)
  - 029: 5 joins + 1 ref faltante (19→14 refs)
  - 030: 1 body text removido (4→3 refs)
  - 031: 12 joins (refs)
  - 032: joins (refs)
  - 033: 2 joins (9→7 refs)
  - 034: 6 joins + 1 ref faltante (19→13 refs)
  - 035: 6 joins (21→14 refs)
  - 036: 1 join (16→14 refs)
  - 037: abstract re-extraído (126→1427c) + 1 não-ref + joins (63→46 refs)
  - 039: 3 joins (19→16 refs)
  - 040: 1 ref faltante (17→18 refs)
  - 041: 3 joins (13→10 refs)
  - 042: 1 join (17→16 refs)
  - 043: 2 joins + 1 dedup (22→19 refs)
  - 044: 5 joins + 1 backfill (23→17 refs)
  - 045: 2 joins (23→21 refs)
  - 046: major cleanup — 16 não-refs removidos (53→27 refs)
  **1.10 — Resultado por artigo:**
  - [x] sdsul07-001: refs corrigidas
  - [x] sdsul07-002: refs corrigidas
  - [x] sdsul07-003: refs corrigidas + 1 faltante
  - [x] sdsul07-004: refs corrigidas
  - [x] sdsul07-005: refs corrigidas
  - [x] sdsul07-006: refs corrigidas
  - [x] sdsul07-007: refs corrigidas + backfills + 1 faltante
  - [x] sdsul07-008: OK
  - [x] sdsul07-009: refs corrigidas
  - [x] sdsul07-010: refs corrigidas
  - [x] sdsul07-011: refs corrigidas
  - [x] sdsul07-012: OK
  - [x] sdsul07-013: refs corrigidas
  - [x] sdsul07-014: refs corrigidas
  - [x] sdsul07-015: refs corrigidas + 1 faltante
  - [x] sdsul07-016: refs corrigidas
  - [x] sdsul07-017: abstract overflow cortado + refs corrigidas
  - [x] sdsul07-018: refs corrigidas
  - [x] sdsul07-019: refs corrigidas
  - [x] sdsul07-020: refs corrigidas + 1 faltante
  - [x] sdsul07-021: refs corrigidas + backfill
  - [x] sdsul07-022: 10 body text removidos + refs corrigidas
  - [x] sdsul07-023: 21 body text removidos + refs corrigidas
  - [x] sdsul07-024: refs corrigidas (sem abstract genuíno)
  - [x] sdsul07-025: OK
  - [x] sdsul07-026: refs corrigidas
  - [x] sdsul07-027: refs corrigidas
  - [x] sdsul07-028: backfills + refs corrigidas
  - [x] sdsul07-029: refs corrigidas + 1 faltante
  - [x] sdsul07-030: 1 body text removido
  - [x] sdsul07-031: refs corrigidas
  - [x] sdsul07-032: refs corrigidas
  - [x] sdsul07-033: refs corrigidas (sem abstract genuíno)
  - [x] sdsul07-034: refs corrigidas + 1 faltante
  - [x] sdsul07-035: refs corrigidas (sem abstract genuíno)
  - [x] sdsul07-036: refs corrigidas
  - [x] sdsul07-037: abstract re-extraído + refs reconstruídas
  - [x] sdsul07-038: OK
  - [x] sdsul07-039: refs corrigidas
  - [x] sdsul07-040: 1 ref faltante adicionada
  - [x] sdsul07-041: refs corrigidas (sem abstract genuíno)
  - [x] sdsul07-042: refs corrigidas
  - [x] sdsul07-043: refs corrigidas + 1 dedup
  - [x] sdsul07-044: refs corrigidas + backfill (sem abstract genuíno)
  - [x] sdsul07-045: refs corrigidas
  - [x] sdsul07-046: major cleanup (16 não-refs removidos)

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação final (1 issue auto-fixável A25, 0 para revisão) + HTML (46 artigos, 8 seções) + dump + commit

Issues genuínos restantes:
- 7 artigos sem abstract (001, 002, 024, 033, 035, 041, 044 — PDFs não têm Resumo)
- 0% keywords (nenhum artigo tem seção Palavras-chave no PDF)
- 0% abstract_en (nenhum artigo tem seção Abstract em inglês no PDF)

## Cobertura final

| Campo | N/46 | % |
|-------|------|---|
| abstract | 39 | 85% |
| abstract_en | 0 | 0% |
| keywords | 0 | 0% |
| keywords_en | 0 | 0% |
| references | 46 | 100% |
| sections | 46/46 | 100% |
| ORCID | 47/56 | 84% |

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [ ] **3.1** Diagnóstico unificado (correções automáticas + humanas → causa raiz)
- [ ] **3.2** Atualizar dict.db (remover genéricos, adicionar nomes próprios)
- [ ] **3.3** Atualizar scripts (se >=3 artigos com mesmo erro não coberto)
- [ ] **3.4** Atualizar pipeline (se gaps na ordem de execução)
- [ ] **3.5** Verificar: dry-run sem regressão
- [ ] **3.6** Registrar aprendizado (JSON + MEMORY.md)
- [ ] **3.7** Revisão de engenharia (autoavaliação + lints)
- [ ] **3.8** Checklist de conclusão
- [ ] **3.9** Fechar: dump + commit + push + CLAUDE.md
