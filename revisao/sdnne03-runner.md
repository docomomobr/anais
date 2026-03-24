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

- [x] **0.0** Checkpoint: 4c39194 (anais.sql já atualizado)
- [x] **0.1** Cobertura: abs 100%, abs_en 71%, kw 93%, kw_en 78%, refs 100% (677 refs)
- [x] **0.2** Fora do padrão: 12 sem abs_en; 013/032/034 sem kw; 9 sem kw_en
- [x] **0.3** PDFs reinspecionados via plumber (41 arts, 6261 blocos). Sem doc/docx
- [x] **0.3b** Fontes plumber extraídas (41 arts, 6261 blocos)
- [x] **0.4** Seções: 4 genéricas (Seção 1-4, hide_title=1). Sem nomes temáticos (rodapé só tem subtítulo do seminário)
- [x] **0.5** Lacunas: 013/032/034 sem kw genuíno (PDF não tem). 007/021/031/032 sem abs_en genuíno
- [x] **0.6** Extrair metadados EN: 8 abstract_en, 3 kw_en extraídos do plumber
- [x] **0.7** ES: 0 artigos com locale=es
- [x] **0.8** Validate --fix: 9 auto-fixes (8 A25 kw no abstract, 1 A27 PT no abstract_en). 25 issues restantes

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 10 alterações normalizer, 7 reversões, 22 correções LLM vs PDF (4 subtítulos adicionados: 013/019/020/027)
- [x] **1.1b** Títulos EN/ES [SKIP: title_en = 0]
- [x] **1.1c** Revisão LLM títulos EN/ES [SKIP: title_en = 0]
- [x] **1.2a** Refs limpeza base: 0 alterações (677 refs)
- [x] **1.2b** Refs sweep: 16 artigos (7 lixo, 17 joins, 11 splits, 3 non-refs, 4 endnotes). 677→657 refs
- [x] **1.2b+** Re-backfills: 0 backfills
- [x] **1.2c** Refs revisão LLM: ~45 correções em 24 artigos (splits, joins, missing, truncated, non-refs). 657→710 refs
- [x] **1.3** Keywords: 1 split (038 kw_en "." separator)
- [x] **1.5** Loop validação: 3 fixes (019/021 abs_en extraídos, 033 abs_en completado). 16 issues restantes
- [x] **1.6** Cobertura OK. Seminário: Núcleo Docomomo NNE / UFPB, 2010
- [x] **1.7** Autores: 13 artigos corrigidos (ordens, familynames, givennames), 61 afiliações inseridas
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: +2 novos (Amélia Reynaldo, Mércia Rocha). Total: 45/79 (56%)
- [x] **1.10** Revisão LLM final:
  - [x] sdnne03-001 a 014: OK (0 issues)
  - [x] sdnne03-015 a 021: OK (exceto 022 kw_en inserido, 024 footnote removido)
  - [x] sdnne03-022: kw_en inserido ("new monumentality; tectonics; Acácio Gil Borsoi")
  - [x] sdnne03-023 a 028: OK
  - [x] sdnne03-029 a 032: OK (031/032 sem abs_en genuíno)
  - [x] sdnne03-033: abstract_en trimmed (contaminação com body text)
  - [x] sdnne03-034: keywords PT inserido ("Paisagem cultural; arquitetura moderna; legislação")
  - [x] sdnne03-035: keywords_en formato corrigido
  - [x] sdnne03-036 a 041: OK

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
