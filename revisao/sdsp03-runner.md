# sdsp03 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-26 | Artigos: 74
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/74 | % |
|-------|-------|---|
| abstract | 74 | 100% |
| abstract_en | 73 | 99% |
| keywords | 73 | 99% |
| keywords_en | 0 | 0% |
| references | 62 | 84% |
| title_en | 0 | 0% |
| sections | 10 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [ ] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit
- [ ] **0.1** Levantar padrão de metadados (query cobertura → classificar campos)
- [ ] **0.2** Listar artigos fora do padrão (campos esperados mas ausentes)
- [ ] **0.3** Reinspecionar PDFs dos artigos fora do padrão (hierarquia: docx → plumber → pdftotext)
- [ ] **0.3b** Extrair fontes plumber
  ```
  python3 scripts/extrair_fontes_plumber.py --slug sdsp03 --profile-only
  python3 scripts/extrair_fontes_plumber.py --slug sdsp03
  ```
- [ ] **0.4** Seções/sessões — verificar nesta ordem:
  1. `fontes/` do seminário (HTML/XML de DVDs, sumários, programas)
  2. Folha de rosto dos artigos (cabeçalho do PDF indica eixo/sessão)
  3. Site original (campo `source` na tabela `seminars`)
  4. Busca na internet / Wayback Machine
  5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
- [ ] **0.5** Preencher lacunas no banco (salvar JSON antes, verificar idioma dos abstracts)
- [ ] **0.6** Extrair metadados EN: `python3 scripts/extrair_metadados_en.py --slug sdsp03`
- [ ] **0.7** Extrair metadados ES (artigos com locale=es: abstract, keywords do plumber)
- [ ] **0.8** Verificar abstracts + auto-fix
  ```
  python3 scripts/validate_metadata.py --slug sdsp03 --fix
  ```
  Depois: varredura manual (truncamento, lixo, cruzamento de idiomas)

## Fase 1 — Revisão automática

- [ ] **1.1a** Títulos PT: seed + normalizar + revisão LLM
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug sdsp03 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug sdsp03
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [ ] **1.1b** Títulos EN/ES:
  ```
  python3 scripts/normalizar_titulos_en.py --slug sdsp03 --dry-run
  python3 scripts/normalizar_titulos_en.py --slug sdsp03
  ``` `[SKIP: title_en = 0]`
- [ ] **1.1c** Revisão LLM títulos EN/ES (cada título vs PDF) `[SKIP: title_en = 0]`
- [ ] **1.2a** Refs limpeza base
  ```
  python3 scripts/clean_references.py --slug sdsp03 --dry-run
  python3 scripts/clean_references.py --slug sdsp03
  python3 scripts/check_references.py --slug sdsp03 --summary
  ```
- [ ] **1.2b** Refs sweep (8 passadas)
  ```
  python3 scripts/fix_validation_issues.py --slug sdsp03 --sweep-refs --dry-run
  python3 scripts/fix_validation_issues.py --slug sdsp03 --sweep-refs
  ```
- [ ] **1.2b+** Re-backfills: `python3 scripts/clean_references.py --slug sdsp03`
- [ ] **1.2c** Refs revisão LLM — TODOS os artigos vs fontes (ver §1.2c)
- [ ] **1.3** Keywords
  ```
  python3 scripts/fix_validation_issues.py --slug sdsp03 --clean-keywords --dry-run
  python3 scripts/fix_validation_issues.py --slug sdsp03 --clean-keywords
  ```
