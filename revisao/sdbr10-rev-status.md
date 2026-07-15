# sdbr10 — Status da revisão

## Ficha

- **Seminário**: X Seminário Docomomo Brasil
- **Tema**: Arquitetura Moderna e Internacional: conexões brutalistas 1955-75
- **Local**: Curitiba, PUCPR
- **Data**: 15-18 out. 2013
- **Artigos**: 118
- **Idiomas**: pt-BR (97), es (14), en (7)

## Pipeline automático (2026-03-09)

### Fase 0 — Diagnóstico e preparação

| Etapa | Status | Resultado |
|-------|--------|-----------|
| 0.1 Diagnóstico | ✅ | 118 artigos, seminário internacional (Brutalismo) |
| 0.2 Fora do padrão | ✅ | — |
| 0.3 Fontes | ✅ | 118 .txt extraídos via pdftotext |
| 0.4 Preencher lacunas | ✅ | abstracts, keywords, refs extraídos |
| 0.5 Validar abstracts | ✅ | 24 abstract_en inválidos (PT no campo EN) → NULL |
| 0.6 Extrair metadados EN | ✅ | 4 title_en válidos (55 garbage limpos) |

### Fase 1 — Revisão automática

| Etapa | Status | Resultado |
|-------|--------|-----------|
| 1.0 Seed dict | ✅ | dict.db atualizado (+7 expressões) |
| 1.1a Normalizar títulos PT (script) | ✅ | 16 títulos normalizados |
| 1.1a Revisão LLM títulos PT | ✅ | 43 correções: obra→minúsc, nomes próprios, subtítulos novos, truncados |
| 1.1b Normalizar títulos EN | ✅ | 12 normalizados, depois 55 garbage limpos |
| 1.1c Revisão LLM títulos EN | ✅ | 4 title_en verificados, subtítulos EN adicionados |
| 1.2 Referências (clean+check) | ✅ | 2274 refs, 53 problemas (2.3%) |
| 1.3 Aplicar correções | ✅ | — |
| 1.4 Validação metadata (1ª rodada) | ✅ | 179 issues |
| 1.4b Correção dos issues | ✅ | 23 abstract_en extraídos, 17 backfills, 2 keywords_es, 5 não-refs removidas, 3 refs split |
| 1.4c Validação metadata (2ª rodada) | ✅ | 111 issues restantes (102 são refs longas de footnotes) |
| 1.4d fix_validation_issues.py --loop | ✅ | 1 abstract_en, 40+ refs split, 45+ notas removidas, convergiu em 2 iterações |
| 1.4e Validação final | ✅ | 9 issues restantes (todos dados ausentes no PDF, não erros) |
| 1.4f Sweep refs (fragmentos+endnotes) | ✅ | 18 fragmentos juntados, 26 endnotes limpas, 33 endnotes removidas, 82 não-refs removidas, 2 concat. manuais |
| 1.4g Validação pós-sweep | ✅ | 8 issues restantes (todos dados ausentes no PDF) |

### Fase 1.5 — Sessões

| Etapa | Status | Resultado |
|-------|--------|-----------|
| 1.5a Obter programa | ✅ | PDF do programa das sessões (xdocomomobrasil.com.br) |
| 1.5b Mapear artigos→sessões | ✅ | 100/118 mapeados em 26 sessões (18 sem sessão no programa) |
| 1.5c Criar seções no DB | ✅ | 26 sections criadas, 100 articles com section_id |

### Fase 2 — HTML de revisão

| Etapa | Status |
|-------|--------|
| 2.0 Gerar HTML | ✅ |

## Estatísticas finais (pós-pipeline automático)

- **abstract**: 118/118 (100%)
- **abstract_en**: 114/118 (97%) — 4 genuinamente sem seção Abstract no PDF
- **keywords**: 112/118 (95%)
- **keywords_es**: 11/14 artigos ES (79%) — 3 genuinamente sem palabras clave no PDF
- **subtitle**: 46/118 (39%)
- **title_en**: 4/118 (3%)
- **references**: 113/118 (96%), 2276 refs, 1.4% problemas residuais
- **Sem refs (footnotes)**: sdbr10-048, 052, 073, 076, 116

## Issues residuais (dados ausentes no PDF — não erros)

| Categoria | Qtd | Descrição |
|-----------|-----|-----------|
| A02 kw_en sem abs_en | 4 | PDFs sem seção Abstract (018, 026, 035, 051) |
| A01 abs_en sem kw_en | 2 | sdbr10-024, sdbr10-100: Keywords vazia no PDF |
| A08 fontes: Keywords | 1 | sdbr10-024: marcador "Keywords:" seguido de campo vazio no PDF |
| A03 abs_es sem kw_es | 1 | sdbr10-096: sem Palabras clave no PDF |

## Dict additions (7 expressões)

- Caixa Econômica Federal, Universidade de Brasília, Brutalismo Paulista
- Modernismo Paulista, Ladeira da Misericórdia, Clube do Professor Gaúcho
- Companhia Hidro Elétrica do São Francisco

## Sessões (26 sessões, 100 artigos mapeados)

| Sessão | Nome | Artigos |
|--------|------|---------|
| S01 | Ética & Estética | 5 |
| S02 | Do Norte | 4 |
| S03 | Do Sul | 4 |
| S04 | Fronteiras | 3 |
| S05 | Miami Modern | 4 |
| S06 | Casas (I) | 4 |
| S07 | Judiciárias | 3 |
| S08 | Universitárias | 3 |
| S09 | Casas (II) | 6 |
| S10 | Institucionais | 4 |
| S11 | Grandes Estruturas | 3 |
| S12 | Conexões | 5 |
| S13 | Caminhos Brutalistas | 5 |
| S14 | Conexões Internacionais | 4 |
| S15 | Arquitetos | 5 |
| S16 | Habitação Coletiva | 4 |
| S17 | Brutalismo em Brasília: passado e presente (I) | 0 (*) |
| S18 | Escolas | 4 |
| S19 | Forma Plástica | 4 |
| S20 | Artigas | 4 |
| S21 | Brutalismo em Brasília: passado e presente (II) | 1 |
| S22 | Preservação | 4 |
| S23 | Lina's | 4 |
| S24 | Brutalismo em Curitiba | 5 |
| S25 | Tectônicas | 4 |
| S26 | Expressão e Construção | 4 |

(*) S17: os 4 papers do programa (Rossetti, Schlee, Macedo/Elcio, Mahler) não foram publicados nos anais.

### 18 artigos sem sessão no programa

sdbr10-004, 007, 011, 014, 022, 033, 034, 042, 047, 048, 049, 061, 069, 086, 096, 099, 108, 115

## Pendente para revisão humana (Fase 3)

- Conferir 46 subtítulos
- Verificar locale dos 14 artigos em espanhol e 7 em inglês
- Conferir nomes próprios (González de León, Hestnes Ferreira, etc.)
- 6 artigos sem keywords (sdbr10-006, 009, 023, 039, 051, 098)
- 4 artigos sem abstract_en (sem seção Abstract no PDF)
- ~31 refs marcadas como possíveis não-refs pelo check_references (refs truncadas/ambíguas)
- 18 artigos sem sessão — verificar se podem ser atribuídos tematicamente
