# sdbr09 — Status do pipeline automático (Fases 0–2)

Data: 2026-03-09
Pipeline: `docs/pipeline_revisao.md` Fases 0–2

## Diagnóstico inicial (Fase 0)

- 170 artigos, 20 mesas (document_type='mesa')
- DVD: `/media/danilomacedo/anais docomomo/DVD/` — 171 PDFs (28 mesas + 143 artigos + pôsteres)
- Fontes originais (.doc): `~/Dropbox/_docomomo/seminarios/2011-Docomomo-Bsb/Docomomo_ANAIS/` — 168 .doc/.docx

## Fase 0.1 — Seções e mesas

### Mesas identificadas (20 artigos)
- ✅ 14 artigos com "Mesa" no título identificados automaticamente
- ✅ 6 artigos curtos (< 6000 bytes) identificados por tamanho de arquivo
- ✅ 20 artigos marcados document_type='mesa'

### Seções criadas (29 seções)
- ✅ 28 mesas (M01–M28) criadas a partir dos nomes do DVD
- ✅ 1 seção Pôsteres (PB) criada
- ✅ IDs 191–219

### Artigos atribuídos a seções (170/170)
- ✅ 165 artigos mapeados automaticamente por hash parcial (PDF ↔ DVD)
- ✅ 4 artigos mapeados manualmente (sdbr09-028→M14, sdbr09-067→M03, sdbr09-106→M28, sdbr09-133→PB) — PDFs não estavam no DVD (re-exportados pelo editor)
- ✅ sdbr09-089→M02 atribuído manualmente (hash não bateu)

## Fase 0.3 — Locale

- ✅ sdbr09-027: locale corrigido pt-BR → es (artigo em espanhol)

## Fase 0.4 — Abstracts extraídos de fontes/

### Primeira rodada (pdftotext)
- ✅ 12 abstracts extraídos de fontes/ (pdftotext)
- ✅ 10 conjuntos de keywords inseridos

### Segunda rodada (validação + limpeza)
- ✅ 31 abstracts corrigidos (KW_LEAKED, headers do seminário, EN_IS_PT, swaps PT↔EN)
- ✅ 14 abstracts com fragmento de header no meio/fim do texto limpos
- ✅ 5 abstracts com header dentro do texto limpos

### Terceira rodada (extração de .doc via LibreOffice)
- ✅ 16 abstracts extraídos de arquivos .doc originais (melhoria significativa sobre pdftotext):
  - sdbr09-015, 024, 036, 040, 042, 067, 079, 088, 101, 115, 132, 143, 145, 152, 165, 170

### Quarta rodada (extração de .doc — artigos restantes)
- ✅ sdbr09-039: abstract PT + EN extraídos de .doc (Marina Grinover, Lina Bo Bardi)
- ✅ sdbr09-050: abstract PT + EN + title_en + subtitle_en extraídos de .rtf (Regina Lustoza)
- ✅ sdbr09-053: abstract_en atualizado de .doc (Ruth Verde Zein)
- ✅ sdbr09-169: abstract PT + EN + keywords_en extraídos de .doc (Maria Beatriz Cappello)
- ✅ sdbr09-100: já tinha abstract mais longo no banco (Anna Beatriz Galvão) — mantido
- ✅ sdbr09-103: já tinha abstract mais longo no banco (Leonardo Castriota) — mantido
- ✅ sdbr09-124: já tinha abstract mais longo no banco (Beatriz Bueno) — mantido
- ⚠️ sdbr09-037: .doc não encontrado (só PDF no ANAIS) — abstract do pdftotext mantido

## Fase 0.5 — Validação de abstracts

### Problemas resolvidos
- ✅ sdbr09-115: abstract_en era em espanhol → movido para abstract_es (artigo locale=es)
- ✅ sdbr09-165: abstract_en era duplicata em PT → limpo

### Problemas aceitáveis (não bloqueantes)
- ℹ️ sdbr09-015: TITLE_IN_ABSTRACT falso positivo (abstract começa com "O projeto do Palácio Farroupilha...")
- ℹ️ sdbr09-170: TITLE_IN_ABSTRACT falso positivo (nome "Archimedes Memória" no título e no abstract)
- ℹ️ sdbr09-094: keywords_en sem abstract_en (artigo sem seção EN no PDF)
- ℹ️ sdbr09-126: keywords_en sem abstract_en (artigo sem seção EN no PDF)

## Fase 0.6 — Metadados EN

- ✅ title_en + subtitle_en inseridos para sdbr09-046, sdbr09-050
- ✅ `extrair_metadados_en.py --dry-run` rodado: apenas 12 extrações, maioria lixo (headers do seminário contaminam os fontes). Não aplicado.
- ℹ️ title_en em massa não é viável pelo extrator automático neste seminário — headers do pdftotext confundem a extração

