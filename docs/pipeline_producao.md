# Pipeline de Publicação no OJS — Versão Definitiva

Pipeline livre de erros para importação dos 21 seminários regionais no OJS de produção. Incorpora todas as lições do teste pré-produção (2026-02-12).

**Escopo**: apenas os 21 regionais (sdnne, sdrj, sdsp, sdsul). Os 15 nacionais (sdbr01–15) já estão publicados na produção — NUNCA importar.

---

## Pré-requisitos

Antes de iniciar, confirmar que o banco está pronto:

```bash
# Verificar contagens
python3 -c "
import sqlite3
db = sqlite3.connect('anais.db')
c = db.cursor()
c.execute('''SELECT s.slug, COUNT(a.id) FROM seminars s
             JOIN articles a ON a.seminar_id = s.id
             WHERE s.slug NOT LIKE 'sdbr%'
             GROUP BY s.slug ORDER BY s.slug''')
for slug, n in c: print(f'{slug}: {n} artigos')
c.execute('SELECT COUNT(*) FROM authors WHERE orcid IS NOT NULL')
print(f'Autores com ORCID: {c.fetchone()[0]}')
"
```

Resultado esperado: 21 slugs, ~920 artigos total, ~1100 ORCIDs.

Checklist:
- [ ] Títulos normalizados (FUNAG) — `scripts/normalizar_maiusculas.py`
- [ ] Autores deduplicados — `scripts/dedup_authors.py`
- [ ] ORCIDs buscados — `scripts/fetch_orcid.py`
- [ ] Fichas catalográficas revisadas — `revisao/fichas_catalograficas.yaml`
- [ ] Dump atualizado — `python3 scripts/dump_anais_db.py`

---

## Fase 1 — Teste de viabilidade na produção

Antes de gerar 920 XMLs, testar se o provedor de produção aceita base64 (o de teste bloqueava via Cloudflare WAF).

### 1.1. Gerar 1 XML grande de teste

```bash
python3 scripts/generate_ojs_xml.py --with-pdf --slug sdrj04 --outdir /tmp/xml_teste_prod
ls -lhS /tmp/xml_teste_prod/sdrj04-*.xml | head -3
```

Escolher o maior XML (idealmente > 5 MB) para o teste.

### 1.2. Tentar importar na produção

```bash
python3 scripts/import_ojs.py --env prod --per-article --xml-dir /tmp/xml_teste_prod --slug sdrj04 --dry-run
# Se OK no dry-run, importar 1 artigo:
python3 scripts/import_ojs.py --env prod --per-article --xml-dir /tmp/xml_teste_prod --slug sdrj04
```

**Se sucesso** (artigo aparece com galley PDF): prosseguir com o pipeline normal (Fase 2).

**Se 403 Forbidden**: o provedor também bloqueia base64. Usar o Plano B (ver seção no final).

### 1.3. Limpar o artigo de teste

Despublicar e deletar o artigo importado + a issue criada. Queremos começar limpo.

---

## Fase 2 — Gerar XMLs com PDFs embutidos

### 2.1. Gerar todos os 21 regionais

```bash
python3 scripts/generate_ojs_xml.py --with-pdf --outdir xml_prod
```

O script:
- Lê `anais.db` + fichas catalográficas + PDFs dos artigos
- Gera 1 XML por artigo (nome: `{slug}-{NNN}.xml`)
- Embute o PDF em base64 dentro de `<embed>`
- Exclui automaticamente os nacionais (sdbr*)
- Formato das citações: `<citations><citation>texto</citation></citations>`
- Seções com títulos únicos: sufixo ` — {slug}` nos genéricos
- `<pages>` posicionado DEPOIS de `<authors>` e `<article_galley>`
- `<keywords>` só gerado se `parse_keywords()` retorna lista não-vazia

**Resultado esperado**: ~920 XMLs em `xml_prod/`, total ~1.5 GB, todos < 20 MB.

### 2.2. Verificar

