# Devlog — Anais Docomomo Brasil

Registro cronológico das sessões de trabalho. Movido do CLAUDE.md para reduzir consumo de contexto.

---

## Devlog

### 2026-04-06 — sdbr16 produção Zenodo + deploy + afiliações

**Zenodo (274 artigos):**
- upload_zenodo.py --seminar sdbr16 --community docomomobr
- Bug corrigido: IPv6 SYN-SENT no upload_zenodo.py (mesmo fix de IPv4 do fetch_orcid.py)
- 273 artigos publicados, 0 erros, todos na community docomomobr
- 60 skips (35 mesas + 15 resumos + 10 conferências sem PDF)

**Volume completo (373 MB):**
- Upload via curl (API InvenioRDM: draft → file upload → commit → publish)
- DOI: 10.5281/zenodo.19435087 | URL: https://zenodo.org/records/19435087
- Checksum verificado: md5:01b39764fac82e50fe07303bc75d3a61
- Submetido e aceito na community docomomobr

**Títulos/subtítulos (complemento):**
- 11 splits adicionais: 003, 020, 037, 042, 053, 085, 184, 201, 218, 238, 253
- 2 mesas corrigidas: m01 (split), m06 (split)
- Typo corrigido: m09 "tranformação" → "transformação"
- 3 artigos corrigidos no Zenodo (fix_zenodo_metadata.py): 003, 020, 053

**Afiliações (complemento):**
- 34 afiliações extraídas dos docx (python-docx) + normalizadas para sigla
- 41 propagadas de outros artigos do mesmo autor dentro do sdbr16
- 9 revertidas (fonte era de outro seminário — só usar fontes do próprio sdbr16)
- sdbr16-037 reclassificado: resumo → artigo (tinha PDF de 3.7 MB)
- Restam 53 sem afiliação (maioria mesas/resumos sem docx)

**Deploy:**
- sdbr16 adicionado à lista SEMINARS no workflow deploy.yml
- Editorial atualizado: 47 seminários, 3.100 artigos, 2.714 autores
- Capa sdbr16.png adicionada a site/static/img/capas/
- Release v1.2 criada → dataset Zenodo atualizado automaticamente

### 2026-04-05 — sdbr16 revisão completa (references, abstracts, rev.md, afiliações, títulos, ORCIDs)

**Referências (pipeline temporário `revisao/sdbr16-references-pipeline.md`):**
- clean_references + sweep_refs + backfills executados
- 10 artigos reclassificados como endnotes-only (R11) → NULL
- 7 artigos com refs truncadas/fragmentadas reconstruídas do plumber/docx
- 1 sweep over-removal corrigido (sdbr16-181: 7 web refs restauradas)
- Estado final: 263 artigos com refs (2461 refs, avg ~9.4/artigo)

**Abstracts (pipeline temporário `revisao/sdbr16-abstract-pipeline.md`):**
- 3 abstracts truncados (IDML) corrigidos: 042, 172, 173
- sdbr16-m25: abstract removido (era de outro artigo — Zalszupin)
- sdbr16-106: abstract_es cortado (ES+PT colados, 3910→1949c)
- sdbr16-139: abstract_es removido (contaminação do sdbr16-006 via IDML)
- sdbr16-174, 229, 193: abstract→NULL (locale=en, abstract_en mantido)

**Revisão humana (`revisao/sdbr16-rev.md` — 22 itens):**
- Títulos corrigidos: m05 (nossa↓), 038 (edifícios-sedes), 041 (split), 282 (título trocado)
- Refs: 088 (3→5), 012 (4 split), 017 (11→13), 168 (5→13), 007 (reextraídas, 15)
- Refs R11: 010, 049 (NULL — endnotes only), 139 (NULL — contaminação)
- Refs: 223 (3→9 do docx)
- Abstracts: 197 (junk removido), 233 (refs coladas removidas), 143 (link removido)
- sdbr16-172: abstract limpo + movido para seção 369

**Afiliações (normalização):**
- 242 variantes → 120 siglas normalizadas (formato UNIDADE-UNIVERSIDADE)
- 73 afiliações com bio removida (mestrando, doutorando, professor, etc.)
- Padrão: FAU-USP, PROPAR-UFRGS, PROURB-FAU-UFRJ, etc.

**Títulos/subtítulos (separação):**
- 182 separações aplicadas (`: `, `. `, ` — `, semânticas)
- Subtítulos: primeira letra minúscula (exceto nome próprio/sigla)

**Conferências preparatórias (10 entradas):**
- Seção "Conferências Preparatórias" (seq=-1, antes das mesas)
- 7 com YouTube embed, 3 presenciais sem vídeo
- Links verificados contra títulos no YouTube (todos corretos)
- Dedup: Fernando Lara (→3356), Nivaldo Andrade Jr. (→1351), Paulo Vidal (→3737 Ribeiro)
- ORCIDs: Zaída Muxí, Fernando Lara, Nivaldo Andrade, Kathrin Rosenfield

**ORCIDs (busca geral sdbr16):**
- fetch_orcid.py --search --slug sdbr16 (OpenAlex + ORCID API + Crossref)
- Bug corrigido: IPv6 travava conexões (forçado IPv4), URL encoding de acentos
- 18 confirmados automaticamente + 23 revisados + 13 verificados = 300/418 (72%)
- 1 falso positivo removido: Marcelo Ferraz (homônimo UFG, não o arquiteto)
- 1 falso positivo removido: Fabiano Maciel (homônimo, cineasta sem ORCID)

**Dedup autores:**
- dedup_authors.py: 3 merges (1 variante + 2 cross-familyname)
- Manuais: Fernando Lara, Nivaldo Andrade Jr., Paulo Vidal Leite Ribeiro

**Hugo:**
- Open Graph / Twitter Cards adicionados às páginas de seminário (list.html)
- section_label=NULL para sdbr16 (mesas não numeradas)
- db2hugo.py + gerar_revisao_html.py: ordenação mesa-first (CASE WHEN id LIKE '%-m%')
- db2hugo.py: suporte a YouTube embed para conferências (document_type='conferencia')

**Cobertura final sdbr16:**
| Campo | Valor |
|-------|-------|
| Total | 333 (270 artigos + 15 resumos + 35 mesas + 10 conferências + 3 sem texto) |
| Abstracts | 309/323 (96%) |
| Keywords | 297/323 (92%) |
| Referências | 263/288 não-mesa (91%) |
| ORCIDs | 300/418 autores (72%) |
| Sessões | 40 (39 mesas + 1 conferências preparatórias) |

### 2026-03-31 — sdbr16 pipeline de tratamento (16º Seminário, Porto Alegre 2025)

