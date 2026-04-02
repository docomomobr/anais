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
- **Resumos (document_type=resumo)**: não subir PDFs ao Zenodo — o conteúdo do resumo vai integralmente nos metadados do site (abstract, keywords, autores). Upload de PDF de resumo é redundante. Afeta: sdbr04 (79), sdnne06 (43), sdbr09 (1), sdbr11 (1).
- **Artigos com DOI externo**: sempre subir o PDF para o Zenodo (fonte canônica do arquivo). Na página do artigo: exibir **um DOI só** — o externo (Even3, periódico) quando existir, senão o do Zenodo. O link de download do PDF sempre aponta para o Zenodo.

### Estimativa de storage

- Site anais (~2400 artigos, 36 seminários): ~30 MB
- Site livros (~100–200 títulos, com capas): ~30–50 MB
- Total: ~60–80 MB (limite GitHub Pages: 1 GB)

---

## Pré-requisitos

Banco `anais.db` com tratamento completo (ver [`pipeline_revisao.md`](pipeline_revisao.md)):

- [ ] Todos os seminários revisados (pipeline de revisão completo)
- [ ] Seções mapeadas para todos os artigos (ou aceitável que faltem para sdbr02, 03, 06, 07)
- [ ] Títulos normalizados — `scripts/normalizar_maiusculas.py`
- [ ] Referências limpas — `scripts/clean_references.py` + `scripts/check_references.py`
- [ ] Autores deduplicados — `scripts/dedup_authors.py`
- [ ] ORCIDs buscados — `scripts/fetch_orcid.py`
- [ ] Fichas catalográficas revisadas — `revisao/fichas_catalograficas.yaml`
- [ ] `document_type` correto para todos os artigos (artigo/resumo/mesa)
- [ ] Dump atualizado — `python3 scripts/dump_anais_db.py`

---

## Fase 0 — Limpeza pré-produção

### 0.1. Limpar DOIs de sandbox

Se houve testes no sandbox, os DOIs de teste (`10.5072/zenodo.*`) podem ter sido gravados no banco. Limpar:

```bash
sqlite3 anais.db "UPDATE articles SET doi = NULL, zenodo_record_id = NULL WHERE doi LIKE '10.5072/%'"
```

### 0.2. Verificar integridade

```bash
# Artigos sem seção (aceitar ou resolver antes)
sqlite3 anais.db "SELECT seminar_slug, COUNT(*) FROM articles WHERE section_id IS NULL GROUP BY seminar_slug"

# document_type inconsistente
sqlite3 anais.db "SELECT document_type, COUNT(*) FROM articles GROUP BY document_type"

# Artigos com PDF mas sem file no banco
sqlite3 anais.db "SELECT id FROM articles WHERE file IS NULL AND document_type='artigo' AND seminar_slug LIKE 'sdbr%'"
```

---

## Fase 1 — Upload para Zenodo

O script `upload_zenodo.py` usa a **API InvenioRDM** (`POST /api/records`), não a legacy.

### 1.0. Testar no sandbox

Já validado (2026-03-16): 1 artigo de cada seminário nacional subiu sem erros.

```bash
# Dry-run para inspecionar payload
python3 scripts/upload_zenodo.py --sandbox --dry-run --seminar sdbr15 --limit 1

# Upload real no sandbox
python3 scripts/upload_zenodo.py --sandbox --seminar sdbr15 --limit 1
```

**ATENÇÃO**: O script grava DOIs no banco mesmo no modo sandbox. Rodar Fase 0.1 antes de ir para produção.

### 1.1. Upload dos artigos (produção)

Um seminário por vez, na ordem. Verificar resultado antes de prosseguir.

```bash
# Dry-run primeiro
python3 scripts/upload_zenodo.py --dry-run --seminar sdbr01

# Upload real
python3 scripts/upload_zenodo.py --seminar sdbr01
```

O script:
- Cria um registro Zenodo por artigo (tipo: `publication-conferencepaper`)
- Upload do PDF em 3 etapas (initiate → content → commit)
- Metadados: creators (com ORCID e afiliação), contributors (editors), meeting (conference), imprint (ISBN, pages), subjects (keywords PT+EN+ES), description (abstracts PT+EN+ES), additional_titles (EN, ES)
- Pula automaticamente: resumos, artigos sem PDF, artigos sem autores, artigos que já têm DOI
- Grava DOI no banco após publicação bem-sucedida
- Rate limit: 1.5s entre artigos
- Log: `/tmp/zenodo_{slug}_results.json`
- Token em `.env`: `ZENODO_TOKEN` (produção) ou `ZENODO_SANDBOX_TOKEN` (sandbox)

### 1.2. Upload dos volumes completos (opcional)

PDF dos anais inteiros, para seminários que possuem `volume_pdf`:

