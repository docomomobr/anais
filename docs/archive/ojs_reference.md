# OJS — Referência Técnica

Referência completa para operações no OJS 3.3 (Open Journal Systems).
Credenciais e endpoints básicos estão em `CLAUDE.md`.

---

## Autenticação na API OJS

A API do OJS requer autenticação via **sessão com cookies** (não aceita Basic Auth):

```bash
# 1. Login e salvar cookies
curl -s -c /tmp/ojs_cookies.txt -b /tmp/ojs_cookies.txt \
  -d "username=dmacedo&password=$OJS_PASS" \
  "https://publicacoes.docomomobrasil.com/anais/login/signIn" -L -o /dev/null

# 2. Usar cookies nas requisições
curl -sS -b /tmp/ojs_cookies.txt \
  "https://publicacoes.docomomobrasil.com/anais/api/v1/issues"
```

---

## Operações destrutivas (requerem CSRF token)

Operações como despublicar e deletar artigos requerem um token CSRF. O token é obtido de páginas autenticadas:

```bash
# 1. Login e salvar cookies
curl -sS -c /tmp/ojs3.txt -b /tmp/ojs3.txt \
  -d "username=dmacedo&password=$OJS_PASS" \
  "https://publicacoes.docomomobrasil.com/anais/login/signIn" -L -o /dev/null

# 2. Obter CSRF token de uma página de workflow
curl -sS -b /tmp/ojs3.txt \
  "https://publicacoes.docomomobrasil.com/anais/workflow/index/{SUBMISSION_ID}/5" \
  -o /tmp/workflow.html

# 3. Extrair o token
CSRF=$(grep -oE '"csrfToken":"[^"]+"' /tmp/workflow.html | cut -d'"' -f4)
echo "Token: $CSRF"
```

### Despublicar artigo

```bash
# Primeiro obter o publication ID (diferente do submission ID)
PUB_ID=$(curl -sS -b /tmp/ojs3.txt -H "Accept: application/json" \
  "https://publicacoes.docomomobrasil.com/anais/api/v1/submissions/{SUBMISSION_ID}" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['currentPublicationId'])")

# Despublicar
curl -sS -b /tmp/ojs3.txt \
  -H "X-Csrf-Token: $CSRF" \
  -H "Accept: application/json" \
  -X PUT \
  "https://publicacoes.docomomobrasil.com/anais/api/v1/submissions/{SUBMISSION_ID}/publications/{PUB_ID}/unpublish"
```

### Deletar artigo (deve estar despublicado primeiro)

```bash
curl -sS -b /tmp/ojs3.txt \
  -H "X-Csrf-Token: $CSRF" \
  -H "Accept: application/json" \
  -X DELETE \
  "https://publicacoes.docomomobrasil.com/anais/api/v1/submissions/{SUBMISSION_ID}"
```

**Nota:** HTTP 200 com retorno do objeto = deletado com sucesso. Verificar com GET que retorna 404.

### Script para deletar em lote

```bash
# Listar IDs de uma edição (issue)
curl -sS -b /tmp/ojs3.txt -H "Accept: application/json" \
  "https://publicacoes.docomomobrasil.com/anais/api/v1/submissions?issueIds={ISSUE_ID}&count=100" | \
  python3 -c "import sys,json; [print(i['id']) for i in json.load(sys.stdin)['items']]" > /tmp/ids.txt

# Deletar cada um
while read -r SUB_ID; do
    PUB_ID=$(curl -sS -b /tmp/ojs3.txt -H "Accept: application/json" \
        "https://publicacoes.docomomobrasil.com/anais/api/v1/submissions/$SUB_ID" | \
        python3 -c "import sys,json; print(json.load(sys.stdin).get('currentPublicationId',''))")

    # Despublicar
    curl -sS -b /tmp/ojs3.txt -H "X-Csrf-Token: $CSRF" -H "Accept: application/json" \
        -X PUT "https://publicacoes.docomomobrasil.com/anais/api/v1/submissions/$SUB_ID/publications/$PUB_ID/unpublish" -o /dev/null

    # Deletar
    curl -sS -b /tmp/ojs3.txt -H "X-Csrf-Token: $CSRF" -H "Accept: application/json" \
        -X DELETE "https://publicacoes.docomomobrasil.com/anais/api/v1/submissions/$SUB_ID" -o /dev/null

    echo "Deletado: $SUB_ID"
done < /tmp/ids.txt
```

