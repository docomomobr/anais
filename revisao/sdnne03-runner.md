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

- [ ] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit
- [ ] **0.1** Levantar padrão de metadados (query cobertura → classificar campos)
- [ ] **0.2** Listar artigos fora do padrão (campos esperados mas ausentes)
- [ ] **0.3** Reinspecionar PDFs dos artigos fora do padrão (hierarquia: docx → plumber → pdftotext)
- [ ] **0.3b** Extrair fontes plumber
  ```
  python3 scripts/extrair_fontes_plumber.py --slug sdnne03 --profile-only
  python3 scripts/extrair_fontes_plumber.py --slug sdnne03
  ```
- [ ] **0.4** Seções/sessões — verificar nesta ordem:
  1. `fontes/` do seminário (HTML/XML de DVDs, sumários, programas)
  2. Folha de rosto dos artigos (cabeçalho do PDF indica eixo/sessão)
  3. Site original (campo `source` na tabela `seminars`)
  4. Busca na internet / Wayback Machine
  5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
- [ ] **0.5** Preencher lacunas no banco (salvar JSON antes, verificar idioma dos abstracts)
- [ ] **0.6** Extrair metadados EN: `python3 scripts/extrair_metadados_en.py --slug sdnne03`
- [ ] **0.7** Extrair metadados ES (artigos com locale=es: abstract, keywords do plumber)
- [ ] **0.8** Verificar abstracts + auto-fix
  ```
  python3 scripts/validate_metadata.py --slug sdnne03 --fix
  ```
  Depois: varredura manual (truncamento, lixo, cruzamento de idiomas)

## Fase 1 — Revisão automática

- [ ] **1.1a** Títulos PT: seed + normalizar + revisão LLM
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug sdnne03 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug sdnne03
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [ ] **1.1b** Títulos EN/ES: `python3 scripts/normalizar_titulos_en.py --slug sdnne03` `[SKIP: title_en = 0]`
- [ ] **1.1c** Revisão LLM títulos EN/ES (cada título vs PDF) `[SKIP: title_en = 0]`
- [ ] **1.2a** Refs limpeza base
  ```
  python3 scripts/clean_references.py --slug sdnne03 --dry-run
  python3 scripts/clean_references.py --slug sdnne03
  python3 scripts/check_references.py --slug sdnne03 --summary
  ```
- [ ] **1.2b** Refs sweep (8 passadas)
  ```
  python3 scripts/fix_validation_issues.py --slug sdnne03 --sweep-refs --dry-run
  python3 scripts/fix_validation_issues.py --slug sdnne03 --sweep-refs
  ```
- [ ] **1.2b+** Re-backfills: `python3 scripts/clean_references.py --slug sdnne03`
- [ ] **1.2c** Refs revisão LLM — TODOS os artigos vs fontes (ver §1.2c)
- [ ] **1.3** Keywords
  ```
  python3 scripts/fix_validation_issues.py --slug sdnne03 --clean-keywords --dry-run
  python3 scripts/fix_validation_issues.py --slug sdnne03 --clean-keywords
  ```
- [ ] **1.5** Loop validação: `python3 scripts/fix_validation_issues.py --slug sdnne03 --loop`
- [ ] **1.6** Cobertura de metadados + metadados do seminário (título, ISBN, editora)
- [ ] **1.7** Autores: verificar completude vs PDF (confrontar cada artigo com o PDF)
- [ ] **1.8** Dedup autores: `python3 dict/seed_authors.py && python3 scripts/dedup_authors.py`
- [ ] **1.9** ORCID: `python3 scripts/fetch_orcid.py --search --slug sdnne03` → `--review` → `--apply`
- [ ] **1.10** Revisão LLM final — TODOS os artigos, TODOS os campos vs plumber
  Para CADA artigo: ler o plumber INTEIRO, confrontar CADA campo (título, subtítulo,
  abstract, abstract_en, keywords, keywords_en, title_en, refs) com o texto do PDF.
  Corrigir na hora (R8). Registrar resultado de CADA artigo abaixo.
  Ver §1.10 do pipeline para procedimento detalhado.
  **1.10 — Resultado por artigo:**
  - [ ] sdnne03-001:
  - [ ] sdnne03-002:
  - [ ] sdnne03-003:
  - [ ] sdnne03-004:
  - [ ] sdnne03-005:
  - [ ] sdnne03-006:
  - [ ] sdnne03-007:
  - [ ] sdnne03-008:
  - [ ] sdnne03-009:
  - [ ] sdnne03-010:
  - [ ] sdnne03-011:
  - [ ] sdnne03-012:
  - [ ] sdnne03-013:
  - [ ] sdnne03-014:
  - [ ] sdnne03-015:
  - [ ] sdnne03-016:
  - [ ] sdnne03-017:
  - [ ] sdnne03-018:
  - [ ] sdnne03-019:
  - [ ] sdnne03-020:
  - [ ] sdnne03-021:
  - [ ] sdnne03-022:
  - [ ] sdnne03-023:
  - [ ] sdnne03-024:
  - [ ] sdnne03-025:
  - [ ] sdnne03-026:
  - [ ] sdnne03-027:
  - [ ] sdnne03-028:
  - [ ] sdnne03-029:
  - [ ] sdnne03-030:
  - [ ] sdnne03-031:
  - [ ] sdnne03-032:
  - [ ] sdnne03-033:
  - [ ] sdnne03-034:
  - [ ] sdnne03-035:
  - [ ] sdnne03-036:
  - [ ] sdnne03-037:
  - [ ] sdnne03-038:
  - [ ] sdnne03-039:
  - [ ] sdnne03-040:
  - [ ] sdnne03-041:

## Fase 2 — HTML de revisão + checkpoint

- [ ] **2.0** Validação final + HTML + commit
  ```
  python3 scripts/validate_metadata.py --slug sdnne03 --fix
  python3 scripts/gerar_revisao_html.py sdnne03
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdnne03-* && git commit -m "sdnne03 revisão automática (Fases 0-2)"
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
