# sdrj02 — Status da revisão

Data de início: 2026-03-23
Seminário: 2º Encontro Docomomo Rio, Rio de Janeiro, 2012
Artigos: 19 | Autores: 38 | Seções: 2
ISBN: 978-85-88341-55-5

## Cobertura inicial

| Campo | N/19 | % |
|-------|------|---|
| abstract | 8 | 42% |
| abstract_en | 1 | 5% |
| keywords | 0 | 0% |
| keywords_en | 0 | 0% |
| references | 7 | 37% |
| title_en | 0 | 0% |

## Log progressivo

### §0.0 Checkpoint
- [x] anais.sql dump + rev-status.md criado

### §0.1 Diagnóstico de cobertura
- [x] Artigos (001-008): 8 artigos na seção Artigos, todos com abstract (manual/editorial)
- [x] Pôsteres (009-019): 11 pôsteres na seção Pôsteres, todos sem abstract/keywords/refs
- [x] Keywords 0% em todo o seminário — genuinamente ausentes nos PDFs
- [x] abstract_en: só 004 (ABSTRACT no PDF). Demais: genuinamente ausentes.

### §0.2 Artigos fora do padrão
- [x] 009-019: pôsteres — PDFs gráficos (1 página), sem metadados estruturados
- [x] 011, 017, 018, 019: sem PDF no CD-ROM
- [x] Artigo faltante: Roberto Segre "Uma Fonte Documental Complexa: os Planos de Alinhamento..." — listado no HTML do CD mas PDF inexistente

### §0.3 Fontes
- [x] Fonte primária: CD-ROM interativo (HTML + PDFs)
  - ARTIGOS/: 8 PDFs texto (artigos completos)
  - POSTERS/: 8 PDFs gráficos (poster layout, 1 página cada)
  - 4 pôsteres sem PDF: 011, 017, 018, 019
  - Sem doc/docx

### §0.3b Plumber
- [x] Plumber extraído: 15 PDFs, 12 ok, 3 erros (pôsteres imagem: 010, 013, 014)
- [x] OCR (ocrmypdf + tesseract-por) rodado nos 5 pôsteres problemáticos (010, 013, 014, 015, 016)
- [x] Re-extração plumber pós-OCR: todos 5 ok (155+92+63+235+96 blocos)
- [x] Texto dos pôsteres: legível mas fragmentado (multi-coluna). Sem abstract/keywords/refs estruturados.

### §0.4 Seções
- [x] 2 seções: Artigos (hide_title=1, 8 arts) + Pôsteres (11 arts)
- [x] HTML mostra subcategorias (Premiados, Seleção, Apresentados) — visual, não seções separadas
- [x] Sem eixos temáticos. Correto para o formato do encontro.

### §0.5 Lacunas
- [x] Abstracts 001-008: já no banco (001/004 do PDF, 002-003/005-008 editoriais manuais). Mantidos.
- [x] Refs: 001-005, 007, 008 têm refs no banco (qualidade boa). 006 genuinamente sem refs.
- [x] Pôsteres (009-019): sem metadados extraíveis dos PDFs. Mantidos como estão.
- [x] Nenhuma lacuna preenchível identificada nesta fase.

### §0.6 Metadados EN
- [skip] abstract_en < 30% → SKIP

### §0.7 Metadados ES
- [skip] 0 artigos com locale=es → SKIP

### §0.8 Validate --fix
- [x] 0 problemas encontrados

---

## Fase 1 — Revisão automática

### Títulos (§1.1a)
- [x] Normalização automática: 5 falsos positivos rejeitados (genéricos)
- ✅ sdrj02-004: title "fundação bienal" → "Fundação Bienal" (nome próprio)
- ✅ sdrj02-011: title "esplanada de Santo Antônio" → "Esplanada de Santo Antônio" (topônimo)

### Referências (§1.2)
- [x] clean_references: 0 alterações (60 refs limpas)
- [x] check_references: 0 problemas
- [x] sweep: 004 — 1 lixo grosso removido
- ✅ sdrj02-003: +3 refs da seção REFERÊNCIAS BIBLIOGRÁFICAS p8 (8→11)
- ✅ sdrj02-004: +11 refs da seção Periódicos + 2 livros (9→20)

### Subtítulos (§1.10)
- ✅ sdrj02-013: +subtitle "um acervo em estudo" (do PDF OCR)
- ✅ sdrj02-015: +subtitle "o Teatro do Museu de Arte Moderna do Rio de Janeiro" (do PDF OCR)

### Notas
- sdrj02-010: discrepância título catálogo ("Banco de dados em Arquitetura") vs PDF ("O Futuro do Passado"). Mantido catálogo.
- sdrj02-008: "saúde" mantido lowercase (genérico, não nome próprio)

### ORCID (§1.9)
- ✅ Rebeca Waltenberg: 0000-0001-8306-8411 (exact match)
- ✅ Débora Zukeran: 0009-0008-0946-4262 (Débora Picorelli Zukeran, Birmingham)
- ✅ Thaís Fernanda Bette: 0000-0002-9934-5206 (Thaís Bette)
- Cobertura: 21/38 (55%)

### Dedup (§1.8)
- [x] 0 merges

### Validate loop (§1.5)
- [x] 0 issues, convergiu em 1 iteração