---

## Importação automática via Native XML Plugin

O OJS permite importação em lote de artigos via Native XML Plugin. O processo requer duas etapas:

1. **Upload do XML** para `uploadImportXML` → retorna `temporaryFileId`
2. **Confirmação da importação** via `importBounce` e acesso à URL de resultado

**Limite de upload:** 20MB por arquivo XML (PDFs embutidos em base64 aumentam ~37% o tamanho)

```bash
# 1. Login e salvar cookies
curl -s -c /tmp/ojs3.txt -b /tmp/ojs3.txt \
  -d "username=dmacedo&password=$OJS_PASS" \
  "https://publicacoes.docomomobrasil.com/anais/login/signIn" -L -o /dev/null

# 2. Obter CSRF token de qualquer página autenticada
CSRF=$(curl -s -b /tmp/ojs3.txt \
  "https://publicacoes.docomomobrasil.com/anais/management/importexport/plugin/NativeImportExportPlugin" \
  | grep -oP '"csrfToken":"[^"]+"' | head -1 | cut -d'"' -f4)

# 3. Upload do XML (campo DEVE ser "uploadedFile", não "file")
RESP=$(curl -s -b /tmp/ojs3.txt \
  -H "X-Requested-With: XMLHttpRequest" \
  -F "csrfToken=$CSRF" \
  -F "uploadedFile=@arquivo.xml;type=text/xml" \
  "https://publicacoes.docomomobrasil.com/anais/management/importexport/plugin/NativeImportExportPlugin/uploadImportXML")

TEMP_ID=$(echo "$RESP" | grep -oP '"temporaryFileId":"?\K[0-9]+')

# 4. Submeter importação
curl -s -b /tmp/ojs3.txt \
  -X POST \
  -d "csrfToken=$CSRF" \
  -d "temporaryFileId=$TEMP_ID" \
  "https://publicacoes.docomomobrasil.com/anais/management/importexport/plugin/NativeImportExportPlugin/importBounce" > /dev/null

# 5. Confirmar resultado (executa a importação)
curl -s -b /tmp/ojs3.txt \
  "https://publicacoes.docomomobrasil.com/anais/management/importexport/plugin/NativeImportExportPlugin/import?temporaryFileId=$TEMP_ID&csrfToken=$CSRF"
```

**Resposta de sucesso:** `"A importação foi concluída com êxito"`

### Script para importar múltiplos XMLs

```bash
for FILE in *.xml; do
  echo "Importando $FILE..."

  RESP=$(curl -s -b /tmp/ojs3.txt -H "X-Requested-With: XMLHttpRequest" \
    -F "csrfToken=$CSRF" -F "uploadedFile=@$FILE;type=text/xml" \
    "https://publicacoes.docomomobrasil.com/anais/management/importexport/plugin/NativeImportExportPlugin/uploadImportXML")

  TEMP_ID=$(echo "$RESP" | grep -oP '"temporaryFileId":"?\K[0-9]+')

  curl -s -b /tmp/ojs3.txt -X POST \
    -d "csrfToken=$CSRF" -d "temporaryFileId=$TEMP_ID" \
    "https://publicacoes.docomomobrasil.com/anais/management/importexport/plugin/NativeImportExportPlugin/importBounce" > /dev/null

  RESULT=$(curl -s -b /tmp/ojs3.txt \
    "https://publicacoes.docomomobrasil.com/anais/management/importexport/plugin/NativeImportExportPlugin/import?temporaryFileId=$TEMP_ID&csrfToken=$CSRF")

  if echo "$RESULT" | grep -q "conclu.*xito"; then
    echo "  OK"
  else
    echo "  ERRO: verificar manualmente"
  fi

  sleep 0.5
done
```