```bash
# Contagem por seminário
for slug in sdnne02 sdnne05 sdnne07 sdnne08 sdnne09 sdnne10 \
            sdrj02 sdrj03 sdrj04 \
            sdsp03 sdsp05 sdsp06 sdsp07 sdsp08 sdsp09 \
            sdsul01 sdsul02 sdsul03 sdsul04 sdsul05 sdsul06 sdsul07 sdsul08; do
  echo "$slug: $(ls xml_prod/${slug}-*.xml 2>/dev/null | wc -l) XMLs"
done

# Maior XML (deve ser < 20 MB)
ls -lhS xml_prod/*.xml | head -5

# Verificar que nenhum nacional escapou
ls xml_prod/sdbr*.xml 2>/dev/null && echo "ERRO: nacionais presentes!" || echo "OK: sem nacionais"
```

---

## Fase 3 — Importar no OJS

### 3.1. Importar tudo (background)

```bash
python3 scripts/import_ojs.py --env prod --per-article --xml-dir xml_prod
```

O script:
- Agrupa XMLs por slug (`{slug}-*.xml`)
- Para cada XML: login fresco → upload → importBounce → import
- Delay de 15s entre artigos
- Para no primeiro erro real (não tenta recuperar parciais)
- Estima ~4h para 920 artigos

**Rodar em background** — nunca bloquear o prompt.

### 3.2. Monitorar

Acompanhar o log. Se parar com erro:

1. **Identificar** qual seminário/artigo falhou
2. **Verificar** na API se a issue ficou parcial (artigos importados < esperado)
3. **Limpar** a issue parcial (despublicar + deletar todos os artigos + a issue)
4. **Corrigir** o XML problemático
5. **Recomeçar** do seminário que falhou: `--slug {slug}`

**Regra de ouro**: deu problema → parar → apagar tudo da issue → recomeçar limpo. NUNCA retentar sem limpar.

### 3.3. Verificar contagens

```bash
python3 scripts/import_ojs.py --env prod --verify
```

Comparar com o esperado do banco:

| Slug | Esperado |
|------|----------|
| sdnne02 | 33 |
| sdnne05 | 32 |
| sdnne07 | 65 |
| sdnne08 | 41 |
| sdnne09 | 50 |
| sdnne10 | 85 |
| sdrj02 | 19 |
| sdrj03 | 4 |
| sdrj04 | 17 |
| sdsp03 | 75 |
| sdsp05 | 69 |
| sdsp06 | 37 |
| sdsp07 | 43 |
| sdsp08 | 40 |
| sdsp09 | 27 |
| sdsul01 | 48 |
| sdsul02 | 35 |
| sdsul03 | 39 |
| sdsul04 | 46 |
| sdsul05 | 37 |
| sdsul06 | 24 |
| sdsul07 | 46 |
| sdsul08 | 51 |

---

## Fase 4 — Configurar issues (pós-importação)

### 4.1. Desmarcar flags de exibição

Em cada issue, desmarcar "Mostrar Volume", "Mostrar Número", "Mostrar Ano". Manter apenas "Mostrar Título".

```python
import requests, re

BASE = 'https://publicacoes.docomomobrasil.com/anais'
s = requests.Session()
s.post(f'{BASE}/login/signIn', data={'username': 'dmacedo', 'password': '***'})

# Listar issues
r = s.get(f'{BASE}/api/v1/issues?count=100')
issues = r.json()['items']
regionais = [i for i in issues if not i.get('urlPath', '').startswith('sdbr')]

for issue in regionais:
    iid = issue['id']
    slug = issue.get('urlPath', f'ID-{iid}')

    # Obter formulário
    r = s.get(f'{BASE}/$$$call$$$/grid/issues/back-issue-grid/edit-issue-data?issueId={iid}',
              headers={'X-Requested-With': 'XMLHttpRequest'})
    html = r.json()['content']
    csrf = re.search(r'name="csrfToken"[^>]*value="([^"]+)"', html).group(1)

    # Extrair TODOS os campos do formulário
    fields = {}
    for m in re.finditer(r'name="([^"]+)"[^>]*value="([^"]*)"', html):
        fields[m.group(1)] = m.group(2)
    for m in re.finditer(r'name="([^"]+)"[^>]*>(.*?)</textarea>', html, re.S):
        fields[m.group(1)] = m.group(2)

    # Desmarcar volume/number/year, manter título
    fields['csrfToken'] = csrf
    fields['showTitle'] = '1'
    for flag in ['showVolume', 'showNumber', 'showYear']:
        fields.pop(flag, None)

    # CRÍTICO: setar urlPath e description explicitamente (senão são apagados!)
    fields['urlPath'] = slug
    # description: setar da ficha catalográfica (ver Fase 4.2)

    s.post(f'{BASE}/$$$call$$$/grid/issues/back-issue-grid/update-issue?issueId={iid}',
           data=fields, headers={'X-Requested-With': 'XMLHttpRequest'})
    print(f'{slug}: OK')

    # Re-login a cada 4 issues (sessão expira rápido)
    if regionais.index(issue) % 4 == 3:
        s.post(f'{BASE}/login/signIn', data={'username': 'dmacedo', 'password': '***'})
```

