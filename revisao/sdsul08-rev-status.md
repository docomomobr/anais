## Diagnóstico — sdsul08 (51 artigos)

### Padrão de metadados
| Campo | Presença | Classificação | Ação |
|-------|----------|---------------|------|
| abstract | 96%→59% | INTERMEDIÁRIO | 19 overflows limpos, 30 re-extraídos, 21 sem abstract genuíno |
| abstract_en | 0% | AUSENTE | PDFs não têm seção Abstract EN |
| keywords | 0% | AUSENTE | PDFs não têm seção Palavras-chave |
| keywords_en | 0% | AUSENTE | PDFs não têm seção Keywords |
| references | 96% | PRESENTE | 003,037 sem refs (resumo expandido genuíno) |
| title_en | 0% | AUSENTE | PDFs não têm título em inglês |

### Progresso
- ✅ 0.0 — Checkpoint inicial
- ✅ 0.1 — Padrão levantado: abs 96%, abs_en 0%, kw 0%, kw_en 0%, refs 96%, 1 EN, 0 ES
- ✅ 0.2 — 2 sem abstract (004, 039), 2 sem refs (003, 037)
- ✅ 0.3 — 003,037 = resumo expandido (sem refs). 004,039 = artigo completo sem Resumo. 19 overflows limpos, 17 re-extraídos
- ✅ 0.3b — Extraído plumber: 52/52 (5190 blocos)
- ✅ 0.4 — 6 seções pré-existentes (51/51 atribuídos), section_label=eixo
- ✅ 0.5 — 19 overflows limpos, 17 re-extraídos, 019+025+031 corrigidos manualmente
- ✅ 0.6 — [SKIP] 0 artigos com Abstract/Keywords EN no PDF
- ✅ 0.7 — [SKIP] 0 artigos ES
- ✅ 0.8 — Validate: 20 issues, 0 auto-fixed. 3 A19 corrigidos (015 completado, 033 limpo, 019 page num removido)
- ✅ 1.1a — 27 normalização automática + 28 correções LLM
- ✅ 1.1b/c — [SKIP] title_en = 0, 0 ES
- ✅ 1.2a — clean: 0 splits, 2 backfills, 0 problemas
- ✅ 1.2b — sweep: 9 joins, 13 splits, 7 não-refs, 8 lixo, 1 endnote
- ✅ 1.2b+ — Re-backfills: 0, 1 URL juntada
- ✅ 1.2c — Revisão LLM: ~40/49 corrigidos (~32 joins, ~21 splits, ~24 adds, 4 backfills, ~20 fixes)
- ✅ 1.3 — Keywords: 0% genuíno
- ✅ 1.5 — Loop: 12 issues → 7 A11 restantes (refs genuinamente longas)
- ✅ 1.6 — abs 59%, refs 96%. ISBN 978-85-61965-82-2
- ✅ 1.7 — 74 autores, 51/51 verificados vs plumber
- ✅ 1.8 — Dedup: 0 merges
- ✅ 1.9 — ORCID: 55/74 (74%), 0 novos
- ✅ 1.10 — Revisão LLM final: 3 agentes paralelos (refs) + verificação campo a campo (títulos, abstracts)
- ✅ 2.0 — Validação final + HTML + dump + commit

### Revisão humana
- ✅ sdsul08-017: subtitle "estadual" → "Estadual" (Plano Rodoviário Estadual = nome próprio)

### Fechamento
- ✅ 5.1 — clean + check refs: 0 problemas / 670 refs
- ✅ 5.2 — HTML regenerado
- ✅ 5.3 — Dict: 20 nomes próprios adicionados (seed_titles)

### Log de correções automáticas

