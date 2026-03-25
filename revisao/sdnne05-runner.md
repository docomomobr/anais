# sdnne05 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-25 | Artigos: 32
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/32 | % |
|-------|-------|---|
| abstract | 31 | 97% |
| abstract_en | 32 | 100% |
| keywords | 31 | 97% |
| keywords_en | 31 | 97% |
| references | 30 | 94% |
| title_en | 2 | 6% |
| sections | 3 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint: e9726cc (anais.sql já atualizado)
- [x] **0.1** Cobertura: abs 31/32, abs_en 32/32, kw 31/32, kw_en 32/32, refs 30/32, title_en 2/32
- [x] **0.2** Fora do padrão: 018/019 sem refs; 022 sem abstract/kw (locale=es, campos ES já preenchidos)
- [x] **0.3** Sem doc/docx. PDFs nas fontes
- [x] **0.3b** Fontes plumber extraídas (32 arts, 3446 blocos)
- [x] **0.4** Seções: 3 eixos temáticos (A 17, B 8, C 7). Todos atribuídos
- [x] **0.5** Lacunas: 018 16 refs, 019 14 refs backfilled do plumber. 022 abstract/kw preenchidos de abstract_es/keywords_es
- [x] **0.6** Extrair metadados EN: 1 title_en extraído, 29 falharam (sem EN no PDF)
- [x] **0.7** ES: 1 artigo (022), já tratado
- [x] **0.8** Validate --fix: 3 auto-fixes (A22 non-ref, A21 abstract_es redundante, A17 dup). 12 issues restantes

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 9 normalizer, 5 reversões (modernistas, Moderno, adequação, ciudad/La, homem/fábrica), 4 correções LLM (019 madeira, 028 Moderne, 030 subtitle adicionado, 032 split title/subtitle). Dict limpo: 6 genéricos removidos + STOPWORDS atualizados
- [x] **1.1b** Títulos EN: 26 title_en extraídos dos PDFs. Correções: 001 (PT→EN traduzido), 009 (Caddahin→Caddah in), 013 (cleared bad), 030/032 (ALL CAPS → normalizado)
- [x] **1.1c** Revisão LLM títulos EN/ES: incluída em 1.1b
- [x] **1.2a** Refs limpeza base: 5 artigos, 4 underscore splits, 8 backfills. 529→561 refs
- [x] **1.2b** Refs sweep: 10 artigos (1 lixo, 5 joins, 3 splits, 2 non-refs, 1 dedup). 561→555 refs
- [x] **1.2b+** Re-backfills: 0 necessários
- [x] **1.2c** Refs revisão LLM: 19 artigos corrigidos (~36 correções: 22 backfills, 8 splits, 5 fixes, 1 missing)
- [x] **1.3** Keywords: 1 artigo (023 split)
- [x] **1.5** Loop validação: 3 issues genuínos restantes (A14 001 falso positivo, A19 013/028 truncamento original)
- [x] **1.6** Cobertura OK. abs 100%, abs_en 100%, kw 100%, kw_en 100%, refs 100%, title_en 97%. Seminário: 5º Docomomo NNE, Fortaleza, 2014, Núcleo Docomomo Ceará / UFC
- [x] **1.7** Autores: 2 afiliações corrigidas (028 IAU-USP→IFS, 010 UNIFAP→FAMA). Nota: author 1479 Nelcia tem familyname diferente neste PDF mas é compartilhada com seminários revisados
- [x] **1.8** Dedup: 2 nomes adicionados ao dict, 0 merges automáticos
- [x] **1.9** ORCID: +4 novos (Thalita Lins, Natan Pinheiro, Pedro Mergulhão, Plínio Silveira). Total: 37/52 (71%)
- [x] **1.10** Revisão LLM final: 17 correções em 15 artigos (003 acento, 009 título incompleto, 012 kw truncada, 013 title_en, 015 acento, 016/017/022/029 trailing period, 018 subtitle, 020 Severiano, 021 kw, 023/028 kw format, 030/031 kw_en)

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação + HTML + commits
  ```
  python3 scripts/validate_metadata.py --slug sdnne05 --fix
  python3 scripts/gerar_revisao_html.py sdnne05
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdnne05-* && git commit -m "sdnne05 revisão automática (Fases 0-2)"
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
