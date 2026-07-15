# sdnne10 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-26 | Artigos: 85
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/85 | % |
|-------|-------|---|
| abstract | 85 | 100% |
| abstract_en | 85 | 100% |
| keywords | 85 | 100% |
| keywords_en | 85 | 100% |
| references | 82 | 96% |
| title_en | 85 | 100% |
| sections | 4 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [ ] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit
- [ ] **0.1** Levantar padrão de metadados (query cobertura → classificar campos)
- [ ] **0.2** Listar artigos fora do padrão (campos esperados mas ausentes)
- [ ] **0.3** Reinspecionar PDFs dos artigos fora do padrão (hierarquia: docx → plumber → pdftotext)
- [ ] **0.3b** Extrair fontes plumber
  ```
  python3 scripts/extrair_fontes_plumber.py --slug sdnne10 --profile-only
  python3 scripts/extrair_fontes_plumber.py --slug sdnne10
  ```
- [ ] **0.4** Seções/sessões — verificar nesta ordem:
  1. `fontes/` do seminário (HTML/XML de DVDs, sumários, programas)
  2. Folha de rosto dos artigos (cabeçalho do PDF indica eixo/sessão)
  3. Site original (campo `source` na tabela `seminars`)
  4. Busca na internet / Wayback Machine
  5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
- [ ] **0.5** Preencher lacunas no banco (salvar JSON antes, verificar idioma dos abstracts)
- [ ] **0.6** Extrair metadados EN: `python3 scripts/extrair_metadados_en.py --slug sdnne10`
- [ ] **0.7** Extrair metadados ES (artigos com locale=es: abstract, keywords do plumber)
- [ ] **0.8** Verificar abstracts + auto-fix
  ```
  python3 scripts/validate_metadata.py --slug sdnne10 --fix
  ```
  Depois: varredura manual (truncamento, lixo, cruzamento de idiomas)

## Fase 1 — Revisão automática

- [ ] **1.1a** Títulos PT: seed + normalizar + revisão LLM
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug sdnne10 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug sdnne10
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [ ] **1.1b** Títulos EN/ES:
  ```
  python3 scripts/normalizar_titulos_en.py --slug sdnne10 --dry-run
  python3 scripts/normalizar_titulos_en.py --slug sdnne10
  ```
- [ ] **1.1c** Revisão LLM títulos EN/ES (cada título vs PDF)
- [ ] **1.2a** Refs limpeza base
  ```
  python3 scripts/clean_references.py --slug sdnne10 --dry-run
  python3 scripts/clean_references.py --slug sdnne10
  python3 scripts/check_references.py --slug sdnne10 --summary
  ```
- [ ] **1.2b** Refs sweep (8 passadas)
  ```
  python3 scripts/fix_validation_issues.py --slug sdnne10 --sweep-refs --dry-run
  python3 scripts/fix_validation_issues.py --slug sdnne10 --sweep-refs
  ```
- [ ] **1.2b+** Re-backfills: `python3 scripts/clean_references.py --slug sdnne10`
- [ ] **1.2c** Refs revisão LLM — TODOS os artigos vs fontes (ver §1.2c)
- [ ] **1.3** Keywords
  ```
  python3 scripts/fix_validation_issues.py --slug sdnne10 --clean-keywords --dry-run
  python3 scripts/fix_validation_issues.py --slug sdnne10 --clean-keywords
  ```
