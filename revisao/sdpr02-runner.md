# sdpr02 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-23 | Artigos: 19
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/19 | % |
|-------|-------|---|
| abstract | 10 | 53% |
| abstract_en | 1 | 5% |
| keywords | 5 | 26% |
| keywords_en | 1 | 5% |
| references | 19 | 100% |
| title_en | 0 | 0% |
| sections | 1 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint
- [x] **0.1** abs 53% (10/19), abs_en 5% (1), kw 26% (5), kw_en 5% (1), refs 100%, 0 EN, 0 ES
- [x] **0.2** 9 sem abstract (011-019), 14 sem keywords, 18 sem abstract_en/keywords_en
- [x] **0.3** Fonte primária: 11 doc/docx para arts 001-010. Arts 011-019 sem doc.
  - PDF completo dos anais (181p) confirma: índice lista exatamente os 19 artigos
  - Programa do seminário (Programa II Docomomo Londrina.docx) lista mais trabalhos apresentados, mas não publicados nos anais
- [x] **0.3b** Plumber extraído (19 artigos, 1460 blocos). Role=abstract nos 011-019 são falsos (autores, legendas, citações)
- [x] **0.4** Seções: 1 seção "Apresentação Oral" (hide_title=1), 19/19 atribuídos. Programa sem sessões temáticas
  - ISBN do livro (978-85-61986-40-7) removido — anais são mais amplos que o livro
  - Editora: UniFil / Núcleo Docomomo Paraná
- [x] **0.5** 9 artigos sem abstract = genuíno (sem RESUMO no PDF). 14 sem keywords = genuíno. Mantidos.
- [skip] **0.6** EN: abs_en < 30% `[SKIP]`. Só 006 tem EN (já completo no DB)
- [skip] **0.7** ES: 0 artigos com locale=es `[SKIP]`
- [x] **0.8** Validate: 8 issues A10 (backfills pendentes em 012, 014, 017) — cobertos pela Fase 1

## Fase 1 — Revisão automática

- [ ] **1.1a** Títulos PT: seed + normalizar + revisão LLM
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug sdpr02 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug sdpr02
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [x] **1.1a** Títulos: 10 normalização + 5 correções manuais (Algumas, Universidade, edificado, estação rodoviária/obra, fronteiras)
  - 002 "Carioca": mantido capitalizado (conceito historiográfico)
  - 007 "Edificado": mantido em "Patrimônio Cultural Edificado" (termo técnico)
  - 013 "fronteira" → "fronteiras" (original do PDF e índice)
- [skip] **1.1b/1.1c** Títulos EN/ES `[SKIP: title_en = 0]`
- [x] **1.2a** Refs: clean (0 splits, 8 backfills, 0 problemas)
- [x] **1.2b** Refs sweep (1 lixo em 018)
- [x] **1.2b+** Re-backfills: 0
- [x] **1.2c+1.10** Revisão LLM (todos campos × todos artigos, 2 agentes, fonte: plumber+docx)
  Resumo: 7/19 artigos corrigidos, 0 issues finais
  **1.10 — Resultado por artigo:**
  - [x] sdpr02-001: OK
  - [x] sdpr02-002: OK
  - [x] sdpr02-003: +2 refs SOUTO (9→11)
  - [x] sdpr02-004: +5 refs (LOPES, SEMINÁRIO, TRAVEL PIC, USC, VIVENDO BAURU) (6→11)
  - [x] sdpr02-005: abstract truncado completado (+1 parágrafo)
  - [x] sdpr02-006: +2 refs (CADERNO DE TERESINA, SABBAG) (10→12)
  - [x] sdpr02-007: abstract truncado reconstruído (1→3 parágrafos), refs reconstruídas do docx (7→35)
  - [x] sdpr02-008: OK
  - [x] sdpr02-009: refs reconstruídas do plumber (6→18)
  - [x] sdpr02-010: OK
  - [x] sdpr02-011: OK (sem abstract genuíno)
  - [x] sdpr02-012: OK (sem abstract genuíno)
  - [x] sdpr02-013: OK (sem abstract genuíno)
  - [x] sdpr02-014: OK (sem abstract genuíno)
  - [x] sdpr02-015: OK (sem abstract genuíno)
  - [x] sdpr02-016: OK (sem abstract genuíno)
  - [x] sdpr02-017: OK (sem abstract genuíno)
  - [x] sdpr02-018: +1 ref FISCHER (13→14)
  - [x] sdpr02-019: OK (sem abstract genuíno)
- [x] **1.3** Keywords: 0 alterações
- [x] **1.5** Loop: 0 issues
- [x] **1.6** abs 53% (10/19), abs_en 5% (1), kw 26% (5), kw_en 5% (1), refs 100% (19). Sem ISBN (anais ≠ livro).
- [x] **1.7** Autores: 43 autores, verificados vs programa e índice
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: 20 buscados, 7 novos (3 confirmados + 4 candidatos aceitos). Cobertura: 30/43 (70%)

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação final (0 issues) + HTML (19 artigos, 1 seção) + dump + commit

Issues genuínos restantes:
- 9 artigos sem abstract (011-019 — sem seção Resumo no PDF)
- 14 artigos sem keywords (genuíno — PDFs não têm Palavras-chave)
- 0% abstract_en exceto 006 (único com seção bilíngue)
- Sem ISBN (anais mais amplos que o livro publicado)

## Cobertura final

| Campo | N/19 | % |
|-------|------|---|
| abstract | 10 | 53% |
| abstract_en | 1 | 5% |
| keywords | 5 | 26% |
| keywords_en | 1 | 5% |
| references | 19 | 100% |
| sections | 19/19 | 100% |
| ORCID | 30/43 | 70% |

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** 3 correções humanas (001 split título/subtítulo, 012 urbanismo, 014 arquitetura). Causa: normalização contextual (áreas do saber em contexto genérico)
- [x] **3.2** Dict: sem alterações — "arquitetura"/"urbanismo" mantidos como área (maioria dos casos requer capitalização)
- [x] **3.3** Scripts: sem alterações (apenas 3 correções contextuais, padrão já conhecido)
- [x] **3.4** Pipeline: sem alterações necessárias
- [x] **3.5** Verificar: dry-run normalizar (8 regressões esperadas = correções humanas), validate 0 issues, dedup 0 merges
- [x] **3.6** Aprendizado: `revisao/sdpr02-aprendizado-revisao.json`
- [x] **3.7** Revisão de engenharia: autoavaliação 8/8 checks OK, sem scripts novos (auditoria completa feita no sdpr01)
- [x] **3.8** Cobertura final: abs 53%, abs_en 5%, kw 26%, kw_en 5%, refs 100%, ORCID 70%
- [x] **3.9** Fechar: dump + commit
