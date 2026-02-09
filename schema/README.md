# Schema de Metadados - Anais Docomomo Brasil

Este diretório define o padrão de metadados para artigos e seminários dos Anais Docomomo Brasil.

## Objetivos

1. **Interoperabilidade com OJS** — campos mapeados para Native XML Plugin
2. **Alimentar momopedia_br** — dados estruturados para a enciclopédia
3. **Arquivamento completo** — inclui texto integral e imagens
4. **Processamento automatizado** — flags de status e qualidade

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `artigo.yaml` | Schema completo de um artigo |
| `seminario.yaml` | Schema de uma edição (issue/seminário) |

## Mapeamento OJS Native XML

### Issue (Seminário)

| Campo YAML | Campo OJS XML | Notas |
|------------|---------------|-------|
| `slug` | — | ID interno, não vai para OJS |
| `titulo` | `<title locale="pt_BR">` | Título da edição |
| `subtitulo` | — | Concatenar com título se necessário |
| `descricao` | `<description locale="pt_BR">` | Descrição da edição |
| `ano` | `<year>` | Ano de publicação |
| `volume` | `<volume>` | Número do volume |
| `numero` | `<number>` | Número da edição |
| `data_publicacao` | `<date_published>` | Formato: YYYY-MM-DD |
| `doi` | `<id type="doi">` | DOI da edição |

### Article (Artigo)

| Campo YAML | Campo OJS XML | Notas |
|------------|---------------|-------|
| `id` | — | ID interno |
| `ojs_id` | `<id type="internal">` | ID no OJS |
| `titulo` | `<title locale="pt_BR">` | Título do artigo |
| `subtitulo` | `<subtitle locale="pt_BR">` | Subtítulo |
| `titulo_en` | `<title locale="en_US">` | Título em inglês |
| `locale` | `locale="pt_BR"` | Atributo do elemento `<article>` |
| `secao` | `section_ref="artigos"` | Atributo do elemento `<article>` |
| `paginas` | `<pages>` | Intervalo: "1-15" |
| `resumo` | `<abstract locale="pt_BR">` | Resumo em português |
| `resumo_en` | `<abstract locale="en_US">` | Resumo em inglês |
| `palavras_chave` | `<keywords locale="pt_BR"><keyword>` | Lista de keywords |
| `doi` | `<id type="doi">` | DOI do artigo |

### Author (Autor)

| Campo YAML | Campo OJS XML | Notas |
|------------|---------------|-------|
| `givenname` | `<givenname locale="pt_BR">` | Nome |
| `familyname` | `<familyname locale="pt_BR">` | Sobrenome |
| `email` | `<email>` | Email (obrigatório OJS) |
| `affiliation` | `<affiliation locale="pt_BR">` | Instituição |
| `country` | `<country>` | Código ISO: BR, PT, US |
| `orcid` | `<orcid>` | Formato: https://orcid.org/0000-... |
| `bio` | `<biography locale="pt_BR">` | Biografia curta |
| `primary_contact` | `primary_contact="true"` | Autor de correspondência |

### Galley (Arquivo PDF)

| Campo YAML | Campo OJS XML | Notas |
|------------|---------------|-------|
| `arquivos.pdf.url` | `<remote src="URL"/>` | URL do PDF |
| `arquivos.pdf.nome` | `<name locale="pt_BR">` | Nome do arquivo |

## Campos Exclusivos (não OJS)

Estes campos são específicos do nosso sistema e não vão para o OJS:

| Campo | Descrição | Uso |
|-------|-----------|-----|
| `texto` | Texto integral extraído | Análise, busca, momopedia |
| `referencias` | Lista de referências | Normalização bibliográfica |
| `imagens` | Imagens extraídas | Galeria, verbetes |
| `entidades` | Entidades relacionadas | momopedia_br |
| `status` | Status de processamento | Pipeline |
| `flags` | Flags de qualidade | Controle |

## Fluxo de Dados

```
PDF do artigo
    ↓ pdftotext / pdfimages
Texto + Imagens extraídos
    ↓ parser
YAML completo (este schema)
    ↓
    ├─→ OJS (Native XML) — metadados bibliográficos
    ├─→ momopedia_br — texto + entidades + refs
    └─→ Arquivo local — backup completo
```

## Convenções

### Nomes de campos

- **Português sem acento**: `titulo`, `resumo`, `paginas`, `secao`
- **Underscore para compostos**: `palavras_chave`, `data_publicacao`
- **Sufixo de idioma**: `_en`, `_es` para traduções

### Valores

- **Texto**: UTF-8 com acentos e cedilha
- **Datas**: ISO 8601 (YYYY-MM-DD)
- **Locale**: BCP-47 (pt-BR, en-US, es-ES)
- **País**: ISO 3166-1 alpha-2 (BR, PT, US)
- **ORCID**: Apenas números (0000-0001-2345-6789), sem URL

### IDs

- **Artigo**: `sdbr{NN}-{NNN}` (ex: sdbr15-001)
- **Seminário**: `sdbr{NN}` (nacional) ou `sdnne{NN}`, `sdsul{NN}` (regional)

## Exemplo de Uso

### Carregar YAML em Python

```python
import yaml

with open('data/artigos/sdbr15-001.yaml', 'r') as f:
    artigo = yaml.safe_load(f)

print(artigo['titulo'])
print(artigo['autores'][0]['familyname'])
print(artigo['resumo'][:100])
```

### Gerar XML para OJS

```python
from lxml import etree

def artigo_to_xml(artigo):
    article = etree.Element('article',
        locale=artigo['locale'].replace('-', '_'),
        section_ref=artigo['secao'].lower().replace(' ', '-')
    )

    title = etree.SubElement(article, 'title',
        locale=artigo['locale'].replace('-', '_'))
    title.text = artigo['titulo']

    if artigo.get('subtitulo'):
        subtitle = etree.SubElement(article, 'subtitle',
            locale=artigo['locale'].replace('-', '_'))
        subtitle.text = artigo['subtitulo']

    # ... (continua para outros campos)

    return article
```

## Versionamento

- **Versão atual**: 1.0
- **Data**: 2026-02-03
- **Changelog**:
  - 1.0: Versão inicial com schema completo

## Referências

- [OJS Native XML Plugin](https://docs.pkp.sfu.ca/admin-guide/en/data-import-and-export)
- [OJS 3 XML Template Examples](https://github.com/gontsa/ojs3-import-xml-template)
- [Dublin Core Metadata](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/)
