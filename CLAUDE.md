# Diretrizes do Projeto - Anais Docomomo Brasil

Este arquivo define as convenções e mapeamentos para migração dos anais dos seminários Docomomo Brasil para o OJS (Open Journal Systems).

---

## Estrutura do Projeto

```
anais/
├── nacionais/           # Seminários nacionais (sdbr01-sdbr15)
│   ├── sdbr*.yaml       # Metadados de cada seminário
│   ├── pdfs_faltantes/  # PDFs a serem adicionados
│   └── sdbr12_fontes/   # Fontes do 12º seminário (Uberlândia 2017)
├── regionais/
│   ├── nne/             # Norte/Nordeste (sdnne01-sdnne10)
│   ├── sul/             # Sul (sdsul*)
│   ├── sp/              # São Paulo (sdsp*)
│   └── rio/             # Rio de Janeiro (sdrio*)
└── fontes/              # Arquivos fonte originais
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
- Tipos de conteúdo: post, page, course (Educaz), dlm_download
- Application Password (claude26): `***`
- Auth: `admindocomomo:***`

### OJS (Open Journal Systems)
- URL: `https://publicacoes.docomomobrasil.com/`
- Journal principal: `/anais`
- Usuário: `dmacedo`
- Senha: `***`

#### Limitações da API OJS

- A API **não retorna todos os campos** dos artigos (ex: `abstract`, `keywords` podem vir vazios mesmo existindo no banco). **Sempre verificar na página real** (`/article/view/{id}`) com WebFetch antes de concluir que dados estão faltando.
- O locale `en_US` não está habilitado. Dados em inglês existem no banco mas não são exibidos. Requer admin do site para habilitar em Configurações do Site > Idiomas.
- Conta `dmacedo`: papel de Editor (não Journal Manager nem Site Admin). Não tem acesso a configurações de idiomas nem de admin do site.

#### Autenticação na API OJS

A API do OJS requer autenticação via **sessão com cookies** (não aceita Basic Auth):

```bash
# 1. Login e salvar cookies
curl -s -c /tmp/ojs_cookies.txt -b /tmp/ojs_cookies.txt \
  -d "username=dmacedo&password=***" \
  "https://publicacoes.docomomobrasil.com/anais/login/signIn" -L -o /dev/null

# 2. Usar cookies nas requisições
curl -sS -b /tmp/ojs_cookies.txt \
  "https://publicacoes.docomomobrasil.com/anais/api/v1/issues"
```

#### Endpoints úteis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/issues` | GET | Lista edições (14 publicadas) |
| `/api/v1/submissions` | GET | Lista artigos (1413 total) |
| `/api/v1/submissions?count=N` | GET | Lista N artigos |
| `/api/v1/submissions/{id}` | GET | Detalhes de um artigo |

#### Operações destrutivas (requerem CSRF token)

Operações como despublicar e deletar artigos requerem um token CSRF. O token é obtido de páginas autenticadas:

```bash
# 1. Login e salvar cookies
curl -sS -c /tmp/ojs3.txt -b /tmp/ojs3.txt \
  -d "username=dmacedo&password=***" \
  "https://publicacoes.docomomobrasil.com/anais/login/signIn" -L -o /dev/null

# 2. Obter CSRF token de uma página de workflow
curl -sS -b /tmp/ojs3.txt \
  "https://publicacoes.docomomobrasil.com/anais/workflow/index/{SUBMISSION_ID}/5" \
  -o /tmp/workflow.html

# 3. Extrair o token
CSRF=$(grep -oE '"csrfToken":"[^"]+"' /tmp/workflow.html | cut -d'"' -f4)
echo "Token: $CSRF"
```

##### Despublicar artigo

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

##### Deletar artigo (deve estar despublicado primeiro)

```bash
curl -sS -b /tmp/ojs3.txt \
  -H "X-Csrf-Token: $CSRF" \
  -H "Accept: application/json" \
  -X DELETE \
  "https://publicacoes.docomomobrasil.com/anais/api/v1/submissions/{SUBMISSION_ID}"
```

**Nota:** HTTP 200 com retorno do objeto = deletado com sucesso. Verificar com GET que retorna 404.

##### Script para deletar em lote

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

#### Importação automática via Native XML Plugin

O OJS permite importação em lote de artigos via Native XML Plugin. O processo requer duas etapas:

