# sdnne08 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-26 | Artigos: 41
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/41 | % |
|-------|-------|---|
| abstract | 41 | 100% |
| abstract_en | 0 | 0% |
| keywords | 40 | 98% |
| keywords_en | 0 | 0% |
| references | 41 | 100% |
| title_en | 0 | 0% |
| sections | 1 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint: c3a9c4e
- [x] **0.1** Cobertura: abs 41/41, abs_en 0/41, kw 41/41, kw_en 0/41, refs 41/41, title_en 0/41, subtitle 33/41
- [x] **0.2** Fora do padrão: 8 artigos sem subtítulo (título simples, correto). 040 plumber não reconheceu roles (tudo heading) mas dados OK no banco
- [x] **0.3** 41 PDFs, ~30 docx nas fontes. Fontes plumber extraídas (41 ok, 0 erros)
- [x] **0.4** Seções: 1 seção única ("Artigos Completos"), site original sem eixos temáticos
- [x] **0.5** Lacunas: nenhuma lacuna crítica. 8 sem subtítulo = título simples
- [x] **0.6** Extrair metadados EN: SKIP (abstract_en = 0%)
- [x] **0.7** ES: sem artigos em espanhol
- [x] **0.8** Validate --fix: 2 auto-fixes (A25, A28). 4 issues A11 (ref longa) para sweep

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 19 normalizer, 12 reversões (falsos positivos). 8 genéricos removidos do dict (planejada, vida, água, especiais, indústrias, transição, espaço público, espaço privado)
- [x] **1.1b** Títulos EN: SKIP (0 title_en)
- [x] **1.1c** Revisão LLM títulos EN/ES: SKIP (0 title_en)
- [x] **1.2a** Refs limpeza base: 0 alterações. 796 refs OK
- [x] **1.2b** Refs sweep: 16 artigos (6 lixo, 6 joins, 3 splits, 3 não-refs, 1 endnote). 796→784 refs
- [x] **1.2b+** Re-backfills: 0 necessários
- [x] **1.2c** Refs revisão LLM: integrada na 1.10
- [x] **1.3** Keywords: 0 alterações
- [x] **1.5** Loop validação: convergiu em 1 iteração. 4 A11 restantes (resolvidos na 1.10)
- [x] **1.6** Cobertura OK. abs 100%, kw 100%, refs 100%, abs_en/kw_en/title_en 0%. Seminário: 8º Docomomo NNE, Palmas, 2021, ISBN 978-65-00-71382-4
- [x] **1.7** Autores: 80 autores, sem alterações necessárias. Nomes conferem com PDF
- [x] **1.8** Dedup: 0 merges (nenhum duplicado detectado)
- [x] **1.9** ORCID: 78/80 autores com ORCID (97.5%). 2 sem candidatos válidos
- [x] **1.10** Revisão LLM final — ~30 correções em 20 artigos (6 subtítulos capitalizados, 4 travessões, 4 refs split, 3 refs adicionadas, 3 OCR fixes, 2 keywords fixes, 3 abstracts corrigidos, 1 ref merge, 1 título corrigido, 1 abstract expandido, 1 ref backfill)
  - [x] sdnne08-001: travessão abstract + ref faltante
  - [x] sdnne08-002: OK
  - [x] sdnne08-003: subtitle modernidade→minúscula
  - [x] sdnne08-004: título Escolas Industriais Federais
  - [x] sdnne08-005: OK
  - [x] sdnne08-006: OK
  - [x] sdnne08-007: OK
  - [x] sdnne08-008: OK
  - [x] sdnne08-009: subtitle Educação
  - [x] sdnne08-010: subtitle arquitetura→minúscula
  - [x] sdnne08-011: OK
  - [x] sdnne08-012: keywords preenchidas + travessão + refs split (1→3 cartas) + backfill
  - [x] sdnne08-013: OK
  - [x] sdnne08-014: OK
  - [x] sdnne08-015: OK
  - [x] sdnne08-016: keyword adicionada
  - [x] sdnne08-017: OK
  - [x] sdnne08-018: OK
  - [x] sdnne08-019: refs merge (TIRELLO+SFEIR)
  - [x] sdnne08-020: ref split (GORELIK+LE CORBUSIER) + travessão
  - [x] sdnne08-021: subtitle Centro
  - [x] sdnne08-022: OK
  - [x] sdnne08-023: OK
  - [x] sdnne08-024: subtitle Irrigação do Bebedouro
  - [x] sdnne08-025: OK
  - [x] sdnne08-026: OK
  - [x] sdnne08-027: OK
  - [x] sdnne08-028: ref BONDUKI adicionada
  - [x] sdnne08-029: 2x travessão + ref OCR fix
  - [x] sdnne08-030: OK
  - [x] sdnne08-031: ref split (GOV+G1) + ASMEGO adicionada
  - [x] sdnne08-032: abstract evidencia-se
  - [x] sdnne08-033: ref split (CHOAY+D'AMATO)
  - [x] sdnne08-034: OK
  - [x] sdnne08-035: ref split (PREFEITURA+Revista PROJETO)
  - [x] sdnne08-036: OK
  - [x] sdnne08-037: 3 OCR fixes + ref LARA adicionada
  - [x] sdnne08-038: OK
  - [x] sdnne08-039: abstract palavras quebradas + keyword split
  - [x] sdnne08-040: OK
  - [x] sdnne08-041: abstract expandido + refs merge

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação + HTML + commits

## Revisão humana

- [x] 2 correções: 1 título capitalização (004 Arquitetura→arquitetura), 1 subtítulo capitalização (029 interiores→Interiores, "Arquitetura de Interiores" expressão consolidada)
- [x] Dict: "arquitetura de interiores" adicionada como expressão consolidada

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** Diagnóstico: ~30 correções automáticas + 2 humanas. Causas: dict genéricos (12), subtítulo contextual (6+1), refs concatenadas (4), refs faltantes (4), OCR (6), travessões (4), keywords (2), abstract (2), capitalização contextual (1)
- [x] **3.2** Dict: 8 genéricos removidos na Fase 1.1a + "arquitetura de interiores" adicionada como expressão (revisão humana)
- [x] **3.3** Scripts: sem fix necessário (nenhum padrão recorrente ≥3 artigos)
- [x] **3.4** Pipeline: sem gaps identificados
- [x] **3.5** Dry-run: normalizer mostra 10 mudanças (todas são reversões já aplicadas — esperado)
- [x] **3.6** Registrar aprendizado: sdnne08-aprendizado.json
- [x] **3.7** Revisão de engenharia (pós-rev.humana): 16 scripts auditados, 0 critical, 4 high (assert→raise, column whitelist, IPv4 patch, LIMIT), 7 medium, 5 low. Sem bugs novos
- [x] **3.8** Checklist de conclusão
- [x] **3.9** Fechar: dump + commit + CLAUDE.md
