# sdnne07 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-25 | Artigos: 65
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/65 | % |
|-------|-------|---|
| abstract | 63 | 97% |
| abstract_en | 61 | 94% |
| keywords | 63 | 97% |
| keywords_en | 59 | 91% |
| references | 60 | 92% |
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
  python3 scripts/extrair_fontes_plumber.py --slug sdnne07 --profile-only
  python3 scripts/extrair_fontes_plumber.py --slug sdnne07
  ```
- [ ] **0.4** Seções/sessões — verificar nesta ordem:
  1. `fontes/` do seminário (HTML/XML de DVDs, sumários, programas)
  2. Folha de rosto dos artigos (cabeçalho do PDF indica eixo/sessão)
  3. Site original (campo `source` na tabela `seminars`)
  4. Busca na internet / Wayback Machine
  5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
- [ ] **0.5** Preencher lacunas no banco (salvar JSON antes, verificar idioma dos abstracts)
- [ ] **0.6** Extrair metadados EN: `python3 scripts/extrair_metadados_en.py --slug sdnne07`
- [ ] **0.7** Extrair metadados ES (artigos com locale=es: abstract, keywords do plumber)
- [ ] **0.8** Verificar abstracts + auto-fix
  ```
  python3 scripts/validate_metadata.py --slug sdnne07 --fix
  ```
  Depois: varredura manual (truncamento, lixo, cruzamento de idiomas)

## Fase 1 — Revisão automática

- [ ] **1.1a** Títulos PT: seed + normalizar + revisão LLM
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug sdnne07 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug sdnne07
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [ ] **1.1b** Títulos EN/ES:
  ```
  python3 scripts/normalizar_titulos_en.py --slug sdnne07 --dry-run
  python3 scripts/normalizar_titulos_en.py --slug sdnne07
  ``` `[SKIP: title_en = 0]`
- [ ] **1.1c** Revisão LLM títulos EN/ES (cada título vs PDF) `[SKIP: title_en = 0]`
- [ ] **1.2a** Refs limpeza base
  ```
  python3 scripts/clean_references.py --slug sdnne07 --dry-run
  python3 scripts/clean_references.py --slug sdnne07
  python3 scripts/check_references.py --slug sdnne07 --summary
  ```
- [ ] **1.2b** Refs sweep (8 passadas)
  ```
  python3 scripts/fix_validation_issues.py --slug sdnne07 --sweep-refs --dry-run
  python3 scripts/fix_validation_issues.py --slug sdnne07 --sweep-refs
  ```
- [ ] **1.2b+** Re-backfills: `python3 scripts/clean_references.py --slug sdnne07`
- [ ] **1.2c** Refs revisão LLM — TODOS os artigos vs fontes (ver §1.2c)
- [ ] **1.3** Keywords
  ```
  python3 scripts/fix_validation_issues.py --slug sdnne07 --clean-keywords --dry-run
  python3 scripts/fix_validation_issues.py --slug sdnne07 --clean-keywords
  ```
- [ ] **1.5** Loop validação: `python3 scripts/fix_validation_issues.py --slug sdnne07 --loop`
- [ ] **1.6** Cobertura de metadados + metadados do seminário (título, ISBN, editora)
- [ ] **1.7** Autores: verificar completude vs PDF (confrontar cada artigo com o PDF)
- [ ] **1.8** Dedup autores: `python3 dict/seed_authors.py && python3 scripts/dedup_authors.py`
- [ ] **1.9** ORCID: `python3 scripts/fetch_orcid.py --search --slug sdnne07` → `--review` → `--apply`
- [ ] **1.10** Revisão LLM final — TODOS os artigos, TODOS os campos vs plumber
  Para CADA artigo: ler o plumber INTEIRO, confrontar CADA campo (título, subtítulo,
  abstract, abstract_en, keywords, keywords_en, title_en, refs) com o texto do PDF.
  Corrigir na hora (R8). Registrar resultado de CADA artigo abaixo.
  Ver §1.10 do pipeline para procedimento detalhado.
  **1.10 — Resultado por artigo:**
  - [ ] sdnne07-001:
  - [ ] sdnne07-002:
  - [ ] sdnne07-003:
  - [ ] sdnne07-004:
  - [ ] sdnne07-005:
  - [ ] sdnne07-006:
  - [ ] sdnne07-007:
  - [ ] sdnne07-008:
  - [ ] sdnne07-009:
  - [ ] sdnne07-010:
  - [ ] sdnne07-011:
  - [ ] sdnne07-012:
  - [ ] sdnne07-013:
  - [ ] sdnne07-014:
  - [ ] sdnne07-015:
  - [ ] sdnne07-016:
  - [ ] sdnne07-017:
  - [ ] sdnne07-018:
  - [ ] sdnne07-019:
  - [ ] sdnne07-020:
  - [ ] sdnne07-021:
  - [ ] sdnne07-022:
  - [ ] sdnne07-023:
  - [ ] sdnne07-024:
  - [ ] sdnne07-025:
  - [ ] sdnne07-026:
  - [ ] sdnne07-027:
  - [ ] sdnne07-028:
  - [ ] sdnne07-029:
  - [ ] sdnne07-030:
  - [ ] sdnne07-031:
  - [ ] sdnne07-032:
  - [ ] sdnne07-033:
  - [ ] sdnne07-034:
  - [ ] sdnne07-035:
  - [ ] sdnne07-036:
  - [ ] sdnne07-037:
  - [ ] sdnne07-038:
  - [ ] sdnne07-039:
  - [ ] sdnne07-040:
  - [ ] sdnne07-041:
  - [ ] sdnne07-042:
  - [ ] sdnne07-043:
  - [ ] sdnne07-044:
  - [ ] sdnne07-045:
  - [ ] sdnne07-046:
  - [ ] sdnne07-047:
  - [ ] sdnne07-048:
  - [ ] sdnne07-049:
  - [ ] sdnne07-050:
  - [ ] sdnne07-051:
  - [ ] sdnne07-052:
  - [ ] sdnne07-053:
  - [ ] sdnne07-054:
  - [ ] sdnne07-055:
  - [ ] sdnne07-056:
  - [ ] sdnne07-057:
  - [ ] sdnne07-058:
  - [ ] sdnne07-059:
  - [ ] sdnne07-060:
  - [ ] sdnne07-061:
  - [ ] sdnne07-062:
  - [ ] sdnne07-063:
  - [ ] sdnne07-064:
  - [ ] sdnne07-065:

## Fase 2 — HTML de revisão + checkpoint

- [ ] **2.0** Validação final + HTML + commit
  ```
  python3 scripts/validate_metadata.py --slug sdnne07 --fix
  python3 scripts/gerar_revisao_html.py sdnne07
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdnne07-* && git commit -m "sdnne07 revisão automática (Fases 0-2)"
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
