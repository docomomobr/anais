# idc06 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-28 | Artigos: 54
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura

| Campo | Inicial | Final | % |
|-------|---------|-------|---|
| title | 54 | 54 | 100% |
| subtitle | 0 | 25 | 46% |
| keywords | 28 | 35 | 65% |
| references | 15 | 24 (339 refs) | 44% |
| sections | 13 | 13 | — |
| ORCIDs | 11 | 18 | — |
| countries | 1 (BR) | 19 | — |

Validação: 0 problemas. Refs: 0% issues.

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint
- [x] **0.1** Cobertura: 54 artigos, locale=en
- [x] **0.2** 44 artigos com lacunas mapeados
- [x] **0.3** Reinspecção via imagens (pdftoppm + multimodal)
- [x] **0.3b** SKIP — plumber já existia da sessão anterior
- [x] **0.4** 13 seções verificadas
- [x] **0.5** Lacunas preenchidas: kw 28→35, refs 15→24
- [x] **0.6** SKIP — locale=en, campos primários já em inglês
- [x] **0.7** SKIP — N/A
- [x] **0.8** validate --fix: 5 body-text corrigidos

## Fase 1 — Revisão automática

- [x] **1.1a** SKIP — locale=en (normalizar_maiusculas.py é para PT)
- [x] **1.1b** SKIP — título primário já é EN
- [x] **1.1c** Revisão LLM títulos: 4 agentes paralelos. Correções: 006/007 trocados, 050 Revisiting, subtítulos.
- [x] **1.2a** clean_references.py
- [x] **1.2b** sweep-refs: 752→528
- [x] **1.2b+** Re-backfills
- [x] **1.2c** Refs revisão LLM: 4 agentes. 752 garbled → 339 refs limpas, 0% issues. Correções: 014 duplicata, 017 artigo errado, 035 duplicata, 039/025/012 garbled.
- [x] **1.3** Keywords: limpeza manual (bio text, OCR artifacts). Lógica spillover descoberta.
- [x] **1.5** Loop validação: 0 issues
- [x] **1.6** Metadados seminário: location=Brasília DF, section_label=session
- [x] **1.7** Autores: nomes verificados via imagem. 42 países corrigidos (19 países).
- [x] **1.8** Dedup: 0 merges no idc06
- [x] **1.9** ORCID: 18 encontrados (58 autores verificados)
- [x] **1.10** Revisão LLM final: títulos, subtítulos, autores, refs verificados contra imagens PDF.

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** revisao-idc06.html gerado (54 artigos, 13 seções). Commits realizados.

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [ ] **3.1** Diagnóstico unificado
- [ ] **3.2** Atualizar dict.db
- [ ] **3.3** Atualizar scripts
- [ ] **3.4** Atualizar pipeline
- [ ] **3.5** Verificar: dry-run sem regressão
- [ ] **3.6** Registrar aprendizado
- [ ] **3.7** Revisão de engenharia
- [ ] **3.8** Checklist de conclusão
- [ ] **3.9** Fechar: dump + commit + push + CLAUDE.md

## Notas

- OCR 2 colunas: descoberta de spillover (keywords na p1 → artigo anterior)
- Lógica NOTES: sem BIBLIOGRAPHY → manter NOTES bibliográficas; com BIBLIOGRAPHY → só BIBLIOGRAPHY
- ~20 artigos genuinamente sem kw/refs (session pages, abstracts 1pg, citações inline)
- Notas detalhadas em revisao/idc06-notas.md