**Aquisição e organização:**
- 2 lotes de docx: PRONTOS (177) + RECEBIDOS (31) = 272 docx, 271 PDFs
- Numeração final 001–285 com lacunas (IDs não usados: 037=resumo, 19 sem texto)
- Caderno de resumos: `fontes/caderno-resumos/Docomomo_Brasil_04.pdf` (362 páginas)
- Volume completo: `fontes/01_ANAIS_DOCO_R01.pdf`
- Programação definitiva: `fontes/programaçao_definitiva.pdf` (29 páginas, 285 entradas)
- 3 arquivos com soft-hyphen no nome corrigidos (146, 169, 186)
- Artigo 170 docx corrompido (XML malformado) — metadados extraídos direto do XML
- Artigo 084: título no docx difere da programação (autor mudou título)

**Extração de metadados:**
- Títulos e autores: python-docx para 272 docx + caderno para resumo-only
- Abstracts: docx + caderno de resumos (14 complementados) + 1 fornecido pelo usuário (008)
- 4 artigos sem abstract, 21 sem keywords, 5 sem referências
- Keywords: docx (249) + caderno + docx espanhol keywords_es (7 locale=es)
- Referências: 265/270 artigos, 2130 refs, 0.3% problemas
  - Fontes: seção REFERÊNCIAS, Word endnotes XML, NOTAS inline
- 35 textos de mesa (intros dos coordenadores) extraídos do caderno
- 15 resumos (artigos da programação sem texto completo)

**Sessões (39 sessões):**
- 270/270 artigos atribuídos a sessões
- Fontes: programação definitiva (match por título+autor), caderno de resumos (fallback)
- 3 sessões duplicadas unificadas (PILOTIS, TRANSFORMAÇÃO, ESPAÇOS DO ÓCIO)
- 1 encoding fix (POSSÏVEIS → POSSÍVEIS)
- Coordenadores extraídos do volume

**Normalização:**
- Travessões: 6 títulos (` - ` → ` — `)
- Capitalização: normalizar_maiusculas.py (3 artigos) + revisão LLM (70+ correções)
  - Nomes próprios, sobrenomes, siglas, instituições, topônimos, publicações
  - Regressões corrigidas (Global South, Pahlavi)
- Referências: clean_references.py (0 mudanças — refs já limpas)
- Validação: validate_metadata.py (85 issues/report, 0 auto-fixes)
- Revisão HTML gerada: `revisao/revisao-sdbr16.html`

**Verificação cruzada:**
- Programação (285) = DB artigos (270) + resumos (15) = 285
- Arquivos (271 docx) = DB artigos (270) + 1 resumo com docx (037)
- 3 artigos na programação sem texto nem resumo (Cotrim, Borges, Blanco Vencio) → registrados como resumos

**Cobertura final:**
| Campo | Valor |
|-------|-------|
| Total | 270 artigos + 15 resumos + 35 mesas = 320 |
| Abstracts | 266/270 (98%) — 4 genuinamente sem |
| Keywords (any) | 249/270 (92%) — 21 sem no docx |
| Referências | 265/270 (98%), 2130 refs — 5 sem referências |
| Sessões | 39, 100% artigos atribuídos |
| Autores únicos | 446 |
| Locales | pt-BR: 263, es: 7 |
| ISBN | 978-65-993024-6-6 |

**Metadados EN:** N/A (organização não exigiu abstract/title em inglês)

**Pendências:**
- PDFs individuais não gerados (artigos em docx apenas)
- Zenodo upload pendente (depende dos PDFs)
- NÃO publicar no site até comando explícito do usuário

### 2026-03-28 — sdsp09 revisão completa + metadados ES sdsp07/08/09 + ORCID global

**sdsp09** (27 artigos, 52 autores, 1 seção "Artigos Completos"):
- Cobertura: abstract 100%, abs_en 100%, kw 96% (015 ausente no PDF), refs 100%, ORCID 81%
- Fonte: plumber (27 JSONL), artigos trilíngues (PT/EN/ES)
- OCR sem espaços em 6 artigos (headings concatenados) — reconstrução manual LLM
- title_en: 26/27 (025 sem EN no PDF), 11 extraídos manualmente
- Refs: 010 (16) e 025 (17) inseridas do plumber (não capturadas na importação original)
- Revisão humana: 4 correções (patrimônio↓, Litoral↑, Santista↑, arquitetura↓, 1 ref espúria)
- Autor 1047: familyname "Junior" → "Simões Junior" (afeta sdsp09-013 e sdbr04-021)

**Metadados ES — sdsp07/08/09 (110 artigos):**
- Extração de title_es, subtitle_es, abstract_es, keywords_es de plumber
- sdsp07: 43/43 completo; sdsp08: 36/40 (4 homenagens); sdsp09: 26/27
- 5 agentes Opus verificaram todos 110 artigos um a um, 32 correções
- gerar_runner.py: step 0.7 corrigido (ES independe do locale do artigo)

**ORCID global (1149 autores buscados):**
- Busca OpenAlex/Crossref/ORCID API para todos os autores sem ORCID
- 57 novos ORCIDs aplicados (29 confirmados + 28 triagem LLM)
- Cobertura: 1375/2465 autores (55.8%)

**dict:** +santista (gentílico), +Pae Cará, +Baixada Santista, +Casa de Saúde (expressão), +Armazém 7 (expressão), -restauração, -imóveis (stopwords)

**45/45 seminários revisados** — todos os seminários do pipeline concluídos.

### 2026-03-25 — sdnne04 revisão completa (Fases 0-3)

**sdnne04** (45 artigos, 83 autores, 3 eixos temáticos — A arquitetura moderna como projeto, Narrativas historiográficas, Experiências de conservação e transformação):
- Cobertura: abstract 100%, abs_en 98%, kw 98%, kw_en 96%, refs 100%, ORCID 55%
- Fonte: CD-ROM (sem doc/docx), plumber (5785 blocos)
- 269 correções (260 auto + 9 humanas)
- 11 normalizer + 34 correções LLM títulos vs PDF
- Refs: 0→192 (backfill plumber) → 677 (clean) → 651 (sweep) → 642 (LLM review)
- 9 dedup merges manuais (givenname prefixo: Carrilho, Gonsales, Lopes, Machado, Meneses, Poppe, Santos, Silva, Vidal)
- 4 ORCIDs novos (Gustavo Sobral, Marília Brito, Regina Cavalcante, Isadora Paiva)
- 2 abstracts truncados completados do plumber (039: 1029→2090, 043: 1235→2299)
- Revisão humana: 5 genéricos no dict (obra, circulação, tessituras/tectônicas, envelopado, mágica), 2 expressões consolidadas (Moderna, Moderno — regra de/no)

**dict — 20 genéricos removidos, 18 STOPWORDS adicionados:**
- obra, circulação, tessituras, tectônicas, envelopado, mágica, esperança, presente, desenho, conservação, apartamentos, arenas, desportivas, iconográfico, escritório, professor, referência, intervenção, escolar + 4 stale (Bienal, Centenário, Esplanada, arquitetônica)

**validate_metadata.py — novo check A33:**
- Detecta abstract truncado comparando DB com plumber (prefix match: DB é início de bloco mais longo)
- Evita falsos positivos de A32 (ratio) quando plumber block inclui corpo do artigo
- 0 falsos positivos nos seminários revisados (sdnne03/sdnne04/sdbr08)

