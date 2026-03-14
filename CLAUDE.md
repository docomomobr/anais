# Diretrizes do Projeto — Anais Docomomo Brasil

Convenções e referência rápida para migração dos anais dos seminários Docomomo Brasil para o OJS.

Referência técnica OJS completa: [`docs/ojs_reference.md`](docs/ojs_reference.md)
Regras de processamento de dados: [`docs/regras_dados.md`](docs/regras_dados.md)

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
| sdbr10 | 118 | 🔄 em revisão | 2026-03-14 |

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
1. Consultar [`docs/pipeline_tratamento.md`](docs/pipeline_tratamento.md) para o fluxo completo
2. Consultar [`docs/dedup_autores.md`](docs/dedup_autores.md) para deduplicação de autores
3. Consultar a memória em `.claude/projects/.../memory/MEMORY.md`
4. Verificar se já existe script em `scripts/` ou `regionais/*/scripts/`
5. Se o script existe, USAR. Se não existe, PERGUNTAR antes de criar.
6. NUNCA escrever Python ad-hoc inline quando existe script para a tarefa.
7. NUNCA alterar o banco sem aprovação explícita do usuário.

Quando o usuário diz "rodar o pipeline", significa executar os scripts documentados na ordem documentada — não inventar processo novo.

### Como rodar o pipeline completo

Quando o usuário pedir "rode o pipeline completo nos seminários X, Y, Z":
1. Abrir `docs/pipeline_tratamento.md` e executar CADA fase na ordem (4→5→6→7)
2. Dentro de cada fase, executar CADA sub-etapa na ordem documentada
3. Reportar resultado de cada etapa de forma concisa e CONTINUAR para a próxima
4. NÃO parar para perguntar entre etapas — só parar se houver erro bloqueante
5. Ao final, apresentar um resumo consolidado com os problemas que precisam de decisão humana

As fases 1-3 (aquisição, extração, construção do YAML) são feitas antes e não fazem parte de "rodar o pipeline".

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
| `scripts/db2hugo.py` | Gera conteúdo Hugo a partir do anais.db |
| `scripts/gerar_revisao_html.py` | HTML de revisão por seminário: capa, ficha, artigos por seção. `python3 scripts/gerar_revisao_html.py SLUG` → `/tmp/revisao-SLUG.html` |

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

### 2026-03-14 — Revisão pipeline + sdbr10 refs + abstracts multilíngues

- **Pipeline revisão refatorado**: sweep_refs agora roda ANTES do loop validate (1.2b); loop 1.5 reduzido a A07/A08/A19 (extração fontes/); A05/A06 removidos (ciclo com A21); A10-A13 removidos do loop (cobertos pelo sweep)
- **sweep_refs melhorado**: threshold 300 chars (era 500), novos patterns: publisher boundary, pipe separator, ano isolado, URL isolada, Disponível em: isolado; NON_REF_STARTERS expandido (Ibíd., Op.cit., créditos de foto); truncate_body_text com +12 verbos narrativos
- **1.2c revisão LLM completa**: documentada como etapa obrigatória para TODAS as refs (não só ambíguas). Agente background revisa refs vs fontes/, corrige concatenações/splits/notas, retroalimenta pipeline
- **sdbr10 refs**: revisão LLM de 113 artigos (51 modificados, ~100 refs corrigidas: 45 concatenações, 40 notas, 15 splits). Correções manuais do rev.md aplicadas (029, 055, 057 entre outros)
- **Abstracts multilíngues**: labels fixos ao campo (abstract=Resumo, abstract_en=Abstract, abstract_es=Resumen), ordem por locale (ES: Resumen primeiro). Fallback no Zenodo: abstract → abstract_en → abstract_es. HTML e Hugo atualizados
- **validate_metadata.py**: fix A17/A22 stale refs (sync in-memory); keywords não-JSON parseadas como comma-separated
- **upload_zenodo.py**: SELECT ampliado com abstract_en/es, keywords_en/es, title_en/subtitle_en; fallback inteligente de abstract e keywords por locale
- **fix_validation_issues.py**: fix_a19 integra fontes_plumber/; "The "/"In " removidos de NON_REF_STARTERS (falsos positivos)

### 2026-03-03 — sdnne06 novos PDFs + pipeline produção Hugo

- **sdnne06**: 8 PDFs novos do livro-cd (3 upgrades só-resumo→com-PDF: arts 22, 40, 45; 5 artigos novos: 105-109). Total: 109 artigos (66 artigo, 43 resumo)
- **Metadados extraídos**: abstract_en, keywords_en, referências para os 8 artigos. Arts 108/109 sem abstract (originais não têm)
- **Autores**: merges manuais (Clóvis Jucá→Jucá Neto, Y. Caddah→Yasmine, E. Coutinho→Elane, D. Pessoa→Daniel Victor, Ana Karolyne Liberato). 5 ORCIDs novos
- **document_type=resumo**: 43 artigos sdnne06 marcados; sdbr04 já estava. `upload_zenodo.py` agora pula resumos
- **db2hugo.py**: exporta title_en, subtitle_en, abstract_en, keywords_en, abstract_es, keywords_es
- **Template Hugo**: abstract/keywords EN e ES exibidos; keywords são links para taxonomia `palavras-chave`
- **Control chars**: removido U+0002 de sdbr08-166.abstract, U+0083 de sdsp03-016.abstract_en
- **Scripts novos**: `extrair_metadados_en.py`, `normalizar_titulos_en.py`
