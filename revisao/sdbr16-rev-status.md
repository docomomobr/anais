## Diagnóstico — sdbr16 (320 artigos: 285 artigos/resumos + 35 mesas)

### Padrão de metadados
| Campo | N/320 | % | Classificação | Acao |
|-------|-------|---|---------------|------|
| abstract | 307 | 96% | PRESENTE | buscar nos faltantes |
| abstract_en | 3 | 1% | AUSENTE | nao buscar |
| abstract_es | 12 | 4% | AUSENTE | nao buscar |
| keywords | 228 | 71% | PRESENTE | buscar nos faltantes |
| keywords_en | 0 | 0% | AUSENTE | nao buscar |
| keywords_es | 8 | 3% | AUSENTE | nao buscar |
| references | 263 | 82% | PRESENTE | buscar nos faltantes |
| title_en | 0 | 0% | AUSENTE | nao buscar |
| subtitle | 0 | 0% | — | avaliar |
| sections | 39 | — | — | verificar |

### Progresso
- ✅ 0.0 — Checkpoint inicial (commit e3d75101c)
- ✅ 0.1 — Padrao levantado: abstract 96%, kw 71%, refs 82% presentes; abstract_en/kw_en/title_en ausentes. Norma citacao: misto (ABNT + Chicago)
- ✅ 0.2 — Fora do padrao: 13 sem abstract, 57 artigos sem keywords, 22 artigos sem refs (mesas excluidas)
- ✅ 0.3 — Reinspecionados: 8 abstracts (docx+caderno), 36 kw (docx+caderno), 6 refs (docx). 5 sem abstract genuino
- ✅ 0.3b — Plumber 271 PDFs extraidos
- ✅ 0.4 — 39 secoes, 320/320 mapeados
- ✅ 0.5 — Validate --fix: 3 A31. sdbr16-028 locale->es, abstract limpo
- ✅ 0.6 — SKIP abstract_en < 30%
- ✅ 0.7 — ES: 10 artigos locale=es, 3 abstract_es redundantes limpos
- ✅ 0.8 — Abstracts OK: 0 truncados, 0 overflow
- ✅ 1.1a — Titulos PT: seed+normalizar+revisao LLM, 90 correcoes, dict -12 palavras
- ✅ 1.1b — SKIP title_en=0
- ✅ 1.1c — SKIP title_en=0
- ✅ 1.2a — Refs limpeza: 0 alteracoes, 3 issues (0.1%)
- ✅ 1.2b — Sweep: 2 splits (073, 257)
- ✅ 1.2b+ — 0 novos backfills
- ✅ 1.2c — Refs LLM: 43 splits, 9 bios removidas em 36 artigos
- ✅ 1.3 — Keywords: 6 ALL CAPS convertidos
- ✅ 1.5 — Loop: convergiu em 2 iteracoes
- ✅ 1.6 — Cobertura OK, description gerada
- ✅ 1.7 — Autores: ALL CAPS normalizados (201+227+39), 79 merges, 2 Hispanic fixados
- ✅ 1.8 — Dedup: 4 LLM merges, 55 distintos, 2 incertos
- ⏳ 1.9 — ORCID em andamento

### Log de correcoes automaticas
| Artigo | Campo | Antes | Depois | Causa |
|--------|-------|-------|--------|-------|