**pipeline_revisao.md:**
- §1.1a: retroalimentação do dict OBRIGATÓRIA na hora da correção LLM (não na Fase 3)
- Regra toponímico clarificada: "de/do/da + lugar" → minúscula, "no/na/em + lugar" → maiúscula

**Engenharia (3 scripts corrigidos):**
- seed_titles.py: try/finally no --apply (DB connection leak)
- dedup_authors.py: try/finally no load_pilotis() (DB connection leak)
- validate_metadata.py: block.get('text','') no A33 (KeyError uncaught)

### 2026-03-24 — sdnne03 revisão completa (Fases 0-3)

**sdnne03** (41 artigos, 79 autores, 4 seções genéricas — Seção 1-4, hide_title=1):
- Cobertura: abstract 100%, abs_en 95%, kw 95%, kw_en 90%, refs 100%, ORCID 56%
- Fonte: CD-ROM (sem doc/docx), plumber (6261 blocos)
- 245 correções automáticas, 0 humanas
- 22 títulos corrigidos vs PDF (4 subtítulos adicionados: 013/019/020/027)
- 10 normalizer, 7 reversões (Presente, preservação, Tectônica, X, Vida, Residencial, Nova)
- Refs: 677→710 (sweep -20 junk, LLM +53 correções em 24 artigos)
- 13 autores corrigidos (nomes, familynames, 5 ordens), 61 afiliações inseridas
- 8 abstract_en extraídos do plumber, 3 abstract_en via loop, 2 abstract_en trimmed (contaminação)
- 2 ORCIDs novos (Amélia Reynaldo, Mércia Parente Rocha)
- Seções genéricas (Seção 1-4): sem nomes temáticos nas fontes (rodapé só tem subtítulo do seminário)

**dict — 5 genéricos adicionados ao STOPWORDS:**
- antiga, exposições, marítima, migrantes, severinos

**Engenharia (46 scripts auditados):**
- 1 HIGH: _post_pipeline.py os.system→subprocess.run (command injection)
- 8 MEDIUM: try/finally em _post_pipeline, split_concat_references, expand_initials, fetch_orcid, dedup_authors, gerar_revisao_html

### 2026-03-24 — sdnne02 revisão completa (Fases 0-3)

**sdnne02** (33 artigos, 44 autores, 1 seção — Artigos Completos):
- Cobertura: abstract 100%, abs_en 93%, kw 96%, kw_en 78%, refs 100%, ORCID 70%
- Fonte: RAR/CD-ROM (sem doc/docx), plumber (5329 blocos)
- 143 correções (140 auto + 3 humanas)
- 20 abstract_en extraídos do plumber (Caso 3: sem marcador "Abstract" explícito)
- 4 abstract_en limpos (contaminação com legendas/notas de figuras)
- 11 títulos corrigidos vs PDF + 13 reversões do normalizador
- Refs: 611→620 (55 correções LLM: splits, joins, missing, truncated, hyphens)
- 033 reclassificado como mesa (texto de conferência, sem abstract/kw/refs)
- 4 afiliações corrigidas (009 Miranda FAU-UFPA, 015 Costa/Rodrigues Filho UnB, 029 Zein UPM)
- Revisão humana: 3 correções (005 abstract_en lixo, 009 subtitle, 031 title capitalização)

**extrair_metadados_en.py — novo Caso 3:**
- Quando não há marcador "Abstract" explícito (heading ou inline), busca blocos `abstract` role com texto EN
- Detecção por: ausência de acentos PT + presença de ≥3 palavras EN comuns
- Continuação de blocos pula footnotes curtos (<200c) e pagenum
- 0 regressões nos seminários revisados (sdbr01/sdbr08/sdsul06/sdnne01)

**dict — 7 genéricos removidos:**
- arquiteto, arquitetos, materiais, tombamento, tradição, anexo, judiciário
- Adicionados ao STOPWORDS de seed_titles.py para evitar reinserção

**Engenharia (42 scripts auditados):**
- 2 HIGH: SQL injection guards (import_yaml_to_db.py, extrair_metadados_doc.py)
- 8 MEDIUM: conn try/finally (fix_capitalization, check_quality, check_references, fix_references, extract_title_en_sdbr13, validar_abstracts, extrair_titulo_es) + hardcoded DB_PATH (validar_abstracts, extrair_titulo_es) + dedup rollback

### 2026-03-24 — sdnne01 revisão completa (Fases 0-3)

**sdnne01** (44 artigos, 73 autores, 10 seções — 8 mesas + Apresentação Oral + Pôsteres):
- Cobertura: abstract 100%, abs_en 95%, kw 100%, kw_en 86%, refs 100%, ORCID 58%
- Fonte: CD-ROM (sem doc/docx), plumber (8023 blocos)
- 190 correções (185 auto + 5 humanas)
- 12 abstract_en truncados da importação YAML original — completados via plumber
- 16 títulos corrigidos vs PDF (009 "na cidade de Fortaleza" removido, 029 caatinga→sertão, 031 norte-nordeste hifenizado)
- Refs: 693→684 (sweep + LLM review: splits, joins, missing, non-refs)
- 10 autores corrigidos (001/006 autores removidos, 016 autora adicionada, 021 +3 autores), 61 afiliações
- Seções reordenadas (mesas 1-8 por número)
- 031 reclassificado como resumo
- Dedup: Mariana Bonates (2→1), Ceila Cardoso (2→1)
- 1 ORCID novo (Hélio Takashi Maciel de Farias, UFRN)
- Revisão humana: 5 correções (009 ponto final, 001 título, 020/029 abstract_en truncado, 031 resumo)

**validate_metadata.py — novo check A32:**
- Detecta abstract_en truncado via ratio PT/EN < 0.65
- Captura truncamentos que A19 (pontuação final) não detectava
- 0 falsos positivos nos seminários revisados

**extrair_metadados_en.py — limites de blocos aumentados:**
- Caso 1 (heading "Abstract"): 5→10 blocos
- Caso 2 (inline "Abstract:"): 4→8 blocos de continuação

**Engenharia (18 scripts auditados):**
- 1 HIGH: upload_zenodo.py file handle leak corrigido
- 6 MEDIUM: SQL injection guards assert→ValueError (seed_authors, seed_titles, normalizar_maiusculas, fix_validation_issues), whitelist em fix_a19 e extrair_metadados_en

### 2026-03-24 — sdrj04 revisão completa (Fases 0-3)