### Notas importantes

- O campo de upload DEVE ser `uploadedFile` (não `file`)
- O header `X-Requested-With: XMLHttpRequest` é necessário
- Se a edição (issue) já existe, os artigos são adicionados a ela
- Recomenda-se 1 artigo por XML para facilitar debug de erros
- **Produção**: usar `scripts/import_ojs.py --env prod --per-article` (1 XML/artigo, 15s delay, re-login automático)
- **Pipeline completo**: ver `docs/pipeline_producao.md` para o procedimento passo a passo validado no teste

---

## Gerenciamento de edições (issues)

### Alterar data de publicação de uma edição

```python
# 1. Login com requests (sessão persistente)
import requests, re
s = requests.Session()
s.post('https://publicacoes.docomomobrasil.com/anais/login/signIn',
       data={'username': 'dmacedo', 'password': os.environ['OJS_PASS']})

# 2. Obter formulário da edição para pegar CSRF
form_resp = s.get('https://publicacoes.docomomobrasil.com/anais/$$$call$$$/grid/issues/back-issue-grid/edit-issue-data?issueId={ISSUE_ID}')
content = form_resp.json()['content']
csrf = re.search(r'name="csrfToken"[^>]*value="([^"]+)"', content).group(1)

# 3. Atualizar (precisa enviar todos os campos obrigatórios)
s.post(f'https://publicacoes.docomomobrasil.com/anais/$$$call$$$/grid/issues/back-issue-grid/update-issue?issueId={ISSUE_ID}',
       data={
           'csrfToken': csrf,
           'datePublished': '2017-11-24',  # Nova data
           'volume': '12',
           'year': '2017',
           'title[pt_BR]': 'Título da edição',
           'showVolume': '1',
           'showYear': '1',
           'showTitle': '1',
           'urlPath': 'sdbr12',
       })
```

**Notas:**
- A sessão expira rapidamente. Use `requests.Session()` em Python para manter a sessão ativa entre requisições.
- **IMPORTANTE:** Enviar TODOS os campos ao atualizar, incluindo `description[pt_BR]`. Campos omitidos são apagados!

### Definir edição atual (current issue)

O OJS define a "edição atual" pelo ID mais alto por padrão. Para alterar manualmente:

```python
# Obter CSRF do grid de issues
resp = s.get('https://publicacoes.docomomobrasil.com/anais/$$$call$$$/grid/issues/back-issue-grid/fetch-grid')
csrf = re.search(r'csrfToken["\s:]+["\']([^"\']+)', resp.json()['content']).group(1)

# Definir edição atual (ex: ID 19 = Vol 15)
s.post('https://publicacoes.docomomobrasil.com/anais/$$$call$$$/grid/issues/back-issue-grid/set-current-issue',
       data={'csrfToken': csrf, 'issueId': 19})
```

---

## Páginas estáticas (Navigation Menu Custom Pages)

O OJS 3.3 suporta páginas HTML customizadas via **NMI_TYPE_CUSTOM** (itens de menu de navegação). Não requer plugin — é nativo do OJS.

**Criar/editar página**:
```python
# Endpoint para editar item existente
GET $$$call$$$/grid/navigation-menus/navigation-menu-items-grid/edit-navigation-menu-item?navigationMenuItemId={id}
# → extrai CSRF do form

POST $$$call$$$/grid/navigation-menus/navigation-menu-items-grid/update-navigation-menu-item
# data: csrfToken, navigationMenuItemId, title[pt_BR], content[pt_BR], path
```

