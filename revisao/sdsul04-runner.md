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

- [x] **3.1** 7 causas raiz: abstracts truncados (12), title_en=lixo (4), refs=notas (6), refs splits (5), ES em campo PT (9), subtítulo no abstract (4), abstract=credenciais (1)
- [x] **3.2** dict.db: sem alterações
- [x] **3.3** Scripts: +A31 (check_es_in_pt_field) no validate — detecta/corrige locale=es com abstract/keywords em campos PT. +move_field fix_action.
- [x] **3.4** Pipeline §1.10 reescrito: 8 passos explícitos, seção PROIBIDO, runner com checklist por artigo
- [x] **3.5** Dry-run sdsul01-03: 0 regressões, 0 A31 (já corrigidos)
- [x] **3.6** Memória: feedback_revisao_llm_real.md (ler plumber, não heurísticas)
- [x] **3.7** Revisão eng: A31 definido+chamado, move_field handler, pipeline §1.10 coerente com runner
- [x] **3.8** Cobertura final: abs 76%, abs_en 76%, abs_es 20%, kw 70%, kw_en 70%, kw_es 20%, refs 100%
- [x] **3.9** Fechar: dump + commit