### 4.2. Atualizar descriptions (fichas catalográficas)

O `update-issue` apaga `description` se não for setada explicitamente. Combinar com a etapa acima: na mesma requisição, setar `fields['description[pt_BR]']` com a ficha catalográfica linkificada.

```python
import yaml

# Carregar fichas
with open('revisao/fichas_catalograficas.yaml', 'r') as f:
    fichas_raw = yaml.safe_load(f)
fichas = {item['slug']: item['ficha'] for item in fichas_raw}

# No loop acima, adicionar:
fields['description[pt_BR]'] = linkify_ficha(fichas.get(slug, ''))
```

A função `linkify_ficha()` (em `generate_ojs_xml.py`) converte URLs e DOIs em hyperlinks.

### 4.3. Upload de capas (PNG)

Duas etapas obrigatórias por issue: upload do arquivo + submit do formulário.

```python
import os

CAPAS = {
    'sdnne02': 'regionais/nne/capas/sdnne02.png',
    'sdnne05': 'regionais/nne/capas/sdnne05.png',
    # ... (preencher todos os 21)
    'sdsul08': 'regionais/sul/capas/sdsul08.png',
}

for issue in regionais:
    iid = issue['id']
    slug = issue.get('urlPath', '')
    capa_path = CAPAS.get(slug)
    if not capa_path or not os.path.exists(capa_path):
        print(f'{slug}: sem capa, pulando')
        continue

    # 1. Obter formulário + CSRF
    r = s.get(f'{BASE}/$$$call$$$/grid/issues/back-issue-grid/edit-issue-data?issueId={iid}',
              headers={'X-Requested-With': 'XMLHttpRequest'})
    html = r.json()['content']
    csrf = re.search(r'name="csrfToken"[^>]*value="([^"]+)"', html).group(1)

    # 2. Upload da imagem → temporaryFileId
    with open(capa_path, 'rb') as f:
        r2 = s.post(f'{BASE}/$$$call$$$/grid/issues/back-issue-grid/upload-file',
                    files={'uploadedFile': (os.path.basename(capa_path), f, 'image/png')},
                    data={'csrfToken': csrf},
                    headers={'X-Requested-With': 'XMLHttpRequest'})
    temp_id = r2.json()['temporaryFileId']

    # 3. Extrair campos do formulário
    fields = {}
    for m in re.finditer(r'name="([^"]+)"[^>]*value="([^"]*)"', html):
        fields[m.group(1)] = m.group(2)
    for m in re.finditer(r'name="([^"]+)"[^>]*>(.*?)</textarea>', html, re.S):
        fields[m.group(1)] = m.group(2)

    # 4. Submeter com tudo explícito
    fields['csrfToken'] = csrf
    fields['temporaryFileId'] = str(temp_id)
    fields['urlPath'] = slug                                    # OBRIGATÓRIO!
    fields['description[pt_BR]'] = linkify_ficha(fichas[slug])  # OBRIGATÓRIO!
    fields['showTitle'] = '1'
    for flag in ['showVolume', 'showNumber', 'showYear']:
        fields.pop(flag, None)

    s.post(f'{BASE}/$$$call$$$/grid/issues/back-issue-grid/update-issue?issueId={iid}',
           data=fields, headers={'X-Requested-With': 'XMLHttpRequest'})
    print(f'{slug}: capa uploaded')

    # Re-login a cada 4
    if list(CAPAS.keys()).index(slug) % 4 == 3:
        s.post(f'{BASE}/login/signIn', data={'username': 'dmacedo', 'password': '***'})
```