## Fase 1.0 — Dicionário

- ✅ `seed_authors.py` rodado (1 autor novo)
- ✅ `seed_titles.py --apply` rodado (36 entradas novas)
- ✅ `dump_db.py` rodado

## Fase 1.1a — Normalização de títulos PT

- ✅ Primeira passada: 72 títulos normalizados
- ✅ Segunda passada (após seed): 35 títulos adicionais normalizados

## Fase 1.1b — Normalização de títulos EN

- ✅ `normalizar_titulos_en.py --slug sdbr09` rodado: 1 subtitle_en normalizado ("review the concepts" → "Review the Concepts")

## Fase 1.1c — Revisão LLM de títulos

- ❌ Revisão LLM de títulos PT — não rodada (fase opcional, para revisão humana)
- ❌ Revisão LLM de títulos EN — não aplicável (só 2 title_en)

## Fase 1.2 — Referências

### Primeira rodada (já no banco)
- ✅ 51 artigos com 898 refs (extraídas pelo pipeline original)

### Segunda rodada (extração de .doc via LibreOffice — batch)
- ✅ 145 .doc/.docx/.rtf convertidos para txt
- ✅ 132 mapeados a artigos do banco (SequenceMatcher >= 0.55)
- ✅ 76 artigos ganharam 907 refs novas extraídas dos .doc
- ✅ 2 matches errados excluídos (sdbr09-120, sdbr09-123 — doc não batia com autor)
- ✅ 59 backfills de autor aplicados, 4 underscores split
- ✅ 1 ref concatenada corrigida (sdbr09-136: XAVIER+BRITO)

### Terceira rodada (extração individual de .doc e fontes/)
- ✅ sdbr09-056: 16 refs (Paviani, .doc)
- ✅ sdbr09-081: 25 refs (Maciel, .doc)
- ✅ sdbr09-084: 15 refs (Santos/Gandolfi, .doc)
- ✅ sdbr09-120: 6 refs (Waihrich/Tolotti, .doc)
- ✅ sdbr09-123: 1 ref (Cabral, .doc)
- ✅ sdbr09-129: 9 refs (Schvasberg, .doc)
- ✅ sdbr09-048: 1 ref (Zakia, .doc)
- ✅ sdbr09-003: 11 refs (Jucá Neto, .doc — marcador "REFERÊNCIA BIBLIOGRÁFICA" singular)
- ✅ sdbr09-030: 7 refs (Koch, .doc — marcador "FUENTES CONSULTADAS")
- ✅ sdbr09-009: 19 refs (Zein/Boscardin, fontes/ — .doc não localizado)
- ✅ sdbr09-028: 1 ref (Raffa/Cirvini, fontes/ — .doc não localizado)
- ✅ sdbr09-037: 34 refs (Marques, fontes/ — .doc não localizado)
- ✅ sdbr09-097: 16 refs (Schlee, fontes/ — .doc só PDF)
- ✅ sdbr09-106: 15 refs (Silva, fontes/ — .doc não localizado)
- ✅ sdbr09-112: 10 refs (Oliveira, fontes/ — .doc não localizado)

### Resultado final das referências
- ✅ `clean_references.py`: 13 backfills adicionais
- ✅ `check_references.py --summary`: **0 problemas / 1996 refs**
- **142/148 artigos com refs (96%)**

### 4 artigos sem referências (verificados — não são mesas)
- sdbr09-010: artigo argentino, sem lista de refs no .doc (termina sem bibliografia)
- sdbr09-060: texto ensaístico de Francisconi, sem lista de refs
- sdbr09-071: texto curto sobre o Edifício A Tarde, sem lista de refs
- sdbr09-115: artigo em espanhol, usa notas de rodapé (sem lista separada)

### Mesas e resumos atualizados
- ✅ sdbr09-146 marcado como document_type='mesa' (texto de abertura de sessão, Ana Fernandes)
- ✅ sdbr09-156 marcado como document_type='mesa' (Moreira é chair da M12, .doc prefixo 000)
- ✅ sdbr09-160 marcado como document_type='mesa' (Galbinski é chair da M15, .doc prefixo 000)
- ✅ sdbr09-130 marcado como document_type='resumo' (só abstract no PDF e no .doc — "sylvia_ficher_abstract.doc")

## Fase 2 — HTML de revisão

- ✅ `gerar_revisao_html.py sdbr09` rodado → `revisao/revisao-sdbr09.html`
- ✅ 170 artigos, 29 seções

## Resumo de contadores finais

| Campo | Preenchidos | Total* | % |
|-------|------------|--------|---|
| Artigos | 170 | 170 | 100% |
| Mesas | 23 | — | — |
| Resumos | 1 | — | — |
| Seções | 170 | 170 | 100% |
| abstract | 145 | 146 | 99% |
| abstract_en | 131 | 146 | 90% |
| keywords | 144 | 146 | 99% |
| title_en | 2 | — | — |
| references | 142 | 146 | 97% |

