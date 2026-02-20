# Pipeline de Publicação — Hugo + Zenodo

Pipeline para publicação dos anais Docomomo Brasil. Substitui o pipeline OJS (arquivado em `archive/pipeline_producao_ojs.md`).

---

## Arquitetura de hospedagem

| Serviço | O que hospeda | URL |
|---------|--------------|-----|
| **GitHub Pages** | Site estático Hugo (anais) | `anais.docomomobrasil.com` |
| **GitHub Pages** | Site estático Hugo (livros) | `livros.docomomobrasil.com` |
| **WordPress** | Site institucional | `docomomobrasil.com` |
| **Zenodo** | PDFs dos artigos e livros (fonte canônica) | `zenodo.org/records/{id}/files/{arquivo}.pdf` |

### DNS (CNAME em `docomomobrasil.com`)

| Tipo | Host | Valor |
|------|------|-------|
| CNAME | `anais` | `docomomobr.github.io` |
| CNAME | `livros` | `docomomobr.github.io` |

### Estratégia de links

- **Download de PDF**: link direto para o arquivo no Zenodo (`zenodo.org/records/{id}/files/{arquivo}.pdf`)
- **DOI**: exibido na página do artigo para citação acadêmica (`doi.org/10.5281/zenodo.{id}`)
- Não usar o DOI como link de download (landing page adiciona clique extra)
- **sdbr04**: os 79 artigos são apenas resumos (sem texto completo). Não subir PDFs ao Zenodo para este seminário.

### Estimativa de storage

- Site anais (~2400 artigos, 36 seminários): ~30 MB
- Site livros (~100–200 títulos, com capas): ~30–50 MB
- Total: ~60–80 MB (limite GitHub Pages: 1 GB)

---

## Pré-requisitos

Banco `anais.db` com tratamento completo (ver [`pipeline_tratamento.md`](pipeline_tratamento.md)):

- [ ] Títulos normalizados — `scripts/normalizar_maiusculas.py`
- [ ] Referências limpas — `scripts/clean_references.py` + `scripts/check_references.py`
- [ ] Autores deduplicados — `scripts/dedup_authors.py`
- [ ] ORCIDs buscados — `scripts/fetch_orcid.py`
- [ ] Fichas catalográficas revisadas — `revisao/fichas_catalograficas.yaml`
- [ ] Dump atualizado — `python3 scripts/dump_anais_db.py`

---

## Fase 1 — Upload para Zenodo

### 1.1. Upload dos PDFs

```bash
# Sandbox (teste)
python3 scripts/upload_zenodo.py --env sandbox --dry-run
python3 scripts/upload_zenodo.py --env sandbox

# Produção
python3 scripts/upload_zenodo.py --env production --dry-run
python3 scripts/upload_zenodo.py --env production
```

O script:
- Lê `anais.db` + PDFs dos artigos
- Cria um registro Zenodo por artigo (tipo: conference paper)
- Campos: creators, contributors (editors), notes (ficha catalográfica), conference_url, ISBN
- Comunidade: `docomomobr`
- Agrupamento por keyword com nome do seminário
- `--skip-existing`: pula artigos já publicados no Zenodo
- Tokens em `.env`: `ZENODO_SANDBOX_TOKEN`, `ZENODO_TOKEN`

**IMPORTANTE — API InvenioRDM (nova)**: O Zenodo migrou para InvenioRDM. Os testes anteriores na sandbox usaram a API legacy (`/api/deposit/depositions`), que tem limitações (ex: `imprint_isbn` falha silenciosamente com ISBNs inválidos). **Usar a nova API** (`/api/records/{id}/draft`) para produção. Ver detalhes em `CLAUDE.md` (seção "Zenodo API").

Antes de subir os ~920 artigos, testar na sandbox com a nova API:
1. Criar 1 depósito via nova API
2. Verificar que `custom_fields["imprint:imprint"]` funciona (ISBN, place, title)
3. Verificar que `custom_fields["meeting:meeting"]` funciona (conference metadata)
4. Só depois escalar para produção

### 1.2. Verificar

```bash
python3 scripts/upload_zenodo.py --env production --verify
```

### 1.3. Registrar DOIs no banco

Após upload, registrar os DOIs e record_ids no `anais.db`:

```bash
python3 scripts/upload_zenodo.py --env production --sync-ids
```

---

## Fase 2 — Gerar site Hugo

### 2.1. Gerar conteúdo

```bash
python3 scripts/db2hugo.py --all --outdir site/content
```

O script gera:
- Uma página por seminário (issue)
- Uma página por artigo (com metadados, link para PDF no Zenodo, DOI)
- Índices por região/grupo

### 2.2. Build

```bash
cd site && hugo
```

Verificar: build sem erros, `public/robots.txt` existe, `public/sitemap.xml` com URLs de artigos.

### 2.3. Indexar busca (Pagefind)

```bash
npx pagefind --site public --glob "artigos/**/*.html"
```

### 2.4. Deploy

Push para o repositório GitHub. GitHub Pages publica automaticamente via GitHub Actions.

---

## Fase 3 — Verificação final

- [ ] Build sem erros
- [ ] Busca funciona (Pagefind)
- [ ] Links para PDFs no Zenodo funcionam (spot check 5-10 artigos)
- [ ] DOIs resolvem corretamente
- [ ] Metadados completos (título, autores, resumo, keywords, referências)
- [ ] ORCIDs aparecem nos autores cadastrados
- [ ] Capas dos seminários exibidas
- [ ] Navegação entre seminários e artigos funciona
- [ ] `robots.txt` e `sitemap.xml` acessíveis
- [ ] Analytics configurado (GoatCounter)

### 3.1. Pós-deploy

- [ ] Submit Google Scholar: [scholar.google.com/intl/en/scholar/inclusion.html](https://scholar.google.com/intl/en/scholar/inclusion.html)
- [ ] Verificar indexação após 2–4 semanas

---

## DOIs

- **DOIs via ABEC/Crossref**: DOI por edição (não por artigo). sdbr15 e sdnne10 já têm DOIs Even3/Crossref (prefixo 10.29327).
- **DOIs Zenodo**: cada artigo recebe DOI individual (`10.5281/zenodo.{id}`)

---

## Scripts de produção

| Script | Fase | Função |
|--------|------|--------|
| `upload_zenodo.py` | 1 | Upload PDFs para Zenodo (sandbox/production, dry-run, skip-existing) |
| `db2hugo.py` | 2 | Gera conteúdo Hugo a partir do anais.db |

---

## OJS (arquivado)

O OJS (`publicacoes.docomomobrasil.com`) foi utilizado para publicação dos 15 nacionais e 21 regionais em teste. A documentação completa está em `archive/pipeline_producao_ojs.md` e `archive/ojs_reference.md`.
