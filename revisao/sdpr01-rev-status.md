# sdpr01 — Status da revisão

Data: 2026-03-23
Artigos: 26 | Autores: 35

## Diagnóstico

| Campo | Antes | Depois | Nota |
|-------|-------|--------|------|
| abstract | 18/26 (69%) | 18/26 (69%) | 8 genuinamente sem Resumo |
| abstract_en | 0/26 | 1/26 | 014 extraído do .doc |
| abstract_es | 0/26 | 1/26 | 024 extraído do .doc (agente LLM) |
| keywords | 17/26 (65%) | 17/26 (65%) | 9 sem Palavras-chave no .doc |
| keywords_en | 0/26 | 5/26 | 003, 005, 014, 021, 023 |
| keywords_es | 0/26 | 1/26 | 024 |
| references | 18/26 (69%) | 23/26 (88%) | +002, +015, +017, +018, +024 |
| ORCID | 16/35 | 17/35 (49%) | +Maria Cecília Tavares |

## Progresso

- ✅ 0.0 Checkpoint
- ✅ 0.1 Diagnóstico: abs 69%, kw 65%, refs 69%
- ✅ 0.2 Artigos fora do padrão identificados
- ✅ 0.3 Extração de .doc (25 arquivos, script extrair_metadados_doc.py)
- ✅ 0.4 Seções: 4 existentes, 26/26 atribuídos
- ✅ 0.5 Lacunas preenchidas (6 campos novos via doc)
- ✅ 0.6 EN: abs_en=1 (014), kw_en=5 (003,005,014,021,023)
- ✅ 0.7 ES: abs_es=1 (024), kw_es=1 (024)
- ✅ 0.8 Validate: 7→0 issues
- ✅ 1.1a Títulos: 7 normalização + 6 correções manuais
- ✅ 1.2a Clean refs: 9 splits
- ✅ 1.2b Sweep: 5 lixo, 4 joins, 2 não-refs
- ✅ 1.2b+ Re-backfills: 0
- ✅ 1.2c+1.10 Revisão LLM (3 agentes, todos artigos): 20/26 corrigidos
- ✅ 1.3 Keywords: 0 alterações
- ✅ 1.5 Validação final: 0 issues
- ✅ 1.6 Cobertura verificada
- ✅ 1.7 Autores: 35
- ✅ 1.8 Dedup: 0 merges
- ✅ 1.9 ORCID: 17/35 (49%)
- ✅ 2.0 HTML gerado, dump feito

## Log de correções automáticas

### Títulos (13 correções)

| Artigo | Campo | Antes | Depois | Causa |
|--------|-------|-------|--------|-------|
| 003 | title | A Obra de Philipp Lohbauer | A obra de Philipp Lohbauer | genérico |
| 004 | title | A Paisagem Urbana como cena moderna | A paisagem urbana como cena moderna | genérico |
| 008 | title | Depoimento de um Arquiteto carioca → Carioca | Depoimento de um arquiteto carioca | gentílico + genérico |
| 010 | title | João Antonio | João Antônio | acento |
| 013 | title | Modernidade | modernidade | genérico |
| 014 | title | COHAB-ct | COHAB-CT | sigla |
| 015 | title | Arquitetura → arquitetura | normalização correta | genérico |
| 016 | title | Carioca, Paranaense | carioca, paranaense | gentílico |
| 018 | title | Modernidade | modernidade | genérico |
| 019 | title | Luis forte Netto | Luis Forte Netto | sobrenome |
| 019 | subtitle | Três→três, Arquitetura→arquitetura | normalização | subtítulo minúscula |
| 025 | subtitle | Desenho | desenho | genérico |
| 026 | subtitle | Galeria→galeria, Arquitetura→ | normalização | subtítulo minúscula |

### Referências (20 artigos corrigidos)

| Artigo | Ação | Detalhes |
|--------|------|---------|
| 002 | +6 refs | ARGAN, CIRNE-LIMA, ENGENHARIA, LE CORBUSIER, XAVIER, ZEVI |
| 003 | 1 fix | ref truncada completada |
| 004 | 2 splits + 2 joins | LARA+LE CORBUSIER split, REGO/DELMONICO+SILVEIRA joined |
| 005 | 2 backfills + 2 joins | CASTELNOU backfills, CASTELNOU+CONDE joins |
| 006 | 1 join | NOBRE join |
| 007 | 1 fix + 1 join | LAMBERTS fix, REGO join |
| 008 | reconstruídas | 4 backfills FERREIRA, 2 GNOATO, splits, joins |
| 009 | 1 backfill + 1 fix + 1 join | COSTA backfill+fix, VERRI join |
| 014 | 3 joins + 1 add | DELY, GNOATO, PRESTES joins + BONDUKI |
| 015 | +11 refs | BLASER, COHEN, DOCZI, FRAMPTON, etc. |
| 016 | splits + joins + adds | BRUAND, WATHEN splits, GOODWIN add |
| 017 | +14 refs | ACAYABA, BRUAND, FARIAS, FRAMPTON, etc. |
| 018 | 18→27 refs | splits massivos, normalização autores |
| 019 | 1 fix | DUQUEQUE→DUDEQUE |
| 020 | 1 fix + 1 add | CIUCCI fix, L'ARCHITECTURE add |
| 021 | 2 joins + 1 add | HARDT, KLOSS joins + DUDEQUE |
| 022 | 9 backfills + 5 joins + 3 adds | AMARAL, ARTIGAS×4, FRAMPTON, RIBEIRO, XAVIER |
| 023 | 1 backfill + 1 join + fixes | CASTELNOU backfill+join, truncamentos |
| 024 | +22 refs | todas novas |
| 025 | 1 join + 1 fix | CUNHA join, GFAUUSP fix |
