# Diretrizes do Projeto — Anais Docomomo Brasil

Convenções e referência rápida para migração dos anais dos seminários Docomomo Brasil para o OJS.

Referência técnica OJS completa: [`docs/ojs_reference.md`](docs/ojs_reference.md)
Regras de processamento de dados: [`docs/regras_dados.md`](docs/regras_dados.md)
Fontes das seções/eixos temáticos: [`docs/fontes_secoes.md`](docs/fontes_secoes.md)

---

## Seminários revisados — NÃO ALTERAR

Os seminários abaixo já foram revisados manualmente pelo usuário (títulos, subtítulos, referências).
**NÃO modificar seus dados** (títulos, subtítulos, autores, referências) em nenhuma circunstância,
a menos que o usuário peça explicitamente uma alteração específica.

| Seminário | Artigos | Status | Data |
|-----------|---------|--------|------|
| sdbr01 | 37 | ✅ revisado | 2026-02-24 |
| sdbr02 | 22 | ✅ revisado | 2026-02-24 |
| sdbr03 | 56 | ✅ revisado | 2026-02-26 |
| sdbr04 | 79 | ✅ revisado | 2026-02-26 |
| sdbr05 | 56 | ✅ revisado | 2026-02-28 |
| sdbr06 | 63 | ✅ revisado | 2026-03-01 |
| sdbr07 | 62 | ✅ revisado | 2026-03-02 |
| sdbr08 | 188 | ✅ revisado | 2026-03-09 |
| sdbr09 | 170 | ✅ revisado | 2026-03-09 |
| sdbr10 | 118 | ✅ revisado | 2026-03-14 |
| sdbr11 | 101 | ✅ revisado | 2026-03-14 |
| sdbr12 | 82 | ✅ revisado | 2026-03-14 |
| sdbr13 | 181 | ✅ revisado | 2026-03-15 |
| sdbr14 | 122 | ✅ revisado | 2026-03-15 |
| sdbr15 | 101 | ✅ revisado | 2026-03-15 |
| sdsul01 | 48 | ✅ revisado | 2026-03-21 |
| sdsul02 | 35 | ✅ revisado | 2026-03-21 |
| sdsul03 | 39 | ✅ revisado | 2026-03-21 |
| sdsul04 | 46 | ✅ revisado | 2026-03-22 |
| sdsul05 | 37 | ✅ revisado | 2026-03-22 |
| sdsul06 | 24 | ✅ revisado | 2026-03-22 |
| sdsul07 | 46 | ✅ revisado | 2026-03-23 |
| sdsul08 | 51 | ✅ revisado | 2026-03-23 |
| sdpr01 | 26 | ✅ revisado | 2026-03-23 |
| sdpr02 | 19 | ✅ revisado | 2026-03-23 |
| sdmg01 | 26 | ✅ revisado | 2026-03-23 |
| sdrj02 | 19 | ✅ revisado | 2026-03-23 |
| sdrj03 | 6 | ✅ revisado | 2026-03-23 |
| sdrj04 | 17 | ✅ revisado | 2026-03-24 |
| sdnne01 | 44 | ✅ revisado | 2026-03-24 |
| sdnne02 | 33 | ✅ revisado | 2026-03-24 |
| sdnne03 | 41 | ✅ revisado | 2026-03-24 |

---

## Regra de ouro — Listas de revisão do usuário

Quando o usuário fornece um arquivo de revisão (`revisao/{slug}-rev.md`) com uma lista de correções:
1. Ler o arquivo **inteiro** antes de começar
2. Listar **todos** os itens encontrados
3. Executar **cada item**, sem exceção, na ordem
4. Verificar cada item no banco após execução
5. Reportar checklist completa (✅/❌) item a item
6. NÃO buscar outros problemas durante a execução da lista — isso é outra fase

---

## Regra de ouro — Pipeline existente

ANTES de escrever qualquer código ou rodar qualquer comando:
1. Verificar se existe `revisao/{slug}-runner.md` — se sim, **seguir o runner**
2. Se não existe, gerar: `python3 scripts/gerar_runner.py {slug}`
3. Consultar `docs/pipeline_*.md` apenas para detalhes e edge cases — o runner é a fonte primária
4. Consultar a memória em `.claude/projects/.../memory/MEMORY.md`
5. Verificar se já existe script em `scripts/` ou `regionais/*/scripts/`
6. Se o script existe, USAR. Se não existe, PERGUNTAR antes de criar.
7. NUNCA escrever Python ad-hoc inline quando existe script para a tarefa.
8. NUNCA alterar o banco sem aprovação explícita do usuário.

