## Diagnóstico — sdmg01 (26 artigos)

### Padrão de metadados
| Campo | Presença | Classificação | Ação |
|-------|----------|---------------|------|
| abstract | 65% (17/26) | INTERMEDIÁRIO | buscar nos PDFs |
| abstract_en | 69% (18/26) | INTERMEDIÁRIO | buscar nos PDFs |
| keywords | 69% (18/26) | INTERMEDIÁRIO | buscar nos PDFs |
| keywords_en | 58% (15/26) | INTERMEDIÁRIO | buscar nos PDFs |
| references | 77% (20/26) | INTERMEDIÁRIO | buscar nos PDFs |
| title_en | 0% | AUSENTE | não buscar |

### Progresso
- ✅ 0.0 — Checkpoint inicial (commit b0071f6)
- ✅ 0.1 — Padrão levantado (acima)
- ✅ 0.2 — 9 sem abs, 8 sem abs_en, 8 sem kw, 11 sem kw_en, 6 sem refs
- ✅ 0.3 — Fonte: DVD (PPT + PDFs), sem doc/docx
- ✅ 0.3b — Plumber extraído (26 artigos, 2526 blocos)
- ✅ 0.4 — Seções: 2 (Apresentações Orais + Pôsteres), sem eixos temáticos
- ✅ 0.5 — Lacunas preenchidas do plumber (12 artigos, 16 campos)
- ✅ 0.6 — EN: 1 abs_en extraído (script), title_en 0 (sem seção EN nos PDFs)
- ✅ 0.7 — ES: skip (0 artigos ES)
- ✅ 0.8 — Validate --fix: 4 auto-fixed, 16 issues para Fase 1
- ✅ 1.1a — 9 normalização + 7 correções LLM
- ✅ 1.1b — skip (title_en = 0)
- ✅ 1.1c — skip (title_en = 0)
- ✅ 1.2a — clean_references: 4 splits, 5 backfills, 1 join
- ✅ 1.2b — sweep: 9 arts, 12 joins, 12 endnotes, 8 non-refs
- ✅ 1.2b+ — 2 re-backfills
- ✅ 1.2c+1.10 — Revisão LLM: 18/26 artigos corrigidos (3 agentes)
- ✅ 1.3 — Keywords: 1 art (2 splits) + 9 kw→JSON
- ✅ 1.5 — Loop: 3 issues genuínos (A01×2, A10×1)
- ✅ 1.6a — Cobertura: abs 73%, abs_en 76%, kw 80%, kw_en 69%, refs 100%
- ✅ 1.6b — Metadados seminário OK (título, editora, editors×9, description)
- ✅ 1.6c — Seções OK (2, confirmado via PPT)
- ✅ 1.7 — 40 autores verificados vs plumber, 2 corrigidos (Di Marco, Silva)
- ✅ 1.8 — Dedup: 0 merges
- ✅ 1.9 — ORCID: 24/40 (60%), 4 novos (Lazzarin, Azevedo, Rezende, Silva)
- ✅ 2.0 — Validação final (3 issues genuínos) + HTML + commit (aa9b10a, f102f44)

### Revisão humana
- ✅ sdmg01-012: subtitle "— mg1" → "— MG" (typo, "1" grudado na sigla do estado)

