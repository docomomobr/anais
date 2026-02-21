# Diretrizes do Projeto — Anais Docomomo Brasil

Convenções e referência rápida para migração dos anais dos seminários Docomomo Brasil para o OJS.

Referência técnica OJS completa: [`docs/ojs_reference.md`](docs/ojs_reference.md)
Regras de processamento de dados: [`docs/regras_dados.md`](docs/regras_dados.md)

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
│   └── sul/             # Sul (sdsul01-08)
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
| `scripts/upload_zenodo.py` | Upload PDFs para Zenodo (sandbox/production, dry-run, skip-existing) |
| `scripts/db2hugo.py` | Gera conteúdo Hugo a partir do anais.db |

Pipeline de tratamento (novos seminários): ver [`docs/pipeline_tratamento.md`](docs/pipeline_tratamento.md).

Pipeline de produção (Hugo + Zenodo): ver [`docs/pipeline_producao.md`](docs/pipeline_producao.md).

OJS (arquivado): ver [`docs/archive/ojs_reference.md`](docs/archive/ojs_reference.md) e [`docs/archive/pipeline_producao_ojs.md`](docs/archive/pipeline_producao_ojs.md).

---

## Regras de dados — Resumo

Regras completas em [`docs/regras_dados.md`](docs/regras_dados.md). Pontos-chave:

- **Travessão**: ` - ` isolado → ` — ` (em-dash). Não tocar em intervalos numéricos, palavras compostas, siglas, referências.
- **Capitalização**: título com maiúscula; subtítulo com minúscula (exceto nome próprio/sigla). Expressões consolidadas: "Arquitetura Moderna Brasileira", "Movimento Moderno", "Educação Patrimonial". Usa `dict/normalizar.py` + `dict.db` (5013 entradas). Ver `docs/devlog_normalizacao_maiusculas.md`.
- **Autores**: partículas (de, da, do) no `givenname`; `familyname` = último sobrenome. Hispânicos: duplo sobrenome.
- **Afiliação**: apenas sigla (`FAU-USP`, `PROPAR-UFRGS`). Sem títulos acadêmicos, endereços, emails.
- **ORCID**: formato `0000-0000-0000-0000` (sem URL).

---

## Organização no OJS

| Volume | Grupo | Diretório | Slugs | Numbers |
|--------|-------|-----------|-------|---------|
| 1 | Brasil | `nacionais/` | sdbr01–sdbr15 | 1–15 |
| 2 | Sudeste | `regionais/se/` | sdmg01, sdrj02–04, sdsp03, 05–09 | varies |
| 3 | Norte/Nordeste | `regionais/nne/` | sdnne01–03, 05, 07–10 | 1, 2, 3, 5, 7, 8, 9, 10 |
| 4 | Sul | `regionais/sul/` | sdsul01–08 | 1–8 |

---

## Status dos Seminários Regionais

### Prontos para produção (26 seminários, ~1130 artigos)

**N/NE** (`regionais/nne/`): sdnne01 (44), sdnne02 (33), sdnne03 (41), sdnne05 (32), sdnne06 (103), sdnne07 (65), sdnne08 (41), sdnne09 (50), sdnne10 (85)

**Sudeste** (`regionais/se/`): sdmg01 (68), sdrj02 (19), sdrj03 (4), sdrj04 (17), sdsp03 (74), sdsp05 (68), sdsp06 (37), sdsp07 (43), sdsp08 (40), sdsp09 (27)

**Sul** (`regionais/sul/`): sdsul01 (48), sdsul02 (35), sdsul03 (39), sdsul04 (46), sdsul05 (37), sdsul06 (24), sdsul07 (46), sdsul08 (51)

Todos importados no OJS teste. Importação na produção pendente.

### Sem dados (não localizados)
- sdnne04 (Natal 2012)
- sdsp04, sdrj01

### Pendências
- Importação dos 23 regionais na produção (ver `docs/pipeline_producao.md`)
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