```bash
python3 scripts/upload_zenodo.py --seminar sdbr01 --upload-volume
```

### 1.3. Comunidade Zenodo (opcional)

Para submeter à comunidade `docomomobr` (se existir na produção):

```bash
python3 scripts/upload_zenodo.py --seminar sdbr01 --community docomomobr
```

O script cria o review request, submete (que também publica) e auto-aceita se o token for do curador.

### 1.4. Verificar

Após upload de cada seminário, verificar 2-3 registros manualmente:

- Abrir no Zenodo: título, autores, ORCID, abstract, keywords
- Baixar o PDF: verificar que é o arquivo correto
- Conferir meeting, ISBN, pages

### 1.5. Resumo de artigos para upload

| Seminário | Artigos | Com PDF | Resumos (skip) | Upload |
|-----------|---------|---------|----------------|--------|
| sdbr01 | 6 | 6 | 0 | 6 |
| sdbr02 | 22 | 22 | 0 | 22 |
| sdbr03 | 56 | 56 | 0 | 56 |
| sdbr04 | 79 | 79 | 79 | 0 |
| sdbr05 | 56 | 56 | 0 | 56 |
| sdbr06 | 64 | 64 | 0 | 64 |
| sdbr07 | 62 | 62 | 0 | 62 |
| sdbr08 | 188 | 188 | 0 | 188 |
| sdbr09 | 170 | 170 | 24 | 146 |
| sdbr10 | 118 | 118 | 0 | 118 |
| sdbr11 | 101 | 101 | 1 | 100 |
| sdbr12 | 82 | 82 | 0 | 82 |
| sdbr13 | 181 | 181 | 0 | 181 |
| sdbr14 | 122 | 122 | 0 | 122 |
| sdbr15 | 101 | 101 | 0 | 101 |
| **Total** | **1408** | **1408** | **104** | **~1304** |

### 1.6. Resumo de artigos regionais para upload

| Seminário | Artigos | Com PDF | Resumos (skip) | Upload |
|-----------|---------|---------|----------------|--------|
| sdmg01 | 26 | 26 | 0 | 26 |
| sdnne01 | 44 | 44 | 0 | 44 |
| sdnne02 | 33 | 33 | 0 | 33 |
| sdnne03 | 41 | 41 | 0 | 41 |
| sdnne04 | 45 | 45 | 0 | 45 |
| sdnne05 | 32 | 32 | 0 | 32 |
| sdnne06 | 109 | 66 | 43 | 66 |
| sdnne07 | 65 | 65 | 0 | 65 |
| sdnne08 | 41 | 41 | 0 | 41 |
| sdnne09 | 50 | 50 | 0 | 50 |
| sdnne10 | 85 | 85 | 0 | 85 |
| sdpr01 | 26 | 26 | 0 | 26 |
| sdpr02 | 19 | 19 | 0 | 19 |
| sdrj02 | 19 | 19 | 0 | 19 |
| sdrj03 | 4 | 4 | 0 | 4 |
| sdrj04 | 17 | 17 | 0 | 17 |
| sdsp03 | 74 | 74 | 0 | 74 |
| sdsp05 | 68 | 68 | 0 | 68 |
| sdsp06 | 37 | 37 | 0 | 37 |
| sdsp07 | 43 | 43 | 0 | 43 |
| sdsp08 | 40 | 40 | 0 | 40 |
| sdsp09 | 27 | 27 | 0 | 27 |
| sdsul01 | 48 | 48 | 0 | 48 |
| sdsul02 | 35 | 35 | 0 | 35 |
| sdsul03 | 39 | 39 | 0 | 39 |
| sdsul04 | 46 | 46 | 0 | 46 |
| sdsul05 | 37 | 37 | 0 | 37 |
| sdsul06 | 24 | 24 | 0 | 24 |
| sdsul07 | 46 | 46 | 0 | 46 |
| sdsul08 | 51 | 51 | 0 | 51 |
| **Total** | **1311** | **1268** | **43** | **~1268** |

### 1.7. Dataset Zenodo

Ver [`zenodo_dataset.md`](zenodo_dataset.md) — procedimento completo para atualizar o dataset do projeto via `.zenodo.json` + GitHub release.

---

## Fase 2 — Gerar site Hugo

### 2.1. Gerar conteúdo

```bash
python3 scripts/db2hugo.py --all --outdir site/content
```

O script gera:
- `_index.md` na raiz (homepage)
- `_index.md` por âmbito (brasil, se, nne, sul)
- `_index.md` por seminário (com capa, ficha, metadados)
- `index.md` por artigo (front matter completo + referências no body)
- DOI e `zenodo_pdf_url` vêm do banco (gravados na Fase 1)

### 2.2. Build

```bash
cd site && hugo
```