1. **Upload do XML** para `uploadImportXML` → retorna `temporaryFileId`
2. **Confirmação da importação** via `importBounce` e acesso à URL de resultado

**Limite de upload:** 20MB por arquivo XML (PDFs embutidos em base64 aumentam ~37% o tamanho)

```bash
# 1. Login e salvar cookies
curl -s -c /tmp/ojs3.txt -b /tmp/ojs3.txt \
  -d "username=dmacedo&password=***" \
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

**Script para importar múltiplos XMLs:**

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

**Notas importantes:**
- O campo de upload DEVE ser `uploadedFile` (não `file`)
- O header `X-Requested-With: XMLHttpRequest` é necessário
- Se a edição (issue) já existe, os artigos são adicionados a ela
- Recomenda-se 1 artigo por XML para facilitar debug de erros

#### Gerenciamento de edições (issues)

##### Alterar data de publicação de uma edição

```bash
# 1. Login com requests (sessão persistente)
import requests, re
s = requests.Session()
s.post('https://publicacoes.docomomobrasil.com/anais/login/signIn',
       data={'username': 'dmacedo', 'password': '***'})

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

##### Definir edição atual (current issue)

O OJS define a "edição atual" pelo ID mais alto por padrão. Para alterar manualmente:

```bash
# Obter CSRF do grid de issues
resp = s.get('https://publicacoes.docomomobrasil.com/anais/$$$call$$$/grid/issues/back-issue-grid/fetch-grid')
csrf = re.search(r'csrfToken["\s:]+["\']([^"\']+)', resp.json()['content']).group(1)

# Definir edição atual (ex: ID 19 = Vol 15)
s.post('https://publicacoes.docomomobrasil.com/anais/$$$call$$$/grid/issues/back-issue-grid/set-current-issue',
       data={'csrfToken': csrf, 'issueId': 19})
```

### Acesso aos Courses (Seminários) via API

**IMPORTANTE: Os Courses TÊM endpoint REST API!**

#### 1. Listar todos os courses (rascunhos):
```bash
curl -s -u "admindocomomo:***" \
  "https://docomomobrasil.com/wp-json/wp/v2/courses?status=draft&per_page=100"
```

#### 2. Acessar um course específico (por ID):
```bash
curl -s -u "admindocomomo:***" \
  "https://docomomobrasil.com/wp-json/wp/v2/courses/{POST_ID}?context=edit"
```

#### 3. OBTER LISTA DE ARTIGOS (PDFs) de um seminário:

**IMPORTANTE:** Os PDFs NÃO estão como media vinculada. Estão no plugin Educaz.
Para extraí-los, é preciso acessar o **preview** do Course com sessão autenticada:

```bash
# Passo 1: Fazer login e salvar cookies
curl -s -c /tmp/wp_cookies.txt -b /tmp/wp_cookies.txt \
  -d "log=admindocomomo&pwd=***&wp-submit=Log+In&testcookie=1" \
  -d "redirect_to=https%3A%2F%2Fdocomomobrasil.com%2Fwp-admin%2F" \
  "https://docomomobrasil.com/wp-login.php" -L > /dev/null

# Passo 2: Acessar preview do Course (rascunho) usando cookies
curl -s -b /tmp/wp_cookies.txt \
  "https://docomomobrasil.com/?post_type=course&p={POST_ID}&preview=true" \
  | grep -oE 'href="[^"]*\.pdf"' | sed 's/href="//;s/"$//'
```

**Nota:** HTTP Basic Auth (Application Password) NÃO funciona para previews.
É necessário login via wp-login.php com cookies de sessão.

---

## OJS 3.3 Native XML - Estrutura de Importação

O OJS 3.3 usa um formato XML específico para importação em lote (Native XML Plugin). A estrutura abaixo foi validada a partir de exports reais do sistema.

### Padrões e recomendações da documentação PKP

