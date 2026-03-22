# sdsul04 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-21 | Artigos: 46
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/46 | % |
|-------|-------|---|
| abstract | 43 | 93% |
| abstract_en | 36 | 78% |
| keywords | 38 | 83% |
| keywords_en | 30 | 65% |
| references | 36 | 78% |
| title_en | 0 | 0% |
| sections | 6 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint
- [x] **0.1** abs 93%, abs_en 78%, kw 83%, refs 78%, 6 seções, 8 ES
- [x] **0.2** 3 sem abstract (007/046 genuínos, 034 extraído), 10 sem refs
- [x] **0.3** RESUMO labels: 21/46 (46%). Plumber extraído (46/46)
- [x] **0.4** Seções: 6 sessões já atribuídas (46/46)
- [x] **0.5** Lacunas: 034 abstract+keywords ES extraídos
- [x] **0.6** EN: 6 title_en, 4 subtitle_en, 2 keywords_en extraídos
- [x] **0.7** ES: 034 já extraído em 0.5
- [x] **0.8** Validate: 48 issues, 8 auto-fixed (A15, A17, A25, A26, 4×A28)
- [x] **1.1a** Títulos: 11 correções manuais
- [skip] **1.1b/1.1c** Títulos EN/ES `[SKIP: title_en 13%]`
- [x] **1.2a-c** Refs: clean (8 backfill, 2 underscore), sweep (28 notas, 20 joins, 7 splits, 10 não-refs)
- [x] **1.3** Keywords: 1 art, 2 garbage removidas
- [x] **1.5** Loop: 21 restantes (4 A01, 1 A02, 1 A03, 1 A09, 3 A10, 4 A11, 1 A14, 6 A19)
- [x] **1.6** abs 93%, abs_en 78%, kw 83%, refs 61%, ORCID 76%
- [x] **1.7** Autores: 55 autores (verificação pendente revisão humana)
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: 13 buscados, 0 novos (3 candidatos descartados)
- [x] **1.2c-LLM** Revisão LLM refs: 8 artigos com refs re-extraídas do plumber (004:1→2, 005:1→11, 008:2→7, 009:3→13, 021:4→1, 024:2→2, 025:3→11, 030:1→2, 045:1→1), 022/028 splits
- [x] **2.0** Validação final (29 issues) + HTML (46 artigos, 6 seções) + dump

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
