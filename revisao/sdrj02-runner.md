# sdrj02 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-23 | Artigos: 19
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/19 | % |
|-------|-------|---|
| abstract | 8 | 42% |
| abstract_en | 1 | 5% |
| keywords | 0 | 0% |
| keywords_en | 0 | 0% |
| references | 7 | 37% |
| title_en | 0 | 0% |
| sections | 2 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint + commit
- [x] **0.1** abs 42% (8/19), abs_en 5% (1), kw 0%, kw_en 0%, refs 37% (7), title_en 0%, 2 seções
- [x] **0.2** 11 pôsteres sem metadados (genuíno: PDFs gráficos). 4 sem PDF (011, 017, 018, 019). Roberto Segre (9º artigo) falta — PDF inexistente.
- [x] **0.3** Fonte primária: CD-ROM interativo (HTML+PDFs). 8 artigos texto + 8 pôsteres gráficos. Sem doc/docx.
- [x] **0.3b** Plumber extraído (15 PDFs, 1240 blocos). OCR (ocrmypdf+tesseract) nos 5 pôsteres imagem/CID → re-extração ok.
- [x] **0.4** Seções: 2 (Artigos hide_title=1, Pôsteres). Sem eixos temáticos. HTML mostra subcategorias pôsteres (Premiados/Seleção/Apresentados) — visual, não seções.
- [x] **0.5** Lacunas verificadas. Abstracts 001-008 no banco (001/004 do PDF, demais editoriais). Refs ok (7/8 artigos). Pôsteres sem metadados extraíveis.
- [x] **0.6** EN: extrair_metadados_en → 0 extraídos (19/19 "sem fonte"). Só 004 tem ABSTRACT no PDF (já no banco).
- [skip] **0.7** ES: 0 artigos com locale=es `[SKIP]`
- [x] **0.8** Validate --fix: 0 problemas

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: normalização dry-run → 5 falsos positivos (genéricos: arquiteto, lei, tombamento). 2 correções manuais: 004 "fundação bienal"→"Fundação Bienal", 011 "esplanada"→"Esplanada"
- [skip] **1.1b/1.1c** Títulos EN/ES `[SKIP: title_en = 0]`
- [x] **1.2a** Refs: clean 0 alterações, check 0 problemas (60 refs)
- [x] **1.2b** Refs sweep: 1 artigo (004: 1 lixo grosso removido)
- [x] **1.2b+** Re-backfills: 0
- [x] **1.2c+1.10** Revisão LLM (todos campos × todos artigos, 2 agentes Opus, fonte: plumber)
  Resumo: 5/19 artigos corrigidos, 0 issues genuínos finais
  **1.10 — Resultado por artigo:**
  - [x] sdrj02-001: OK
  - [x] sdrj02-002: OK
  - [x] sdrj02-003: +3 refs (REFERÊNCIAS BIBLIOGRÁFICAS p8: Conservar/Restaurar, Carlos Leão, Meiriño)
  - [x] sdrj02-004: +11 refs (Bibliografia Periódicos: Alencastro, Estevão, Fernandes, Bienal, etc. 9→20)
  - [x] sdrj02-005: OK
  - [x] sdrj02-006: OK (sem refs, genuíno)
  - [x] sdrj02-007: OK
  - [x] sdrj02-008: OK (título "saúde" minúsculo mantido — genérico)
  - [x] sdrj02-009: OK (pôster)
  - [x] sdrj02-010: OK (pôster, discrepância título CD-ROM vs PDF — mantido catálogo)
  - [x] sdrj02-011: OK (pôster, sem PDF)
  - [x] sdrj02-012: OK (pôster)
  - [x] sdrj02-013: +subtitle "um acervo em estudo" (do PDF)
  - [x] sdrj02-014: OK (pôster)
  - [x] sdrj02-015: +subtitle "o Teatro do Museu de Arte Moderna do Rio de Janeiro" (do PDF)
  - [x] sdrj02-016: OK (pôster, OCR)
  - [x] sdrj02-017: OK (pôster, sem PDF)
  - [x] sdrj02-018: OK (pôster, sem PDF)
  - [x] sdrj02-019: OK (pôster, sem PDF)
- [x] **1.3** Keywords: 0 artigos (genuinamente ausentes em todos os PDFs)
- [x] **1.5** Loop: 0 issues, convergiu em 1 iteração
- [x] **1.6** Cobertura: abs 42%, abs_en 5%, kw 0%, refs 37%. Seminário: ISBN, editores, descrição OK.
- [x] **1.7** Autores: 38, verificados vs HTML do CD-ROM
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: 20 buscados, 3 candidatos aceitos (Waltenberg, Zukeran, Bette). Cobertura: 21/38 (55%)

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação final (0 issues) + HTML (19 artigos, 2 seções) + dump + commit
  ```
  python3 scripts/validate_metadata.py --slug sdrj02 --fix
  python3 scripts/gerar_revisao_html.py sdrj02
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdrj02-* && git commit -m "sdrj02 revisão automática (Fases 0-2)"
  ```

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** 2 correções humanas (002 arquitetura lowercase, 007 Arquivologia uppercase). Causa: capitalização contextual do YAML original.
  7 correções automáticas: 2 títulos, 2 subtítulos, 14 refs, 1 sweep, 3 ORCIDs
- [x] **3.2** Dict: "Arquivologia" adicionado como area. Sem remoções.
- [x] **3.3** Scripts: sem alterações (2 correções < threshold 3)
- [x] **3.4** Pipeline: §0.6 agora executada (antes era SKIP por heurística)
- [x] **3.5** Verificar: dry-run normalizar (9 regressões esperadas = correções manuais/LLM), validate 0 issues, dedup 0 merges
- [x] **3.6** Aprendizado: `revisao/sdrj02-aprendizado-revisao.json`
- [x] **3.7** Revisão de engenharia (11 scripts auditados, Opus): 5 bugs corrigidos:
  - check_references.py:228,233 — json.loads sem guard (crash em refs JSON inválido)
  - fix_validation_issues.py:691 — JSONL parsing sem guard em _read_fontes_lines
  - fix_validation_issues.py:1172 — JSONL parsing sem guard em read_plumber_abstract
  - extrair_metadados_en.py:88 — JSONL parsing sem guard em read_plumber_blocks
  - extrair_metadados_en.py:324 — JSONL parsing sem guard em read_fontes_text
- [x] **3.8** Cobertura final: abs 42%, abs_en 5%, kw 0%, refs 37%, ORCID 55%
- [x] **3.9** Fechar: dump + commit