**sdrj04** (17 artigos, 25 autores, 3 seções — 2 eixos + 1 workshop):
- Cobertura: abstract 94%, abs_en 64%, kw 88%, kw_en 64%, refs 88%, ORCID 72%
- PDFs em 2 colunas (PT+EN ou PT+ES lado a lado) — causa principal de problemas
- 42 correções (37 auto + 5 humanas)
- 003/006: artigos PT+ES (não PT+EN) — abstract_es e keywords_es inseridos
- 8 títulos corrigidos: 008 título errado no DB, 016 subtítulo errado, 006 Instituto/protomoderna/arquitetura
- Refs: 285→265 (image credits FONTE DAS IMAGENS em 7 artigos, 8 concatenadas por 2-col merge)
- 006/012/013/016: abstracts completados ou limpos (truncamento 2-col, duplicação)
- 003/004/007/013: keywords limpas (contaminação com autor/afiliação)
- 11 afiliações inseridas, 1 ORCID novo (Barbara Cortizo de Aguiar)
- Revisão humana: 5 correções (001/010 refs image credits, 003 label leak, 006/014 capitalização)
- 017: workshop report sem metadados acadêmicos (genuíno)

### 2026-03-23 — sdmg01 revisão completa (Fases 0-3)

**sdmg01** (26 artigos, 40 autores, 2 seções):
- Cobertura: abstract 73%, abs_en 76%, kw 80%, kw_en 69%, refs 100%, ORCID 60%
- Fonte primária: DVD (PPT interativo + PDFs individuais), sem doc/docx
- Seções: 2 (Apresentações Orais + Pôsteres), sem eixos temáticos (confirmado via PPT)
- 9 títulos normalizados + 7 correções LLM (engenheiro, presente, materiais, complexo, etc.)
- Refs: 77%→100% (002 +14, 006 +46, 016 +34, 022 +30 reconstruídas 2-col)
- 6 abstracts corrigidos (completados, limpos, ou removidos por falta de RESUMO)
- 2 autores corrigidos: Di Marco (sobrenome composto), Lisandra Mara Silva (familyname errado)
- 4 ORCIDs novos (Lazzarin, Azevedo, Rezende, Silva)
- Revisão humana: 1 correção (012 subtitle "mg1" → "MG" — typo dado de origem)
- Revisão engenharia (15 scripts auditados): 4 bugs corrigidos (json.loads sem guard em 3 scripts, WHERE inconsistente)

### 2026-03-23 — sdpr02 revisão completa (Fases 0-3)

**sdpr02** (19 artigos, 43 autores, 1 seção):
- Cobertura: abstract 53%, abs_en 5%, kw 26%, kw_en 5%, refs 100%, ORCID 70%
- Fonte primária: 11 doc/docx (arts 001-010), plumber (011-019). PDF completo dos anais (livro 180p)
- 9 artigos sem abstract — genuíno (sem RESUMO no PDF)
- 15 títulos normalizados + 5 correções manuais LLM (Algumas, Universidade, edificado, estação/obra, fronteiras)
- 2 abstracts truncados completados (005 +1 parágrafo, 007 1→3 parágrafos)
- Refs: 185→234 (+49 refs em 7 artigos: 007 reconstruído 7→35, 009 reconstruído 6→18)
- 7 ORCIDs novos (3 confirmados + 4 candidatos aceitos)
- Revisão humana: 3 correções (001 split título/subtítulo, 012 urbanismo, 014 arquitetura — normalização contextual)
- Ficha catalográfica normatizada: GNOATO/MAGALHÃES (org.), ISBN do livro discriminado
- Galley do livro completo: volume_pdf com label "PDF do livro (12 dos 19 artigos)"
- volume_pdf_label: novo campo no DB + db2hugo.py + template Hugo

### 2026-03-23 — sdsul07 revisão completa (Fases 0-3)

**sdsul07** (46 artigos, 56 autores, 8 sessões):
- Cobertura: abstract 87%, abs_en 0%, kw 0%, kw_en 0%, refs 100%, ORCID 86%
- 0% keywords e abstract_en — genuíno (PDFs não têm seções EN nem Palavras-chave)
- 35 títulos corrigidos (normalização + LLM + agente): B/b, nomes próprios (Taba Guaianases, Cine Marrocos, EMEIs, CIAMs, etc.)
- 17 abstracts overflow re-extraídos do plumber, 3 truncados completados (blocos adjacentes)
- Refs: 1083 → 678 (limpeza extensiva: 142 joins sweep, 43/46 artigos revisão LLM)
- 033 PDF: 4 primeiras páginas eram imagens escaneadas — re-extraído com pikepdf, abstract inserido via OCR visual
- Revisão humana: 1 correção (033 "Pé do Morro" topônimo)

**fetch_orcid.py v3.1 — ORCID fulltext search + name_compatible fix:**
- Nova Fase E: quando busca estruturada (family-name+given-names) falha, busca nome completo como texto livre na API ORCID
- Pega nomes registrados com familyname diferente (ex: "Martins Marques" vs "Marques")
- name_compatible: exige sufixo no familyname (evita falso positivo "Franco" in "Regis Franco de Almeida")
- 2 ORCIDs novos: Valentina Martins Marques, Diego Fonseca Brasil Vianna

### 2026-03-22 — sdsul06 revisão completa (Fases 0-3)

**sdsul06** (24 artigos, 35 autores, 5 subtemas):
- Cobertura: abstract 96%, abstract_en 96%, keywords 92%, keywords_en 92%, refs 100%, ORCID 71%
- 5 subtemas criados (Renovação, Restauro, Equipamento, Ampliação, Mistura) — 10/24 atribuídos (8 do PDF + 2 do subtítulo)
- 18 correções de capitalização LLM, 20/24 artigos refs corrigidas por LLM
- 21 abstract_en extraídos do plumber (10 truncados completados com blocos adjacentes)
- Revisão humana: 1 correção (021 título→subtítulo) — melhor resultado até agora (vs 6 sdsul05, 10 sdsul04)
- Ficha catalográfica: "Disponível também em" → "Disponível originalmente em" corrigido em 22 seminários

**extrair_metadados_en.py — suporte a fontes_plumber:**
- Nova função `extract_en_from_plumber()`: extração estruturada usando role/page dos blocos
- Verifica blocos adjacentes (role=footnote/small) para continuação de abstract_en
- `find_fontes_dir()`: verifica presença de .txt/.jsonl (não só existência do diretório)
- `fix_validation_issues.py`: `read_plumber_abstract()` reutiliza `extract_en_from_plumber`
- Testado: sdsul04 (11 abs, 29 kw), sdsul05 (5 abs, 32 kw), sdsul06 (20 abs, 21 kw), sdbr08 0 regressões

**Pipeline atualizado:**
- §0.6: nota sobre suporte plumber no script
- §1.6c: verificar subtítulos para atribuição de seções quando fontes externas esgotadas

### 2026-03-21 — sdsul01/sdsul02 revisão completa (Fases 0-3)

**sdsul02** (35 artigos, 41 autores, 1 seção):
- Abstracts: 30/35 (86%), abstract_en: 26/35 (74%), keywords: 26/35 (74%), refs: 33/33 (100%)
- ORCID: 29/41 (71%)
- 10 correções de capitalização, 12 refs split (005), keywords cleanup
- Revisão humana: 5 abstracts truncados reextraídos, 3 abstract_en contaminados, 2 title_en extraídos
- 033/034 reclassificados como resumo
- Contaminação EN/PT recorrente nos regionais Sul (abstracts no mesmo bloco)

