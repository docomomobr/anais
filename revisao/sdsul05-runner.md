# sdsul05 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-22 | Artigos: 37
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/37 | % |
|-------|-------|---|
| abstract | 26 | 70% |
| abstract_en | 24 | 65% |
| keywords | 35 | 95% |
| keywords_en | 23 | 62% |
| references | 36 | 97% |
| title_en | 0 | 0% |
| sections | 1 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint
- [x] **0.1** abs 70%, abs_en 65%, kw 95%, kw_en 62%, refs 97%, 2 EN, 0 ES
- [x] **0.2** 11 sem abstract (genuínos: sem label RESUMO no PDF)
- [x] **0.3** Plumber: 37/37 extraídos (4740 blocos)
- [x] **0.3b** Extraído plumber
- [x] **0.4** Seções: 37/37 já atribuídas (1 seção)
- [x] **0.5** 10 abstracts PT extraídos do plumber (p2), 7 abstract_en extraídos
- [x] **0.6** EN: 5 title_en, 4 subtitle_en, 8 keywords_en extraídos
- [x] **0.7** ES: 0 artigos ES (2 EN, 35 PT)
- [x] **0.8** Validate: 54 issues, 17 auto-fixed (A17×2, A22×4, A25×11)

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos: 17 normalização + 24 correções LLM (Artes→artes, Brutalista→brutalista, Viollet-le-duc→Viollet-le-Duc, etc.)
- [skip] **1.1b/1.1c** Títulos EN/ES `[SKIP: title_en 13%]`
- [x] **1.2a** Refs: clean (3 splits, 6 backfills)
- [x] **1.2b** Refs sweep (37 notas, 9 lixo, 29 joins, 5+11 endnotes, 8 splits, 25 não-refs, 2 dedup)
- [x] **1.2b+** Re-backfills: 1 backfill
- [x] **1.3** Keywords: 10 artigos (6 garbage, 21 splits), 6 kw_en re-extraídas do plumber
- [x] **1.5** Loop: 19 restantes (A01×2, A02×2, A10×7, A11×1, A12×1, A19×3)
- [x] **1.2c** Refs revisão LLM: 008 (30→14, notas removidas), 009 (16→5, legendas/body), 012 (12→11, footnote+header), 028 (1→13, re-extraído), 029 (6→14, re-extraído), 030 (16→15, footnote)
- [x] **1.6** abs 97%, abs_en 89%, kw 100%, kw_en 86%, refs 97%, ORCID 70%
- [x] **1.6b** Metadados seminário: OK (título, ISBN 978-85-61965-40-2, publisher Marcavisual, description)
- [x] **1.6c** Seções: 1 seção genérica "Artigos" — site PROPAR/Wayback/Google: sem eixos publicados
- [x] **1.6d** Autores verificados: 37/37 artigos confrontados com PDF. 1 correção: Marchetto→Marquetto (018)
- [x] **1.7** Autores: 48 autores
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: 14 buscados, 0 novos (1 candidato descartado)
- [x] **1.10** Revisão LLM final — 6 agentes paralelos (37 artigos)
  Correções aplicadas:
  - 002: abstract_en re-extraído (contaminado com legendas/citações do corpo)
  - 005: abstract_en completado (faltava 1o parágrafo — bloco role=footnote no plumber)
  - 009: abstract e abstract_en — removido ". " inicial (artefato label "Resumo.")
  - 010: keywords_en re-extraído (só tinha ["modern"])
  - 012: abstract/abstract_en — cortada bibliografia colada no final; keyword limpa (". TRC")
  - 015: abstract/abstract_en — removido "!" final (artefato template)
  - 016: abstract completado (faltava continuação em bloco footnote)
  - 019: abstract — removido EN colado; abstract_en re-extraído
  - 024: keyword corrigida ("moderna"→"modernas")
  - 034: abstract — removido heading EN colado no final
  Issues para revisão humana: refs contaminadas com notas em 008, 009, 012
  **1.10 — Resultado por artigo:**
  - [x] sdsul05-001: OK
  - [x] sdsul05-002: abstract_en re-extraído (contaminado), title "de"→"em" Montevidéu (anotado)
  - [x] sdsul05-003: OK
  - [x] sdsul05-004: keywords_en "building rehabilitation, environmental comfort" é 1 entrada (deveria ser 2)
  - [x] sdsul05-005: abstract_en completado (1o parágrafo faltava)
  - [x] sdsul05-006: OK (title "A preservação" vs PDF "Preservação" — mantido)
  - [x] sdsul05-007: OK
  - [x] sdsul05-008: refs contaminadas — notas [12]-[30], body text [1]. Para rev humana.
  - [x] sdsul05-009: abstract ". " removido; refs [1]-[11] são legendas/body, só [12]-[16] são refs reais
  - [x] sdsul05-010: keywords_en corrigido
  - [x] sdsul05-011: refs [9] word-run, [10] misattributed (Summerson→Viollet-le-Duc)
  - [x] sdsul05-012: abstract/kw limpos; refs [3] body text, [4] header, [10] footnote
  - [x] sdsul05-013: OK (refs genuínas, sem kw_en no PDF)
  - [x] sdsul05-014: OK
  - [x] sdsul05-015: abstract "!" removido, kw_en vazio (genuíno)
  - [x] sdsul05-016: abstract completado (continuação em footnote block)
  - [x] sdsul05-017: OK (kw_en "Gravel" = erro do autor, não extração)
  - [x] sdsul05-018: OK
  - [x] sdsul05-019: abstract limpo (EN removido), abstract_en re-extraído
  - [x] sdsul05-020: OK
  - [x] sdsul05-021: OK
  - [x] sdsul05-022: OK (em-dash é convenção do projeto)
  - [x] sdsul05-023: OK
  - [x] sdsul05-024: keyword corrigida
  - [x] sdsul05-025: OK
  - [x] sdsul05-026: OK (EN, sem abstract genuíno)
  - [x] sdsul05-027: OK
  - [x] sdsul05-028: OK
  - [x] sdsul05-029: OK
  - [x] sdsul05-030: OK
  - [x] sdsul05-031: OK
  - [x] sdsul05-032: OK
  - [x] sdsul05-033: OK
  - [x] sdsul05-034: abstract limpo (heading EN removido)
  - [x] sdsul05-035: OK
  - [x] sdsul05-036: OK (subtitle "Expo 92" vs PDF "Expo´92" — aceito)
  - [x] sdsul05-037: OK

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação final (13 issues) + HTML (37 artigos, 1 seção) + dump

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