## Regra de ouro — Hierarquia de fontes para extração

Verificar **nesta ordem** antes de qualquer extração de texto:
1. **doc/docx originais** → ler com `python-docx` (preserva estilos de parágrafo). **NÃO converter para .txt** — perde-se a estrutura. Originais podem estar em `fontes/anais/`.
2. **pdfplumber** → `fontes_plumber/`. Boa qualidade, separa refs de notas por font_size.
3. **pdftotext** → `fontes/`. Fallback. Não lida com colunas.

**SEMPRE verificar se existem doc/docx ANTES de rodar pdfplumber.** Muitos seminários têm os originais em Word.
**NUNCA tentar reconstruir manualmente texto fragmentado** — é perda de tempo e gera erros.

Quando o usuário diz "rodar o pipeline", significa seguir o runner do seminário — não ler o pipeline inteiro nem inventar processo novo.

## Regra de ouro — Zenodo API (InvenioRDM)

**PUT no draft SUBSTITUI TODO o metadata** — não faz merge. Se fizer PUT com apenas o campo que quer corrigir, todos os outros campos obrigatórios desaparecem e o publish falha.

Para corrigir metadados de um record publicado:
1. `POST /api/records/{id}/versions` → cria draft de nova versão
2. `POST /api/records/{new_id}/draft/actions/files-import` → copia arquivos da versão anterior
3. `PUT /api/records/{new_id}/draft` → enviar payload **COMPLETO** (reconstruir todos os campos: title, resource_type, creators, description, languages, rights, publisher, subjects, related_identifiers com relation_type e resource_type, custom_fields, identifiers, etc.)
4. `POST /api/records/{new_id}/draft/actions/publish` → publicar

**Community**: a API de produção exige o **UUID** da comunidade, não o slug. Usar `_resolve_community_id()` para converter slug → UUID via `GET /api/communities/{slug}`.

**Editors nos artigos**: NÃO incluir ORCID dos editors/contributors. Cada artigo geraria uma notificação no perfil ORCID do editor — spam indesejado. ORCID só nos **creators** (autores do artigo e organizadores de volume).

### Como rodar o pipeline

O **runner** (`revisao/{slug}-runner.md`) é o checklist executável do seminário.
Os pipelines (`docs/pipeline_*.md`) são a referência de consulta para edge cases.

Quando o usuário pedir "rode o pipeline" num seminário:
1. Verificar se existe `revisao/{slug}-runner.md`
2. Se não existe, gerar: `python3 scripts/gerar_runner.py {slug}`
3. Ler o runner — encontrar a primeira etapa `[ ]`
4. Executar a etapa, marcar `[x]` no runner, avançar
5. Se precisar de detalhes sobre uma etapa, consultar o pipeline referenciado no runner
6. NUNCA pular etapa — se falha, parar e reportar
7. Ao retomar uma sessão, reler o runner para encontrar onde parou

**Runners por tipo:**
- `python3 scripts/gerar_runner.py SLUG` — revisão automática (pipeline_revisao.md)
- `python3 scripts/gerar_runner.py SLUG --type producao` — publicação (Hugo + Zenodo)
- `python3 scripts/gerar_runner.py` — lista seminários e runners existentes
- `python3 scripts/gerar_runner.py SLUG --status` — mostra progresso

---

## Estrutura do Projeto

