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
- [x] **1.2c** Refs revisão LLM: 008 (30→14, notas removidas), 009 (16→5, legendas/body), 012 (12→12 footnote+header+split), 028 (1→13, re-extraído), 029 (6→14, re-extraído), 030 (16→15, footnote)
- [x] **1.3** Keywords: 10 artigos (6 garbage, 21 splits), 6 kw_en re-extraídas do plumber
- [x] **1.5** Loop: 19→13 issues após correções pós-1.10
- [x] **1.6a** abs 97%, abs_en 89%, kw 100%, kw_en 86%, refs 97%, ORCID 70%
- [x] **1.6b** Metadados seminário: OK (título, ISBN 978-85-61965-40-2, publisher Marcavisual, description)
- [x] **1.6c** Seções: 1 seção genérica "Artigos" — esgotadas fontes (site PROPAR 404, Wayback inacessível, Google, Facebook, cabeçalhos dos PDFs: nenhuma indicação de eixos)
- [x] **1.6d** Autores verificados: 37/37 artigos confrontados com PDF. 1 correção: Marchetto→Marquetto (018)
- [x] **1.7** Autores: 48 autores
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: 14 buscados, 0 novos (1 candidato descartado)
- [x] **1.10** Revisão LLM final — 6 agentes paralelos (37 artigos)
  Correções 1.10 (revisão LLM por campo):
  - 002: abstract_en re-extraído (contaminado com legendas/citações do corpo)
  - 005: abstract_en completado (faltava 1o parágrafo — bloco role=footnote no plumber)
  - 009: abstract e abstract_en — removido ". " inicial (artefato label "Resumo.")
  - 010: keywords_en re-extraído (só tinha ["modern"])
  - 012: abstract/abstract_en — cortada bibliografia colada no final; keyword limpa (". TRC")
  - 015: abstract/abstract_en — removido "!" final (artefato template)
  - 016: abstract completado (faltava continuação em bloco footnote)
  - 019: abstract — removido EN colado; abstract_en re-extraído + completado (bloco adjacente)
  - 024: keyword corrigida ("moderna"→"modernas")
  - 034: abstract — removido heading EN colado no final
  Correções pós-1.10 (issues residuais resolvidos):
  - 004: keywords_en split ("building rehabilitation, environmental comfort" → 2 entradas)
  - 008: 7 backfills (Comas ×2 + underscores)
  - 010: underscores removidos de refs [0],[1]
  - 012: ref [8] split (Lima+Luz concatenadas)
  - 018: 2 backfills (Imbronito)
  - 019: abstract_en completado (bloco footnote adjacente: "preservation of modern industrial heritage.")
  - 020: 1 backfill (Ana Luiza Nobre)
  - 025: abstract_en re-extraído (truncado 1999→3182c)
  - 027: keywords limpa (prefixo "/key words:" removido); keywords_en zerada (= PT, não EN real)
  - 030: keywords split (3 termos concatenados com "-"); keywords_en corrigida (body text → 3 termos)
  - 031: abstract_en re-extraído (truncado 1240→2672c)
  **1.10 — Resultado por artigo:**
  - [x] sdsul05-001: OK
  - [x] sdsul05-002: abstract_en re-extraído (contaminado com body text)
  - [x] sdsul05-003: OK
  - [x] sdsul05-004: keywords_en split (1→3 entradas)
  - [x] sdsul05-005: abstract_en completado (1o parágrafo faltava)
  - [x] sdsul05-006: OK (title "A preservação" vs PDF "Preservação" — mantido)
  - [x] sdsul05-007: OK
  - [x] sdsul05-008: refs limpas (30→14, notas removidas) + 2 backfills Comas
  - [x] sdsul05-009: abstract ". " removido; refs limpas (16→5, legendas/body removidos)
  - [x] sdsul05-010: keywords_en corrigido; underscores removidos de refs
  - [x] sdsul05-011: OK (refs [9] word-run e [10] misattribution são do PDF original)
  - [x] sdsul05-012: abstract/kw limpos; refs: footnote removido, header limpo, split Lima+Luz
  - [x] sdsul05-013: OK (sem kw_en no PDF — genuíno)
  - [x] sdsul05-014: OK
  - [x] sdsul05-015: abstract "!" removido, kw_en vazio (genuíno)
  - [x] sdsul05-016: abstract completado (continuação em bloco footnote)
  - [x] sdsul05-017: OK (kw_en "Gravel" = erro do autor, não extração)
  - [x] sdsul05-018: OK + 2 backfills Imbronito
  - [x] sdsul05-019: abstract limpo (EN removido), abstract_en completado (bloco adjacente)
  - [x] sdsul05-020: OK + 1 backfill Nobre
  - [x] sdsul05-021: OK
  - [x] sdsul05-022: OK (em-dash é convenção do projeto)
  - [x] sdsul05-023: OK
  - [x] sdsul05-024: keyword corrigida ("moderna"→"modernas")
  - [x] sdsul05-025: abstract_en re-extraído (1999→3182c)
  - [x] sdsul05-026: OK (EN, sem abstract genuíno)
  - [x] sdsul05-027: keywords limpa (prefix removido), kw_en zerada
  - [x] sdsul05-028: refs re-extraídas do plumber (1→13)
  - [x] sdsul05-029: refs re-extraídas do plumber (6 body text → 14 refs reais)
  - [x] sdsul05-030: keywords split, keywords_en corrigida, refs: footnote+header removidos
  - [x] sdsul05-031: abstract_en re-extraído (1240→2672c)
  - [x] sdsul05-032: OK
  - [x] sdsul05-033: OK
  - [x] sdsul05-034: abstract limpo (heading EN removido)
  - [x] sdsul05-035: OK
  - [x] sdsul05-036: OK (subtitle "Expo 92" vs PDF "Expo´92" — aceito)
  - [x] sdsul05-037: OK

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação final (4 issues genuínos) + HTML (37 artigos, 1 seção) + dump + commit

Issues genuínos restantes:
- A01: 015, 025 — kw_en ausente no PDF
- A02: 016 — abs_en ausente no PDF
- A11: 006 — ref legítima com URL longa (não é concatenação)

## Cobertura final

| Campo | N/37 | % |
|-------|-------|---|
| abstract | 36 | 97% |
| abstract_en | 33 | 89% |
| keywords | 37 | 100% |
| keywords_en | 32 | 86% |
| references | 36 | 97% |
| title_en | 5 | 13% |
| sections | 37 | 100% |
| ORCID | 34/48 | 70% |

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** 5 causas raiz: abs_en truncado por bloco adjacente (5), refs contaminadas (4), label ABSTRACT colado (1), title_en ALL CAPS (1), normalizer over-capitaliza subtítulos (11)
- [x] **3.2** Dict: sem alterações (palavras ambíguas — regressão em títulos se removidas)
- [x] **3.3** Scripts: validate_metadata.py A29 expandido (strip labels ABSTRACT/RESUMO); gerar_runner.py (skip 1.1b só se title_en=0)
- [x] **3.4** Pipeline: sem alterações (ordem OK, problema era skip no runner)
- [x] **3.5** Dry-run: sdsul05 0 regressões, sdsul04 0 regressões
- [x] **3.6** Aprendizado: sdsul05-aprendizado-revisao.json
- [x] **3.7** Engenharia: A29 testado (label strip OK), gerar_runner.py verificado
- [x] **3.8** Cobertura final: abs 97%, abs_en 89%, kw 100%, kw_en 86%, refs 97%, ORCID 70%
- [x] **3.9** Fechar: dump + commit