### 2026-03-21 — sdsul01 revisão completa (Fases 0-3)

**sdsul01** (48 artigos, 60 autores, 6 seções):
- 96% dos artigos sem RESUMO no PDF — abstracts falsos (texto do corpo) limpos, mantidos só 2 genuínos (001, 040)
- Refs: 45/48 (92%), 4 artigos reconstruídos do plumber (004: 1→7, 034: 1→21, 037: 1→23, 048: 4→11)
- 20 correções de capitalização (nomes próprios, instituições)
- ORCID: 41/60 (68%), 19 sem ORCID (todos já checados)
- Revisão humana: 2 títulos lowercase, 8 correções de refs (splits, notas vs refs, legendas)
- Aprendizado: check obrigatório de label RESUMO na Fase 0

**Runner system implementado:**
- `scripts/gerar_runner.py`: gerador de checklists executáveis por seminário
- Modos: `--status` (progresso), `--type producao`, sem args (lista todos)
- CLAUDE.md atualizado com instruções de uso

### 2026-03-20 — sdbr11 sessões atribuídas, SEO, CSL-YAML

**sdbr11 — 17 sessões criadas (fonte: Wayback Machine, seminario2016.docomomo.org.br):**
- 16 sessões + Campo de Liça, extraídas da programação do site original (captura 2017-02-18)
- 66 artigos atribuídos (fuzzy matching título), 35 sem sessão (artigos não apresentados mas aceitos)
- Sessões 2 e 13 ambas "Artes Integradas" → "Artes Integradas I" e "Artes Integradas II" (constraint UNIQUE)
- Diretórios `sessao 17/18` no site eram overflow das sessões 15/16 (não sessões reais)
- "Isso não matou aquilo" (programa) não encontrado no DB
- `section_label = 'sessão'`

### 2026-03-19 — SEO: títulos e meta descriptions para Google

**Site title corrigido:**
- `config.toml`: title "Anais" → "Anais Docomomo Brasil"
- `baseof.html`: `<title>` agora inclui subtítulo do seminário

**Meta descriptions adicionadas em todas as páginas:**
- Homepage (`index.html`): description + Open Graph + Twitter Cards
- Seminários (`list.html`): ficha catalográfica como description
- Índice de autores/palavras-chave (`terms.html`): contagem de itens
- Página de autor/keyword (`taxonomy.html`): contagem de artigos

**Verificação:** DNS CNAME ativo (`docomomobr.github.io`), robots.txt permite indexação, sitemap declarado. Google ainda não indexou (site com <2 dias).

**Exportação CSL-YAML:**
- Template `single.yaml` reescrito como CSL-YAML padrão (campos: `type`, `container-title`, `event-title`, `issued.date-parts`, `DOI`, `author.family/given/ORCID`, etc.)
- 1438 arquivos validados (yaml.safe_load + campos obrigatórios), 0 erros
- Expediente atualizado: "YAML" → "CSL-YAML | pandoc-citeproc, processamento automatizado"

### 2026-03-19 — sdbr07 renumerado, 5 artigos novos, seções sdbr03/06/07