- [ ] **1.5** Loop validação: `python3 scripts/fix_validation_issues.py --slug sdsp03 --loop`
- [ ] **1.6** Cobertura de metadados + metadados do seminário (título, ISBN, editora)
- [ ] **1.7** Autores: verificar completude vs PDF (confrontar cada artigo com o PDF)
- [ ] **1.8** Dedup autores: `python3 dict/seed_authors.py && python3 scripts/dedup_authors.py`
- [ ] **1.9** ORCID: `python3 scripts/fetch_orcid.py --search --slug sdsp03` → `--review` → `--apply`
- [ ] **1.10** Revisão LLM final — TODOS os artigos, TODOS os campos vs plumber
  Para CADA artigo: ler o plumber INTEIRO, confrontar CADA campo (título, subtítulo,
  abstract, abstract_en, keywords, keywords_en, title_en, refs) com o texto do PDF.
  Corrigir na hora (R8). Registrar resultado de CADA artigo abaixo.
  **ATENÇÃO**: subtítulo começa com minúscula (exceto nome próprio/sigla/expressão consolidada).
  PDFs em ALL CAPS devem ser convertidos respeitando essa regra.
  Ver §1.10 do pipeline para procedimento detalhado.
  **1.10 — Resultado por artigo:**
  - [ ] sdsp03-001:
  - [ ] sdsp03-002:
  - [ ] sdsp03-003:
  - [ ] sdsp03-004:
  - [ ] sdsp03-005:
  - [ ] sdsp03-006:
  - [ ] sdsp03-007:
  - [ ] sdsp03-008:
  - [ ] sdsp03-009:
  - [ ] sdsp03-010:
  - [ ] sdsp03-011:
  - [ ] sdsp03-012:
  - [ ] sdsp03-013:
  - [ ] sdsp03-014:
  - [ ] sdsp03-015:
  - [ ] sdsp03-016:
  - [ ] sdsp03-017:
  - [ ] sdsp03-018:
  - [ ] sdsp03-019:
  - [ ] sdsp03-020:
  - [ ] sdsp03-021:
  - [ ] sdsp03-022:
  - [ ] sdsp03-023:
  - [ ] sdsp03-024:
  - [ ] sdsp03-025:
  - [ ] sdsp03-026:
  - [ ] sdsp03-027:
  - [ ] sdsp03-028:
  - [ ] sdsp03-029:
  - [ ] sdsp03-030:
  - [ ] sdsp03-031:
  - [ ] sdsp03-032:
  - [ ] sdsp03-033:
  - [ ] sdsp03-034:
  - [ ] sdsp03-035:
  - [ ] sdsp03-036:
  - [ ] sdsp03-037:
  - [ ] sdsp03-038:
  - [ ] sdsp03-039:
  - [ ] sdsp03-040:
  - [ ] sdsp03-041:
  - [ ] sdsp03-042:
  - [ ] sdsp03-043:
  - [ ] sdsp03-044:
  - [ ] sdsp03-045:
  - [ ] sdsp03-046:
  - [ ] sdsp03-047:
  - [ ] sdsp03-048:
  - [ ] sdsp03-049:
  - [ ] sdsp03-050:
  - [ ] sdsp03-051:
  - [ ] sdsp03-052:
  - [ ] sdsp03-053:
  - [ ] sdsp03-054:
  - [ ] sdsp03-055:
  - [ ] sdsp03-056:
  - [ ] sdsp03-057:
  - [ ] sdsp03-058:
  - [ ] sdsp03-059:
  - [ ] sdsp03-060:
  - [ ] sdsp03-061:
  - [ ] sdsp03-062:
  - [ ] sdsp03-063:
  - [ ] sdsp03-064:
  - [ ] sdsp03-065:
  - [ ] sdsp03-066:
  - [ ] sdsp03-067:
  - [ ] sdsp03-068:
  - [ ] sdsp03-069:
  - [ ] sdsp03-070:
  - [ ] sdsp03-071:
  - [ ] sdsp03-072:
  - [ ] sdsp03-073:
  - [ ] sdsp03-074:

## Fase 2 — HTML de revisão + checkpoint

- [ ] **2.0** Validação final + HTML + commit
  ```
  python3 scripts/validate_metadata.py --slug sdsp03 --fix
  python3 scripts/gerar_revisao_html.py sdsp03
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdsp03-* && git commit -m "sdsp03 revisão automática (Fases 0-2)"
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
