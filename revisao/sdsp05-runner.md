# sdsp05 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-27 | Artigos: 68
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/68 | % |
|-------|-------|---|
| abstract | 68 | 100% |
| abstract_en | 60 | 88% |
| keywords | 68 | 100% |
| keywords_en | 57 | 84% |
| references | 63 | 93% |
| title_en | 0 | 0% |
| sections | 3 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [ ] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit
- [ ] **0.1** Levantar padrão de metadados (query cobertura → classificar campos)
- [ ] **0.2** Listar artigos fora do padrão (campos esperados mas ausentes)
- [ ] **0.3** Reinspecionar PDFs dos artigos fora do padrão (hierarquia: docx → plumber → pdftotext)
- [ ] **0.3b** Extrair fontes plumber
  ```
  python3 scripts/extrair_fontes_plumber.py --slug sdsp05 --profile-only
  python3 scripts/extrair_fontes_plumber.py --slug sdsp05
  ```
- [ ] **0.4** Seções/sessões — verificar nesta ordem:
  1. `fontes/` do seminário (HTML/XML de DVDs, sumários, programas)
  2. Folha de rosto dos artigos (cabeçalho do PDF indica eixo/sessão)
  3. Site original (campo `source` na tabela `seminars`)
  4. Busca na internet / Wayback Machine
  5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
- [ ] **0.5** Preencher lacunas no banco (salvar JSON antes, verificar idioma dos abstracts)
- [ ] **0.6** Extrair metadados EN: `python3 scripts/extrair_metadados_en.py --slug sdsp05`
- [ ] **0.7** Extrair metadados ES (artigos com locale=es: abstract, keywords do plumber)
- [ ] **0.8** Verificar abstracts + auto-fix
  ```
  python3 scripts/validate_metadata.py --slug sdsp05 --fix
  ```
  Depois: varredura manual (truncamento, lixo, cruzamento de idiomas)

## Fase 1 — Revisão automática

- [ ] **1.1a** Títulos PT: seed + normalizar + revisão LLM
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug sdsp05 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug sdsp05
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [ ] **1.1b** Títulos EN/ES:
  ```
  python3 scripts/normalizar_titulos_en.py --slug sdsp05 --dry-run
  python3 scripts/normalizar_titulos_en.py --slug sdsp05
  ``` `[SKIP: title_en = 0]`
- [ ] **1.1c** Revisão LLM títulos EN/ES (cada título vs PDF) `[SKIP: title_en = 0]`
- [ ] **1.2a** Refs limpeza base
  ```
  python3 scripts/clean_references.py --slug sdsp05 --dry-run
  python3 scripts/clean_references.py --slug sdsp05
  python3 scripts/check_references.py --slug sdsp05 --summary
  ```
- [ ] **1.2b** Refs sweep (8 passadas)
  ```
  python3 scripts/fix_validation_issues.py --slug sdsp05 --sweep-refs --dry-run
  python3 scripts/fix_validation_issues.py --slug sdsp05 --sweep-refs
  ```
- [ ] **1.2b+** Re-backfills: `python3 scripts/clean_references.py --slug sdsp05`
- [ ] **1.2c** Refs revisão LLM — TODOS os artigos vs fontes (ver §1.2c)
- [ ] **1.3** Keywords
  ```
  python3 scripts/fix_validation_issues.py --slug sdsp05 --clean-keywords --dry-run
  python3 scripts/fix_validation_issues.py --slug sdsp05 --clean-keywords
  ```
- [ ] **1.5** Loop validação: `python3 scripts/fix_validation_issues.py --slug sdsp05 --loop`
- [ ] **1.6** Cobertura de metadados + metadados do seminário (título, ISBN, editora)
- [ ] **1.7** Autores: verificar completude vs PDF (confrontar cada artigo com o PDF)
- [ ] **1.8** Dedup autores: `python3 dict/seed_authors.py && python3 scripts/dedup_authors.py`
- [ ] **1.9** ORCID: `python3 scripts/fetch_orcid.py --search --slug sdsp05` → `--review` → `--apply`
- [ ] **1.10** Revisão LLM final — TODOS os artigos, TODOS os campos vs plumber
  Para CADA artigo: ler o plumber INTEIRO, confrontar CADA campo (título, subtítulo,
  abstract, abstract_en, keywords, keywords_en, title_en, refs) com o texto do PDF.
  Corrigir na hora (R8). Registrar resultado de CADA artigo abaixo.
  **ATENÇÃO**: subtítulo começa com minúscula (exceto nome próprio/sigla/expressão consolidada).
  PDFs em ALL CAPS devem ser convertidos respeitando essa regra.
  Ver §1.10 do pipeline para procedimento detalhado.
  **1.10 — Resultado por artigo:**
  - [ ] sdsp05-001:
  - [ ] sdsp05-002:
  - [ ] sdsp05-003:
  - [ ] sdsp05-004:
  - [ ] sdsp05-005:
  - [ ] sdsp05-006:
  - [ ] sdsp05-007:
  - [ ] sdsp05-008:
  - [ ] sdsp05-009:
  - [ ] sdsp05-010:
  - [ ] sdsp05-011:
  - [ ] sdsp05-012:
  - [ ] sdsp05-013:
  - [ ] sdsp05-014:
  - [ ] sdsp05-015:
  - [ ] sdsp05-016:
  - [ ] sdsp05-017:
  - [ ] sdsp05-018:
  - [ ] sdsp05-019:
  - [ ] sdsp05-020:
  - [ ] sdsp05-021:
  - [ ] sdsp05-022:
  - [ ] sdsp05-023:
  - [ ] sdsp05-024:
  - [ ] sdsp05-025:
  - [ ] sdsp05-026:
  - [ ] sdsp05-027:
  - [ ] sdsp05-028:
  - [ ] sdsp05-029:
  - [ ] sdsp05-030:
  - [ ] sdsp05-031:
  - [ ] sdsp05-032:
  - [ ] sdsp05-033:
  - [ ] sdsp05-034:
  - [ ] sdsp05-035:
  - [ ] sdsp05-036:
  - [ ] sdsp05-037:
  - [ ] sdsp05-038:
  - [ ] sdsp05-039:
  - [ ] sdsp05-040:
  - [ ] sdsp05-041:
  - [ ] sdsp05-042:
  - [ ] sdsp05-043:
  - [ ] sdsp05-044:
  - [ ] sdsp05-045:
  - [ ] sdsp05-046:
  - [ ] sdsp05-047:
  - [ ] sdsp05-048:
  - [ ] sdsp05-049:
  - [ ] sdsp05-050:
  - [ ] sdsp05-051:
  - [ ] sdsp05-052:
  - [ ] sdsp05-053:
  - [ ] sdsp05-054:
  - [ ] sdsp05-055:
  - [ ] sdsp05-056:
  - [ ] sdsp05-057:
  - [ ] sdsp05-058:
  - [ ] sdsp05-059:
  - [ ] sdsp05-060:
  - [ ] sdsp05-061:
  - [ ] sdsp05-062:
  - [ ] sdsp05-063:
  - [ ] sdsp05-064:
  - [ ] sdsp05-065:
  - [ ] sdsp05-066:
  - [ ] sdsp05-067:
  - [ ] sdsp05-068:

## Fase 2 — HTML de revisão + checkpoint

- [ ] **2.0** Validação final + HTML + commit
  ```
  python3 scripts/validate_metadata.py --slug sdsp05 --fix
  python3 scripts/gerar_revisao_html.py sdsp05
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdsp05-* && git commit -m "sdsp05 revisão automática (Fases 0-2)"
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