```
anais/
├── nacionais/           # Seminários nacionais (sdbr01-sdbr15) — todos publicados no OJS
│   ├── sdbr*.yaml       # Metadados consolidados (1 YAML/seminário)
│   ├── capas/           # Capas PNG (sdbr01-sdbr15)
│   └── sdbr12/          # Pipeline sdbr12 (15 scripts, fontes/)
├── regionais/
│   ├── nne/             # Norte/Nordeste (sdnne01-10)
│   ├── se/              # Sudeste: MG + RJ + SP (sdmg01, sdrj02-04, sdsp03-09)
│   └── sul/             # Sul (sdsul01-08, sdpr01-02)
├── scripts/             # Scripts principais (generate_ojs_xml, import_ojs, dedup_authors, etc.)
│   └── legacy/          # Scripts antigos de processamento (não mais usados)
├── dict/                # Módulo NER + Entity Resolution (dict.db, normalizar.py)
├── docs/                # Documentação técnica e relatórios
├── revisao/             # Revisão humana (fichas, seções, títulos/autores)
├── xml_test/            # XMLs de teste (só metadados)
├── xml_with_pdf/        # XMLs com PDF base64 para produção
├── site/                # Site Hugo (em construção)
├── schema/              # Schema YAML de referência
├── anais.db             # Banco SQLite (gitignored)
└── anais.sql            # Dump textual do banco (versionado)
```

Cada grupo regional segue a mesma estrutura:
```
regionais/{grupo}/
  {slug}.yaml              ← metadados consolidados (produto final)
  capas/                   ← capas dos seminários (gitignored)
  scripts/                 ← scripts de processamento do grupo
  docs/                    ← documentação do grupo (quando houver)
  {slug}/
    fontes/                ← material bruto original (gitignored)
    pdfs/                  ← PDFs renomeados/finais (gitignored)
```

---

## Credenciais de Acesso

Credenciais em `.credentials` (gitignored). Resumo dos serviços:

- **FTP**: `ftp.app.docomomobrasil.com` (usuário `app`)
- **WordPress**: `https://docomomobrasil.com/wp-admin/` (usuário `admindocomomo`)
- **WordPress REST API**: `https://docomomobrasil.com/wp-json/wp/v2/` (Application Password)
- **OJS produção**: `https://publicacoes.docomomobrasil.com/anais` (usuário `dmacedo`, papel Editor)
- **OJS teste**: `docomomo.ojs.com.br/index.php/ojs` (usuário `editor`)

---

## Scripts principais

| Script | Função |
|--------|--------|
| `scripts/normalizar_maiusculas.py` | Normaliza capitalização nos títulos do `anais.db`. `--dry-run`, `--slug SLUG` |
| `dict/normalizar.py` | Módulo de normalização de maiúsculas. 3 passadas: palavra, expressão, toponímico contextual |
| `scripts/clean_references.py` | Limpeza automática de refs: split underscores ABNT, backfill autores, join URLs. `--dry-run`, `--slug` |
| `scripts/check_references.py` | Detecta erros em referências: concatenadas, não-referências, fragmentos. `--summary`, `--slug`, `--type` |
| `scripts/validate_metadata.py` | Validação abrangente pós-pipeline: cruzamentos idioma, backfills, refs longas, locale, fontes/. `--fix`, `--dry-run`, `--slug` |
| `scripts/upload_zenodo.py` | Upload PDFs para Zenodo (sandbox/production, dry-run, skip-existing) |
| `scripts/fix_zenodo_metadata.py` | Corrige metadados de artigos já publicados no Zenodo. Cria nova versão com payload completo reconstruído do DB. `--dry-run`, aceita múltiplos IDs |
| `scripts/db2hugo.py` | Gera conteúdo Hugo a partir do anais.db |
| `scripts/gerar_revisao_html.py` | HTML de revisão por seminário: capa, ficha, artigos por seção. `python3 scripts/gerar_revisao_html.py SLUG` → `/tmp/revisao-SLUG.html` |
| `scripts/gerar_runner.py` | Gera/consulta runners (checklists executáveis). Sem args: lista seminários. `SLUG`: gera runner. `--status`: progresso. `--type producao` |

Pipeline de tratamento (novos seminários): ver [`docs/pipeline_tratamento.md`](docs/pipeline_tratamento.md).

Pipeline de revisão automática (diagnóstico, normalização, extração): ver [`docs/pipeline_revisao.md`](docs/pipeline_revisao.md).

Pipeline de revisão humana (correções manuais, log, fechamento): ver [`docs/pipeline_revisao_humana.md`](docs/pipeline_revisao_humana.md).

Pipeline de produção (Hugo + Zenodo): ver [`docs/pipeline_producao.md`](docs/pipeline_producao.md).

OJS (arquivado): ver [`docs/archive/ojs_reference.md`](docs/archive/ojs_reference.md) e [`docs/archive/pipeline_producao_ojs.md`](docs/archive/pipeline_producao_ojs.md).

---

