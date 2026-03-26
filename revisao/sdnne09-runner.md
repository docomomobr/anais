# sdnne09 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-26 | Artigos: 50
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/50 | % |
|-------|-------|---|
| abstract | 50 | 100% |
| abstract_en | 38 | 76% |
| keywords | 49 | 98% |
| keywords_en | 37 | 74% |
| references | 50 | 100% |
| title_en | 0 | 0% |
| sections | 5 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [ ] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit
- [ ] **0.1** Levantar padrão de metadados (query cobertura → classificar campos)
- [ ] **0.2** Listar artigos fora do padrão (campos esperados mas ausentes)
- [ ] **0.3** Reinspecionar PDFs dos artigos fora do padrão (hierarquia: docx → plumber → pdftotext)
- [ ] **0.3b** Extrair fontes plumber
  ```
  python3 scripts/extrair_fontes_plumber.py --slug sdnne09 --profile-only
  python3 scripts/extrair_fontes_plumber.py --slug sdnne09
  ```
- [ ] **0.4** Seções/sessões — verificar nesta ordem:
  1. `fontes/` do seminário (HTML/XML de DVDs, sumários, programas)
  2. Folha de rosto dos artigos (cabeçalho do PDF indica eixo/sessão)
  3. Site original (campo `source` na tabela `seminars`)
  4. Busca na internet / Wayback Machine
  5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
- [ ] **0.5** Preencher lacunas no banco (salvar JSON antes, verificar idioma dos abstracts)
- [ ] **0.6** Extrair metadados EN: `python3 scripts/extrair_metadados_en.py --slug sdnne09`
- [ ] **0.7** Extrair metadados ES (artigos com locale=es: abstract, keywords do plumber)
- [ ] **0.8** Verificar abstracts + auto-fix
  ```
  python3 scripts/validate_metadata.py --slug sdnne09 --fix
  ```
  Depois: varredura manual (truncamento, lixo, cruzamento de idiomas)

## Fase 1 — Revisão automática

- [ ] **1.1a** Títulos PT: seed + normalizar + revisão LLM
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug sdnne09 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug sdnne09
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [ ] **1.1b** Títulos EN/ES:
  ```
  python3 scripts/normalizar_titulos_en.py --slug sdnne09 --dry-run
  python3 scripts/normalizar_titulos_en.py --slug sdnne09
  ``` `[SKIP: title_en = 0]`
- [ ] **1.1c** Revisão LLM títulos EN/ES (cada título vs PDF) `[SKIP: title_en = 0]`
- [ ] **1.2a** Refs limpeza base
  ```
  python3 scripts/clean_references.py --slug sdnne09 --dry-run
  python3 scripts/clean_references.py --slug sdnne09
  python3 scripts/check_references.py --slug sdnne09 --summary
  ```
- [ ] **1.2b** Refs sweep (8 passadas)
  ```
  python3 scripts/fix_validation_issues.py --slug sdnne09 --sweep-refs --dry-run
  python3 scripts/fix_validation_issues.py --slug sdnne09 --sweep-refs
  ```
- [ ] **1.2b+** Re-backfills: `python3 scripts/clean_references.py --slug sdnne09`
- [ ] **1.2c** Refs revisão LLM — TODOS os artigos vs fontes (ver §1.2c)
- [ ] **1.3** Keywords
  ```
  python3 scripts/fix_validation_issues.py --slug sdnne09 --clean-keywords --dry-run
  python3 scripts/fix_validation_issues.py --slug sdnne09 --clean-keywords
  ```
- [ ] **1.5** Loop validação: `python3 scripts/fix_validation_issues.py --slug sdnne09 --loop`
- [ ] **1.6** Cobertura de metadados + metadados do seminário (título, ISBN, editora)
- [ ] **1.7** Autores: verificar completude vs PDF (confrontar cada artigo com o PDF)
- [ ] **1.8** Dedup autores: `python3 dict/seed_authors.py && python3 scripts/dedup_authors.py`
- [ ] **1.9** ORCID: `python3 scripts/fetch_orcid.py --search --slug sdnne09` → `--review` → `--apply`
- [ ] **1.10** Revisão LLM final — TODOS os artigos, TODOS os campos vs plumber
  Para CADA artigo: ler o plumber INTEIRO, confrontar CADA campo (título, subtítulo,
  abstract, abstract_en, keywords, keywords_en, title_en, refs) com o texto do PDF.
  Corrigir na hora (R8). Registrar resultado de CADA artigo abaixo.
  **ATENÇÃO**: subtítulo começa com minúscula (exceto nome próprio/sigla/expressão consolidada).
  PDFs em ALL CAPS devem ser convertidos respeitando essa regra.
  Ver §1.10 do pipeline para procedimento detalhado.
  **1.10 — Resultado por artigo:**
  - [ ] sdnne09-001:
  - [ ] sdnne09-002:
  - [ ] sdnne09-003:
  - [ ] sdnne09-004:
  - [ ] sdnne09-005:
  - [ ] sdnne09-006:
  - [ ] sdnne09-007:
  - [ ] sdnne09-008:
  - [ ] sdnne09-009:
  - [ ] sdnne09-010:
  - [ ] sdnne09-011:
  - [ ] sdnne09-012:
  - [ ] sdnne09-013:
  - [ ] sdnne09-014:
  - [ ] sdnne09-015:
  - [ ] sdnne09-016:
  - [ ] sdnne09-017:
  - [ ] sdnne09-018:
  - [ ] sdnne09-019:
  - [ ] sdnne09-020:
  - [ ] sdnne09-021:
  - [ ] sdnne09-022:
  - [ ] sdnne09-023:
  - [ ] sdnne09-024:
  - [ ] sdnne09-025:
  - [ ] sdnne09-026:
  - [ ] sdnne09-027:
  - [ ] sdnne09-028:
  - [ ] sdnne09-029:
  - [ ] sdnne09-030:
  - [ ] sdnne09-031:
  - [ ] sdnne09-032:
  - [ ] sdnne09-033:
  - [ ] sdnne09-034:
  - [ ] sdnne09-035:
  - [ ] sdnne09-036:
  - [ ] sdnne09-037:
  - [ ] sdnne09-038:
  - [ ] sdnne09-039:
  - [ ] sdnne09-040:
  - [ ] sdnne09-041:
  - [ ] sdnne09-042:
  - [ ] sdnne09-043:
  - [ ] sdnne09-044:
  - [ ] sdnne09-045:
  - [ ] sdnne09-046:
  - [ ] sdnne09-047:
  - [ ] sdnne09-048:
  - [ ] sdnne09-049:
  - [ ] sdnne09-050:

## Fase 2 — HTML de revisão + checkpoint

- [ ] **2.0** Validação final + HTML + commit
  ```
  python3 scripts/validate_metadata.py --slug sdnne09 --fix
  python3 scripts/gerar_revisao_html.py sdnne09
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdnne09-* && git commit -m "sdnne09 revisão automática (Fases 0-2)"
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