Verificar:
- Build sem erros
- `public/sitemap.xml` com URLs de artigos
- `public/robots.txt` existe

### 2.3. Indexar busca (Pagefind)

```bash
npx pagefind --site public
```

(Sem `--glob` — indexa tudo. Pagefind detecta automaticamente as páginas relevantes.)

### 2.4. Preview local

```bash
cd site && hugo server
```

Verificar:
- Navegação entre âmbitos, seminários e artigos
- Capas exibidas nas páginas de artigo e de seminário
- Links de PDF apontam para Zenodo
- DOIs aparecem e resolvem
- Busca funciona (Pagefind)
- Abstracts em PT/EN/ES renderizam
- Keywords são links para taxonomia

---

## Fase 3 — Deploy

### 3.1. GitHub Actions — deploy automático

O deploy é automático via `.github/workflows/deploy.yml`. A cada push na branch `main`, o workflow:

1. Reconstrói o banco a partir de `anais.sql`
2. **Limpa** todo o conteúdo Hugo gerado (`site/content/brasil/`, `site/content/sul/` etc.)
3. **Gera** conteúdo apenas para os seminários listados na variável `SEMINARS`
4. Build Hugo + Pagefind
5. Deploy para GitHub Pages

**TRAVA DE PUBLICAÇÃO:** O workflow contém uma lista explícita de seminários autorizados para publicação (`env: SEMINARS`). Mesmo que `site/content/` de um seminário não autorizado seja commitado no repo, ele será **apagado** antes do build. Isso impede publicação acidental.

### 3.2. Publicar um novo seminário no site

Para publicar um seminário que completou a revisão:

1. Editar `.github/workflows/deploy.yml`
2. Adicionar o slug na variável `SEMINARS` (ex: `sdbr16`)
3. Commit e push — o deploy inclui o novo seminário automaticamente

```bash
# Exemplo: publicar sdbr16
# Editar .github/workflows/deploy.yml, adicionar sdbr16 à lista SEMINARS
git add .github/workflows/deploy.yml
git commit -m "deploy: publicar sdbr16 no site"
git push
```

**NÃO** usar `db2hugo.py --all` + commit de `site/content/` como forma de publicar. A geração de conteúdo acontece no workflow, não localmente.

### 3.3. Atualizar seminários já publicados

Alterações no banco (títulos, abstracts, refs, autores) são automaticamente refletidas no próximo deploy — basta fazer push de `anais.sql`. O workflow regenera o conteúdo Hugo a partir do banco.

### 3.3. Configurar DNS

No provedor de DNS de `docomomobrasil.com`:
- Criar CNAME `anais` → `docomomobr.github.io`
- No GitHub Pages (repo settings): adicionar custom domain `anais.docomomobrasil.com`, habilitar HTTPS

---

## Fase 4 — Verificação final

### Checklist funcional