## Regras de dados — Resumo

Regras completas em [`docs/regras_dados.md`](docs/regras_dados.md). Pontos-chave:

- **Travessão**: ` - ` isolado → ` — ` (em-dash). Não tocar em intervalos numéricos, palavras compostas, siglas, referências.
- **Capitalização**: título com maiúscula; subtítulo com minúscula (exceto nome próprio/sigla). Expressões consolidadas: "Arquitetura Moderna Brasileira", "Movimento Moderno", "Educação Patrimonial". Usa `dict/normalizar.py` + `dict.db` (5279 entradas). Ver `docs/devlog_normalizacao_maiusculas.md`.
- **Autores**: partículas (de, da, do) no `givenname`; `familyname` = último sobrenome. Hispânicos: duplo sobrenome.
- **Afiliação**: apenas sigla (`FAU-USP`, `PROPAR-UFRGS`). Sem títulos acadêmicos, endereços, emails.
- **ORCID**: formato `0000-0000-0000-0000` (sem URL).

---

## Organização no OJS

| Volume | Grupo | Diretório | Slugs | Numbers |
|--------|-------|-----------|-------|---------|
| 1 | Brasil | `nacionais/` | sdbr01–sdbr15 | 1–15 |
| 2 | Sudeste | `regionais/se/` | sdmg01, sdrj02–04, sdsp03, 05–09 | varies |
| 3 | Norte/Nordeste | `regionais/nne/` | sdnne01–05, 07–10 | 1–5, 7–10 |
| 4 | Sul | `regionais/sul/` | sdsul01–08, sdpr01–02 | 1–8, PR1–2 |

---

## Status dos Seminários Regionais

### Prontos para produção (29 seminários, ~1211 artigos)

**N/NE** (`regionais/nne/`): sdnne01 (44), sdnne02 (33), sdnne03 (41), sdnne04 (45), sdnne05 (32), sdnne06 (109), sdnne07 (65), sdnne08 (41), sdnne09 (50), sdnne10 (85)

**Sudeste** (`regionais/se/`): sdmg01 (68), sdrj02 (19), sdrj03 (4), sdrj04 (17), sdsp03 (74), sdsp05 (68), sdsp06 (37), sdsp07 (43), sdsp08 (40), sdsp09 (27)

**Sul** (`regionais/sul/`): sdsul01 (48), sdsul02 (35), sdsul03 (39), sdsul04 (46), sdsul05 (37), sdsul06 (24), sdsul07 (46), sdsul08 (51), sdpr01 (26), sdpr02 (10)

Seminários nacionais importados no OJS teste. Importação dos regionais na produção pendente.

### Sem dados (não localizados)
- sdsp04, sdrj01

### Pendências
- Importação dos regionais na produção (ver `docs/pipeline_producao.md`)
- DOIs via ABEC/Crossref (DOI por edição, não por artigo)

---

## GitHub e Sites Estáticos

### Repositório
- **GitHub**: `https://github.com/docomomobr/anais` (público)
- Conta `docomomobr` (usuário, plano free)
- Token PAT em `.env` (gitignored)

### GitHub Pages — Sites estáticos

| Site | Domínio | Repo | Branch | Status |
|------|---------|------|--------|--------|
| Anais | `anais.docomomobrasil.com` | `docomomobr/anais` | `gh-pages` | placeholder |
| Livros | `livros.docomomobrasil.com` | `docomomobr/livros` | `main` | placeholder |

- **DNS**: CNAMEs em `docomomobrasil.com` apontando para `docomomobr.github.io` (provedor Labasoft, pendente criação)
- **Site Hugo**: `site/` (config, layouts, static). Conteúdo gerado (`site/content/`, `site/public/`) é gitignored
- **Imagens do site**: exceção no `.gitignore` para `site/static/img/**`

### Credenciais e segurança
- Credenciais removidas do repo e do histórico git (2026-02-19)
- Senhas em `.credentials` e `.env` (ambos gitignored)
- Scripts leem credenciais de variáveis de ambiente (`OJS_TEST_PASS`, `OJS_PROD_PASS`, etc.)
- Docs usam placeholders (`$OJS_PASS`, `(ver .credentials)`)

---

## Devlog

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
- **Scripts novos**: `extrair_metadados_en.py`, `normalizar_titulos_en.py`
