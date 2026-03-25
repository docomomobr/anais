# sdnne04 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-25 | Artigos: 45
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/45 | % |
|-------|-------|---|
| abstract | 45 | 100% |
| abstract_en | 39 | 87% |
| keywords | 44 | 98% |
| keywords_en | 42 | 93% |
| references | 33 | 73% |
| title_en | 0 | 0% |
| sections | 3 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint: b8af95d (anais.sql já atualizado)
- [x] **0.1** Cobertura: abs 100%, abs_en 87%, kw 98%, kw_en 93%, refs 73% (33/45)
- [x] **0.2** Fora do padrão: 12 sem refs; 6 sem abs_en (013/015/026/031/032/039); 1 sem kw (043); 3 sem kw_en (026/032/043)
- [x] **0.3** Sem doc/docx. PDFs nas fontes (47 originais DOCONATAL*.pdf)
- [x] **0.3b** Fontes plumber extraídas (45 arts, 5785 blocos)
- [x] **0.4** Seções: 3 eixos temáticos (A arquitetura moderna como projeto 14, Narrativas historiográficas 19, Experiências de conservação e transformação 12). Todos atribuídos
- [x] **0.5** Lacunas: 12 artigos backfilled com 192 refs do plumber. 026 genuinamente sem abs_en/kw_en
- [x] **0.6** Extrair metadados EN: 3 abstract_en do script + 4 manuais (013/015/031/032/039). 043 abstract_en limpo (contaminação PT)
- [x] **0.7** ES: 0 artigos com locale=es
- [x] **0.8** Validate --fix: 2 auto-fixes (A17 dup, A25 kw no abstract). 24 issues restantes

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 11 normalizer, 4 reversões (Tombamento, Presente, Três, SE), 34 correções LLM vs PDF
- [x] **1.1b** Títulos EN/ES [SKIP: title_en = 0]
- [x] **1.1c** Revisão LLM títulos EN/ES [SKIP: title_en = 0]
- [x] **1.2a** Refs limpeza base: 7 backfills, 1 URL juntada (678→677 refs)
- [x] **1.2b** Refs sweep: 25 artigos (5 lixo, 48 joins, 38 splits, 10 non-refs, 1 endnote). 677→651 refs
- [x] **1.2b+** Re-backfills: 1 backfill
- [x] **1.2c** Refs revisão LLM: ~104 correções em 28 artigos (splits, joins, missing, truncated, non-refs). 651→642 refs
- [x] **1.3** Keywords: limpos, sem issues
- [x] **1.5** Loop validação: 2 issues genuínos (A01 043 kw_en, A19 032 truncamento)
- [x] **1.6** Cobertura OK. Seminário: Núcleo Docomomo NNE / UFRN, 2012
- [x] **1.7** Autores: 6 correções (3 afiliações inseridas 024, 1 corrigida 024/045, 1 familyname composto 038 Sá Carneiro)
- [x] **1.8** Dedup: 9 merges manuais (prefixo givenname: Carrilho, Gonsales, Lopes, Machado, Meneses, Poppe, Santos, Silva, Vidal) + 1 merge automático (Célia Mesquita)
- [x] **1.9** ORCID: +4 novos (Gustavo Sobral, Marília Brito, Regina Cavalcante, Isadora Paiva). Total: 46/83 (55%)
- [x] **1.10** Revisão LLM final: 5 correções em 3 artigos (032 abstract_en limpo, 032 kw_en formato, 039 kw_en corrigido, 045 kw/kw_en split)

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação + HTML + commits (7b55382)
  ```
  python3 scripts/validate_metadata.py --slug sdnne04 --fix
  python3 scripts/gerar_revisao_html.py sdnne04
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdnne04-* && git commit -m "sdnne04 revisão automática (Fases 0-2)"
  ```

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Revisão humana — 9 correções

1. ✅ sdnne04-004 subtitle: moderna → Moderna (expressão consolidada)
2. ✅ sdnne04-012 title: Obra → obra (genérico no dict)
3. ✅ sdnne04-039 abstract: truncado 1029→2090 chars
4. ✅ sdnne04-011 title: Circulação → circulação (genérico no dict)
5. ✅ sdnne04-016 title: Tessituras Tectônicas → tessituras tectônicas (genéricos no dict)
6. ✅ sdnne04-019 title: moderno → Moderno (expressão consolidada)
7. ✅ sdnne04-043 abstract: truncado 1235→2299 chars
8. ✅ sdnne04-007 title: Envelopado → envelopado (genérico no dict)
9. ✅ sdnne04-026 title: Mágica → mágica (genérico no dict)

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** Diagnóstico: 5/9 dict genérico, 2/9 regra toponímico LLM, 2/9 abstract truncado
- [x] **3.2** Dict: 20 genéricos removidos + 18 STOPWORDS adicionados
- [x] **3.3** Scripts: novo check A33 (abstract vs plumber prefix match), validate_metadata.py block.get('text','')
- [x] **3.4** Pipeline: 1.1a retroalimentação dict obrigatória + regra toponímico de/no clarificada
- [x] **3.5** Dry-run: 0 A33 falsos positivos em sdnne03/sdnne04/sdbr08
- [x] **3.6** Aprendizado: sdnne04-aprendizado.json + MEMORY.md feedback_dict_retroalimentacao
- [x] **3.7** Engenharia: 0 HIGH, 3 MEDIUM corrigidos (validate KeyError, seed_titles try/finally, dedup pilotis try/finally), 1 LOW (STOPWORDS duplicatas removidas)
- [x] **3.8** Checklist de conclusão
- [ ] **3.9** Fechar: dump + commit + push + CLAUDE.md
