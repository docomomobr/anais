# sdnne02 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-24 | Artigos: 33
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/33 | % |
|-------|-------|---|
| abstract | 32 | 97% |
| abstract_en | 0 | 0% |
| keywords | 31 | 94% |
| keywords_en | 0 | 0% |
| references | 30 | 91% |
| title_en | 0 | 0% |
| sections | 1 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint: 173b100 (anais.sql já atualizado)
- [x] **0.1** Cobertura: abs 97%, abs_en 0%, kw 94%, kw_en 0%, refs 91%
- [x] **0.2** Fora do padrão: 011/027 sem refs; 012 sem kw; 033 sem abs/kw/refs
- [x] **0.3** PDFs reinspecionados via plumber (33 arts, 5329 blocos). Sem doc/docx (RAR/CD-ROM)
- [x] **0.3b** Fontes plumber extraídas (33 arts, 5329 blocos)
- [x] **0.4** Seções: 1 genérica (Artigos Completos, hide_title=1). Sem eixos disponíveis
- [x] **0.5** Lacunas preenchidas: 011 +18 refs, 027 +8 refs do plumber. 033 reclassificado como mesa
- [x] **0.6** Extrair metadados EN: 7 abstract_en, 19 kw_en extraídos
- [x] **0.7** ES: 0 artigos com locale=es
- [x] **0.8** Validate --fix: 13 auto-fixes (1 A17 dup ref, 12 manuais: 003 split ref, 004/011/017 abs_en+kw_en, 009 abs_en truncado, 014 abs truncado, 016 kw_en extraído, 017 backfill, 020 abs_en limpo, 027 backfill+split). 029 A14 falso positivo (retórica)

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 14 alterações normalizer, 13 reversões, 11 correções LLM vs PDF
- [x] **1.1b** Títulos EN/ES [SKIP: title_en = 0]
- [x] **1.1c** Revisão LLM títulos EN/ES [SKIP: title_en = 0]
- [x] **1.2a** Refs limpeza base: 0 alterações (611 refs)
- [x] **1.2b** Refs sweep: 11 artigos (4 lixo, 9 joins, 3 splits, 2 non-refs). 611→599 refs
- [x] **1.2b+** Re-backfills: 0 backfills
- [x] **1.2c** Refs revisão LLM: 55 correções em 23 artigos (splits, joins, missing, truncated, non-refs, hyphens). 599→620 refs
- [x] **1.3** Keywords: 1 split (032 kw_en), 1 falso positivo revertido (005 "Cia.")
- [x] **1.5** Loop validação: 0 auto-fixes. 34 issues restantes (genuínos/falsos positivos)
- [x] **1.6** Cobertura OK. Seminário: Núcleo Docomomo BA.SE / UFBA, 2008
- [x] **1.7** Autores: 4 correções afiliação (009 Miranda FAU-UFPA, 015 Costa/Rodrigues Filho UnB, 029 Zein UPM)
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: +0 novos. Total: 31/44 (70%)
- [x] **1.10** Revisão LLM final:
  - [x] sdnne02-001: abstract_en inserido (2729c)
  - [x] sdnne02-002: abstract_en inserido (4092c)
  - [x] sdnne02-003: abstract_en inserido (3429c), title Escola maiúscula
  - [x] sdnne02-004: OK
  - [x] sdnne02-005: abstract_en inserido (2578c)
  - [x] sdnne02-006: abstract_en inserido (1278c)
  - [x] sdnne02-007: OK
  - [x] sdnne02-008: OK (abstract_en genuinamente ausente)
  - [x] sdnne02-009: abstract_en limpo (header seminário removido)
  - [x] sdnne02-010: abstract_en inserido (3290c)
  - [x] sdnne02-011: OK
  - [x] sdnne02-012: OK (abstract_en genuinamente ausente)
  - [x] sdnne02-013: abstract_en inserido (3190c), hifenização corrigida
  - [x] sdnne02-014: abstract_en inserido+trimmed (6086→2993c, legendas removidas)
  - [x] sdnne02-015: abstract_en inserido (2461c), kw_en +Natal Air Base
  - [x] sdnne02-016: OK
  - [x] sdnne02-017: OK
  - [x] sdnne02-018: abstract_en inserido+trimmed (3849→1935c, legendas removidas)
  - [x] sdnne02-019: abstract_en inserido (2773c)
  - [x] sdnne02-020: keywords numbering removed, "Tumble"→"Heritage listing"
  - [x] sdnne02-021: keywords_en "tumble"→"Heritage listing"
  - [x] sdnne02-022: OK
  - [x] sdnne02-023: abstract_en inserido (2517c)
  - [x] sdnne02-024: abstract_en inserido (1918c)
  - [x] sdnne02-025: abstract_en inserido+trimmed (3608→1554c), kw_en inserido
  - [x] sdnne02-026: OK (abstract_en inserido 2293c, ratio 0.60 genuíno)
  - [x] sdnne02-027: abstract_en inserido (2892c)
  - [x] sdnne02-028: abstract_en inserido (1541c)
  - [x] sdnne02-029: abstract_en inserido (1786c)
  - [x] sdnne02-030: abstract_en inserido+trimmed (6753→4405c, fig refs removidas)
  - [x] sdnne02-031: abstract_en inserido (2437c), kw_en inserido
  - [x] sdnne02-032: OK
  - [x] sdnne02-033: OK (mesa, sem metadados acadêmicos)

## Fase 2 — HTML de revisão + checkpoint

- [ ] **2.0** Validação final + HTML + commit
  ```
  python3 scripts/validate_metadata.py --slug sdnne02 --fix
  python3 scripts/gerar_revisao_html.py sdnne02
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdnne02-* && git commit -m "sdnne02 revisão automática (Fases 0-2)"
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