**OJS não aceita SVG** — usar sempre PNG. Para seminários que só têm SVG, converter antes: `inkscape --export-type=png capa.svg`.

---

## Fase 5 — Páginas estáticas e navegação

### 5.1. Gerar HTMLs

```bash
python3 scripts/generate_static_pages.py \
  --base-url /anais \
  --ojs-url https://publicacoes.docomomobrasil.com/anais \
  --ojs-user dmacedo --ojs-pass *** \
  --outdir paginas_estaticas
```

**IMPORTANTE**: executar DEPOIS do upload de capas (Fase 4.3). O script consulta `coverImageUrl` de cada issue na API do OJS para montar os HTMLs com as URLs reais das capas (padrão `/public/journals/{jid}/cover_issue_{ID}_pt_BR.png`).

Resultado: 6 HTMLs em `paginas_estaticas/`:
- `landing.html` — página inicial com os 5 grupos
- `brasil.html`, `norte-nordeste.html`, `rio-de-janeiro.html`, `sao-paulo.html`, `sul.html`

### 5.2. Criar/atualizar páginas no OJS

Páginas são **itens de navegação personalizados** (NMI_TYPE_CUSTOM), nativos do OJS 3.3. NÃO usam o plugin Static Pages.

**Endpoint correto:**
```
$$$call$$$/grid/navigation-menus/navigation-menu-items-grid/update-navigation-menu-item
```

**NÃO usar** (retorna 404):
```
$$$call$$$/plugins/generic/static-pages/static-page-grid/...
```

Se os itens já existem (editar):

```python
# Mapeamento item_id → (path, título, arquivo)
items = {
    ID_LANDING:  ('landing',        'Seminários Docomomo Brasil', 'paginas_estaticas/landing.html'),
    ID_BRASIL:   ('brasil',         'Brasil',                     'paginas_estaticas/brasil.html'),
    ID_NNE:      ('norte-nordeste', 'Norte/Nordeste',             'paginas_estaticas/norte-nordeste.html'),
    ID_RJ:       ('rio-de-janeiro', 'Rio de Janeiro',             'paginas_estaticas/rio-de-janeiro.html'),
    ID_SP:       ('sao-paulo',      'São Paulo',                  'paginas_estaticas/sao-paulo.html'),
    ID_SUL:      ('sul',            'Sul',                        'paginas_estaticas/sul.html'),
}

for item_id, (path, title, html_file) in items.items():
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Obter CSRF do formulário de edição
    r = s.get(f'{BASE}/$$$call$$$/grid/navigation-menus/navigation-menu-items-grid/edit-navigation-menu-item?navigationMenuItemId={item_id}',
              headers={'X-Requested-With': 'XMLHttpRequest'})
    csrf = re.search(r'name="csrfToken"[^>]*value="([^"]+)"', r.json()['content']).group(1)

    data = {
        'csrfToken': csrf,
        'navigationMenuItemId': str(item_id),
        'title[pt_BR]': title,
        'menuItemType': 'NMI_TYPE_CUSTOM',
        'path': path,
        'content[pt_BR]': html_content,
    }
    r = s.post(f'{BASE}/$$$call$$$/grid/navigation-menus/navigation-menu-items-grid/update-navigation-menu-item',
               data=data, headers={'X-Requested-With': 'XMLHttpRequest'})
    print(f'{path}: {r.json().get("status")}')
```

Se os itens ainda não existem (criar): usar `add-navigation-menu-item` em vez de `edit-...`, sem `navigationMenuItemId`.

### 5.3. Configurar homepage

```python
with open('paginas_estaticas/landing.html', 'r', encoding='utf-8') as f:
    landing_html = f.read()

csrf = re.search(r'"csrfToken":"([^"]+)"', s.get(f'{BASE}/management/settings/context').text).group(1)
s.put(f'{BASE}/api/v1/contexts/1',
      json={'additionalHomeContent': {'pt_BR': landing_html}},
      headers={'X-Csrf-Token': csrf})
```

### 5.4. Montar menu de navegação

