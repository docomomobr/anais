# sdnne06 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-25 | Artigos: 109
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/109 | % |
|-------|-------|---|
| abstract | 107 | 98% |
| abstract_en | 19 | 17% |
| keywords | 106 | 97% |
| keywords_en | 6 | 6% |
| references | 66 | 61% |
| title_en | 0 | 0% |
| sections | 3 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint: f62551c (anais.sql já atualizado)
- [x] **0.1** Cobertura: abs 107/109, abs_en 19/109, kw 106/109, kw_en 6/109, refs 66/109, title_en 0/109
- [x] **0.2** Fora do padrão: 43 resumo-only (sem PDF), 2 sem abstract (108/109 sem resumo no PDF), 3 sem kw (108/109/80)
- [x] **0.3** 57 docx + 30 PDFs em fontes/artigos_completos, 66 PDFs em pdfs/
- [x] **0.3b** Fontes plumber extraídas (66 arts, 5420 blocos)
- [x] **0.4** Seções: 3 tipos de comunicação (Apresentação Oral 60, Poster Digital 28, Doco Jovem 21). Todos atribuídos
- [x] **0.5** Lacunas: 43 artigos resumo-only (sem refs). 108/109 sem abstract (PDF sem resumo formal)
- [x] **0.6** Extrair metadados EN: 0 title_en, 26 abstract_en extraídos, 41 keywords_en extraídos
- [x] **0.7** ES: 1 artigo (034 colombiano), locale corrigido, abstract→abstract_es
- [x] **0.8** Validate --fix: 3 auto-fixes (locale, dedup refs, abstract idioma). 18 issues restantes

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 53 normalizer, 40 reversões (falsos positivos), 14 genéricos removidos do dict (complexo, desenvolvimento, edificado, elementos, longo, monumento, monumentos, residências, tectônica, urbanos, vernacular, antigo, interrompido, privado). 4 EXCLUDE_COMMON_WORDS em seed_authors (longo, marco, mestre, nascimento). FIFA/Copa, Moderne, Teresina-Piauí adicionados ao dict
- [x] **1.1b** Títulos EN: SKIP (0 title_en)
- [x] **1.1c** Revisão LLM títulos EN/ES: SKIP (0 title_en)
- [x] **1.2a** Refs limpeza base: 0 alterações, 924 refs OK
- [x] **1.2b** Refs sweep: 12 artigos (7 lixo, 6 joins, 3 splits, 1 non-ref). 924→913 refs
- [x] **1.2b+** Re-backfills: 0 necessários
- [x] **1.2c** Refs revisão LLM: 10 artigos, 35 correções (27 backfills, 7 joins, 1 split). Refs longas em 17/44/86 split manualmente
- [x] **1.3** Keywords: 0 alterações
- [x] **1.5** Loop validação: 4 issues genuínos (A03 art 34 ES sem kw_es, A10 backfill resumo-only, A12 entrevistas válidas em 106)
- [x] **1.6** Cobertura OK. abs 97%, abs_en 41%, kw 97%, kw_en 43%, refs 61%, title_en 0%. Seminário: 6º Docomomo NNE, Teresina, 2016, UFPI, ISBN 978-85-7463-919-2
- [x] **1.7** Autores: Valle expandido, Franco expandido, art 048 (Cavalcante, Cândido, +Cadena, +Carvalho), art 062 merge Oliveira Silva, art 026 Furtado removido (não consta no PDF)
- [x] **1.8** Dedup: Célia Mesquita → Célia Regina Mesquita Santos (cross-familyname)
- [x] **1.9** ORCID: +15 novos. Total: 120/208 (58%)
- [x] **1.10** Revisão LLM final: 28 correções em 18 artigos (5 typos, 5 título/subtítulo do PDF, 10 keywords, 10 keywords_en)

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação + HTML + commits

## Revisão humana

- [x] 16 correções: 11 Modernista→modernista, 3 capitalização (antigo, público/privado, apartamentos, arquitetos), 2 abstracts truncados (19 final, 58 início)
- [x] Nova regra: expressão consolidada + gentílico capitalizado (Arquitetura Moderna Piauiense)
- [x] Observações: ficha catalográfica a compor; caderno de resumos como galley do seminário

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** Diagnóstico: 16 correções humanas, ~120 automáticas. Causa principal: normalizer não força minúsculas, apenas capitaliza do dict
- [x] **3.2** Dict: 17 genéricos removidos + 3 STOPWORDS adicionados (antigo, interrompido, privado) + 4 EXCLUDE_COMMON_WORDS (longo, marco, mestre, nascimento)
- [x] **3.3** Scripts: 0 atualizações necessárias (limitação arquitetural do normalizer aceita)
- [x] **3.4** Pipeline: sem gaps
- [x] **3.5** Dry-run: 42 regressões (falsos positivos do normalizer — capitaliza palavras do dict como Residências, Praça, Hospital)
- [x] **3.6** Aprendizado: sdnne06-aprendizado.json
- [x] **3.7** Engenharia: 0 HIGH, 1 MEDIUM (42 regressões normalizer), 2 LOW (scripts one-shot)
- [x] **3.8** Checklist de conclusão
- [x] **3.9** Fechar: dump + commit + CLAUDE.md
