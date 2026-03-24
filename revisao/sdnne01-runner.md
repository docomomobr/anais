# sdnne01 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-24 | Artigos: 44
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/44 | % |
|-------|-------|---|
| abstract | 44 | 100% |
| abstract_en | 41 | 93% |
| keywords | 44 | 100% |
| keywords_en | 35 | 80% |
| references | 43 | 98% |
| title_en | 0 | 0% |
| sections | 10 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint: 07f66e0 (anais.sql já atualizado)
- [x] **0.1** Cobertura: abs 100%, abs_en 93%, kw 100%, kw_en 80%, refs 98%
- [x] **0.2** Fora do padrão: 027/031/044 sem abs_en; 006/010/012/020/021/026/030/041/044 sem kw_en; 031 sem refs
- [x] **0.3** PDFs reinspecionados via plumber (44 arts, 8023 blocos). Sem doc/docx (CD-ROM)
- [x] **0.3b** Fontes plumber extraídas (44 arts, 8023 blocos)
- [x] **0.4** Seções: 10 já existentes, todos os artigos atribuídos
- [x] **0.5** Lacunas preenchidas: 006 kw_en inseridas, 003 kw_en limpas (contaminação)
- [x] **0.6** Extrair metadados EN: 1 title_en, 2 kw_en extraídos
- [x] **0.7** ES: 0 artigos com locale=es
- [x] **0.8** Validate --fix: 12 auto-fixes (11 A25 kw coladas, 1 A28 título). 13 issues revisados: 027/031/044 abs_en genuinamente ausentes, 010/020/021/026 kw_en genuinamente ausentes, 008/009 A19 falsos positivos, 035 abstract_en OK

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 3 aceitos (portuguesa, 2× modernista), 8 revertidos. 16 correções LLM vs PDF (002/005/009/016/017/025/028/029/031/034/036/037/040/041/044)
- [x] **1.1b** Títulos EN/ES [SKIP: title_en = 0]
- [x] **1.1c** Revisão LLM títulos EN/ES [SKIP: title_en = 0]
- [x] **1.2a** Refs limpeza base: 0 alterações (693 refs)
- [x] **1.2b** Refs sweep: 16 artigos (6 lixo, 12 joins, 1 split, 10 non-refs). 693→666 refs
- [x] **1.2b+** Re-backfills: 0 backfills
- [x] **1.2c** Refs revisão LLM: 23 correções em 13 artigos (splits, joins, missing, non-refs). 666→684 refs
- [x] **1.3** Keywords: 2 artigos (1 ALL CAPS removido, 1 split). 034/028 keywords_en contaminação limpa
- [x] **1.5** Loop validação: 030 abs_en re-extraído (934→3444c). 9 issues restantes (genuínos)
- [x] **1.6** Cobertura OK. Seminário: ISBN 978-85-98747-02-6, DEA-UNICAP/MDU-UFPE/CECI, 2006
- [x] **1.7** Autores: 10 correções (001/006 autor removido, 015 nome restaurado, 016/021 autores adicionados, 025/030/036/040 nomes corrigidos). 61 afiliações inseridas
- [x] **1.8** Dedup: 2 merges (Mariana Bonates, Ceila Cardoso)
- [x] **1.9** ORCID: +1 (Hélio Farias). Total: 43/73 (58%)
- [x] **1.10** Revisão LLM final:
  - [x] sdnne01-001: OK
  - [x] sdnne01-002: OK
  - [x] sdnne01-003: OK
  - [x] sdnne01-004: OK
  - [x] sdnne01-005: OK
  - [x] sdnne01-006: OK
  - [x] sdnne01-007: OK
  - [x] sdnne01-008: OK
  - [x] sdnne01-009: OK
  - [x] sdnne01-010: OK
  - [x] sdnne01-011: OK
  - [x] sdnne01-012: keywords_en "São" → "São Paulo"
  - [x] sdnne01-013: OK
  - [x] sdnne01-014: keywords split (1→2 itens)
  - [x] sdnne01-015: OK
  - [x] sdnne01-016: OK
  - [x] sdnne01-017: abstract: nome preposto
  - [x] sdnne01-018: OK
  - [x] sdnne01-019: OK
  - [x] sdnne01-020: OK
  - [x] sdnne01-021: OK
  - [x] sdnne01-022: keywords split (1→3 itens)
  - [x] sdnne01-023: OK
  - [x] sdnne01-024: keywords limpa (contaminação título)
  - [x] sdnne01-025: OK
  - [x] sdnne01-026: keywords split (1→3 itens)
  - [x] sdnne01-027: OK
  - [x] sdnne01-028: OK
  - [x] sdnne01-029: OK
  - [x] sdnne01-030: keywords label removido
  - [x] sdnne01-031: OK
  - [x] sdnne01-032: OK
  - [x] sdnne01-033: keywords split, abstract_en título removido
  - [x] sdnne01-034: OK
  - [x] sdnne01-035: OK
  - [x] sdnne01-036: keywords_en garbage removido
  - [x] sdnne01-037: OK
  - [x] sdnne01-038: keywords split PT+EN
  - [x] sdnne01-039: OK
  - [x] sdnne01-040: OK
  - [x] sdnne01-041: OK
  - [x] sdnne01-042: OK
  - [x] sdnne01-043: OK
  - [x] sdnne01-044: OK

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação + HTML + commits (80c97e5, deb7c69, c56ec91, 3976da3)

## Revisão humana

- [x] 5 correções aplicadas (009 ponto final, 001 título, 020/029 abstract_en truncado, 031 resumo)

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** Diagnóstico: 190 correções (185 auto + 5 humanas). Causa principal: abstract_en truncados da importação YAML (12 artigos)
- [x] **3.2** Dict: nenhuma alteração necessária
- [x] **3.3** Scripts: A32 (ratio PT/EN) + limites plumber aumentados (4-5→8-10)
- [x] **3.4** Pipeline: sem gaps a adicionar
- [x] **3.5** Dry-run: 0 regressões em sdbr01/sdbr08/sdsul06
- [x] **3.6** Aprendizado registrado (sdnne01-aprendizado.json)
- [x] **3.7** Engenharia: 18 scripts auditados, 7 fixes (1 HIGH + 6 MEDIUM)
- [x] **3.8** Checklist: abstract 100%, abs_en 95%, kw 100%, kw_en 86%, refs 100%, ORCID 58%, 7 issues genuínos
- [x] **3.9** Fechar: dump + commit + push + CLAUDE.md