#### Abstracts (Fase 0)
| Artigo | Campo | Antes | Depois | Causa |
|--------|-------|-------|--------|-------|
| sdsul08-003 | abstract | 7539c (corpo inteiro) | NULL | resumo expandido, overflow |
| sdsul08-005 | abstract | 6504c | NULL | resumo expandido, overflow |
| sdsul08-010 | abstract | 15467c | NULL | resumo expandido, overflow |
| sdsul08-013 | abstract | 6163c | NULL | resumo expandido, overflow |
| sdsul08-016 | abstract | 8760c | NULL | resumo expandido, overflow |
| sdsul08-020 | abstract | 6606c | NULL | resumo expandido, overflow |
| sdsul08-026 | abstract | 5537c | NULL | resumo expandido, overflow |
| sdsul08-027 | abstract | 7461c | NULL | resumo expandido, overflow |
| sdsul08-028 | abstract | 6696c | NULL | resumo expandido, overflow |
| sdsul08-029 | abstract | 7995c | NULL | resumo expandido, overflow |
| sdsul08-032 | abstract | 6232c | NULL | resumo expandido, overflow |
| sdsul08-034 | abstract | 6667c | NULL | resumo expandido, overflow |
| sdsul08-037 | abstract | 7007c | NULL | resumo expandido, overflow |
| sdsul08-038 | abstract | 6716c | NULL | resumo expandido, overflow |
| sdsul08-041 | abstract | 6988c | NULL | resumo expandido, overflow |
| sdsul08-042 | abstract | 7327c | NULL | resumo expandido, overflow |
| sdsul08-043 | abstract | 5241c | NULL | resumo expandido, overflow |
| sdsul08-044 | abstract | 7066c | NULL | resumo expandido, overflow |
| sdsul08-045 | abstract | 5522c | NULL | resumo expandido, overflow |
| sdsul08-002 | abstract | 3609c | 1726c | re-extraído do plumber |
| sdsul08-006 | abstract | 1697c | 1539c | re-extraído do plumber |
| sdsul08-011 | abstract | 3460c | 1528c | re-extraído do plumber |
| sdsul08-015 | abstract | 1886c→1663c | 2234c | truncado, completado do plumber |
| sdsul08-017 | abstract | 3271c | 1469c | re-extraído do plumber |
| sdsul08-019 | abstract | 4372c | 2635c | re-extraído do plumber (label "R." split, page num removido) |
| sdsul08-022 | abstract | 2607c | 787c | re-extraído do plumber |
| sdsul08-024 | abstract | 3426c | 1580c | re-extraído do plumber |
| sdsul08-025 | abstract | 3991c | 1998c | re-extraído do plumber (body+abstract join, hifens corrigidos) |
| sdsul08-031 | abstract | 1753c | 1753c | re-extraído do plumber (body+abstract join) |
| sdsul08-033 | abstract | 4522c→6516c | NULL | corpo, não resumo (sem seção Resumo separada) |
| sdsul08-036 | abstract | 2872c | 1117c | re-extraído do plumber |
| sdsul08-040 | abstract | 3860c | 1902c | re-extraído do plumber |
| sdsul08-046 | abstract | 3193c | 1327c | re-extraído do plumber |
| sdsul08-047 | abstract | 3616c | 1740c | re-extraído do plumber (hifens corrigidos) |
| sdsul08-048 | abstract | 3775c | 1781c | re-extraído do plumber |
| sdsul08-049 | abstract | 3296c | 1435c | re-extraído do plumber |

#### Títulos (Fase 1.1a) — 28 correções LLM
| Artigo | Campo | Antes | Depois | Causa |
|--------|-------|-------|--------|-------|
| sdsul08-002 | title | As piscinas das marés | As Piscinas das Marés | nome próprio (obra Siza) |
| sdsul08-003 | title | River basin heritage | River Basin Heritage | Title Case EN |
| sdsul08-004 | title | Barragem do salto | Barragem do Salto | nome próprio (barragem) |
| sdsul08-006 | title | O refúgio das Águas | O refúgio das águas | genérico |
| sdsul08-006 | subtitle | Ruy viveiros de leiria | Ruy Viveiros de Leiria | nome de pessoa |
| sdsul08-007 | subtitle | Pontes destruídas | pontes destruídas | genérico |
| sdsul08-008 | subtitle | Torres de Água | torres de água | genérico |
| sdsul08-009 | title | Torres de Água | Torres de água | genérico |
| sdsul08-010 | subtitle | Ribeirão das lages | Ribeirão das Lages | topônimo |
| sdsul08-011 | subtitle | proposta Técnica | proposta técnica | genérico |
| sdsul08-013 | title | D'Água | d'água | contração, genérico |
| sdsul08-013 | subtitle | um Panorama | um panorama | genérico |
| sdsul08-017 | subtitle | plano Rodoviário / revista Técnica | Plano Rodoviário / Revista Técnica | nome de plano / publicação |
| sdsul08-018 | subtitle | grandes Obras | grandes obras | genérico |
| sdsul08-019 | title | a Serviço | a serviço | genérico |
| sdsul08-019 | subtitle | texaco / irace | Texaco / Irace | nome próprio |
| sdsul08-024 | subtitle | evolução dos passeios | os passeios | correção vs PDF |
| sdsul08-025 | title | Criação / anhangabaú | criação / Anhangabaú | genérico / topônimo |
| sdsul08-025 | subtitle | Ensaio | ensaio | genérico |
| sdsul08-030 | title | plataforma Rodoviária | Plataforma Rodoviária | nome de edifício |
| sdsul08-031 | subtitle | Carlos m. / Cláudio l. g. | Carlos M. / Cláudio L. G. | iniciais maiúsculas |
| sdsul08-034 | title | Memphis S.A | Memphis S.A. | pontuação |
| sdsul08-035 | title | cidade industrial | Cidade Industrial | nome próprio (distrito) |
| sdsul08-036 | subtitle | Água abaixo | água abaixo | idioma (por água abaixo) |
| sdsul08-038 | subtitle | Três projetos | três projetos | subtítulo lowercase |
| sdsul08-040 | title | Técnica e modernidade | técnica e modernidade | genéricos |
| sdsul08-042 | subtitle | cadernos do centro | Cadernos do Centro de Desenvolvimento... | publicação / instituição |
| sdsul08-044 | subtitle | Obra dos Irmãos Roberto | obra dos Irmãos Roberto | obra genérico |
| sdsul08-047 | title | Espaço Público / alameda / Encontro | espaço público / Alameda / encontro | genéricos / Alameda topônimo |
| sdsul08-048 | subtitle | Torres del parque | Torres del Parque | nome de edifício |
| sdsul08-049 | title | Sertão | sertão | genérico |
| sdsul08-051 | title | Arquitetônicas | arquitetônicas | genérico |