```python
# Descobrir navigationMenuId do menu primário
r = s.get(f'{BASE}/$$$call$$$/grid/navigation-menus/navigation-menus-grid/fetch-grid',
          headers={'X-Requested-With': 'XMLHttpRequest'})
# Identificar o menu com areaName=primary (geralmente ID 1 ou 3)
MENU_ID = ...

# Obter CSRF
r = s.get(f'{BASE}/$$$call$$$/grid/navigation-menus/navigation-menus-grid/edit-navigation-menu?navigationMenuId={MENU_ID}',
          headers={'X-Requested-With': 'XMLHttpRequest'})
csrf = re.search(r'name="csrfToken"[^>]*value="([^"]+)"', r.json()['content']).group(1)

data = {
    'csrfToken': csrf,
    'navigationMenuId': str(MENU_ID),
    'title': 'Primary Navigation Menu',
    'areaName': 'primary',   # OBRIGATÓRIO! Sem isso o menu desaparece do site.

    # Top-level: regiões
    f'menuTree[{ID_BRASIL}][seq]':  '0',
    f'menuTree[{ID_NNE}][seq]':    '1',
    f'menuTree[{ID_RJ}][seq]':     '2',
    f'menuTree[{ID_SP}][seq]':     '3',
    f'menuTree[{ID_SUL}][seq]':    '4',

    # Dropdown "Sobre" (ID do item existente)
    f'menuTree[{ID_SOBRE}][seq]':  '5',
    # Sub-itens do dropdown
    f'menuTree[{ID_ATUAL}][seq]':         '0',
    f'menuTree[{ID_ATUAL}][parentId]':    str(ID_SOBRE),
    f'menuTree[{ID_ARQUIVOS}][seq]':      '1',
    f'menuTree[{ID_ARQUIVOS}][parentId]': str(ID_SOBRE),
    # ... demais sub-itens
}
s.post(f'{BASE}/$$$call$$$/grid/navigation-menus/navigation-menus-grid/update-navigation-menu',
       data=data, headers={'X-Requested-With': 'XMLHttpRequest'})
```

**Menu desejado:**
```
Brasil → /brasil
Norte/Nordeste → /norte-nordeste
Rio de Janeiro → /rio-de-janeiro
São Paulo → /sao-paulo
Sul → /sul
Sobre ▾
  ├─ Atual
  ├─ Arquivos
  ├─ Sobre a Revista
  ├─ Submissões
  ├─ Equipe Editorial
  ├─ Privacidade
  └─ Contato
```

---

## Fase 6 — Verificação final

### 6.1. Contagem de artigos por issue

```bash
python3 scripts/import_ojs.py --env prod --verify
```

Conferir cada slug com a tabela da Fase 3.

### 6.2. Spot-check de metadados

Para cada issue, abrir 2 artigos no navegador e verificar:

- [ ] Título e subtítulo corretos (capitalização FUNAG)
- [ ] Autores na ordem certa (givenname + familyname)
- [ ] Abstract presente (quando o artigo tem)
- [ ] Keywords presentes (quando o artigo tem)
- [ ] Citações/referências listadas (quando o artigo tem)
- [ ] Galley PDF abre e é o arquivo correto
- [ ] Páginas (ex: "70-79") exibidas
- [ ] ORCID do autor aparece (quando cadastrado)

### 6.3. Navegação ponta a ponta

Testar a cadeia completa no navegador:

1. **Homepage** (`/anais`) → landing com 5 grupos, thumbnails, legendas "N (Ano)"
2. **Menu** → clicar em cada região, verificar que abre a página certa
3. **Página de grupo** (ex: `/anais/norte-nordeste`) → cards com capas/placeholders, títulos, contagens, seções
4. **Issue** (ex: `/anais/issue/view/sdnne07`) → lista de artigos por seção
5. **Artigo** → metadados completos + botão PDF
6. **PDF** → abre no visualizador do OJS, download funciona

### 6.4. Verificar issues sem capa

Todas as issues devem ter capa PNG ou placeholder colorido na página de grupo. Listar as que faltam:

```python
r = s.get(f'{BASE}/api/v1/issues?count=100')
for issue in r.json()['items']:
    slug = issue.get('urlPath', '')
    if slug.startswith('sdbr'):
        continue
    cover = issue.get('coverImageUrl', {}).get('pt_BR', '')
    if not cover:
        print(f'{slug}: SEM CAPA')
```

### 6.5. Verificar urlPaths