### Log de correções automáticas
| Artigo | Campo | Antes | Depois | Causa |
|--------|-------|-------|--------|-------|
| sdmg01-002 | references_ | NULL | 14 refs | bibliografia em body block (não role=reference) |
| sdmg01-004 | abstract_en | truncado+cid | limpo | garbage (cid:1) + footnote no fim |
| sdmg01-004 | references_ | 16 refs | 17 refs | ref GAZETA faltante |
| sdmg01-005 | subtitle | Engenheiro | engenheiro | profissão genérica capitalizada pelo dict |
| sdmg01-006 | abstract | truncado | completo (4 par.) | plumber p3-p4, 9.8pt |
| sdmg01-006 | abstract_en | truncado | completo (3 par.) | plumber p2, 9.8pt |
| sdmg01-006 | references_ | NULL | 46 refs | blocos reference p14-17 |
| sdmg01-008 | references_ | 38 refs | 39 refs | ref EMBRATUR faltante |
| sdmg01-009 | subtitle | errado (eixo) | correto (vilas Furnas) | subtítulo era label de eixo |
| sdmg01-009 | references_ | 7 fragmentos | 5 refs limpas | line-wrap split |
| sdmg01-009 | subtitle | Presente | presente | adjetivo genérico |
| sdmg01-010 | abstract_en | contaminado PT | limpo | footnotes + bios no abstract |
| sdmg01-010 | references_ | 13 refs | 14 refs | split CAVALCANTI concatenação |
| sdmg01-011 | references_ | 20 refs | 18 refs | joins + split (COSTA, LIMA, REZENDE, TABACOW, UFJF) |
| sdmg01-012 | references_ | 13 refs | 14 refs | join PIRES, backfill incorreto removido |
| sdmg01-014 | references_ | 12 refs | 12 refs | footnote removida do PAPADAKI |
| sdmg01-015 | subtitle | Materiais | materiais | genérico capitalizado pelo dict |
| sdmg01-015 | references_ | 20 refs | 17 refs | joins MALARD, VASCONCELLOS×2 |
| sdmg01-016 | subtitle | Complexo/Nacionais/Internacionais | complexo/nacionais/internacionais | genéricos capitalizados pelo dict |
| sdmg01-016 | references_ | 25 refs | 34 refs | reconstrução splits (BRUAND, GOODWIN, GUEGEN, MARTINS) |
| sdmg01-017 | references_ | 8 refs | 5 refs | joins ASTOS/LARA, MALARD completado |
| sdmg01-018 | title | Jardim | jardim | "jardim de infância" genérico |
| sdmg01-019 | abstract | body text | NULL | sem RESUMO no PDF (era intro do corpo) |
| sdmg01-019 | keywords | NULL | 4 keywords | "Palavras-chave:" em small p4 |
| sdmg01-021 | abstract_en | PT kw no fim | limpo | keywords PT grudadas no abstract EN |
| sdmg01-021 | keywords | NULL | 3 kw PT | split bilingual line |
| sdmg01-021 | keywords_en | NULL | 3 kw EN | split bilingual line |
| sdmg01-022 | abstract_en | contaminado | limpo | footnotes de autor no abstract |
| sdmg01-022 | references_ | 2 mangled | 30 refs | reconstrução 2-col layout |
| sdmg01-023 | title | Arquitetônica | arquitetônica | adjetivo genérico |
| sdmg01-024 | abstract | body text incluso | só resumo | plumber misclassified body as abstract |
| sdmg01-024 | references_ | NULL | 5 refs | blocos reference |
| sdmg01-025 | title | Desenvolvimento | desenvolvimento | genérico capitalizado pelo dict |
| sdmg01-025 | abstract_en | typo "M odern" | "Modern" | espaço espúrio |
| sdmg01-025 | references_ | 6 refs | 7 refs | +FICHER, -footnote |
| sdmg01-026 | references_ | 9 refs | 7 refs | joins CHRYSOSTOMO, REZENDE |
| sdmg01-040 (Anita) | familyname | Marco | Di Marco | sobrenome composto |
| sdmg01-002 (Lisandra) | familyname | Mara | Silva | nome completo confirmado via legendas PDF |

### Issues genuínos (não corrigíveis)
- A01: sdmg01-004, sdmg01-014 — abstract_en presente mas keywords_en ausente no PDF
- A10: sdmg01-005 — 1 backfill pendente (ref com ______)
- 7 artigos sem abstract PT (genuíno: 009, 010, 012, 019, 020, 021, 026 — sem RESUMO no PDF)
- 6 artigos sem abstract_en (genuíno: 007, 008, 009, 018, 019, 020 — sem ABSTRACT no PDF)