Fontes: [Code4Lib/Oregon State migration](https://journal.code4lib.org/articles/15988), [PKP Forum](https://forum.pkp.sfu.ca/t/native-xml-plugin-import-file-size-error/29542), [pkp-lib #7898](https://github.com/pkp/pkp-lib/issues/7898), [pkp-lib #3276](https://github.com/pkp/pkp-lib/issues/3276)

| Aspecto | Recomendação |
|---------|-------------|
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

### Mapeamento de seções (sdbr12)

| Seção | section_ref | sectionId |
|-------|-------------|-----------|
| Eixo 1 - A recepção e a difusão... | E1-sdbr12 | 20 |
| Eixo 2 - Práticas de preservação... | E2-sdbr12 | 21 |
| Eixo 3 - Práticas (ações e projetos)... | E3-sdbr12 | 22 |
| Eixo 4 - A formação dos futuros... | E4-sdbr12 | 23 |

### Script de geração

O script `gerar_prototipo_xml.py` em `nacionais/sdbr12_fontes/` gera XML no formato correto:

```bash
cd /home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes
python3 gerar_prototipo_xml.py
```

**Nota:** O script gera protótipo com 3 artigos para teste. Para produção, ajustar `ARTIGOS_TESTE` para incluir todos os 82.

### Importação no OJS

1. Acessar: Ferramentas > Importar/Exportar > Native XML Plugin
2. Selecionar o arquivo XML gerado
3. Clicar em "Importar"
4. Verificar erros no log

**Limite de upload:** 20 MB por arquivo XML. Dividir em lotes menores (3-5 artigos) para garantir que fiquem abaixo do limite.

**Limitação de memória:** XMLs com muitos PDFs embutidos podem travar. Se necessário, dividir em lotes de 3-5 artigos.

---

## IDs dos Courses (Seminários Nacionais)

| Seminário | Post ID | Status no OJS |
|-----------|---------|---------------|
| 1º Salvador 1995 | 3870 | ✅ Migrado |
| 2º Salvador 1997 | 3673 | ✅ Migrado |
| 3º São Paulo 1999 | 1787 | ✅ Migrado |
| 4º Viçosa 2001 | 1786 | ✅ Migrado |
| 5º São Carlos 2003 | 1785 | ✅ Migrado |
| 6º Niterói 2005 | 1784 | ✅ Migrado |
| 7º Porto Alegre 2007 | 1783 | ✅ Migrado |
| 8º Rio de Janeiro 2009 | 1782 | ✅ Migrado |
| 9º Brasília 2011 | 1781 | ✅ Migrado |
| 10º Curitiba 2013 | 1613 | ✅ Migrado |
| 11º Recife 2016 | 1615 | ✅ Migrado |
| 12º Uberlândia 2017 | 3020 | ✅ Migrado |
| 13º Salvador 2019 | 3676 | ✅ Migrado |
| 14º Belém 2021 | 4376 | ✅ Migrado |
| 15º São Carlos 2023 | - | ✅ Migrado |

---

## Estrutura dos Arquivos YAML

Os campos devem usar nomenclatura em **inglês**, conforme padrão OJS.

### Mapeamento de Campos: Issue (Edição)

| Campo YAML | Campo OJS | Obrigatório | Notas |
|------------|-----------|-------------|-------|
| `title` | title | Sim | Título da edição |
| `subtitle` | subtitle | Não | Subtítulo da edição |
| `description` | description | Não | Descrição completa (pode incluir local, ISBN, fonte) |
| `year` | year | Sim | Ano de publicação |
| `volume` | volume | Sim | Número do volume |
| `number` | number | Sim | Número da edição |
| `date_published` | date_published | Sim | Formato: YYYY-MM-DD |
| `editors` | editors | Não | Lista de **organizadores** (pessoas que organizaram os anais) |
| `publisher` | — | Não | **Editora** (instituição que publicou os anais). Incluir na `description` para OJS. |
| `isbn` | — | Não | ISBN da publicação |
| `location` | — | Não | Cidade e UF do evento (ex: "São Carlos, SP") |

**IMPORTANTE — Organizadores vs. Editora:**
- **`editors`** (organizadores): as pessoas que organizam os anais (em inglês, "editors"). Ex: "Miguel Antonio Buzzar"
- **`publisher`** (editora): a instituição que publica os anais (em inglês, "publisher"). Ex: "IAU/USP", "EDUFU", "Mack Pesquisa/UPM"
- O OJS não tem campo dedicado para `publisher` na importação XML; incluir na `description` da issue.

### Campos internos (não vão para OJS)

| Campo | Uso |
|-------|-----|
| `slug` | Identificador interno do seminário |
| `source` | URL de origem dos dados |

### Mapeamento de Campos: Article (Artigo)

| Campo YAML | Campo OJS | Obrigatório | Notas |
|------------|-----------|-------------|-------|
| `title` | title | Sim | Título do artigo |
| `subtitle` | subtitle | Não | Manter separado do title |
| `abstract` | abstract | Não | Resumo do artigo |
| `keywords` | keywords | Não | Lista de palavras-chave |
| `section` | section_ref | Sim | Seção (ex: "Artigos Completos - Documentação") |
| `pages` | pages | Não | Páginas (ex: "1-15") |
| `file` | galley | Não | Caminho para o arquivo PDF |
| `locale` | locale | Sim | Formato: pt-BR (não pt_BR) |

### Mapeamento de Campos: Author (Autor)

| Campo YAML | Campo OJS | Obrigatório | Notas |
|------------|-----------|-------------|-------|
| `givenname` | givenname | Sim | Nome |
| `familyname` | familyname | Sim | Sobrenome |
| `email` | email | Sim | Email do autor |
| `affiliation` | affiliation | Não | **Apenas instituição** (ver regras abaixo) |
| `orcid` | orcid | Não | Formato: 0000-0000-0000-0000 |
| `country` | country | Não | Código do país (BR, PT, etc.) |
| `bio` | biography | Não | Título acadêmico (Doutor, Professor, etc.) |
| `primary_contact` | primary_contact | Sim | true/false - autor de correspondência |

---

## Regras para Títulos e Subtítulos

### Separação título/subtítulo
- O subtítulo é separado do título por `: ` (dois-pontos seguido de espaço)
- Ao parsear, dividir em `title` e `subtitle` no primeiro `: `

### Travessão vs. hífen

- **Hífen isolado** (` - `) usado como separador **não é hífen, é travessão** (` — `, em-dash U+2014)
- Aplicar em todos os campos textuais: títulos, subtítulos, nomes de eventos, eixos temáticos, seções
- Exemplos:
  - `Rino Levi - Hespéria nos trópicos` → `Rino Levi — Hespéria nos trópicos`
  - `Mesa 1 - Modos de usar a cidade` → `Mesa 1 — Modos de usar a cidade`
  - `Artigos Completos - Documentação` → `Artigos Completos — Documentação`
  - `Teresina - PI` → `Teresina — PI`
- **Não substituir** hífens que são parte de:
  - Intervalos numéricos: `1930-1960`, `pp. 89-94`
  - Palavras compostas: `art-déco`, `pré-fabricado`
  - Siglas com hífen: `E1-sdbr12`, `AC-CONS-sdnne09`
  - Referências bibliográficas (campo `references`)

### Capitalização (norma brasileira - Ref: FUNAG)

Referência: https://funag.gov.br/manual/index.php?title=Mai%C3%BAsculas_e_min%C3%BAsculas

- **Título**: Primeira letra maiúscula
- **Subtítulo**: Começa com minúscula (exceto se iniciar com nome próprio, sigla, etc.)

**Regras específicas:**

| Categoria | Regra | Exemplos |
|-----------|-------|----------|
| Nomes próprios | MAIÚSCULA | Maria, Brasília, UFMT, Docomomo |
| Adjetivos pátrios (isolados) | minúscula | brasileiro, francês, português |
| Adjetivos pátrios em expressão consolidada | Maiúscula | Arquitetura Moderna **Brasileira**, Escola **Paulista** |
| Disciplinas/áreas do saber | Maiúscula | Arquitetura, Urbanismo, História |
| Movimentos/períodos históricos | Maiúscula | Modernismo, Renascimento, Art Déco |
| Conceitos substantivados (período/ideia) | Maiúscula | Modernidade, Brutalismo |
| Expressões consolidadas | Maiúscula | Educação Patrimonial, Patrimônio Cultural, Movimento Moderno, Arquitetura Moderna |
| Regiões geográficas | Maiúscula | Nordeste, Norte, Sudeste |
| Artigos/preposições/conjunções | minúscula | o, a, de, da, e, ou, para |
| Palavras comuns | minúscula | edifício, casa, projeto, estudo |
| Siglas | MAIÚSCULA | BNB, SESI, SENAI, IPHAN, VANT |
| Séculos (algarismos romanos) | MAIÚSCULA | XX, XXI, XIX, XVIII |

**Consistência em expressões consolidadas:**
- Quando um adjetivo pátrio ou toponímico faz parte de uma expressão consolidada capitalizada, ele também deve ser capitalizado para manter a consistência. Ex: "Arquitetura Moderna Brasileira" (não "Arquitetura Moderna brasileira"), "Urbanismo Moderno Paulista" (não "Urbanismo Moderno paulista").
- Da mesma forma, "Moderna/Moderno" deve acompanhar a capitalização de "Arquitetura/Urbanismo": "Arquitetura Moderna" (não "Arquitetura moderna"), "Urbanismo Moderno" (não "Urbanismo moderno").
- "Modernidade" substantivado (como período ou conceito histórico) leva maiúscula: "a Modernidade brasileira", "imagens da Modernidade paulistana". Quando usado como qualidade abstrata genérica, minúscula: "a modernidade do projeto".

---

## Regras de Limpeza de Dados

### Affiliation (Afiliação)

O campo `affiliation` deve conter **apenas** a sigla da instituição, no formato `UNIDADE-UNIVERSIDADE`.

**Formato padrão:**

| Original | Normalizado |
|----------|-------------|
| Faculdade de Arquitetura e Urbanismo da USP | FAU-USP |
| Instituto de Arquitetura e Urbanismo da USP | IAU-USP |
| PROPAR UFRGS | PROPAR-UFRGS |
| Faculdade de Arquitetura da UFBA | FAUFBA |
| Faculdade de Arquitetura da UFRGS | FA-UFRGS |
| PROARQ UFRJ | PROARQ-UFRJ |
| MDU - UFPE | MDU-UFPE |
| UNICEP São Carlos | UNICEP |
| AA School of Architecture | AA School |

Se não houver unidade específica, usar apenas a sigla: `USP`, `UFRJ`, `UFBA`, `UFU`, etc.

Para instituições estrangeiras, usar nome abreviado reconhecido internacionalmente.

**Remover:**
- Títulos acadêmicos (Doutor, Mestre, Professor, Graduando)
- Endereços postais (Rua, Av., CEP, etc.)
- ORCID (extrair para campo próprio)
- Emails (já existe campo próprio)
- Nomes completos de faculdades/departamentos (substituir por sigla)

### ORCID

- Extrair do campo afiliação se presente
- Formato padrão: `0000-0000-0000-0000` (sem URL)
- Aceita formatos de entrada: `orcid.org/...`, `https://orcid.org/...`, número direto

### Bio (Biografia)

O campo `bio` deve conter informação acadêmica completa e válida:
- Grau acadêmico + área + instituição (ex: "Doutora em Arquitetura pela FAUUSP")
- Cargo + instituição (ex: "Professora Adjunta da UFCG")

**Remover:**
- Endereços postais (Rua, Av., CEP)
- Informações incompletas (ex: apenas "Arquitetura e Urbanismo" sem contexto)

**Se não houver informação válida:** usar `null`

---

## Schema YAML Completo de Artigo

O schema completo está em `schema/artigo.yaml`. Abaixo um resumo dos campos principais:

```yaml
# IDENTIFICAÇÃO
id: sdbr12-001                    # ID único: sdbr{NN}-{NNN}
seminario: sdbr12                 # Slug do seminário
ojs_id: "692"                     # ID no OJS (se disponível)

# METADADOS BIBLIOGRÁFICOS
titulo: "Título do artigo"
subtitulo: "subtítulo após primeiro dois-pontos"
locale: pt-BR                     # Idioma principal
secao: "Eixo 1 - Nome do eixo"    # Seção/eixo do seminário
paginas: "1-15"                   # Intervalo de páginas

# TÍTULOS EM OUTROS IDIOMAS (opcional)
titulo_en: "English title"
titulo_es: "Título en español"

# AUTORES
autores:
  - givenname: "Nome"
    familyname: "Sobrenome"
    email: "email@exemplo.com"
    affiliation: "SIGLA-UNIVERSIDADE"   # Formato normalizado!
    country: BR                          # ISO 3166-1 alpha-2
    orcid: "0000-0000-0000-0000"        # Sem URL
    bio: "Título acadêmico completo"
    primary_contact: true                # Primeiro autor = true

# RESUMOS
resumo: |
  Texto do resumo em português.

resumo_en: |
  Abstract in English.

resumo_es: |
  Resumen en español.

# PALAVRAS-CHAVE
palavras_chave:
  - palavra 1
  - palavra 2

palavras_chave_en:
  - keyword 1
  - keyword 2

# TEXTO COMPLETO (opcional)
texto: |
  Texto integral extraído do PDF/Word.
  [IMAGEM: img-001.jpg]
  Continuação do texto...

# REFERÊNCIAS BIBLIOGRÁFICAS
referencias:
  - "AUTOR. Título. Local: Editora, Ano."
  - "..."

# FIGURAS DO ARTIGO
figuras:
  - numero: 1
    legenda: "Fig. 1. Descrição completa da figura. Fonte: ..."
    arquivo: "media/image1.jpeg"    # Caminho dentro do docx ou extraído

# ARQUIVOS
arquivo_fonte: "E01-AUTOR, A. Título.docx"            # Nome do Word original
arquivo_pdf_original: "E01-AUTOR, A. Título.pdf"      # Nome do PDF original
arquivo_pdf: "sdbr12-001.pdf"                          # Nome padronizado

# CONTROLE
status: pendente_revisao          # pendente_revisao | revisado | publicado
```

### Convenções de IDs

| Tipo | Formato | Exemplo |
|------|---------|---------|
| Artigo nacional | `sdbr{NN}-{NNN}` | sdbr12-001 |
| Artigo N/NE | `sdnne{NN}-{NNN}` | sdnne07-001 |
| Artigo Sul | `sdsul{NN}-{NNN}` | sdsul03-001 |
| Seminário | `sdbr{NN}` | sdbr12 |

---

## Eixos Temáticos - 12º Seminário (sdbr12)

| Eixo | Título | Artigos |
|------|--------|---------|
| 1 | A recepção e a difusão da arquitetura e urbanismo modernos brasileiros | 61 |
| 2 | Práticas de preservação da arquitetura e do urbanismo modernos | 18 |
| 3 | Práticas (ações e projetos) de Educação Patrimonial | 1 |
| 4 | A formação dos futuros profissionais e a preservação do Movimento Moderno | 2 |

**Total processado:** 82 artigos (2026-02-03)

**Status do processamento:**
- ✅ 82 YAMLs gerados em `nacionais/sdbr12_fontes/yaml/`
- ✅ 82 PDFs padronizados em `nacionais/sdbr12_fontes/pdfs/`
- ✅ Autores estruturados (givenname/familyname) em todos os YAMLs
- ✅ Script XML pronto (`gerar_prototipo_xml.py`)
- ⏳ Teste de importação XML pendente

**Fontes:** `nacionais/sdbr12_fontes/`
- `anais/EIXO {N}/` — PDFs dos artigos
- `anais/EIXO {N} - Versão Word/` — Arquivos .docx (fonte da extração)
- `yaml/` — YAMLs processados (sdbr12-001.yaml a sdbr12-082.yaml)
- `yaml_teste/` — 5 YAMLs de teste (modelo de qualidade)
- `processar_artigos.py` — Script de extração

### Scripts de Processamento (sdbr12_fontes/)

| Script | Função |
|--------|--------|
| `processar_artigos.py` | Extrai texto, figuras e metadados dos .docx para YAML |
| `mapear_pdfs.py` | Mapeia PDFs aos YAMLs por título/autor (81/82 mapeados) |
| `corrigir_titulos.py` | Move título real do subtítulo quando há placeholder |
| `normalizar_maiusculas.py` | Aplica regras FUNAG de capitalização |
| `limpar_autores.py` | Remove lixo do campo autores_raw (endereços, telefones, etc.) |
| `estruturar_autores.py` | Estrutura autores via Claude API (requer créditos) |

---

## Processamento de Autores

### Campo `autores_raw` (dados brutos)

Os arquivos fonte frequentemente misturam nos campos de autor:
- Nomes de pessoas
- Endereços postais (Rua, Av., CEP)
- Telefones (+55, P:, F:)
- Afiliações inline (Universidade X, Faculdade Y)
- Títulos acadêmicos (PhD, MSc, Doutor, Mestrando)
- Placeholders ("Nome Completo Autor", "Instituição, Endereço...")
- ORCID e emails

### Abordagem recomendada

**Scripts de regex têm limitações.** Cada documento tem estrutura diferente. A melhor abordagem é usar LLM para parsear caso a caso:

```python
# Prompt para estruturar autores
prompt = f"""
Extraia os autores desta lista bruta. Retorne JSON estruturado.
autores_raw: {autores_raw}

Formato: [{{"givenname": "...", "familyname": "...", "affiliation": "..."}}]
Ignore endereços, telefones, placeholders. Separe nome/sobrenome no padrão brasileiro.
"""
```

### Separação de nome brasileiro

| Nome completo | givenname | familyname |
|---------------|-----------|------------|
| Maria Beatriz Camargo Cappello | Maria Beatriz Camargo | Cappello |
| Fernando Antonio Oliveira Mello | Fernando Antonio Oliveira | Mello |
| João Carlos da Silva Neto | João Carlos da Silva | Neto |
| Ana Elísia da Costa | Ana Elísia da | Costa |
| Claudia dos Reis e Cunha | Claudia dos Reis e | Cunha |
| Patricia Ataíde Solon de Oliveira | Patricia Ataíde Solon de | Oliveira |

**Regra:** givenname = todos menos o último; familyname = último sobrenome apenas.

**Partículas (de, da, do, dos, das, e):** ficam no `givenname`, não no `familyname`. Isso mantém consistência e evita ambiguidade na ordenação alfabética por sobrenome.

**Nomes hispânicos (duplo sobrenome):** Respeitar a convenção hispânica, mantendo os dois sobrenomes no `familyname`. Ex: `Fernando Guillermo | Vázquez Ramos`, `Pablo Andrés | Maita Zambrano`. Não reduzir a um sobrenome só.

---

## Problemas Conhecidos e Soluções

### YAML: campos desordenados

O `yaml.dump()` ordena alfabeticamente por padrão. Solução:

```python
ORDEM_CAMPOS = ['id', 'seminario', 'secao', 'titulo', 'subtitulo', 'locale',
                'autores_raw', 'autores', 'resumo', 'palavras_chave', ...]

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

### Normalização de maiúsculas (FUNAG)

Listas de referência em `normalizar_maiusculas.py`:

```python
SIGLAS = {'bnh', 'iphan', 'ufmg', 'usp', ...}  # sempre MAIÚSCULAS
NOMES_PROPRIOS = {'niemeyer', 'brasília', 'pedregulho', ...}  # Capitalizar
```

**Subtítulo:** primeira letra minúscula, exceto se for sigla/nome próprio.

---

## Ordem de Processamento dos Seminários Regionais

### Nível 1 - Dados estruturados (Even3)
| Seminário | Fonte | Formato | Status |
|-----------|-------|---------|--------|
| N/NE X - Campina Grande 2024 | Even3 | Metadados + PDFs estruturados | ⬜ Pendente |

### Nível 2 - PDF compilado com sumário
| Seminário | Fonte | Formato | Status |
|-----------|-------|---------|--------|
| Sul 7º - Porto Alegre 2022 | UFRGS PROPAR | PDF único com índice | ⬜ Pendente |
| SP 5º - 2017 | docomomobrasil | e-book com ISBN | ⬜ Pendente |
| SP 6º - 2018 | docomomobrasil | e-book com ISBN | ⬜ Pendente |

### Nível 3 - PDFs individuais organizados
| Seminário | Fonte | Formato | Status |
|-----------|-------|---------|--------|
| Sul 3º - 2010 | UFRGS PROPAR | Artigos individuais | ⬜ Pendente |
| Sul 4º - 2013 | UFRGS PROPAR | Artigos individuais | ⬜ Pendente |
| Sul 5º - 2016 | UFRGS PROPAR | Artigos individuais | ⬜ Pendente |
| Sul 2º - 2008 | docomomobrasil | PDF download | ⬜ Pendente |
| Sul 6º - 2019 | docomomobrasil | PDF download | ⬜ Pendente |
| Rio 1º - 2008 | docomomobrasil | PDF único | ⬜ Pendente |

### Nível 4 - Precisam tratamento manual
| Seminário | Fonte | Problema | Status |
|-----------|-------|----------|--------|
| N/NE 2º - Salvador 2008 | Google Drive | ZIP a extrair | ⬜ Pendente |
| N/NE 5º - Fortaleza 2014 | Docomomo CE | Disperso por eixos | ⬜ Pendente |
| N/NE 6º - Teresina 2016 | docomomobrasil | Só resumos | ⬜ Pendente |

### Já processados ✅
| Seminário | Artigos | Status |
|-----------|---------|--------|
| N/NE 7º - Manaus 2018 | 65 | ✅ Completo |
| N/NE 9º - São Luís 2022 | 50 | ✅ Completo |

### Não localizados (buscar com organizadores)
- N/NE 1º - Recife 2006 (UFPE/UNICAP)
- N/NE 3º - João Pessoa 2010 (UFPB)
- N/NE 4º - Natal 2012 (UFRN)
- N/NE 8º - Palmas 2021 (UFT)
- SP 8º - 2022 (UNIP)
- Rio 2º, 3º, 4º (Núcleo Rio)
- CE 1º, 2º (será incorporado ao N/NE)

---

## Pendências

### 12º Seminário (Uberlândia, 2017) - ✅ IMPORTADO

**Status:** Importação concluída em 2026-02-04 (82 artigos no OJS)

**Referência bibliográfica:**
12° Seminário Docomomo Brasil: anais: arquitetura e urbanismo do movimento moderno: patrimônio cultural brasileiro: difusão, preservação e sociedade [recurso eletrônico] / organização: Maria Beatriz Camargo Cappello e Maria Marta Camisassa. Uberlândia: EDUFU, 2017.
ISBN 978-85-64554-03-0

**Organizadores:** Maria Beatriz Camargo Cappello, Maria Marta Camisassa

**Datas:** 23 a 24 de novembro de 2017

**Capa:** `nacionais/capas/sdbr12.png`

**Seções no OJS** (criadas em 2026-02-03):

| sectionId | Título | Artigos |
|-----------|--------|---------|
| 20 | Eixo 1 - A recepção e a difusão da arquitetura e urbanismo modernos brasileiros | 61 |
| 21 | Eixo 2 - Práticas de preservação da arquitetura e do urbanismo modernos | 18 |
| 22 | Eixo 3 - Práticas (ações e projetos) de Educação Patrimonial | 1 |
| 23 | Eixo 4 - A formação dos futuros profissionais e a preservação do Movimento Moderno | 2 |

**Fontes:** `nacionais/sdbr12_fontes/`

**Progresso:**
- ✅ 82 YAMLs gerados com texto completo, figuras e referências
- ✅ 82 PDFs padronizados em `pdfs/` (sdbr12-001.pdf a sdbr12-082.pdf)
- ✅ sdbr12-007.pdf gerado a partir do .docx (não tinha PDF na fonte)
- ✅ Títulos e subtítulos separados e normalizados (FUNAG)
- ✅ Autores estruturados (givenname/familyname/primary_contact) em todos os 82 YAMLs
- ✅ XMLs gerados (82 lotes, 1 artigo por lote) em `xml_lotes/`
- ✅ **82 artigos importados no OJS** (edição 31, issue sdbr12)

**Fluxo de importação utilizado:**

1. **Geração de YAMLs** (`processar_artigos.py`)
   - Extrai metadados dos .docx (título, autores, resumo, palavras-chave, texto, referências)
   - Mapeia PDFs aos YAMLs por similaridade de título/autor

2. **Estruturação de autores** (manual + LLM)
   - Separa givenname/familyname seguindo convenção brasileira
   - Partículas (de, da, do) ficam no givenname
   - Primeiro autor recebe `primary_contact: true`

3. **Geração de XMLs** (`gerar_xml_lotes.py`)
   - Gera 1 artigo por arquivo XML (limite 20MB)
   - PDFs embutidos em base64 dentro do `<embed>`
   - Seções referenciadas por `section_ref` (E1-sdbr12, E2-sdbr12, etc.)

4. **Upload automático via curl**
   - Login para obter cookies de sessão
   - Upload para `uploadImportXML` (campo `uploadedFile`)
   - Submissão via `importBounce`
   - Confirmação via URL de resultado

**Arquivos gerados:**
- `yaml/*.yaml` - 82 arquivos de metadados
- `pdfs/*.pdf` - 82 PDFs padronizados (sdbr12-001.pdf a sdbr12-082.pdf)
- `xml_lotes/*.xml` - 82 arquivos XML para importação

### Exclusão de 22 PDFs órfãos do servidor

**Status:** ⏳ Pendente (requer acesso ao painel da hospedagem ou FTP)

**Lista de arquivos:** `pdfs_orfaos_pendentes.txt`

### Correção de títulos e subtítulos no OJS

**Status:** ⏳ Pendente (aguardando acesso de Journal Manager)

**Problema:**
- A maioria dos títulos no OJS está em CAIXA ALTA
- Subtítulos não estão separados (concatenados com `:` no título)

---

*Última atualização: 2026-02-04 (12º Seminário importado - 82 artigos)*