Todas as issues regionais devem ter `urlPath` setado (não vazio):

```python
for issue in r.json()['items']:
    slug = issue.get('urlPath', '')
    if not slug:
        print(f'Issue {issue["id"]}: urlPath VAZIO!')
```

Se algum estiver vazio, corrigir via `update-issue` (setando todos os campos obrigatórios).

### 6.6. Verificar descriptions

```python
for issue in r.json()['items']:
    slug = issue.get('urlPath', '')
    if slug.startswith('sdbr'):
        continue
    desc = issue.get('description', {}).get('pt_BR', '')
    if not desc or len(desc) < 20:
        print(f'{slug}: description vazia ou curta')
```

---

## Referência rápida — Armadilhas conhecidas

| # | Armadilha | O que acontece | Prevenção |
|---|-----------|---------------|-----------|
| 1 | `update-issue` sem `urlPath` | urlPath apagado, links `/issue/view/{slug}` quebram | Sempre setar `urlPath` explicitamente |
| 2 | `update-issue` sem `description[pt_BR]` | Ficha catalográfica apagada | Sempre setar da fonte (fichas_catalograficas.yaml) |
| 3 | `update-issue` com `seq` | Silenciosamente ignorado + apaga urlPath/description | NUNCA injetar `seq` nesse endpoint |
| 4 | Seções com título igual em issues diferentes | HTTP 500 na importação (bug pkp-lib #9755) | Títulos únicos: "Título — {slug}" |
| 5 | `<citations>` com texto direto | Erro de validação XML | Usar `<citation>` como child elements |
| 6 | `<pages>` antes de `<authors>` | Erro de validação XSD | Ordem: `authors → article_galley → citations → pages` |
| 7 | `<keywords>` sem `<keyword>` filho | Erro de validação XSD | Só gerar `<keywords>` se lista não-vazia |
| 8 | Sessão OJS expira (~4-5 requests) | Requests falham silenciosamente | Re-login a cada 4 operações |
| 9 | curl perde sessão entre requests | 403 ou resposta vazia | Usar `requests.Session()` em Python |
| 10 | `areaName` omitido em `update-navigation-menu` | Menu desaparece do site | Sempre incluir `areaName=primary` |
| 11 | Upload de capa sem submit do formulário | Capa não aparece (fica como temp) | Dois passos: upload → update-issue |
| 12 | Textarea description no form HTML | Pode estar vazio mesmo com dados no banco | Nunca confiar, setar da fonte original |
| 13 | Endpoint Static Pages Plugin sem `controllers/grid/` | 404 | Path correto: `.../static-pages/controllers/grid/static-page-grid/...` |
| 14 | Usar Static Pages Plugin em vez de NMI_TYPE_CUSTOM | Depende de plugin habilitado | Preferir NMI_TYPE_CUSTOM (nativo OJS 3.3) |
| 15 | SVG como capa | OJS rejeita | Converter para PNG antes (`inkscape --export-type=png`) |
| 16 | Importação parcial sem limpeza | Issues duplicadas, artigos órfãos | Parar → limpar tudo → recomeçar limpo |
| 17 | API retorna abstract/keywords vazios | Dados existem no banco, só não na API | Verificar na página real, não confiar só na API |
| 18 | Cloudflare WAF bloqueia base64 > ~1.4 MB | 403 no upload | Exclusivo do teste. Produção usa outro provedor — testar logo |

---

## Referência rápida — Endpoints OJS

Todos os endpoints grid usam `$$$call$$$` no path e requerem header `X-Requested-With: XMLHttpRequest`.

### Issues

| Operação | Endpoint (após `$$$call$$$`) |
|----------|------------------------------|
| Form editar issue | `/grid/issues/back-issue-grid/edit-issue-data?issueId={id}` |
| Salvar issue | `/grid/issues/back-issue-grid/update-issue?issueId={id}` |
| Upload capa | `/grid/issues/back-issue-grid/upload-file` |
| Deletar issue | `/grid/issues/back-issue-grid/delete-issue?issueId={id}` |

### Navegação

| Operação | Endpoint (após `$$$call$$$`) |
|----------|------------------------------|
| Listar menus | `/grid/navigation-menus/navigation-menus-grid/fetch-grid` |
| Listar itens | `/grid/navigation-menus/navigation-menu-items-grid/fetch-grid` |
| Form criar item | `/grid/navigation-menus/navigation-menu-items-grid/add-navigation-menu-item` |
| Form editar item | `/grid/navigation-menus/navigation-menu-items-grid/edit-navigation-menu-item?navigationMenuItemId={id}` |
| Salvar item | `/grid/navigation-menus/navigation-menu-items-grid/update-navigation-menu-item` |
| Form editar menu | `/grid/navigation-menus/navigation-menus-grid/edit-navigation-menu?navigationMenuId={id}` |
| Salvar menu | `/grid/navigation-menus/navigation-menus-grid/update-navigation-menu` |

### Importação

| Operação | Endpoint |
|----------|----------|
| Upload XML | `/management/importexport/plugin/NativeImportExportPlugin/uploadImportXML` |
| Confirmar importação | `/management/importexport/plugin/NativeImportExportPlugin/importBounce` |
| Resultado | `/management/importexport/plugin/NativeImportExportPlugin/import?temporaryFileId={id}&csrfToken={token}` |

### API REST

| Operação | Endpoint |
|----------|----------|
| Listar issues | `GET /api/v1/issues?count=100` |
| Listar artigos | `GET /api/v1/submissions?issueIds={id}&count=200` |
| Detalhe artigo | `GET /api/v1/submissions/{id}` |
| Atualizar journal | `PUT /api/v1/contexts/1` (requer header `X-Csrf-Token`) |

---

## Referência rápida — Ordem dos elementos XML

```
<issue>
  <id>
  <description locale="pt_BR">
  <issue_identification>
    <volume> <number> <year> <title locale="pt_BR">
  </issue_identification>
  <date_published>
  <last_modified>
  <sections>
    <section ref="ABBREV" seq="N">
      <id> <abbrev locale="pt_BR"> <title locale="pt_BR">
    </section>
  </sections>
  <articles>
    <article locale="pt_BR" status="3" stage="production">
      <id>
      <submission_file id="N" stage="proof" genre="Texto do artigo">
        <name locale="pt_BR">arquivo.pdf</name>
        <file id="N" filesize="BYTES" extension="pdf">
          <embed encoding="base64">...</embed>
        </file>
      </submission_file>
      <publication locale="pt_BR" version="1" status="3" section_ref="ABBREV">
        <id>
        <title locale="pt_BR">
        <subtitle locale="pt_BR">
        <abstract locale="pt_BR">
        <keywords locale="pt_BR">
          <keyword>...</keyword>
        </keywords>
        <authors>
          <author user_group_ref="Autor" seq="N">
            <givenname locale="pt_BR"> <familyname locale="pt_BR">
            <affiliation locale="pt_BR"> <country> <email> <orcid>
          </author>
        </authors>
        <article_galley locale="pt_BR">
          <name locale="pt_BR">PDF</name>
          <seq>0</seq>
          <submission_file_ref id="N"/>
        </article_galley>
        <citations>
          <citation>Texto da referência</citation>
        </citations>
        <pages>1-15</pages>
      </publication>
    </article>
  </articles>
</issue>
```

---

## Plano B — Se produção bloquear base64

Se o provedor de produção também bloquear uploads com base64 (como o Cloudflare do teste):

1. Importar **metadata-only** (sem `--with-pdf`): `python3 scripts/import_ojs.py --env prod --xml-dir xml_test`
2. Upload de PDFs como **galleys separados** (endpoint diferente, POST menor)
3. Alternativa: pedir ao provedor para aumentar limite ou whitelist do IP

---

## Diferenças teste → produção

| Aspecto | Teste | Produção |
|---------|-------|----------|
| Base URL | `docomomo.ojs.com.br/index.php/ojs` | `publicacoes.docomomobrasil.com/anais` |
| `--base-url` | `/index.php/ojs` | `/anais` |
| Credenciais | `editor` / `***` | `dmacedo` / `***` |
| `--env` | `test` | `prod` |
| WAF | Cloudflare (bloqueia base64 > 1.4 MB) | Outro provedor (testar) |
| Nacionais | Ausentes | 15 issues publicadas (não tocar) |
| Papel | Editor | Editor |
| SSH | Não | Não |