**Definir conteúdo da homepage** (landing page):
```python
PUT /api/v1/contexts/1
headers: {'X-Csrf-Token': csrf}
json: {'additionalHomeContent': {'pt_BR': '<div>...</div>'}}
```

**ATENÇÃO — `areaName=primary`**: ao atualizar o menu de navegação, o campo `areaName` é **obrigatório**. Omitir causa desaparecimento do menu.

**Alternativa (NÃO usada)**: Plugin Static Pages — endpoint correto inclui `controllers/grid/`:
```
$$$call$$$/plugins/generic/static-pages/controllers/grid/static-page-grid/add-static-page
```
(NÃO é `static-pages/static-page-grid/` — esse retorna 404.)

---

## Native XML — Estrutura de Importação

O OJS 3.3 usa um formato XML específico para importação em lote (Native XML Plugin). A estrutura abaixo foi validada a partir de exports reais do sistema.

### Padrões e recomendações da documentação PKP

Fontes: [Code4Lib/Oregon State migration](https://journal.code4lib.org/articles/15988), [PKP Forum](https://forum.pkp.sfu.ca/t/native-xml-plugin-import-file-size-error/29542), [pkp-lib #7898](https://github.com/pkp/pkp-lib/issues/7898), [pkp-lib #3276](https://github.com/pkp/pkp-lib/issues/3276)

| Aspecto | Recomendação |
|---------|-------------|
| Agrupamento (só metadados) | **1 XML por issue** (edição/seminário) funciona quando não há PDFs embutidos. Migração Code4Lib importou 93 issues inteiras assim |
| Agrupamento (com PDFs) | **1 artigo por XML**. PDFs em base64 aumentam ~37% o tamanho; um seminário com 65 PDFs de 2MB cada geraria ~170MB, muito acima do limite. Abordagem validada no sdbr12 (82 XMLs, 1 artigo cada) |
| Tamanho máximo upload | Padrão **8 MB** (definido por `upload_max_filesize` e `post_max_size` do PHP, não pelo plugin). Configurável pelo admin do servidor |
| Issues múltiplas | **Nunca 2+ issues no mesmo XML** — pode causar corrupção no banco (limitação documentada) |
| Importação via web | Sujeita a timeout de sessão e rate limiting. Na prática, falha após ~6-7 importações consecutivas mesmo com XMLs pequenos (~100-500KB). Importação de 850 artigos sem PDFs levou 2h+ e não completou. Funciona para lotes muito pequenos (3-5 XMLs) com delays de 10-30s |
| Importação via CLI | `php tools/importExport.php NativeImportExportPlugin import arquivo.xml journal_path admin_user` — evita todos os problemas de sessão web. Requer SSH. Disponível no teste, **não disponível na produção** |
| Validação | Erros de importação nem sempre são claros. Testar com 1-2 XMLs antes de rodar o lote completo |
| Pós-importação | A "edição atual" (current issue) precisa ser definida manualmente |
| Submissões órfãs | Importações falhadas podem deixar submissões sem publicação. Verificar com: `SELECT s.submission_id FROM submissions s LEFT JOIN publications p ON s.current_publication_id = p.publication_id WHERE p.publication_id IS NULL` |

### Estrutura geral do arquivo

```xml
<?xml version="1.0" encoding="UTF-8"?>
<issue xmlns="http://pkp.sfu.ca" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       published="0" current="0" access_status="1" url_path="sdbr12"
       xsi:schemaLocation="http://pkp.sfu.ca native.xsd">
  <id type="internal" advice="ignore">sdbr12</id>
  <description locale="pt_BR">Descrição da edição...</description>
  <issue_identification>
    <volume>12</volume>
    <year>2017</year>
    <title locale="pt_BR">12º Seminário Docomomo Brasil, Uberlândia, 2017</title>
  </issue_identification>
  <date_published>2017-11-24</date_published>
  <last_modified>2017-11-24</last_modified>
  <sections>
    <!-- Seções da issue -->
  </sections>
  <articles>
    <!-- Artigos -->
  </articles>
</issue>
```

### Estrutura de seção

```xml
<section ref="E1-sdbr12" seq="0" editor_restricted="0" meta_indexed="1"
         meta_reviewed="1" abstracts_not_required="0" hide_title="0"
         hide_author="0" abstract_word_count="0">
  <id type="internal" advice="ignore">20</id>
  <abbrev locale="pt_BR">E1-sdbr12</abbrev>
  <title locale="pt_BR">Eixo 1 - A recepção e a difusão...</title>
</section>
```

**Importante:** O atributo `ref` deve corresponder ao `abbrev` da seção.

### Estrutura de artigo (article)

```xml
<article xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         locale="pt_BR" date_submitted="2017-11-24" status="3"
         submission_progress="0" current_publication_id="{publication_id}"
         stage="production">
  <id type="internal" advice="ignore">{submission_id}</id>

  <!-- Arquivo PDF embutido -->
  <submission_file id="{file_id}" created_at="2017-11-24" date_created=""
                   file_id="{file_id}" stage="proof" updated_at="2017-11-24"
                   viewable="false" genre="Texto do artigo"
                   xsi:schemaLocation="http://pkp.sfu.ca native.xsd">
    <name locale="pt_BR">{nome_arquivo.pdf}</name>
    <file id="{file_id}" filesize="{tamanho_bytes}" extension="pdf">
      <embed encoding="base64">{conteudo_base64}</embed>
    </file>
  </submission_file>

  <!-- Publicação (metadados do artigo) -->
  <publication xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               locale="pt_BR" version="1" status="3" url_path=""
               seq="{ordem}" date_published="2017-11-24"
               section_ref="{abbrev_secao}" access_status="0"
               xsi:schemaLocation="http://pkp.sfu.ca native.xsd">
    <id type="internal" advice="ignore">{publication_id}</id>
    <title locale="pt_BR">{titulo}</title>
    <subtitle locale="pt_BR">{subtitulo}</subtitle>
    <abstract locale="pt_BR">{resumo}</abstract>
    <keywords locale="pt_BR">
      <keyword>{palavra1}</keyword>
      <keyword>{palavra2}</keyword>
    </keywords>
    <authors>
      <!-- Autores -->
    </authors>
    <pages>{paginas}</pages>
    <citations>
      <citation>{referencia_1}</citation>
      <citation>{referencia_2}</citation>
    </citations>
    <article_galley xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    locale="pt_BR" url_path="" approved="false"
                    xsi:schemaLocation="http://pkp.sfu.ca native.xsd">
      <id type="internal" advice="ignore">{galley_id}</id>
      <name locale="pt_BR">PDF</name>
      <seq>0</seq>
      <submission_file_ref id="{file_id}"/>
    </article_galley>
  </publication>
</article>
```

### Estrutura de autor

```xml
<author include_in_browse="true" user_group_ref="Autor" seq="0" id="{autor_id}">
  <givenname locale="pt_BR">{nome}</givenname>
  <familyname locale="pt_BR">{sobrenome}</familyname>
  <affiliation locale="pt_BR">{afiliacao}</affiliation>
  <country>BR</country>
  <email>{email}</email>
</author>
```

**Campos do autor:**
- `seq`: ordem do autor (0 = primeiro)
- `user_group_ref`: sempre "Autor" para autores de artigos
- `include_in_browse`: true para aparecer na navegação por autor

### Ordem dos elementos dentro de `<publication>`

A ordem dos elementos é obrigatória. Referência validada:

1. `<title>` / `<subtitle>` / `<abstract>`
2. `<keywords>`
3. `<authors>`
4. **`<pages>`** (DEPOIS de `<authors>`, não antes!)
5. `<citations>` (com `<citation>` child elements — **não** texto direto!)
6. `<article_galley>`

**CUIDADO — `<citations>`:** O conteúdo deve ser `<citation>` child elements, nunca texto direto:
```xml
<!-- CORRETO -->
<citations>
  <citation>AUTOR. Título. Local: Editora, Ano.</citation>
  <citation>AUTOR2. Título2. Cidade: Ed., Ano.</citation>
</citations>

<!-- ERRADO (causa erro de validação) -->
<citations>AUTOR. Título.\nAUTOR2. Título2.</citations>
```

### Valores de status

| status | Significado |
|--------|-------------|
| 1 | Submetido (em avaliação) |
| 3 | Publicado |
| 4 | Rejeitado |

### Valores de stage

| stage | Significado |
|-------|-------------|
| submission | Submissão |
| externalReview | Avaliação externa |
| editorial | Editorial |
| production | Produção |
| proof | Prova final (para arquivos) |

### Scripts de geração e importação

| Script | Função |
|--------|--------|
| `scripts/generate_ojs_xml.py` | Gera XMLs a partir do `anais.db`. Modos: `--with-pdf` (1 artigo/XML com PDF base64) ou metadata-only (1 XML/issue) |
| `scripts/import_ojs.py` | Importa XMLs no OJS. Modos: `--per-article` (1 XML/artigo, 15s delay) ou issue inteira. Suporta `--env test` e `--env prod` |

```bash
# Gerar XMLs com PDF para produção (21 regionais)
python3 scripts/generate_ojs_xml.py --with-pdf --outdir xml_prod

# Importar 1 artigo por vez na produção
python3 scripts/import_ojs.py --env prod --per-article --xml-dir xml_prod
```

**Limite de upload:** 20 MB por arquivo XML (PDFs em base64 aumentam ~37%).

**Pipeline completo**: ver `docs/pipeline_producao.md` e `docs/devlog_teste_completo.md`.

---

## Problemas conhecidos e soluções

### YAML: campos desordenados

O `yaml.dump()` ordena alfabeticamente por padrão. Solução:

```python
class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

OrderedDumper.add_representer(dict, dict_representer)

yaml.dump(dados_ordenados, f, Dumper=OrderedDumper, width=10000, sort_keys=False)
```

**IMPORTANTE:** `width=10000` evita truncamento de strings longas (nomes de PDF).

### Word corrompido

Alguns .docx não abrem corretamente. Soluções:
1. Abrir no LibreOffice e salvar como .odt
2. Usar `odfpy` para extrair do .odt
3. Fallback: extrair texto do PDF com `pdftotext`

### Caracteres especiais em títulos

O apóstrofo pode variar: `'` (ASCII) vs `´` (acento). Tratar ambos:

```python
if palavra.lower().startswith("d'") or palavra.lower().startswith("d´"):
    return palavra[0] + palavra[1] + palavra[2:].capitalize()  # d'Alva
```

### Seções OJS são journal-wide

`_sectionExist()` busca por TÍTULO, não abbrev. Títulos iguais entre issues causam crash (pkp-lib #9755). Solução: títulos únicos por seminário (ex: "Artigos Completos — sdnne07"). Corrigido em `generate_ojs_xml.py`.

### `update-issue` apaga campos omitidos

`urlPath`, `description`, `datePublished` são apagados se não setados explicitamente. Nunca confiar nos valores do textarea do form (pode estar vazio). Sempre setar da fonte original.

### `save-sequence` requer Journal Manager

Papel de Editor retorna HTTP 500 vazio. Conta `editor` no teste não tem esse papel. Ordenação de issues requer `save-sequence` (papel Journal Manager) ou SQL direto.

### NUNCA injetar `seq` no `update-issue`

`seq` não é campo do form, é silenciosamente ignorado, e o POST apaga `urlPath`/`description` de brinde.

### Sessão OJS expira rápido

Ao iterar issues no OJS, re-login a cada ~5 requests. Usar try/except + re-login automático.
