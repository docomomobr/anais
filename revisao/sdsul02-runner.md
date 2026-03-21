# sdsul02 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-21 | Artigos: 35
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/35 | % |
|-------|-------|---|
| abstract | 28 | 80% |
| abstract_en | 24 | 69% |
| keywords | 25 | 71% |
| keywords_en | 21 | 60% |
| references | 34 | 97% |
| title_en | 0 | 0% |
| sections | 1 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint
- [x] **0.1** Cobertura: abs 80%, abs_en 69%, kw 71%, refs 97%, 1 seção, 1 ES
- [x] **0.2** 7 sem abstract (5 genuínos, 2 extraídos: 015, 026), 1 sem refs (034)
- [x] **0.3** Check RESUMO labels: 12/35 (34%) com label, mas abstracts font 10.0 são genuínos
- [x] **0.3b** Extrair fontes plumber (35/35)
- [x] **0.4** Extraídos: 015 (abs+abs_en+kw), 026 (abs+abs_en)
- [x] **0.5** Validate: 16 issues (5 A11, 3 A10, 5 A01, 2 A19, 1 A02)
- [x] **0.6** Extrair metadados EN (0 novos — já importados anteriormente)

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 10 correções manuais (nomes próprios, instituições)
- [skip] **1.1b** Títulos EN/ES `[SKIP: title_en = 0%]`
- [skip] **1.1c** Revisão LLM títulos EN/ES `[SKIP]`
- [x] **1.2a** Refs limpeza (1 backfill, 0 problemas)
- [x] **1.2b** Sweep (16 arts, 8 joins, 9 splits, 7 lixo, 1 não-ref, 1 dedup)
- [x] **1.2b+** Re-backfills (2)
- [x] **1.2c** Refs revisão LLM (005: 3→12 split, 035: long refs fixed)
- [x] **1.3** Keywords (2 arts limpos, 10 garbage removidas)
- [x] **1.5** Loop validação (8 restantes: 5 A01, 1 A02, 2 A19 — genuínos)
- [x] **1.6a** Cobertura: abs 86%, abs_en 74%, kw 74%, refs 97%, ORCID 71%
- [x] **1.6b** Metadados OK (ISBN 978-85-60188-09-3, PROPAR-UFRGS, 3 editors)
- [x] **1.6c** Seção genérica "Artigos" (35/35)
- [x] **1.6d** Autores: 41, 29 com ORCID (71%), 0 dedup

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação final (8 issues genuínos) + HTML + dump

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