**sdbr07 renumeração (PROPAR/UFRGS):**
- 69 artigos renumerados conforme ordem original do PROPAR (https://www.ufrgs.br/propar/anais-do-7o-seminario-docomomo-brasil/)
- IDs, PDFs, fontes, YAML, OJS mapping, anais.sql atualizados; Zenodo não alterado
- Gaps 028 e 048 normais (numeração do PROPAR pula)
- 5 artigos faltantes identificados, PDFs baixados do PROPAR, inseridos no DB:
  - sdbr07-020: Arquitetura dos anexos na Praça dos Três Poderes (Silva, Sánchez)
  - sdbr07-022: "Tanto cemitério!" (Holanda, Vasconcellos)
  - sdbr07-023: A tectônica na reciclagem e requalificação de obras arquitetônicas modernas (Rocha)
  - sdbr07-030: Park Hotel, a urgência de uma ação (Corrêa, Piquet, Cabral)
  - sdbr07-031: Centro Cultural FIESP (Vasconcellos)
- Pipeline de revisão completo nos 5 novos (abstracts, refs, keywords, autores, ORCIDs)
- 5 artigos publicados no Zenodo (community docomomobr)

**Seções atribuídas a partir do site antigo (docomomobrasil.com/old/):**
- HTMLs de sessões/trabalhos/autores salvos em `revisao/site_antigo/` (sdbr03-09)
- sdbr03: 6 sessões criadas (Conceitos do MoMo, Inventários, Práticas, Pesquisas tecnológicas, Ensino, Experiências internacionais). 58/58 artigos
- sdbr06: 4 sessões (A preservação e o moderno, A problemática do moderno nacional, A construção da história, Conferências). 64/64 artigos
- sdbr07: 10 mesas (Praça e Palácio, Palácio e Residência, Residência, Urbanismo, Casa, Cultura e Educação, Paisagem/Transporte/Mercado, Agência e Consideração, Autor e Consideração, Hotel/Escritório/Expansão). 74/74 artigos
- sdbr07: 29 títulos/subtítulos revisados (capitalização LLM — 2 passadas)

**Diagnóstico site antigo vs banco:**
- sdbr03: 3 artigos faltantes (PDFs 404 na Wayback, não encontrados online)
- sdbr05: 0 faltantes reais (títulos abreviados no DB)
- sdbr06: 13 artigos faltantes (PDFs 404, não encontrados online)
- sdbr08/09: 7/4 faltantes (verificar com DVDs)
- Artigos faltantes registrados em `revisao/artigos_faltantes_buffer.yaml`
- Diagnóstico completo em `revisao/site_antigo_diagnostico.md`

**sdbr02 — sessões pendentes:**
- 3 eixos conhecidos, mapeamento artigo→mesa no arquivo físico do Lab20/UFBA (Prof. Huapaya)

**gerar_revisao_html.py:** suporte a `--articles id1,id2` para filtrar artigos específicos

### 2026-03-19 — 13 artigos faltantes: pipeline revisão completo

**Artigos inseridos (comparação OJS vs banco):**
- sdbr03: 1 (Marcos Carrilho, "A ruína da Casa Modernista")
- sdbr05: 5 mesas temáticas (Comas, Lara, Camisassa, Camargo, Conduru) — seção "Mesas Temáticas" criada (seq=90)
- sdbr07: 7 (Rocha, Leão, Alves, Diez, Moreira/Naslavsky, Schlee/Donato, Pellegrini/Machado)
- PDFs baixados do OJS, fontes salvas (txt/jsonl)
- Dedup: Fernando Luiz Camargos Lara → Fernando Luiz Lara; Ricardo Rocha → Ricardo de Souza Rocha

**Pipeline revisão (etapas 0.3b a Fase 2):**
- Extração pdfplumber: abstracts, keywords, abstract_en, keywords_en, referências
- sdbr07: 6 abstracts completos (064-069), keywords PT/EN, abstract_en extraídos
- sdbr05-058: 42 refs; sdbr05-060: 3 refs
- sdbr07: 19+37+12+14+32+30+10 refs (154 total)
- Normalização de títulos + revisão LLM: 3 correções (descritiva+toponímico, IPESP sigla)
- clean_references: 6 backfills (063), 2 junções (058), 1 split (063, 064)
- validate --fix: 0 issues nos novos artigos
- HTML de revisão: `revisao/revisao-artigos-novos.html`

**Mapeamento OJS:**
- Revista: 120 artigos, 13 edições em `docs/ojs_revista_mapping.json`
- Artigos faltantes documentados: `docs/artigos_faltantes_ojs.md`
- Falsos negativos identificados: sdbr03-005 (Maísa Veloso), sdbr05-003/020/031, sdbr02-001

### 2026-03-18 — sdbr09 mesas publicadas, reclassificações, Hugo weight

**sdbr09 mesas (21+2 textos publicados no Zenodo):**
- 21 mesas-redondas publicadas no Zenodo com PDF (community docomomobr)
- 2 artigos reclassificados de mesa→artigo: sdbr09-156 (Capacitação em conservação), sdbr09-160 (Função social da propriedade)
- Títulos corrigidos: removido "Mesa" genérico, usando o tema real da seção
- Abstracts reescritos com parágrafos corretos (confrontados com PDFs)
- Removidos: bibliografia, notas de rodapé, lixo de template, hifenização de PDF
- Keywords: formato JSON array → separado por `;`, hífens removidos

**Hugo — mesas primeiro na seção:**
- `weight: 0` para mesas, `weight: 10` para artigos no front matter (db2hugo.py)
- Template `list.html`: ordenação `sort (sort (sort .Pages "File.Path") "Weight") "Params.section_seq"`
- Mesas aparecem antes dos artigos dentro de cada seção

**upload_zenodo.py:**
- Bloqueio de `mesa` removido (só `resumo` continua bloqueado)

**Hugo — abstracts e mesas no template:**
- Abstracts renderizam com parágrafos (`<p>`) via `replaceRE "\n\n+" "</p><p>"` + `safeHTML`
- Mesas mostram botão "Baixar PDF" e DOI badge (removida exclusão de `mesa` da seção `pdf-action`)

**Deploy do site Hugo:**
- GitHub Actions workflow: reconstruct DB → db2hugo → hugo build → Pagefind → deploy
- Pagefind: busca estática indexando todos os artigos
- Favicon: ícone Docomomo do site principal
- Google Search Console: verificação HTML, sitemap submetido
- CNAME: `anais.docomomobrasil.com`
- Workflow gera só nacionais (regionais ainda não publicados)
- Capas: db2hugo busca em `site/static/img/capas/` (tracked) antes de `nacionais/capas/` (gitignored)

**13 artigos faltantes inseridos (comparação OJS vs banco):**
- sdbr03: 1 (Marcos Carrilho, "A ruína da Casa Modernista")
- sdbr05: 5 mesas temáticas (Comas, Lara, Camisassa, Camargo, Conduru) — seção "Mesas Temáticas" criada
- sdbr07: 7 (Rocha, Leão, Alves, Diez, Moreira/Naslavsky, Schlee/Donato, Pellegrini/Machado)
- Dedup autores: Fernando Luiz Camargos Lara → Fernando Luiz Lara
- Normalização de títulos + revisão LLM: 3 correções (descritiva+toponímico, IPESP sigla)
- Mapeamento OJS completo documentado: `docs/ojs_revista_mapping.json`, `docs/artigos_faltantes_ojs.md`

### 2026-03-18 — 3 artigos novos, 11 videoposters sdbr14, seções agrupadas

**sdbr14 videoposters (11 vídeos):**
- Metadados extraídos do PDF dos anais (p.16), inseridos no banco (document_type=video, seção "Videoposters")
- 11 MP4s publicados no Zenodo (community docomomobr, resource_type=video)
- Dedup: Bierrenbach (3346→1259), Maria Cristina Cabral (3341→2175), Luciana Saboia (3343→416)
- ORCIDs: Azevedo, Derenusson, Passaro; Luciana Saboia corrigida em 5 artigos no Zenodo
- sdbr13: seções renumeradas (eixos 1-4, Mesa Redonda sem seq)
- fix_zenodo_metadata.py: novo script para corrigir metadados no Zenodo (nova versão com payload completo)
- sdbr13-146: lixo removido do abstract_en (instruções de formatação)

**Hugo — seções e vídeos:**
- Seções agrupadas por seq (não alfabético), formato "label N. nome"
- Seções sem label (Videoposters, Mesa Redonda): só nome, sem prefixo
- seq >= 90 usado para ordenação interna (não exibido)
- Player de vídeo embutido (`<video>`) na página do artigo para document_type=video
- Botão "Baixar MP4" + DOI na página do vídeo
- Listagem: "MP4" em vez de "PDF" para vídeos

**upload_zenodo.py:**
- Suporte a vídeos: find_file (pdfs/ + videos/), resource_type=video
- Timeout proporcional ao tamanho do arquivo para uploads grandes

**3 artigos novos (sdbr01-001, sdbr02-001, sdbr02-002):**
- Pipeline revisão completo: PDFs extraídos (pdfplumber), sem abstract/keywords (genuinamente ausentes — textos editoriais)
- sdbr01-001: 2 referências extraídas (GOMES 1998, PROJETO s/d)
- sdbr02-001: título corrigido ("Apresentação: o 2º Seminário Docomomo_Brasil", subtítulo "proposta, realização, memória")
- Afiliações: UFBA×6, UFPI×1
- Dedup: Caio Anderson da Silva Almeida (3334) → Caio Anderson da Silva de Almeida (1090) — partícula "de" faltante
- ORCID: Thiscianne Pessoa (0000-0002-1459-2460)
- Publicados no Zenodo (community docomomobr): DOIs 10.5281/zenodo.19079958, .19079991, .19079997

**upload_zenodo.py — TimeoutSession:**
- Adicionado `TimeoutSession` (connect=15s, read=120s) para evitar travamento indefinido
- Todas as chamadas `requests` agora usam timeout via Session subclass

**Hugo fixes:**
- `list.html`: artigos sem seção não mostram mais heading "Sem seção" (default "" + condicional)
- `single.html`: "parte: Parte 02" → redundância já resolvida (hasPrefix + lower funcionava, build antigo)
- sdbr11 e sdbr12: título do seminário corrigido no banco (faltava ", Cidade, Ano") — agora aparecem nos estados corretos (PE, MG) no sort "por estado"
- DOI badge: botão copiar ao lado (clipboard API, copia `https://doi.org/...`)

### 2026-03-17 — Zenodo produção: sdbr15 publicado, pipeline auditado

**Zenodo produção:**
- sdbr15 completo: 101 artigos publicados, 0 erros
- Community `docomomobr` criada e todos os records incluídos
- Fix: API produção exige UUID da community (não slug) — `_resolve_community_id()` adicionado
- DOIs e `zenodo_record_id` gravados no banco
- Volumes completos: sdbr01, sdbr02, sdbr15 (PDFs baixados do OJS)

**upload_zenodo.py reescrito (API InvenioRDM):**
- API nova (`POST /api/records`), não legacy (`/api/deposit/depositions`)
- Upload 3-step (initiate → content → commit)
- Retry com backoff exponencial (429/5xx), draft cleanup em caso de erro
- `--all`, `--community`, `--license`, `--no-skip-existing`, `--upload-volume`
- Progresso `[n/total]`, .env com strip de quotes
- Licença CC-BY-4.0 (alinhada com Hugo)

**Auditoria completa do pipeline:**
- Templates Hugo: Highwire Press, Dublin Core, Schema.org JSON-LD, COinS, Signposting, OG/Twitter
- Exports de citação validados: BibTeX, RIS, CSL-JSON, YAML (todos parseiam sem erro)
- Cobertura de metadados: 95% abstract, 70% abstract_en, 83% keywords, 65% ORCID (nacionais)
- Relatórios em `docs/auditoria_producao_2026-03-16.md`, `auditoria_citacoes_2026-03-16.md`, `auditoria_metadados_2026-03-16.md`

**Section labels documentados:**
- `section_label` na tabela seminars com fonte documental para cada um
- Seções genéricas escondidas (`hide_title=1`): "Artigos", "Artigos Completos", etc.
- Template exibe "eixo temático: nome" / "sessão: nome" / "mesa: nome"
- Fontes documentadas em `docs/fontes_secoes.md`
- Pendentes: sdbr08 (DVD), sdmg01 (DVD) — resolvidos pelo usuário

**Migração OJS documentada (Fase 5):**
- Mapeamento OJS ID → artigo (anais): 1421 artigos em `docs/ojs_article_mapping.json`
- Mapeamento OJS revista: 120 artigos + 13 edições em `docs/ojs_revista_mapping.json`
- Fluxo: coexistência → repo de redirects → DNS → desligar OJS
- Repo separado `docomomobr/publicacoes` para redirects (GitHub Pages = 1 domain/repo)
- Redirects: `/anais/*` → `anais.docomomobrasil.com/*`, `/revista/*` → `revista.docomomobrasil.com/*`

**Site Hugo:**
- Homepage simplificada (só nacionais, regionais comentados no nav)
- Página de expediente criada (`site/content/expediente/`)
- Rodapé com licença CC BY 4.0
- `_default/single.html` para páginas genéricas
- sdbr05: 13 sessões criadas e 56 artigos mapeados (fonte: DVD)
- sdbr08: `article` → `artigo` (4 artigos)
- sdpr02: título corrigido ("Londrina, 2012")

**Fixes da auditoria (todos resolvidos):**
- H1: file handle retry (lê PDF em memória)
- H2: draft órfão no upload_volume
- H3: licença CC-BY-4.0 alinhada
- H4: JSON-LD Book (não Periodical)
- RIS: locale dinâmico, SP/EP separados
- CSL-JSON: +abstract/keyword, jsonify em strings, trim \\n
- BibTeX: key sem hifens, escape &, +abstract/keywords/organization
- Dublin Core: ISBN como URN
- YAML: indentação autores corrigida, jsonify
- og:image/twitter:image fallback
- meta description, citation_keywords
- Acessibilidade: lang en/es, aria-label, role=search, h1, prefers-reduced-motion
- CSS: contraste --gray-500, Google Fonts non-blocking
- db2hugo: +sdpr, +title_es/subtitle_es, escape refs/yaml, hide_title

### 2026-03-15 — Hugo: capa do seminário na página do artigo

**Template artigo (`site/layouts/artigo/single.html`):**
- Capa do seminário exibida como miniatura (160px) no bloco `event-meta`, ao lado do eixo temático e título do evento
- Clicável, leva à página do seminário (via `.CurrentSection`)
- Capas copiadas de `nacionais/capas/` para `site/static/img/capas/` (15 PNGs)

**CSS (`site/static/css/style.css`):**
- `.event-meta` agora é flex container com gap
- `.event-meta-cover`: 160px, borda, border-radius, hover verde
- `.event-meta-text`: wrapper para section_label + event_title

### 2026-03-15 — sdbr12/sdbr13 revisados, Fase 3 refatorada, checks A26/A27

**sdbr13** (181 artigos): pipeline completo (Fases 0-2), revisão humana (10 itens), Fase 3 completa.
- Cobertura: abstract 100%, seções 100%, demais >94%
- 5 eixos criados (HTML do site inscricoes13docomomobrasil.ufba.br)
- 11 overflows abstract_en corrigidos, 36 backfills resolvidos, 31 keywords_en com lixo re-extraídas
- 93 correções de capitalização (agente LLM), 91 artigos refs limpas (sweep)

**sdbr12** (82 artigos): revisão humana (12 itens) aplicada em sessão anterior. 0 issues finais.

**Fase 3 refatorada:**
- Movida de §5.4 do pipeline_revisao_humana.md para Fase 3 autônoma no pipeline_revisao.md
- 8 etapas: diagnóstico unificado (3.1), dict (3.2), scripts (3.3), pipeline (3.4), verificação (3.5), registro (3.6), engenharia (3.7), fechar (3.8)
- Diagnóstico agora cobre TODAS as correções (automáticas + humanas), não só humanas
- Registro de status obriga log de cada correção automática (artigo/campo/antes/depois/causa)

**Novos checks:**
- A26: abstract em idioma errado (ES no campo PT) → AUTO-FIX (move para abstract_es)
- A27: PT colado no abstract_en → AUTO-FIX (corta no boundary)

**Scripts corrigidos:**
- validate_metadata.py: +A26, +A27, guard no A25 (falso positivo narrativo), A16 filtra keywords vazias após strip, EMAIL_RE com word boundary, JSON fallback logado, A05/A06 mortos removidos
- fix_validation_issues.py: clean_keywords com KW_JUNK_RE, ALL CAPS ≥15, newlines, >80c, zero-width spaces, template prefix inteligente
- clean_references.py: extract_author refatorado (AUTHOR_CHARS unificado)

**Pipeline atualizado:**
- Fase 0.4: verificar idioma ao inserir abstract, extrair ES, rodar sweep após inserir refs
- Fase 0.5: rodar validate --fix ANTES da varredura manual
- Fase 1.2b+: re-rodar clean_references após sweep
- §1.1a: prompt LLM reforçado (arquiteto genérico, grupos artísticos, split vs PDF, PDFs escaneados)
- §1.2c: procedimento para A11 (refs longas que o sweep não resolveu)

### 2026-03-14 — sdbr10/sdbr11 revisados, pipeline refatorado, checks A23/A24

**Pipeline revisão refatorado:**
- sweep_refs ANTES do loop validate (1.2b); loop 1.5 reduzido a A07/A08/A19
- A05/A06 removidos (ciclo com A21); A10-A13 removidos do loop (cobertos pelo sweep)
- 1.2c: revisão LLM de TODAS as refs (obrigatória, corrige na hora, não relata)
- pdfplumber obrigatório na fase de revisão (fontes/ é fallback)
- Prompt LLM reescrito: passo crítico = identificar boundary BIBLIOGRAFIA→NOTAS

**sweep_refs melhorado:**
- Threshold 300 chars (era 500), +publisher/pipe/em-dash boundaries
- NON_REF_STARTERS expandido (Ibíd., Op.cit., créditos de foto)
- Passada 0-pre: corta bloco de NOTAS numeradas do final (3+ consecutivas)
- truncate_body_text +12 verbos narrativos
- has_narrative_structure: early exit + markers pré-compilados

**Novos checks:**
- A23: abstract_en colado no abstract PT → AUTO-FIX (separa no boundary)
- A24: encoding ruim (ĕ/ė) → REPORT (extração via imagem do PDF)

**Performance:**
- build_profile: 9 queries → 1 (COUNT CASE WHEN)
- check_no_authors: N+1 → set pré-computado
- EN_BOUNDARY regex: pré-compilado no topo do módulo

**sdbr10** (118 artigos): revisão LLM completa, 51 artigos corrigidos (~100 refs), rev.md aplicado
**sdbr11** (101 artigos): pipeline completo (Fases 0-2), 25 itens do rev.md corrigidos, 2 issues genuínos

**Abstracts multilíngues:**
- abstract=PT (Resumo), abstract_en=EN (Abstract), abstract_es=ES (Resumen). Labels fixos.
- Display: mostra o que existe, sem lógica de locale. Zenodo: fallback por locale.
- Hugo e gerar_revisao_html atualizados

**upload_zenodo.py**: SELECT +abstract_en/es/kw_en/es, fallback inteligente por locale
**regras_dados.md**: tabela completa de campos por idioma documentada

### 2026-03-03 — sdnne06 novos PDFs + pipeline produção Hugo

- **sdnne06**: 8 PDFs novos do livro-cd (3 upgrades só-resumo→com-PDF: arts 22, 40, 45; 5 artigos novos: 105-109). Total: 109 artigos (66 artigo, 43 resumo)
- **Metadados extraídos**: abstract_en, keywords_en, referências para os 8 artigos. Arts 108/109 sem abstract (originais não têm)
- **Autores**: merges manuais (Clóvis Jucá→Jucá Neto, Y. Caddah→Yasmine, E. Coutinho→Elane, D. Pessoa→Daniel Victor, Ana Karolyne Liberato). 5 ORCIDs novos
- **document_type=resumo**: 43 artigos sdnne06 marcados; sdbr04 já estava. `upload_zenodo.py` agora pula resumos
- **db2hugo.py**: exporta title_en, subtitle_en, abstract_en, keywords_en, abstract_es, keywords_es
- **Template Hugo**: abstract/keywords EN e ES exibidos; keywords são links para taxonomia `palavras-chave`
- **Control chars**: removido U+0002 de sdbr08-166.abstract, U+0083 de sdsp03-016.abstract_en

### 2026-03-29 — idc06: 6th International DOCOMOMO Conference

- **idc06**: 53 artigos da 6ª Conferência Internacional DOCOMOMO (Brasília, 2000). Primeiro seminário internacional no acervo.
- **Re-split do PDF**: proceedings completo (358p) re-splitado com páginas corrigidas por revisão humana. idc06-052 removido (absorvido pelo 051).
- **Referências**: 409 refs extraídas (imagens + plumber), 0 problemas no check_references.
- **Zenodo**: 53 artigos publicados com DOI na community docomomobr + volume completo (record 19316491).
- **Site Hugo**: âmbito "Internacional" adicionado. Menu com link "int". Capa na home.
- **Scripts**: db2hugo.py e upload_zenodo.py atualizados com mapeamento `idc` → `internacional/`.
- **Template**: botão "PDF da edição completa" agora aponta para URL (Zenodo) em vez de href="#".
- **Dataset Zenodo**: v1.1 via GitHub release. Documentado em `docs/zenodo_dataset.md`.
- **Totais**: 46 seminários, 2.767 artigos, 2.514 autores.

### 2026-03-30 — Seções: numeração e redundâncias

- **Numeração de seções**: 16 seminários corrigidos (IDs do banco usados como seq → numeração sequencial)
- **Títulos redundantes**: 29 prefixos removidos ("Mesa 1 — descrição" → "descrição")
- **section_label removido**: 13 seminários onde a fonte original não numera (sdbr03, sdbr07, sdbr08, sdbr09, sdbr11, sdnne03, sdsp03, sdsp05, sdsul02, sdsul04, sdsul06, sdsul07, sdsul08)
- **Nota de divulgação**: `docs/nota_divulgacao_2026-03-29.md` + release WhatsApp
- **Mosaico de capas**: `docs/mosaico_docomomo_brasil.png` (2000x1200) para WordPress

### 2026-03-30 — Keywords EN/ES taxonomia + limpeza

- **Taxonomias separadas**: keywords (EN) e palabras-clave (ES) adicionadas como taxonomias Hugo independentes, com abas PT/EN/ES na página de palavras-chave
- **robots.txt**: bloqueio de indexação de arquivos de exportação (.bib, .ris, .json, .yaml)
- **Keywords limpeza**: 7 keywords_en com texto absurdamente longo removidos (abstracts no campo de keywords). 13 artigos com PT/ES em keywords_en corrigidos (7 esvaziados, 2 substituídos por EN correto, 3 movidos para keywords_es, 1 fragmentos de título removidos)
- **Capitalização**: 9 "Obra/Obras" → "obra/obras" (substantivo comum)
- **Seções**: numeração corrigida em 16 seminários (IDs do banco → sequencial). 29 títulos redundantes limpos. section_label removido de 13 seminários sem numeração na fonte original

### 2026-03-30 — Fechamento idc06 + deploy final

- **idc06 revisão fechada**: rev-status.md criado, seminarios_revisados.md atualizado
- **Deploy**: taxonomias EN/ES, abas CSS, robots.txt, capitalização — tudo pushado e deployado
- **Nota de divulgação**: `docs/nota_divulgacao_2026-03-29.md` + release WhatsApp

### 2026-03-30 — Zenodo: verificação e correção sdbr07

- **sdbr07 record IDs trocados**: 69 record IDs re-mapeados (renumeração PROPAR desalinhou IDs com records). 7 artigos (070-076) com PDFs renomeados no Zenodo via nova versão (fix_zenodo_metadata.py + build_record_payload).
- **Verificação completa**: 2559 artigos verificados contra API Zenodo. 0 mismatches fora do sdbr07.
