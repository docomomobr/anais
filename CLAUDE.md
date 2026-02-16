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

### FTP (servidor auxiliar)
- Host: `ftp.app.docomomobrasil.com`
- Usuário: `app`
- Senha: `***`

### WordPress Admin
- URL: `https://docomomobrasil.com/wp-admin/`
- Usuário: `admindocomomo`
- Senha: `***`

### WordPress REST API
- URL base: `https://docomomobrasil.com/wp-json/wp/v2/`
- Application Password (claude26): `***`
- Auth: `admindocomomo:***`

### OJS (Open Journal Systems)
- URL: `https://publicacoes.docomomobrasil.com/`
- Journal principal: `/anais`
- Usuário: `dmacedo`
- Senha: `***`

---

## OJS — Referência rápida

### Limitações da API

- A API **não retorna todos os campos** (ex: `abstract`, `keywords` podem vir vazios). **Sempre verificar na página real** (`/article/view/{id}`) com WebFetch antes de concluir que dados estão faltando.
- O locale `en_US` não está habilitado. Dados em inglês existem no banco mas não são exibidos.
- Conta `dmacedo`: papel de Editor (não Journal Manager nem Site Admin).

### Endpoints úteis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/issues` | GET | Lista edições |
| `/api/v1/submissions` | GET | Lista artigos |
| `/api/v1/submissions?count=N` | GET | Lista N artigos |
| `/api/v1/submissions/{id}` | GET | Detalhes de um artigo |

### Scripts

| Script | Função |
|--------|--------|
| `scripts/generate_ojs_xml.py` | Gera XMLs a partir do `anais.db`. `--with-pdf` (1 artigo/XML) ou metadata-only (1 XML/issue) |
| `scripts/import_ojs.py` | Importa XMLs no OJS. `--per-article` (1 XML/artigo, 15s delay). `--env test` ou `--env prod` |
| `scripts/normalizar_maiusculas.py` | Normaliza capitalização nos títulos do `anais.db`. `--dry-run`, `--slug SLUG` |
| `dict/normalizar.py` | Módulo de normalização de maiúsculas. 3 passadas: palavra, expressão, toponímico contextual |
| `scripts/check_references.py` | Detecta erros em referências: concatenadas, não-referências, fragmentos. `--summary`, `--slug`, `--type` |

Para autenticação, CSRF, operações destrutivas, importação via curl, e estrutura do XML: ver [`docs/ojs_reference.md`](docs/ojs_reference.md).

Pipeline de produção: ver [`docs/pipeline_producao.md`](docs/pipeline_producao.md).

---

## Regras de dados — Resumo

Regras completas em [`docs/regras_dados.md`](docs/regras_dados.md). Pontos-chave:

- **Travessão**: ` - ` isolado → ` — ` (em-dash). Não tocar em intervalos numéricos, palavras compostas, siglas, referências.
- **Capitalização**: título com maiúscula; subtítulo com minúscula (exceto nome próprio/sigla). Expressões consolidadas: "Arquitetura Moderna Brasileira", "Movimento Moderno", "Educação Patrimonial". Usa `dict/normalizar.py` + `dict.db` (4270 entradas). Ver `docs/devlog_normalizacao_maiusculas.md`.
- **Autores**: partículas (de, da, do) no `givenname`; `familyname` = último sobrenome. Hispânicos: duplo sobrenome.
- **Afiliação**: apenas sigla (`FAU-USP`, `PROPAR-UFRGS`). Sem títulos acadêmicos, endereços, emails.
- **ORCID**: formato `0000-0000-0000-0000` (sem URL).

---

## Organização no OJS

| Volume | Grupo | Diretório | Slugs | Numbers |
|--------|-------|-----------|-------|---------|
| 1 | Brasil | `nacionais/` | sdbr01–sdbr15 | 1–15 |
| 2 | Sudeste | `regionais/se/` | sdmg01, sdrj02–04, sdsp03, 05–09 | varies |
| 3 | Norte/Nordeste | `regionais/nne/` | sdnne02, 05, 07–10 | 2, 5, 7, 8, 9, 10 |
| 4 | Sul | `regionais/sul/` | sdsul01–08 | 1–8 |

---

## Status dos Seminários Regionais

### Prontos para produção (23 seminários, ~943 artigos)

**N/NE** (`regionais/nne/`): sdnne02 (33), sdnne05 (32), sdnne07 (65), sdnne08 (41), sdnne09 (50), sdnne10 (85)

**Sudeste** (`regionais/se/`): sdmg01 (68), sdrj02 (19), sdrj03 (4), sdrj04 (17), sdsp03 (74), sdsp05 (68), sdsp06 (37), sdsp07 (43), sdsp08 (40), sdsp09 (27)

**Sul** (`regionais/sul/`): sdsul01 (48), sdsul02 (35), sdsul03 (39), sdsul04 (46), sdsul05 (37), sdsul06 (24), sdsul07 (46), sdsul08 (51)

Todos importados no OJS teste. Importação na produção pendente.

### Sem dados (não localizados)
- sdnne01 (Recife 2006), sdnne03 (João Pessoa 2010), sdnne04 (Natal 2012)
- sdnne06 (Teresina 2016 — só caderno de resumos)
- sdsp04, sdrj01

### Pendências
- Importação dos 23 regionais na produção (ver `docs/pipeline_producao.md`)
- DOIs via ABEC/Crossref (DOI por edição, não por artigo)
