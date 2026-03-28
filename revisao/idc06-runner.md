# idc06 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-28 | Artigos: 54
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/54 | % |
|-------|-------|---|
| abstract | 0 | 0% |
| abstract_en | 0 | 0% |
| keywords | 28 | 52% |
| keywords_en | 0 | 0% |
| references | 15 | 28% |
| title_en | 0 | 0% |
| sections | 13 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [ ] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit
- [ ] **0.1** Levantar padrão de metadados (query cobertura → classificar campos)
- [ ] **0.2** Listar artigos fora do padrão (campos esperados mas ausentes)
- [ ] **0.3** Reinspecionar PDFs dos artigos fora do padrão (hierarquia: docx → plumber → pdftotext)
- [ ] **0.3b** Extrair fontes plumber
  ```
  python3 scripts/extrair_fontes_plumber.py --slug idc06 --profile-only
  python3 scripts/extrair_fontes_plumber.py --slug idc06
  ```
- [ ] **0.4** Seções/sessões — verificar nesta ordem:
  1. `fontes/` do seminário (HTML/XML de DVDs, sumários, programas)
  2. Folha de rosto dos artigos (cabeçalho do PDF indica eixo/sessão)
  3. Site original (campo `source` na tabela `seminars`)
  4. Busca na internet / Wayback Machine
  5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
- [ ] **0.5** Preencher lacunas no banco (salvar JSON antes, verificar idioma dos abstracts)
- [ ] **0.6** Extrair metadados EN `[SKIP: abstract_en < 30%]`: `python3 scripts/extrair_metadados_en.py --slug idc06`
- [ ] **0.7** Extrair metadados ES (title_es, subtitle_es, abstract_es, keywords_es do plumber — independe do locale)
- [ ] **0.8** Verificar abstracts + auto-fix
  ```
  python3 scripts/validate_metadata.py --slug idc06 --fix
  ```
  Depois: varredura manual (truncamento, lixo, cruzamento de idiomas)

## Fase 1 — Revisão automática

- [ ] **1.1a** Títulos PT: seed + normalizar + revisão LLM
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug idc06 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug idc06
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [ ] **1.1b** Títulos EN/ES:
  ```
  python3 scripts/normalizar_titulos_en.py --slug idc06 --dry-run
  python3 scripts/normalizar_titulos_en.py --slug idc06
  ``` `[SKIP: title_en = 0]`
- [ ] **1.1c** Revisão LLM títulos EN/ES (cada título vs PDF) `[SKIP: title_en = 0]`
- [ ] **1.2a** Refs limpeza base
  ```
  python3 scripts/clean_references.py --slug idc06 --dry-run
  python3 scripts/clean_references.py --slug idc06
  python3 scripts/check_references.py --slug idc06 --summary
  ```
- [ ] **1.2b** Refs sweep (8 passadas)
  ```
  python3 scripts/fix_validation_issues.py --slug idc06 --sweep-refs --dry-run
  python3 scripts/fix_validation_issues.py --slug idc06 --sweep-refs
  ```
- [ ] **1.2b+** Re-backfills: `python3 scripts/clean_references.py --slug idc06`
- [ ] **1.2c** Refs revisão LLM — TODOS os artigos vs fontes (ver §1.2c)
- [ ] **1.3** Keywords
  ```
  python3 scripts/fix_validation_issues.py --slug idc06 --clean-keywords --dry-run
  python3 scripts/fix_validation_issues.py --slug idc06 --clean-keywords
  ```
- [ ] **1.5** Loop validação: `python3 scripts/fix_validation_issues.py --slug idc06 --loop`
- [ ] **1.6** Cobertura de metadados + metadados do seminário (título, ISBN, editora)
- [ ] **1.7** Autores: verificar completude vs PDF (confrontar cada artigo com o PDF)
- [ ] **1.8** Dedup autores: `python3 dict/seed_authors.py && python3 scripts/dedup_authors.py`
- [ ] **1.9** ORCID: `python3 scripts/fetch_orcid.py --search --slug idc06` → `--review` → `--apply`
- [ ] **1.10** Revisão LLM final — TODOS os artigos, TODOS os campos vs plumber
  Para CADA artigo: ler o plumber INTEIRO, confrontar CADA campo (título, subtítulo,
  abstract, abstract_en, keywords, keywords_en, title_en, refs) com o texto do PDF.
  Corrigir na hora (R8). Registrar resultado de CADA artigo abaixo.
  **ATENÇÃO**: subtítulo começa com minúscula (exceto nome próprio/sigla/expressão consolidada).
  PDFs em ALL CAPS devem ser convertidos respeitando essa regra.
  Ver §1.10 do pipeline para procedimento detalhado.
  **1.10 — Resultado por artigo:**
  - [ ] idc06-001:
  - [ ] idc06-002:
  - [ ] idc06-003:
  - [ ] idc06-004:
  - [ ] idc06-005:
  - [ ] idc06-006:
  - [ ] idc06-007:
  - [ ] idc06-008:
  - [ ] idc06-009:
  - [ ] idc06-010:
  - [ ] idc06-011:
  - [ ] idc06-012:
  - [ ] idc06-013:
  - [ ] idc06-014:
  - [ ] idc06-015:
  - [ ] idc06-016:
  - [ ] idc06-017:
  - [ ] idc06-018:
  - [ ] idc06-019:
  - [ ] idc06-020:
  - [ ] idc06-021:
  - [ ] idc06-022:
  - [ ] idc06-023:
  - [ ] idc06-024:
  - [ ] idc06-025:
  - [ ] idc06-026:
  - [ ] idc06-027:
  - [ ] idc06-028:
  - [ ] idc06-029:
  - [ ] idc06-030:
  - [ ] idc06-031:
  - [ ] idc06-032:
  - [ ] idc06-033:
  - [ ] idc06-034:
  - [ ] idc06-035:
  - [ ] idc06-036:
  - [ ] idc06-037:
  - [ ] idc06-038:
  - [ ] idc06-039:
  - [ ] idc06-040:
  - [ ] idc06-041:
  - [ ] idc06-042:
  - [ ] idc06-043:
  - [ ] idc06-044:
  - [ ] idc06-045:
  - [ ] idc06-046:
  - [ ] idc06-047:
  - [ ] idc06-048:
  - [ ] idc06-049:
  - [ ] idc06-050:
  - [ ] idc06-051:
  - [ ] idc06-052:
  - [ ] idc06-053:
  - [ ] idc06-054:

## Fase 2 — HTML de revisão + checkpoint

- [ ] **2.0** Validação final + HTML + commit
  ```
  python3 scripts/validate_metadata.py --slug idc06 --fix
  python3 scripts/gerar_revisao_html.py idc06
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/idc06-* && git commit -m "idc06 revisão automática (Fases 0-2)"
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
