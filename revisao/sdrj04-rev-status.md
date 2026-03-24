# sdrj04 — Log de revisão

Data início: 2026-03-23
Commit inicial: 8c85977

## Cobertura inicial

| Campo | N/17 | % |
|-------|------|---|
| abstract | 16 | 94% |
| abstract_en | 11 | 65% |
| keywords | 15 | 88% |
| keywords_en | 11 | 65% |
| references | 15 | 88% |
| title_en | 0 | 0% |
| sections | 3 | — |

## Modificações

### Fase 0 — Diagnóstico e preenchimento

- 003: abstract_es + keywords_es inseridos (ES, não EN)
- 006: abstract_es + keywords_es inseridos (ES, não EN)
- 007, 008, 016, 017: metadados EN/refs genuinamente ausentes (poster, workshop, sem seção EN)
- 016: email removido do abstract (vinicius.ferreira.mattos@gmail.com)
- Fontes plumber extraídas (17 artigos, 2834 blocos)

### Fase 1.1a — Títulos

- 004: "Obra" → "obra" (genérico, não nome próprio)
- 006: "instituto" → "Instituto" (nome de instituição), "Protomoderna" → "protomoderna" (adjetivo)
- 008: título corrigido: "As escolas dos anos 1950" → "As escolas construídas na década de 1950 no antigo Distrito Federal" (confronto PDF)
- 010: "instituto" → "Instituto" Vital Brazil
- 011: "pavilhão" → "Pavilhão" Arthur Neiva (parte do nome)
- 013: "pavilhão" → "Pavilhão" da Febre Amarela
- 016: subtítulo inteiro corrigido: "patrimônio paisagístico moderno para a contemporaneidade" → "patrimônio moderno, possibilidades contemporâneas através das estruturas paisagísticas" (confronto PDF)
- 016: "Contemporaneidade" → "contemporaneidade" (genérico)

### Fase 1.2 — Refs

- Sweep: 285 → 261 refs (notas cortadas, lixo removido, image credits removidos)
- 001: 3 non-refs removidas (image credits URLs), 1 garbled prefix removida
- 002: split LEMOS + O'DONNELL
- 003: 4 non-refs removidas (image credits)
- 005: split SEGAWA + SELIGMANN-SILVA
- 006: split BRUAND + CASA DAS PALMEIRAS
- 009: split D'ORSI + ENVIRONMENT + INPE (3-way), split PCRJ + ROBERT, split Case Studies + WWE
- 010: 3 non-refs removidas, split CONDURU + FABRICA, split GOODWIN + GRUA + ITAU, split SERRES + SOLAR
- 011: join split PBMC
- 012: join split CARBONARA, removed last ref (image credits)
- 013: 4 non-refs removidas (DAD/COC credits)
- 014: 3 image credit URLs removidas, UNESCO ref limpa
- 015: 16 → 1 ref (15 eram body text/legendas)

### Fase 1.3 — Keywords

- 003: limpa contaminação autora/afiliação nas keywords
- 004: limpa contaminação autor/afiliação nas keywords
- 007: removidas 2 entries contaminadas (autor/afiliação)
- 013: keywords_en limpa (removida afiliação concatenada)

### Fase 1.7 — Autores/afiliações

- 11 afiliações inseridas (002 USP, 003 PROURB-FAU-UFRJ, 004 UFF/UNIGRANRIO, 006 PROURB-LAPA, 008 PPGAU-UFF, 010 COC-Fiocruz, 012 UFRJ, 014 UFRRJ/FAU-USP, 015 FAU-UFRJ)
- 009 Carla Coelho: sem afiliação no PDF (genuinamente ausente)

### Fase 1.9 — ORCID

- Barbara Cortizo de Aguiar → 0000-0003-0286-0250 (confirmado ORCID API)
- ORCID total: 16/25 (64%)

### Fase 1.10 — Revisão LLM final

- 001–005, 008–011, 014–015, 017: OK
- 006: abstract PT completado (1→3 parágrafos, 1317c)
- 007: keywords limpas (removido autor/afiliação)
- 012: abstract PT e EN completados (2 parágrafos cada), footnote marker "1" removido, last ref (image credits) removida
- 013: abstract PT e EN completados (1→3 parágrafos cada)
- 016: abstract limpo (4357→1881 chars, removida duplicação + contaminação autor)

