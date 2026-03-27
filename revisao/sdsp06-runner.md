# sdsp06 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-27 | Artigos: 37
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/37 | % |
|-------|-------|---|
| abstract | 37 | 100% |
| abstract_en | 1 | 3% |
| keywords | 37 | 100% |
| keywords_en | 1 | 3% |
| references | 36 | 97% |
| title_en | 0 | 0% |
| sections | 9 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [ ] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit
- [ ] **0.1** Levantar padrão de metadados (query cobertura → classificar campos)
- [ ] **0.2** Listar artigos fora do padrão (campos esperados mas ausentes)
- [ ] **0.3** Reinspecionar PDFs dos artigos fora do padrão (hierarquia: docx → plumber → pdftotext)
- [ ] **0.3b** Extrair fontes plumber
  ```
  python3 scripts/extrair_fontes_plumber.py --slug sdsp06 --profile-only
  python3 scripts/extrair_fontes_plumber.py --slug sdsp06
  ```
- [ ] **0.4** Seções/sessões — verificar nesta ordem:
  1. `fontes/` do seminário (HTML/XML de DVDs, sumários, programas)
  2. Folha de rosto dos artigos (cabeçalho do PDF indica eixo/sessão)
  3. Site original (campo `source` na tabela `seminars`)
  4. Busca na internet / Wayback Machine
  5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
- [ ] **0.5** Preencher lacunas no banco (salvar JSON antes, verificar idioma dos abstracts)
- [ ] **0.6** Extrair metadados EN `[SKIP: abstract_en < 30%]`: `python3 scripts/extrair_metadados_en.py --slug sdsp06`
- [ ] **0.7** Extrair metadados ES (artigos com locale=es: abstract, keywords do plumber)
- [ ] **0.8** Verificar abstracts + auto-fix
  ```
  python3 scripts/validate_metadata.py --slug sdsp06 --fix
  ```
  Depois: varredura manual (truncamento, lixo, cruzamento de idiomas)

## Fase 1 — Revisão automática

- [ ] **1.1a** Títulos PT: seed + normalizar + revisão LLM
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug sdsp06 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug sdsp06
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [ ] **1.1b** Títulos EN/ES:
  ```
  python3 scripts/normalizar_titulos_en.py --slug sdsp06 --dry-run
  python3 scripts/normalizar_titulos_en.py --slug sdsp06
  ``` `[SKIP: title_en = 0]`
- [ ] **1.1c** Revisão LLM títulos EN/ES (cada título vs PDF) `[SKIP: title_en = 0]`
- [ ] **1.2a** Refs limpeza base
  ```
  python3 scripts/clean_references.py --slug sdsp06 --dry-run
  python3 scripts/clean_references.py --slug sdsp06
  python3 scripts/check_references.py --slug sdsp06 --summary
  ```
- [ ] **1.2b** Refs sweep (8 passadas)
  ```
  python3 scripts/fix_validation_issues.py --slug sdsp06 --sweep-refs --dry-run
  python3 scripts/fix_validation_issues.py --slug sdsp06 --sweep-refs
  ```
- [ ] **1.2b+** Re-backfills: `python3 scripts/clean_references.py --slug sdsp06`
- [ ] **1.2c** Refs revisão LLM — TODOS os artigos vs fontes (ver §1.2c)
- [ ] **1.3** Keywords
  ```
  python3 scripts/fix_validation_issues.py --slug sdsp06 --clean-keywords --dry-run
  python3 scripts/fix_validation_issues.py --slug sdsp06 --clean-keywords
  ```
- [ ] **1.5** Loop validação: `python3 scripts/fix_validation_issues.py --slug sdsp06 --loop`
- [ ] **1.6** Cobertura de metadados + metadados do seminário (título, ISBN, editora)
- [ ] **1.7** Autores: verificar completude vs PDF (confrontar cada artigo com o PDF)
- [ ] **1.8** Dedup autores: `python3 dict/seed_authors.py && python3 scripts/dedup_authors.py`
- [ ] **1.9** ORCID: `python3 scripts/fetch_orcid.py --search --slug sdsp06` → `--review` → `--apply`
- [ ] **1.10** Revisão LLM final — TODOS os artigos, TODOS os campos vs plumber
  Para CADA artigo: ler o plumber INTEIRO, confrontar CADA campo (título, subtítulo,
  abstract, abstract_en, keywords, keywords_en, title_en, refs) com o texto do PDF.
  Corrigir na hora (R8). Registrar resultado de CADA artigo abaixo.
  **ATENÇÃO**: subtítulo começa com minúscula (exceto nome próprio/sigla/expressão consolidada).
  PDFs em ALL CAPS devem ser convertidos respeitando essa regra.
  Ver §1.10 do pipeline para procedimento detalhado.
  **1.10 — Resultado por artigo:**
  - [ ] sdsp06-001:
  - [ ] sdsp06-002:
  - [ ] sdsp06-003:
  - [ ] sdsp06-004:
  - [ ] sdsp06-005:
  - [ ] sdsp06-006:
  - [ ] sdsp06-007:
  - [ ] sdsp06-008:
  - [ ] sdsp06-009:
  - [ ] sdsp06-010:
  - [ ] sdsp06-011:
  - [ ] sdsp06-012:
  - [ ] sdsp06-013:
  - [ ] sdsp06-014:
  - [ ] sdsp06-015:
  - [ ] sdsp06-016:
  - [ ] sdsp06-017:
  - [ ] sdsp06-018:
  - [ ] sdsp06-019:
  - [ ] sdsp06-020:
  - [ ] sdsp06-021:
  - [ ] sdsp06-022:
  - [ ] sdsp06-023:
  - [ ] sdsp06-024:
  - [ ] sdsp06-025:
  - [ ] sdsp06-026:
  - [ ] sdsp06-027:
  - [ ] sdsp06-028:
  - [ ] sdsp06-029:
  - [ ] sdsp06-030:
  - [ ] sdsp06-031:
  - [ ] sdsp06-032:
  - [ ] sdsp06-033:
  - [ ] sdsp06-034:
  - [ ] sdsp06-035:
  - [ ] sdsp06-036:
  - [ ] sdsp06-037:

## Fase 2 — HTML de revisão + checkpoint

- [ ] **2.0** Validação final + HTML + commit
  ```
  python3 scripts/validate_metadata.py --slug sdsp06 --fix
  python3 scripts/gerar_revisao_html.py sdsp06
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdsp06-* && git commit -m "sdsp06 revisão automática (Fases 0-2)"
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