- [ ] Site acessível em `anais.docomomobrasil.com`
- [ ] HTTPS funciona (certificado Let's Encrypt via GitHub Pages)
- [ ] Build sem erros
- [ ] Busca funciona (Pagefind)
- [ ] Links para PDFs no Zenodo funcionam (spot check 5-10 artigos de seminários diferentes)
- [ ] DOIs resolvem corretamente (`curl -I https://doi.org/10.5281/zenodo.XXXXX`)
- [ ] Metadados completos (título, autores, resumo, keywords, referências)
- [ ] ORCIDs aparecem nos autores cadastrados
- [ ] Capas dos seminários exibidas (página do artigo e do seminário)
- [ ] Navegação: início → âmbito → seminário → artigo → voltar
- [ ] Taxonomias: autores e palavras-chave listam e filtram
- [ ] `robots.txt` e `sitemap.xml` acessíveis
- [ ] Resumos (sdbr04 etc.) aparecem sem botão "Baixar PDF"

### Checklist SEO / indexação

- [ ] `<meta>` tags (Open Graph, Dublin Core) presentes nas páginas de artigo
- [ ] JSON-LD (ScholarlyArticle) renderiza no HTML
- [ ] COinS tags presentes
- [ ] Sitemap submetido ao Google Search Console
- [ ] Submit Google Scholar: [scholar.google.com/intl/en/scholar/inclusion.html](https://scholar.google.com/intl/en/scholar/inclusion.html)
- [ ] Verificar indexação após 2–4 semanas

### Checklist Zenodo

- [ ] Todos os registros publicados e acessíveis
- [ ] DOIs resolvem para a landing page correta
- [ ] PDFs baixam corretamente
- [ ] Metadados no Zenodo batem com o site (título, autores, abstract)
- [ ] Comunidade `docomomobr` aparece nos registros (se configurada)

---

## DOIs

- **DOIs Zenodo**: cada artigo recebe DOI individual (`10.5281/zenodo.{id}`)
- **DOIs externos (Even3/Crossref)**: sdbr15 e sdnne10 já têm DOIs Even3 (prefixo `10.29327`). Estes DOIs devem ser preservados — o script pula artigos que já têm DOI.
- **DOIs de coleção**: Even3 vende DOI como serviço opcional. A maioria dos artigos NÃO tem DOI individual, apenas o DOI da coleção. Verificar artigo por artigo se necessário.

---

## Scripts de produção

| Script | Fase | Função |
|--------|------|--------|
| `upload_zenodo.py` | 1 | Upload PDFs para Zenodo via API InvenioRDM. `--sandbox`, `--dry-run`, `--seminar`, `--limit`, `--community`, `--upload-volume` |
| `fix_zenodo_metadata.py` | pós-1 | Corrige metadados de artigos já publicados no Zenodo. Cria nova versão com payload completo do DB (PUT substitui tudo). Aceita múltiplos IDs. `--dry-run` |
| `db2hugo.py` | 2 | Gera conteúdo Hugo a partir do anais.db. `--all`, `--seminar`, `--outdir` |

---

## Fase 5 — Migração do OJS

Fluxo para desativar o OJS (`publicacoes.docomomobrasil.com`) e redirecionar para o site Hugo (`anais.docomomobrasil.com`).

**Restrição técnica**: GitHub Pages aceita apenas 1 custom domain por repositório. Os redirects de `publicacoes.docomomobrasil.com` precisam de um repo separado.

### 5.1. Coexistência (2-4 semanas após deploy)

- OJS continua rodando normalmente em `publicacoes.docomomobrasil.com` (sem alteração)
- Site novo já ativo em `anais.docomomobrasil.com`
- Submeter sitemap do novo site ao Google Search Console
- Esperar Google Scholar começar a indexar o novo site
- Enquanto isso, preparar o repo de redirects (5.2)

### 5.2. Preparar repo de redirects

Criar repositório `docomomobr/publicacoes` com GitHub Pages:
- Custom domain: `publicacoes.docomomobrasil.com`
- Conteúdo: páginas HTML estáticas com `<meta http-equiv="refresh">` para cada URL antiga

Mapeamento de URLs:

| URL antiga (OJS) | URL nova (Hugo) |
|-------------------|-----------------|
| `/anais/issue/archive` | `anais.docomomobrasil.com/` |
| `/anais/issue/view/sdbr15` | `anais.docomomobrasil.com/brasil/sdbr15/` |
| `/anais/article/view/692` | `anais.docomomobrasil.com/brasil/sdbr15/sdbr15-001/` |
| `/anais/index` | `anais.docomomobrasil.com/` |
| `/anais/issue/current` | `anais.docomomobrasil.com/brasil/sdbr15/` |

O mapeamento OJS numeric ID → article ID está em `docs/ojs_article_mapping.json`.

Cada página de redirect:
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=https://anais.docomomobrasil.com/brasil/sdbr15/sdbr15-001/">
  <link rel="canonical" href="https://anais.docomomobrasil.com/brasil/sdbr15/sdbr15-001/">
  <title>Redirecionando...</title>
</head>
<body>
  <p>Este conteúdo foi movido para <a href="https://anais.docomomobrasil.com/brasil/sdbr15/sdbr15-001/">anais.docomomobrasil.com</a>.</p>
</body>
</html>
```

### 5.3. Ativar redirects

1. Fazer deploy do repo `docomomobr/publicacoes` no GitHub Pages
2. Testar redirects: abrir URLs antigas e verificar que redirecionam
3. Configurar DNS: CNAME `publicacoes` → `docomomobr.github.io`
4. No GitHub Pages (repo settings): custom domain `publicacoes.docomomobrasil.com`, habilitar HTTPS

### 5.4. Desligar OJS

- [ ] Confirmar que Google Scholar indexou o novo site (verificar 2-4 semanas após deploy)
- [ ] Confirmar que redirects funcionam para todas as URLs
- [ ] Desligar o servidor OJS
- [ ] Manter repo de redirects indefinidamente (preserva citações antigas)

### Checklist de migração

- [ ] Site novo acessível e completo
- [ ] Banner no OJS ativo
- [ ] Sitemap submetido ao Google Search Console
- [ ] Google Scholar indexando novo site
- [ ] Repo de redirects criado e deployado
- [ ] DNS `publicacoes` apontando para GitHub Pages
- [ ] Redirects testados (amostra de 10-20 artigos)
- [ ] OJS desligado
- [ ] Redirects funcionando após desligamento

---

## OJS (arquivado)

O OJS (`publicacoes.docomomobrasil.com`) foi utilizado para publicação dos 15 nacionais e 21 regionais em teste. A documentação completa está em `archive/pipeline_producao_ojs.md` e `archive/ojs_reference.md`.
