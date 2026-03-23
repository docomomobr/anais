# sdsul06 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-22 | Artigos: 24
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/24 | % |
|-------|-------|---|
| abstract | 23 | 96% |
| abstract_en | 0 | 0% |
| keywords | 22 | 92% |
| keywords_en | 0 | 0% |
| references | 24 | 100% |
| title_en | 0 | 0% |
| sections | 1 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint
- [x] **0.1** abs 96%, abs_en 0%, kw 92%, kw_en 0%, refs 100%, 0 EN, 0 ES
- [x] **0.2** 021 sem abstract, 005/019 sem keywords
- [x] **0.3** 005/019 sem keywords no PDF (genuíno), 021 sem abstract (genuíno, tem keywords)
- [x] **0.3b** Extraído plumber: 24/24 (4558 blocos)
- [x] **0.4** Seções: 5 subtemas (Renovação, Restauro, Equipamento, Ampliação, Mistura) — 8/24 atribuídos (PDF), 16 sem subtema (site CAU/RS confirma 5 subtemas mas sem mapeamento artigo→subtema; PROPAR 404, Wayback inacessível)
- [x] **0.5** 019 abstract_en extraído (1800c, blocos 1+2), 021 keywords+keywords_en extraídas do plumber
- [x] **0.6** EN: 21 abstract_en, 21 keywords_en extraídos do plumber (006 sem abstract_en genuíno)
- [x] **0.7** ES: 0 artigos ES (24 PT)
- [x] **0.8** Validate: 28 issues, 6 auto-fixed (A25), 8 abstract_en completados (blocos adjacentes), 10 restantes (A01×3, A02×3, A10×1, A11×3)

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos: 10 normalização + 18 correções LLM (Obra→obra, lado b→lado B, Estrela→estrela, nomes próprios, etc.)
- [skip] **1.1b/1.1c** Títulos EN/ES `[SKIP: title_en = 0]`
- [x] **1.2a** Refs: clean (0 splits, 0 backfills, 0 problemas)
- [x] **1.2b** Refs sweep (10 joins, 2 splits, 2 lixo, 1 não-ref, 1 dedup, 1 endnote)
- [x] **1.2b+** Re-backfills: 0
- [x] **1.2c** Refs revisão LLM: 20/24 artigos corrigidos (joins, splits, refs faltantes, lixo removido)
- [x] **1.3** Keywords: 1 artigo (1 trimmed)
- [x] **1.5** Loop: 6 issues (A01×3, A02×3 — abs/kw_en cruzados, genuínos)
- [x] **1.6** abs 96%, abs_en 88%, kw 92%, kw_en 88%, refs 100%. Metadados seminário OK (ISBN 978-85-61965-77-8, publisher Marcavisual)
- [x] **1.7** Autores: 35 autores, 24/24 verificados. 1 correção: Abreu Filho givenname (duplicação "Abreu")
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: 10 buscados, 0 novos confirmados. Cobertura: 25/35 (71%)
- [x] **1.10** Revisão LLM final — 3 agentes paralelos (24 artigos)
  Correções 1.10:
  - 004: keywords_en completadas (2→5 termos)
  - 006: abstract_en extraído (1940c, bloco p2), keywords_en corrigida
  - 007: abstract_en completado (873→1705c, bloco adjacente)
  - 009: keywords_en adicionadas (5 termos)
  - 011: keywords_en corrigidas (2→5 termos)
  - 022: keywords/keywords_en split ("Grupo do Paraná" e Brutalismo separados)
  - 023: abstract_en extraído (1651c, blocos p1+p2)
  **1.10 — Resultado por artigo:**
  - [x] sdsul06-001: OK
  - [x] sdsul06-002: OK
  - [x] sdsul06-003: OK
  - [x] sdsul06-004: keywords_en completadas
  - [x] sdsul06-005: OK (sem keywords no PDF — genuíno)
  - [x] sdsul06-006: abstract_en extraído + keywords_en corrigida
  - [x] sdsul06-007: abstract_en completado
  - [x] sdsul06-008: OK
  - [x] sdsul06-009: keywords_en adicionadas
  - [x] sdsul06-010: OK
  - [x] sdsul06-011: keywords_en corrigidas
  - [x] sdsul06-012: OK
  - [x] sdsul06-013: OK
  - [x] sdsul06-014: OK ("funionalidade" é typo no PDF original)
  - [x] sdsul06-015: OK
  - [x] sdsul06-016: OK
  - [x] sdsul06-017: OK
  - [x] sdsul06-018: OK
  - [x] sdsul06-019: OK (sem keywords no PDF — genuíno)
  - [x] sdsul06-020: OK
  - [x] sdsul06-021: OK (sem abstract no PDF — genuíno)
  - [x] sdsul06-022: keywords/keywords_en split
  - [x] sdsul06-023: abstract_en extraído
  - [x] sdsul06-024: OK

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação final (3 issues genuínos) + HTML (24 artigos, 5 seções) + dump + commit

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
