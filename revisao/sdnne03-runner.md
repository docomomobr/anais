# sdnne03 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-24 | Artigos: 41
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/41 | % |
|-------|-------|---|
| abstract | 41 | 100% |
| abstract_en | 29 | 71% |
| keywords | 38 | 93% |
| keywords_en | 32 | 78% |
| references | 41 | 100% |
| title_en | 0 | 0% |
| sections | 4 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint: 4c39194 (anais.sql já atualizado)
- [x] **0.1** Cobertura: abs 100%, abs_en 71%, kw 93%, kw_en 78%, refs 100% (677 refs)
- [x] **0.2** Fora do padrão: 12 sem abs_en; 013/032/034 sem kw; 9 sem kw_en
- [x] **0.3** PDFs reinspecionados via plumber (41 arts, 6261 blocos). Sem doc/docx
- [x] **0.3b** Fontes plumber extraídas (41 arts, 6261 blocos)
- [x] **0.4** Seções: 4 genéricas (Seção 1-4, hide_title=1). Sem nomes temáticos (rodapé só tem subtítulo do seminário)
- [x] **0.5** Lacunas: 013/032/034 sem kw genuíno (PDF não tem). 007/021/031/032 sem abs_en genuíno
- [x] **0.6** Extrair metadados EN: 8 abstract_en, 3 kw_en extraídos do plumber
- [x] **0.7** ES: 0 artigos com locale=es
- [x] **0.8** Validate --fix: 9 auto-fixes (8 A25 kw no abstract, 1 A27 PT no abstract_en). 25 issues restantes

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 10 alterações normalizer, 7 reversões, 22 correções LLM vs PDF (4 subtítulos adicionados: 013/019/020/027)
- [x] **1.1b** Títulos EN/ES [SKIP: title_en = 0]
- [x] **1.1c** Revisão LLM títulos EN/ES [SKIP: title_en = 0]
- [x] **1.2a** Refs limpeza base: 0 alterações (677 refs)
- [x] **1.2b** Refs sweep: 16 artigos (7 lixo, 17 joins, 11 splits, 3 non-refs, 4 endnotes). 677→657 refs
- [x] **1.2b+** Re-backfills: 0 backfills
- [x] **1.2c** Refs revisão LLM: ~45 correções em 24 artigos (splits, joins, missing, truncated, non-refs). 657→710 refs
- [x] **1.3** Keywords: 1 split (038 kw_en "." separator)
- [x] **1.5** Loop validação: 3 fixes (019/021 abs_en extraídos, 033 abs_en completado). 16 issues restantes
- [x] **1.6** Cobertura OK. Seminário: Núcleo Docomomo NNE / UFPB, 2010
- [x] **1.7** Autores: 13 artigos corrigidos (ordens, familynames, givennames), 61 afiliações inseridas
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: +2 novos (Amélia Reynaldo, Mércia Rocha). Total: 45/79 (56%)
- [x] **1.10** Revisão LLM final:
  - [x] sdnne03-001 a 014: OK (0 issues)
  - [x] sdnne03-015 a 021: OK (exceto 022 kw_en inserido, 024 footnote removido)
  - [x] sdnne03-022: kw_en inserido ("new monumentality; tectonics; Acácio Gil Borsoi")
  - [x] sdnne03-023 a 028: OK
  - [x] sdnne03-029 a 032: OK (031/032 sem abs_en genuíno)
  - [x] sdnne03-033: abstract_en trimmed (contaminação com body text)
  - [x] sdnne03-034: keywords PT inserido ("Paisagem cultural; arquitetura moderna; legislação")
  - [x] sdnne03-035: keywords_en formato corrigido
  - [x] sdnne03-036 a 041: OK

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação + HTML + commits (87c867f)
  ```
  python3 scripts/validate_metadata.py --slug sdnne03 --fix
  python3 scripts/gerar_revisao_html.py sdnne03
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdnne03-* && git commit -m "sdnne03 revisão automática (Fases 0-2)"
  ```

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Revisão humana

- [x] 5 correções humanas aplicadas:
  - sdnne03-004: refs split (ANDRADE+IAB concatenadas), removido Ibid colado
  - sdnne03-006: backfill 3 Idem/Ibidem, split entrevista+ofício, removido ref "."
  - sdnne03-007: title lowercase (antiga, análise, especial, moderna)
  - sdnne03-013: refs concatenadas (ref[6] 4-em-1 truncada, PACHECO+Projeto splitada)
  - sdnne03-021: subtitle "Património" → "património"

> Próximo: Fase 3

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** Diagnóstico: 245 correções automáticas + 5 humanas. Causas: 4 subtítulos ausentes, 53 refs LLM, 22 títulos LLM, 13 autores corrigidos, 61 afiliações. Humanas: 3 refs concatenadas (004/013), 1 backfill idem/ibidem (006), 1 title capitalização (007), 1 subtitle capitalização (021)
- [x] **3.2** Dict: 5 genéricos adicionados ao STOPWORDS (antiga, exposições, marítima, migrantes, severinos)
- [x] **3.3** Scripts: sem alterações (padrões já cobertos)
- [x] **3.4** Pipeline: sem gaps a adicionar
- [x] **3.5** Dry-run: 0 regressões em sdbr01/sdbr08/sdsul06/sdnne01
- [x] **3.6** Aprendizado registrado (sdnne03-aprendizado.json)
- [x] **3.7** Engenharia: 46 scripts auditados, 22 fixes total (3+1 HIGH + 10+8 MEDIUM) em 16 scripts
  - HIGH: _scan_fonts_sdbr13.py, _find_no_abstract_label.py, _check_pdf_text.py (file handle leaks)
  - MEDIUM: dump_anais_db, db2hugo, generate_ojs_xml, generate_static_pages, export_db_to_yaml, import_yaml_to_db, extract_title_en_sdbr13, dict/dump_db, dict/seed_titles, dict/seed_authors (try/finally)
- [x] **3.8** Checklist: abstract 100%, abs_en 95%, kw 95%, kw_en 90%, refs 100%, ORCID 56%, 5 issues genuínos
- [x] **3.9** Fechar: dump + commit + push + CLAUDE.md
