## Diagnóstico — sdsul07 (46 artigos)

### Padrão de metadados
| Campo | Presença | Classificação | Ação |
|-------|----------|---------------|------|
| abstract | 85% (39/46) | PRESENTE | buscar nos PDFs faltantes |
| abstract_en | 0% | AUSENTE | não buscar — PDFs não têm seção EN |
| keywords | 0% | AUSENTE | não buscar — PDFs não têm seção Palavras-chave |
| keywords_en | 0% | AUSENTE | não buscar |
| references | 98% (45/46) | PRESENTE | extrair do plumber (008) |
| title_en | 0% | AUSENTE | não buscar |

Norma de citação: ABNT predominante

### Progresso
- ✅ 0.0 — Checkpoint inicial (dump)
- ✅ 0.1 — Padrão levantado: abs 85%, kw 0%, refs 98%, EN/ES 0%
- ✅ 0.2 — 7 sem abstract (001,002,024,033,035,041,044), 1 sem refs (008)
- ✅ 0.3 — 7 sem abstract genuíno (sem label Resumo). 008 com refs no plumber
- ✅ 0.3b — Plumber extraído: 47/47 (5326 blocos)
- ✅ 0.4 — 8 sessões pré-existentes, 46/46 atribuídos
- ✅ 0.5 — 008 10 refs inseridas. 17 abstracts overflow re-extraídos. 012/025 truncados completados (blocos adjacentes). 037 truncado completado
- ✅ 0.6 — SKIP (0% abstract_en)
- ✅ 0.7 — SKIP (0 artigos ES)
- ✅ 0.8 — Validate: 20→1 issues (17 A20 auto-fixed, 2 A19 corrigidos manualmente)
- ✅ 1.1a — 23 normalização + 31+4 correções LLM
- ✅ 1.1b/c — SKIP (0 title_en, 0 ES)
- ✅ 1.2a — 2 backfills, 0 problemas
- ✅ 1.2b — 142 joins, 1 split, 20 não-refs, 14 lixo, 5 dedup
- ✅ 1.2b+ — 1 backfill adicional
- ✅ 1.2c — 43/46 artigos refs corrigidos (3 agentes LLM)
- ✅ 1.3 — 0% keywords genuíno
- ✅ 1.5 — Convergiu em 1 iteração. 15→0 issues (14 backfills + 1 ref longa resolvidos)
- ✅ 1.6a — abs 85%, refs 100%, seções 100%, ORCID 84%
- ✅ 1.6b — ISBN 978-65-89263-60-9, publisher Núcleo Docomomo RS / Marcavisual, ficha verificada
- ✅ 1.6c — 8 sessões pré-existentes (Projetos esquecidos, Especulações preservacionistas e Revisões Cênicas, Revisões mobiliárias, Reformas, Casas esquecidas, Edifícios esquecidos, Séries esquecidas e Revisões urbanas, Revisões arquitetônicas)
- ✅ 1.7 — 56 autores, verificados vs sumário anais
- ✅ 1.8 — 0 merges
- ✅ 1.9 — 2 ORCIDs novos (Andrey de Aspiazu Schlee, Larissa Nogueira Agnelo). 47/56 (84%)
- ✅ 1.10 — 46/46 artigos revisados (3 agentes paralelos). Resultado por artigo no runner
- ✅ 2.0 — Validação final (1 A25 auto-fix, 0 report), HTML gerado, dump + commit

### Log de correções automáticas
| Artigo | Campo | Antes | Depois | Causa |
|--------|-------|-------|--------|-------|
| 17 artigos | abstract | overflow (3954-4496c) | re-extraído plumber (287-2124c) | extração sem ponto de corte |
| sdsul07-012 | abstract | truncado (287c) | completado (2290c) | bloco split no plumber |
| sdsul07-025 | abstract | truncado (490c) | completado (1990c) | bloco split no plumber |
| sdsul07-037 | abstract | truncado (126c) | completado (1427c) | bloco split no plumber |
| sdsul07-017 | abstract | overflow (4293c) | cortado (3353c) | body text vazado |
| sdsul07-034 | abstract | lixo no final | removido "1. O PIONEIRISMO DO" | heading grudado |
| sdsul07-008 | references_ | NULL | 10 refs | faltava extração |
| 31 artigos | title/subtitle | capitalização incorreta | corrigido vs PDF | normalização + LLM |
| 4 artigos | title/subtitle | nomes próprios | Casa Edgar Duvivier, Metalúrgica Abramo Eberle, Cidade Matarazzo, centro histórico | revisão adicional |
| 43 artigos | references_ | fragmentos, não-refs, body text | corrigido (1083→678 refs) | 3 agentes LLM |
| 14 refs | references_ | backfill ______ | autor preenchido | backfill manual |
| sdsul07-044 | references_ | 1 ref concatenada (561c) | split em 2 | revisão manual |
