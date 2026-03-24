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

- [ ] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit
- [ ] **0.1** Levantar padrão de metadados (query cobertura → classificar campos)
- [ ] **0.2** Listar artigos fora do padrão (campos esperados mas ausentes)
- [ ] **0.3** Reinspecionar PDFs dos artigos fora do padrão (hierarquia: docx → plumber → pdftotext)
- [ ] **0.3b** Extrair fontes plumber
  ```
  python3 scripts/extrair_fontes_plumber.py --slug sdnne02 --profile-only
  python3 scripts/extrair_fontes_plumber.py --slug sdnne02
  ```
- [ ] **0.4** Seções/sessões — verificar nesta ordem:
  1. `fontes/` do seminário (HTML/XML de DVDs, sumários, programas)
  2. Folha de rosto dos artigos (cabeçalho do PDF indica eixo/sessão)
  3. Site original (campo `source` na tabela `seminars`)
  4. Busca na internet / Wayback Machine
  5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
- [ ] **0.5** Preencher lacunas no banco (salvar JSON antes, verificar idioma dos abstracts)
- [ ] **0.6** Extrair metadados EN `[SKIP: abstract_en < 30%]`: `python3 scripts/extrair_metadados_en.py --slug sdnne02`
- [ ] **0.7** Extrair metadados ES (artigos com locale=es: abstract, keywords do plumber)
- [ ] **0.8** Verificar abstracts + auto-fix
  ```
  python3 scripts/validate_metadata.py --slug sdnne02 --fix
  ```
  Depois: varredura manual (truncamento, lixo, cruzamento de idiomas)

## Fase 1 — Revisão automática

- [ ] **1.1a** Títulos PT: seed + normalizar + revisão LLM
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug sdnne02 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug sdnne02
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [ ] **1.1b** Títulos EN/ES: `python3 scripts/normalizar_titulos_en.py --slug sdnne02` `[SKIP: title_en = 0]`
- [ ] **1.1c** Revisão LLM títulos EN/ES (cada título vs PDF) `[SKIP: title_en = 0]`
- [ ] **1.2a** Refs limpeza base
  ```
  python3 scripts/clean_references.py --slug sdnne02 --dry-run
  python3 scripts/clean_references.py --slug sdnne02
  python3 scripts/check_references.py --slug sdnne02 --summary
  ```
- [ ] **1.2b** Refs sweep (8 passadas)
  ```
  python3 scripts/fix_validation_issues.py --slug sdnne02 --sweep-refs --dry-run
  python3 scripts/fix_validation_issues.py --slug sdnne02 --sweep-refs
  ```
- [ ] **1.2b+** Re-backfills: `python3 scripts/clean_references.py --slug sdnne02`
- [ ] **1.2c** Refs revisão LLM — TODOS os artigos vs fontes (ver §1.2c)
- [ ] **1.3** Keywords
  ```
  python3 scripts/fix_validation_issues.py --slug sdnne02 --clean-keywords --dry-run
  python3 scripts/fix_validation_issues.py --slug sdnne02 --clean-keywords
  ```
- [ ] **1.5** Loop validação: `python3 scripts/fix_validation_issues.py --slug sdnne02 --loop`
- [ ] **1.6** Cobertura de metadados + metadados do seminário (título, ISBN, editora)
- [ ] **1.7** Autores: verificar completude vs PDF (confrontar cada artigo com o PDF)
- [ ] **1.8** Dedup autores: `python3 dict/seed_authors.py && python3 scripts/dedup_authors.py`
- [ ] **1.9** ORCID: `python3 scripts/fetch_orcid.py --search --slug sdnne02` → `--review` → `--apply`
- [ ] **1.10** Revisão LLM final — TODOS os artigos, TODOS os campos vs plumber
  Para CADA artigo: ler o plumber INTEIRO, confrontar CADA campo (título, subtítulo,
  abstract, abstract_en, keywords, keywords_en, title_en, refs) com o texto do PDF.
  Corrigir na hora (R8). Registrar resultado de CADA artigo abaixo.
  Ver §1.10 do pipeline para procedimento detalhado.
  **1.10 — Resultado por artigo:**
  - [ ] sdnne02-001:
  - [ ] sdnne02-002:
  - [ ] sdnne02-003:
  - [ ] sdnne02-004:
  - [ ] sdnne02-005:
  - [ ] sdnne02-006:
  - [ ] sdnne02-007:
  - [ ] sdnne02-008:
  - [ ] sdnne02-009:
  - [ ] sdnne02-010:
  - [ ] sdnne02-011:
  - [ ] sdnne02-012:
  - [ ] sdnne02-013:
  - [ ] sdnne02-014:
  - [ ] sdnne02-015:
  - [ ] sdnne02-016:
  - [ ] sdnne02-017:
  - [ ] sdnne02-018:
  - [ ] sdnne02-019:
  - [ ] sdnne02-020:
  - [ ] sdnne02-021:
  - [ ] sdnne02-022:
  - [ ] sdnne02-023:
  - [ ] sdnne02-024:
  - [ ] sdnne02-025:
  - [ ] sdnne02-026:
  - [ ] sdnne02-027:
  - [ ] sdnne02-028:
  - [ ] sdnne02-029:
  - [ ] sdnne02-030:
  - [ ] sdnne02-031:
  - [ ] sdnne02-032:
  - [ ] sdnne02-033:

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