*Excluindo 23 mesas e 1 resumo.

## Fase 1.1a — Revisão LLM de títulos PT

Data: 2026-03-09

- ✅ 170 artigos revisados (146 artigos + 23 mesas + 1 resumo)
- ✅ 100 correções aplicadas (títulos e subtítulos)
- ✅ dict.db atualizado: 2 nomes adicionados (Tochetto, Medaglia)
- ✅ HTML regenerado, banco exportado

### Categorias de correções
- **Descritiva + toponímico** (18): "Arquitetura Moderna em [cidade]" → minúscula
- **Termos genéricos** (35): obra, conservação, intervenção, arquitetônica, metropolitana, etc.
- **Espanhol: la/al minúscula** (16): artigos em espanhol com "La" maiúscula
- **Subtítulo inicia minúscula** (8): subtítulos que começavam com maiúscula indevida
- **Nomes próprios** (12): edifícios, instituições, logradouros (Praça Ernesto Tochetto, Cemitério São João Batista, etc.)
- **Demônimos** (4): carioca, cearense, paulista → minúscula
- **Títulos profissionais** (3): professor, arquiteto → minúscula
- **Outros** (4): Lucio Costa sem acento, travessão, etc.

### Detalhes em `revisao/sdbr09-titulos-aprendizado.json`

## Pipeline automático — CONCLUÍDO

Todas as fases 0–2 executadas. Pendências para a revisão humana (Fase 3):

1. **title_en**: artigos do sdbr09 não têm título em inglês nos originais (verificado em amostra de .doc)
2. **4 artigos sem refs**: verificados individualmente — sem lista de referências nos originais (notas de rodapé ou sem bibliografia)
3. **sdbr09-037**: abstract possivelmente truncado (.doc não localizado)

## Fase 4 — Revisão humana aplicada (2026-03-09)

### Keywords EN inseridas
- ✅ sdbr09-019: 5 keywords_en
- ✅ sdbr09-076: 4 keywords_en
- ✅ sdbr09-006: 5 keywords_en
- ✅ sdbr09-007: 3 keywords_en

### Abstracts inseridos/corrigidos
- ✅ sdbr09-017: abstract limpo (removido lixo de currículo)
- ✅ sdbr09-021: abstract_es + abstract_en inseridos
- ✅ sdbr09-050: abstract_en inserido
- ✅ sdbr09-126: abstract_en inserido
- ✅ sdbr09-094: abstract_en inserido
- ✅ sdbr09-010: abstract_es + keywords_es inseridos, keywords PT corrigidas (eram ES)
- ✅ sdbr09-115: verificado — abstract_es já correto, locale=es, sem duplicação

### Referências — backfill corrigido (via fix do extract_author + re-run clean_references)
- ✅ sdbr09-026, 140, 008, 090, 017, 093, 039, 113, 055, 070, 104: backfill aplicado

### Referências — concatenadas separadas (re-extração de .doc via LibreOffice)
- ✅ sdbr09-006, 128, 028, 073, 139, 087, 052, 032, 059, 048, 027, 118, 104: refs re-extraídas

### Referências — adições/substituições específicas
- ✅ sdbr09-124: 3 refs adicionadas
- ✅ sdbr09-119: 1 ref adicionada (BONDUKI)
- ✅ sdbr09-079: 2 refs adicionadas (NIEMEYER, CARVALHO)
- ✅ sdbr09-121: 9 refs substituídas (lista completa do rev.md)
- ✅ sdbr09-021: 2 refs adicionadas (Candela, Cardiel Reyes)

### Referências — extração de fonte
- ✅ sdbr09-123: refs extraídas da última página (.doc)
- ✅ sdbr09-031: refs extraídas após "Bibliografía" (.doc)

### Referências — remoção
- ✅ sdbr09-077: removidas "fontes das figuras" do final
- ✅ sdbr09-065: removido crédito de ilustrações do final

### Correções de código (clean_references.py)
- ✅ `extract_author()`: regex expandido (parênteses, &, ;, hífen, apóstrofo)
- ✅ Novo padrão para `AUTHOR (YEAR) Title` (sdbr09-140, ~50 refs afetadas)
- ✅ Causas documentadas no docstring e na memória

### Fontes .doc convertidas
- ✅ 16 arquivos .txt salvos em `nacionais/sdbr09/fontes_doc/`

### Resultado final
- **143/148 artigos com refs** (excluindo 22 mesas + 1 resumo = 147 artigos; 4 sem refs confirmados)
- **0 problemas / 2151 refs** (check_references.py)
- **abstract_es**: 3 artigos (010, 021, 115)
- **keywords_es**: 1 artigo (010)
