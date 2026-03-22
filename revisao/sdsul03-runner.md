# sdsul03 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-21 | Artigos: 39
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/39 | % |
|-------|-------|---|
| abstract | 33 | 85% |
| abstract_en | 28 | 72% |
| keywords | 30 | 77% |
| keywords_en | 24 | 62% |
| references | 33 | 85% |
| title_en | 0 | 0% |
| sections | 1 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint
- [x] **0.1** Cobertura: abs 85%, abs_en 72%, kw 77%, refs 85%, 3 ES
- [x] **0.2** 6 sem abstract (4 genuínos, 2 extraídos: 027, 028), 6 sem refs
- [x] **0.3** RESUMO labels: 33/39 (85%). Plumber extraído (39/39)
- [x] **0.4** Extraídos: 027 (abs+kw ES), 028 (abs PT+EN)
- [x] **0.5** Validate: 26→14 issues (1 A25 auto-fixed)
- [x] **0.6** EN: 0 novos (já importados)
- [x] **1.1a** Títulos: 14 correções manuais (nomes próprios, instituições, lowercase)
- [skip] **1.1b/1.1c** Títulos EN/ES `[SKIP: title_en = 0%]`
- [x] **1.2a-c** Refs: clean (3 backfill, 2 underscore), sweep (15 arts, 27 splits), 001/034 split manual
- [x] **1.3** Keywords: 0 alterações
- [x] **1.5** Loop: 14 restantes (5 A01, 2 A14, 7 A19)
- [x] **1.6a** abs 90%, abs_en 74%, kw 77%, refs 85%, ORCID 65%
- [x] **1.6b** ISBN 978-85-60188-11-6, PROPAR-UFRGS
- [x] **1.6c** Seção genérica "Artigos" (39/39)
- [x] **1.6d** 57 autores, 37 ORCID (65%), 0 dedup
- [x] **2.0** Validação final (14 issues) + HTML + dump

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** Diagnóstico: ":" no início (2), abstract_en em ES (1), credenciais (2), heading em ref (1)
- [x] **3.2** dict.db: sem alterações
- [x] **3.3** Scripts: A29 (pontuação no início do abstract), A30 (abstract_en em ES para locale=es)
- [x] **3.4** Pipeline: hierarquia de fontes para seções documentada
- [x] **3.5** Validação: 0 regressões em sdsul01/03, 0 falsos positivos em sdsul04
- [x] **3.6** Aprendizado registrado
- [x] **3.7** OK
- [x] **3.8** Checklist: 25/25 ✅
- [x] **3.9** Fechar