- [ ] **1.5** Loop validação: `python3 scripts/fix_validation_issues.py --slug sdnne10 --loop`
- [ ] **1.6** Cobertura de metadados + metadados do seminário (título, ISBN, editora)
- [ ] **1.7** Autores: verificar completude vs PDF (confrontar cada artigo com o PDF)
- [ ] **1.8** Dedup autores: `python3 dict/seed_authors.py && python3 scripts/dedup_authors.py`
- [ ] **1.9** ORCID: `python3 scripts/fetch_orcid.py --search --slug sdnne10` → `--review` → `--apply`
- [ ] **1.10** Revisão LLM final — TODOS os artigos, TODOS os campos vs plumber
  Para CADA artigo: ler o plumber INTEIRO, confrontar CADA campo (título, subtítulo,
  abstract, abstract_en, keywords, keywords_en, title_en, refs) com o texto do PDF.
  Corrigir na hora (R8). Registrar resultado de CADA artigo abaixo.
  **ATENÇÃO**: subtítulo começa com minúscula (exceto nome próprio/sigla/expressão consolidada).
  PDFs em ALL CAPS devem ser convertidos respeitando essa regra.
  Ver §1.10 do pipeline para procedimento detalhado.
  **1.10 — Resultado por artigo:**
  - [ ] sdnne10-001:
  - [ ] sdnne10-002:
  - [ ] sdnne10-003:
  - [ ] sdnne10-004:
  - [ ] sdnne10-005:
  - [ ] sdnne10-006:
  - [ ] sdnne10-007:
  - [ ] sdnne10-008:
  - [ ] sdnne10-009:
  - [ ] sdnne10-010:
  - [ ] sdnne10-011:
  - [ ] sdnne10-012:
  - [ ] sdnne10-013:
  - [ ] sdnne10-014:
  - [ ] sdnne10-015:
  - [ ] sdnne10-016:
  - [ ] sdnne10-017:
  - [ ] sdnne10-018:
  - [ ] sdnne10-019:
  - [ ] sdnne10-020:
  - [ ] sdnne10-021:
  - [ ] sdnne10-022:
  - [ ] sdnne10-023:
  - [ ] sdnne10-024:
  - [ ] sdnne10-025:
  - [ ] sdnne10-026:
  - [ ] sdnne10-027:
  - [ ] sdnne10-028:
  - [ ] sdnne10-029:
  - [ ] sdnne10-030:
  - [ ] sdnne10-031:
  - [ ] sdnne10-032:
  - [ ] sdnne10-033:
  - [ ] sdnne10-034:
  - [ ] sdnne10-035:
  - [ ] sdnne10-036:
  - [ ] sdnne10-037:
  - [ ] sdnne10-038:
  - [ ] sdnne10-039:
  - [ ] sdnne10-040:
  - [ ] sdnne10-041:
  - [ ] sdnne10-042:
  - [ ] sdnne10-043:
  - [ ] sdnne10-044:
  - [ ] sdnne10-045:
  - [ ] sdnne10-046:
  - [ ] sdnne10-047:
  - [ ] sdnne10-048:
  - [ ] sdnne10-049:
  - [ ] sdnne10-050:
  - [ ] sdnne10-051:
  - [ ] sdnne10-052:
  - [ ] sdnne10-053:
  - [ ] sdnne10-054:
  - [ ] sdnne10-055:
  - [ ] sdnne10-056:
  - [ ] sdnne10-057:
  - [ ] sdnne10-058:
  - [ ] sdnne10-059:
  - [ ] sdnne10-060:
  - [ ] sdnne10-061:
  - [ ] sdnne10-062:
  - [ ] sdnne10-063:
  - [ ] sdnne10-064:
  - [ ] sdnne10-065:
  - [ ] sdnne10-066:
  - [ ] sdnne10-067:
  - [ ] sdnne10-068:
  - [ ] sdnne10-069:
  - [ ] sdnne10-070:
  - [ ] sdnne10-071:
  - [ ] sdnne10-072:
  - [ ] sdnne10-073:
  - [ ] sdnne10-074:
  - [ ] sdnne10-075:
  - [ ] sdnne10-076:
  - [ ] sdnne10-077:
  - [ ] sdnne10-078:
  - [ ] sdnne10-079:
  - [ ] sdnne10-080:
  - [ ] sdnne10-081:
  - [ ] sdnne10-082:
  - [ ] sdnne10-083:
  - [ ] sdnne10-084:
  - [ ] sdnne10-085:

## Fase 2 — HTML de revisão + checkpoint

- [ ] **2.0** Validação final + HTML + commit
  ```
  python3 scripts/validate_metadata.py --slug sdnne10 --fix
  python3 scripts/gerar_revisao_html.py sdnne10
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdnne10-* && git commit -m "sdnne10 revisão automática (Fases 0-2)"
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
