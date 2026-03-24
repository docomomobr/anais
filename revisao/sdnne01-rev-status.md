# sdnne01 — Log de revisão

Data início: 2026-03-24
Commit inicial: 07f66e0

## Cobertura inicial

| Campo | N/44 | % |
|-------|------|---|
| abstract | 44 | 100% |
| abstract_en | 41 | 93% |
| keywords | 44 | 100% |
| keywords_en | 35 | 80% |
| references | 43 | 98% |
| title_en | 0 | 0% |
| sections | 10 | — |

## Modificações

### Fase 0 — Diagnóstico e preenchimento

- Fontes plumber extraídas (44 artigos, 8023 blocos). Sem doc/docx (CD-ROM)
- 006: keywords_en inseridas ("Architecture; Amazonia; project")
- 003: keywords_en limpas (contaminação com texto do corpo)
- 12 auto-fixes: 11 A25 (keywords coladas em abstracts), 1 A28 (título no abstract de 017)
- 027/031/044: abstract_en genuinamente ausente nos PDFs
- 010/020/021/026: keywords_en genuinamente ausentes nos PDFs

### Fase 1.1a — Títulos

- Normalizer: 3 aceitos (portuguesa, 2× modernista), 8 revertidos (obra, urbanístico, arquiteto, espaço público, ecumênica, IAPs/PAR)
- 002: "Tradição" → "tradição", "de morar" → "do morar" (confronto PDF)
- 005: "Pela" → "pela" (subtítulo minúscula)
- 009: título corrigido: removido "na cidade de Fortaleza e" (ausente no PDF)
- 016: "Residências" → "residências" (subtítulo)
- 017: "Arquitetura" → "arquitetura" (subtítulo genérico)
- 025: "Arquitetônica" → "arquitetônica" (PDF minúscula)
- 028: "parque" → "Parque" do Derby (nome próprio)
- 029: "caatinga" → "sertão" (título no PDF; resumo usa "caatinga")
- 031: título split corrigido, "Norte Nordeste" → "norte-nordeste" (hifenizado)
- 034: "Modernista" → "modernista", "Arquiteto" → "arquiteto"
- 036: "bangalôs" → "bangalô" (singular no PDF)
- 037: subtítulo: "Capela Ecumênica do Campus Central da UFRN" (maiúsculas como no PDF)
- 040: "Modernidade e Tradição" → "modernidade e tradição" (PDF minúscula)
- 041: "Modernistas" → "modernistas"
- 044: "Pernambucana" → "pernambucana" (adjetivo)

### Fase 1.2 — Refs

- Sweep: 693 → 666 refs (16 artigos: 6 lixo grosso, 12 joins, 1 split, 10 non-refs)
- LLM review (43 artigos): 23 correções em 13 artigos
  - 001: split 2 refs concatenadas (CORBUSIER+EL-JAICK, GUIMARAENS+URLs), join 2 pares fragmentados (SIQUEIRA, TOSTES)
  - 006: split ref concatenada (OLIVEIRA+Primeira mostra+2 revistas)
  - 007: +1 ref faltante (O QUE SÃO, Diário da Borborema)
  - 012: removidas 2 non-refs (agradecimento FAPESP) — já removidas pelo sweep
  - 013: split ref concatenada (BICCA+Cadernos), trim ref FICHER
  - 017: join DOMINGUES fragmentada, fix hifenização "catálogo geral"
  - 018: +4 refs faltantes (jornais A REPÚBLICA/O GRANDE Hotel)
  - 019: fix ref 5 concatenação, removidas 3 refs duplicadas (14/15/17), +6 refs faltantes
  - 020: split CAVALCANTI+Cronica
  - 022: split PEREIRA+REVISTA AU
  - 029: removida non-ref (nota de campo)
  - 030: removidos 3 fragmentos, split HOWARD+IBGE, split PINHEIRO+PREFEITURA
  - 040: split 2 refs concatenadas (PREFEITURA+RIBEIRO, SÃO LUÍS+SÃO LUÍS)
  - 042: join 2 pares fragmentados (FREYRE, FRIDMAN)
  - 043: completadas 2 truncadas (CALDEIRA, RIBEIRO JÚNIOR), +2 refs faltantes (O IMPARCIAL, VILLAÇA)
- Total final: 684 refs

### Fase 1.3 — Keywords

- clean_keywords: 2 artigos (023 ALL CAPS, 037 split)
- 034/028 keywords_en contaminação limpa manualmente

### Fase 1.5 — Validação loop

- 030 abstract_en re-extraído (934→3444c, depois trimado a 917c — "Palavras-chave" removido)
- 009 A19 falso positivo (abstract_en completo)

### Fase 1.7 — Autores/afiliações

- 001: André Jorge removido (crédito de foto, não autor)
- 006: Ana Rita Sá Carneiro removida (pertence ao 028)
- 015: "Galvão" restaurado (nome mais completo de outros seminários)
- 016: Juliana Cardoso Nery adicionada como 1ª autora (PPGAU-UFBA)
- 021: +3 autores (Denivaldo Leite, Fernando Laucevicius, Patrizia Cirrincione), Paulo Mauro → Paulo Rodolpho Junior, Rosa Matilde → Rosa Matilde Pimpão Carlos
- 025: Eunice García → Eunice del Carmen García García
- 028: Ana Rita Sá Carneiro adicionada como 1ª autora (UFPE)
- 030: "Oliveisa" → "D'Oliveira"
- 036: "Eliane" → "Etianne"
- 040: Tayana nome completo, Célia Regina Mesquita Santos
- 61 afiliações inseridas
- Dedup: Mariana Bonates (2→1), Ceila Cardoso (2→1)

### Fase 1.9 — ORCID

- Hélio Takashi Maciel de Farias → 0000-0002-0514-6389 (UFRN confirmado)
- ORCID total: 43/73 (58%)

### Fase 1.10 — Revisão LLM final

- 001–011: OK
- 012: keywords_en "São" → "São Paulo"
- 013: OK
- 014: keywords split (1→2 itens PT+EN)
- 015–016: OK
- 017: abstract: nome "Frank Algot Eugen Svensson" preposto
- 018–021: OK
- 022: keywords split (1→3 itens)
- 023: OK
- 024: keywords limpa (contaminação título removida)
- 025: OK
- 026: keywords split (1→3 itens)
- 027–029: OK
- 030: keywords label "key-words:" removido, abstract_en "Palavras-chave /" removido
- 031–032: OK
- 033: keywords split (1→3 itens), abstract_en título removido
- 034–035: OK
- 036: keywords_en garbage "3 1 INTRODUÇÃO" removido
- 037: OK
- 038: keywords split PT+EN (1→4 itens cada)
- 039–044: OK

