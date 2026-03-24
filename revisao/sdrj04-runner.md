# sdrj04 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-23 | Artigos: 17
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/17 | % |
|-------|-------|---|
| abstract | 16 | 94% |
| abstract_en | 11 | 65% |
| keywords | 15 | 88% |
| keywords_en | 11 | 65% |
| references | 15 | 88% |
| title_en | 0 | 0% |
| sections | 3 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit (8c85977)
- [x] **0.1** Levantar padrão de metadados (query cobertura → classificar campos)
- [x] **0.2** Listar artigos fora do padrão (003,006,007,008,016,017)
- [x] **0.3** Reinspecionar PDFs dos artigos fora do padrão
- [x] **0.3b** Extrair fontes plumber (17 artigos, 2834 blocos)
- [x] **0.4** Seções/sessões — 3 seções já existentes, todos os artigos atribuídos
- [x] **0.5** Preencher lacunas: 003/006 abstract_es+keywords_es (ES, não EN); 007/008/016/017 genuinamente ausentes
- [x] **0.6** Extrair metadados EN: 0 novos (11 já existentes, 6 sem seção EN)
- [x] **0.7** ES: 003/006 já inseridos em 0.5
- [x] **0.8** Validate --fix: 1 auto-fix (A20 overflow), 016 email removido do abstract

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 4 normalizados, 2 revertidos (genéricos), 3 corrigidos vs PDF (008 título errado, 016 subtítulo errado, 006 Instituto+protomoderna)
- [x] **1.1b** Títulos EN/ES [SKIP: title_en = 0]
- [x] **1.1c** Revisão LLM títulos EN/ES [SKIP: title_en = 0]
- [x] **1.2a** Refs limpeza base: 6 backfills, 0 problemas
- [x] **1.2b** Refs sweep: 13 artigos alterados (42 notas cortadas, 25 joins, 11 endnotes, 4 splits)
- [x] **1.2b+** Re-backfills: +4 splits, 285 refs
- [x] **1.2c** Refs revisão LLM: 24 non-refs removidas, 8 concatenadas splitadas. 285→261 refs
- [x] **1.3** Keywords: 003/004/007/013 limpas (contaminação autor/afiliação)
- [x] **1.5** Loop validação: 8 A10 (backfills genuínos), 0 outros
- [x] **1.6** Cobertura OK, metadados do seminário OK
- [x] **1.7** Autores: 25 autores, todos verificados vs PDF. 11 afiliações inseridas
- [x] **1.8** Dedup: 0 merges propostos
- [x] **1.9** ORCID: +1 (Barbara Cortizo). Total: 16/25 (64%)
- [x] **1.10** Revisão LLM final:
  - [x] sdrj04-001: OK
  - [x] sdrj04-002: OK
  - [x] sdrj04-003: OK
  - [x] sdrj04-004: OK
  - [x] sdrj04-005: OK
  - [x] sdrj04-006: abstract PT completado (1→3 parágrafos)
  - [x] sdrj04-007: keywords limpas
  - [x] sdrj04-008: OK
  - [x] sdrj04-009: OK
  - [x] sdrj04-010: OK
  - [x] sdrj04-011: OK
  - [x] sdrj04-012: abstract PT+EN completados, footnote marker removido, image credits removidas
  - [x] sdrj04-013: abstract PT+EN completados (1→3 parágrafos cada)
  - [x] sdrj04-014: OK
  - [x] sdrj04-015: OK
  - [x] sdrj04-016: abstract limpo (duplicação+contaminação removidas, 4357→1881c)
  - [x] sdrj04-017: OK (workshop, sem metadados acadêmicos)

## Fase 2 — HTML de revisão + checkpoint

- [ ] **2.0** Validação final + HTML + commit
  ```
  python3 scripts/validate_metadata.py --slug sdrj04 --fix
  python3 scripts/gerar_revisao_html.py sdrj04
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdrj04-* && git commit -m "sdrj04 revisão automática (Fases 0-2)"
  ```

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
